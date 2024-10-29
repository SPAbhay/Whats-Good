from typing import List, Dict, Any
from langchain_community.vectorstores import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from pinecone import Pinecone as PineconeClient
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class DynamicFewShotLearner:
    def __init__(self, index_name: str = "articles", namespace: str = "Whats-Good"):
        """Initialize Dynamic Few Shot Learner"""
        load_dotenv()

        self.pc = PineconeClient(api_key=os.getenv('PINECONE_API_KEY'))
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.llm = OllamaLLM(model="mistral", temperature=0.2)

        self.index_name = index_name
        self.namespace = namespace
        self.vector_store = Pinecone.from_existing_index(
            index_name=self.index_name,
            embedding=self.embeddings,
            namespace=self.namespace
        )

        # Store successful examples
        self.examples = []

        self.setup_logging()
        self.setup_prompts()

    def setup_logging(self):
        """Setup logging configuration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        logging.basicConfig(
            filename=f'few_shot_{timestamp}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def setup_prompts(self):
        """Setup prompts for dynamic learning"""
        self.few_shot_prompt = PromptTemplate(
            template="""
            You are helping find relevant content for brands based on their descriptions.
            Here are some examples of successful matches:

            {examples}

            Given these examples, help find relevant content for this new brand:
            Brand Description: {brand_description}
            Primary Categories: {categories}

            Based on the patterns in successful examples, generate a search query that will find 
            similar relevant content for this brand. Focus on key aspects that made previous 
            matches successful.

            Query:
            """,
            input_variables=["examples", "brand_description", "categories"]
        )

    def add_example(self,
                    brand_description: str,
                    matched_content: Dict[str, Any],
                    relevance_score: float) -> None:
        """
        Add a successful example to the learner

        Args:
            brand_description: Original brand description
            matched_content: Content that was successfully matched
            relevance_score: How relevant the match was (0-1)
        """
        if relevance_score >= 0.7:  # Only store high-quality matches
            example = {
                'brand_description': brand_description,
                'content': matched_content,
                'score': relevance_score,
                'timestamp': datetime.now().isoformat()
            }
            self.examples.append(example)
            logging.info(f"Added new example with score {relevance_score}")

    def format_examples(self, category_weights: Dict[str, float], num_examples: int = 3) -> str:
        """Format examples for few-shot learning"""
        if not self.examples:
            return "No examples available yet."

        # Filter examples relevant to current categories
        relevant_examples = []
        for example in self.examples:
            content_category = example['content'].get('category', 'unknown')
            if category_weights.get(content_category, 0) > 0.5:
                relevant_examples.append(example)

        # Sort by score and recency
        relevant_examples.sort(
            key=lambda x: (x['score'], x['timestamp']),
            reverse=True
        )

        # Format top examples
        formatted_examples = []
        for example in relevant_examples[:num_examples]:
            formatted_example = (
                f"Brand: {example['brand_description']}\n"
                f"Matched Content: {example['content']['title']}\n"
                f"Category: {example['content']['category']}\n"
                f"Why it worked: This content matched the brand's focus on "
                f"{example['content']['category']} and provided relevant information.\n"
            )
            formatted_examples.append(formatted_example)

        return "\n---\n".join(formatted_examples)

    def generate_learned_query(self,
                               brand_description: str,
                               category_weights: Dict[str, float]) -> str:
        """Generate a query using learned examples"""
        try:
            # Format examples for few-shot learning
            examples_text = self.format_examples(category_weights)

            # Get primary categories
            primary_cats = [
                cat for cat, weight in category_weights.items()
                if weight > 0.5
            ]
            categories_str = ", ".join(primary_cats)

            # Generate query using few-shot learning
            response = self.llm.invoke(
                self.few_shot_prompt.format(
                    examples=examples_text,
                    brand_description=brand_description,
                    categories=categories_str
                )
            )

            return str(response).strip()

        except Exception as e:
            logging.error(f"Error generating learned query: {str(e)}")
            return ""

    def compute_similarity_to_examples(self,
                                       content: Dict[str, Any],
                                       category_weights: Dict[str, float]) -> float:
        """
        Compute similarity between content and successful examples
        """
        if not self.examples:
            return 1.0  # No examples to compare against

        similarities = []
        for example in self.examples:
            # Category similarity
            category_match = (
                    content.get('category') == example['content'].get('category')
            )
            category_weight = category_weights.get(content.get('category'), 0.1)

            # Compute embedding similarity with example content
            try:
                content_embedding = self.embeddings.embed_query(content.get('summary', ''))
                example_embedding = self.embeddings.embed_query(
                    example['content'].get('summary', '')
                )

                # Compute cosine similarity
                similarity = sum(
                    a * b for a, b in zip(content_embedding, example_embedding)
                ) / (
                                     (sum(a * a for a in content_embedding) ** 0.5) *
                                     (sum(b * b for b in example_embedding) ** 0.5)
                             )

                # Combine similarities
                weighted_similarity = (
                        similarity * 0.7 +  # Content similarity weight
                        (1.0 if category_match else 0.0) * 0.3 *  # Category match weight
                        category_weight  # Category importance weight
                )

                similarities.append(weighted_similarity)

            except Exception as e:
                logging.error(f"Error computing similarity: {str(e)}")
                continue

        return max(similarities) if similarities else 1.0

    def search_with_learning(self,
                             brand_description: str,
                             category_weights: Dict[str, float],
                             top_k: int = 3) -> List[Dict]:
        """
        Search for content using learned patterns
        """
        try:
            # Generate query using few-shot learning
            query = self.generate_learned_query(brand_description, category_weights)
            if not query:
                return []

            # Get initial results
            docs = self.vector_store.similarity_search(
                query=query,
                k=top_k * 3
            )

            # Process and weight results
            results = []
            for doc in docs:
                try:
                    category = doc.metadata.get('category', 'unknown')
                    category_weight = category_weights.get(category, 0.1)

                    # Create result dict
                    result = {
                        'article_id': doc.metadata.get('article_id'),
                        'title': doc.metadata.get('title', ''),
                        'category': category,
                        'summary': doc.page_content,
                        'category_weight': category_weight,
                        'metadata': doc.metadata
                    }

                    # Compute similarity to successful examples
                    example_similarity = self.compute_similarity_to_examples(
                        result, category_weights
                    )

                    # Combined score
                    result['final_score'] = category_weight * example_similarity
                    results.append(result)

                except Exception as doc_error:
                    logging.error(f"Error processing document: {str(doc_error)}")
                    continue

            # Sort by final score and return top_k
            results.sort(key=lambda x: x['final_score'], reverse=True)
            return results[:top_k]

        except Exception as e:
            logging.error(f"Error in search with learning: {str(e)}")
            return []


def main():
    """Example usage of Dynamic Few-Shot Learner"""
    try:
        learner = DynamicFewShotLearner()

        # Example brand profile
        brand_description = """
        We are a healthcare technology startup focusing on developing AI-powered diagnostic tools.
        Our main focus is on improving patient care through innovative technology solutions.
        We also provide data analytics services to healthcare providers for better decision making.
        """

        category_weights = {
            "healthcare": 1.0,
            "technology": 0.9,
            "science": 0.7,
            "business": 0.5
        }

        # First search without any examples
        print("\nSearching without examples...")
        initial_results = learner.search_with_learning(
            brand_description=brand_description,
            category_weights=category_weights
        )

        # Add some results as examples (simulating user feedback)
        for result in initial_results[:2]:  # Add top 2 as positive examples
            learner.add_example(
                brand_description=brand_description,
                matched_content=result,
                relevance_score=0.8  # Simulated high relevance
            )

        # Search again with learned examples
        print("\nSearching with learned examples...")
        learned_results = learner.search_with_learning(
            brand_description=brand_description,
            category_weights=category_weights
        )

        # Display results
        print("\nResults after learning:")
        for i, result in enumerate(learned_results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"Category: {result['category']} (weight: {result['category_weight']:.2f})")
            print(f"Final Score: {result['final_score']:.2f}")
            print(f"Summary: {result['summary'][:200]}...")

    except Exception as e:
        logging.error(f"Error in main: {str(e)}")


if __name__ == "__main__":
    main()
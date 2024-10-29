from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo
from langchain_core.prompts import PromptTemplate
from pinecone import Pinecone as PineconeClient
import logging
from datetime import datetime
import os
from dotenv import load_dotenv


class SelfQueryingEngine:
    def __init__(self, index_name: str = "articles", namespace: str = "Whats-Good"):
        """Initialize Self Querying Engine"""
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

        self.metadata_field_info = [
            AttributeInfo(
                name="category",
                description="The category of the article",
                type="string"
            ),
            AttributeInfo(
                name="title",
                description="The title of the article",
                type="string"
            ),
            AttributeInfo(
                name="summary_word_count",
                description="Number of words in the article summary",
                type="integer"
            ),
        ]

        self.setup_logging()
        self.setup_retriever()

    def setup_logging(self):
        """Setup logging configuration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        logging.basicConfig(
            filename=f'self_query_{timestamp}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def setup_retriever(self):
        """Setup the self-querying retriever"""
        try:
            sample_docs = self.vector_store.similarity_search(query="", k=3)
            document_contents = [doc.page_content for doc in sample_docs]

            self.retriever = SelfQueryRetriever.from_llm(
                llm=self.llm,
                vectorstore=self.vector_store,
                document_content_description=(
                    "Articles about technology, healthcare, business, and science, "
                    "focusing on innovations, developments, and industry trends."
                ),
                metadata_field_info=self.metadata_field_info,
                document_contents=document_contents,
                verbose=False
            )

        except Exception as e:
            logging.error(f"Error setting up retriever: {str(e)}")
            raise

    def process_query(self, query: str, category_weights: Dict[str, float], top_k: int = 3) -> List[Dict]:
        """Process a natural language query with category weights"""
        try:
            docs = self.vector_store.similarity_search(query=query, k=top_k * 3)
            results = []

            for doc in docs:
                try:
                    category = doc.metadata.get('category', 'unknown')
                    category_weight = category_weights.get(category, 0.1)

                    result = {
                        'article_id': doc.metadata.get('article_id'),
                        'title': doc.metadata.get('title', ''),
                        'category': category,
                        'summary': doc.page_content,
                        'category_weight': category_weight,
                        'metadata': doc.metadata
                    }
                    results.append(result)

                except Exception as doc_error:
                    logging.error(f"Error processing document: {str(doc_error)}")
                    continue

            results.sort(key=lambda x: x['category_weight'], reverse=True)
            return results[:top_k]

        except Exception as e:
            logging.error(f"Error in query processing: {str(e)}")
            return []

    def generate_structured_query(self, brand_description: str, category_weights: Dict[str, float]) -> str:
        """Generate a structured query from brand description"""
        try:
            prompt = PromptTemplate(
                template="""
                Given a brand description and category interests, generate a focused search query.
                The query should be natural and focused on the key concepts, without mentioning specific
                categories or weights.

                Brand Description: {description}
                Primary Categories: {categories}

                Generate a search query that will find relevant articles for this brand.
                Focus on the main business aspects and technology areas.
                Keep it under 50 words and make it focused on finding relevant content.

                Query:
                """,
                input_variables=["description", "categories"]
            )

            primary_cats = [cat for cat, weight in category_weights.items() if weight > 0.5]
            categories_str = ", ".join(primary_cats)

            response = self.llm.invoke(
                prompt.format(
                    description=brand_description,
                    categories=categories_str
                )
            )
            return str(response).strip()

        except Exception as e:
            logging.error(f"Error generating structured query: {str(e)}")
            return ""


def main():
    """Main execution function"""
    try:
        engine = SelfQueryingEngine()

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

        query = engine.generate_structured_query(brand_description, category_weights)
        if query:
            results = engine.process_query(query, category_weights, top_k=3)

            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['title']}")
                print(f"Category: {result['category']} (weight: {result['category_weight']:.2f})")
                print(f"Summary: {result['summary'][:200]}...")

    except Exception as e:
        logging.error(f"Error in main execution: {str(e)}")


if __name__ == "__main__":
    main()
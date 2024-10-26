from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
# from langchain.retrievers import BM25Retriever, EnsembleRetriever
# from langchain_core.documents import Document
from pinecone import Pinecone as PineconeClient
import numpy as np
from rank_bm25 import BM25Okapi
import logging
from datetime import datetime
from tqdm import tqdm
import os
from dotenv import load_dotenv
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

class HybridSearchEngine:
    def __init__(self, index_name: str = "articles", namespace: str = "Whats-Good"):
        """
                Initialize Hybrid Search Engine combining vector and keyword search
                """
        # Load environment variables
        load_dotenv()

        # Download required NLTK data
        nltk.download('punkt')
        nltk.download('stopwords')

        # Initialize Pinecone client
        self.pc = PineconeClient(api_key=os.getenv('PINECONE_API_KEY'))

        # Initialize embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # Initialize vector store
        self.index_name = index_name
        self.namespace = namespace
        self.vector_store = Pinecone.from_existing_index(
            namespace=self.namespace,
            index_name=self.index_name,
            embedding=self.embeddings
        )

        # Initialize BM25 components
        self.bm25_index = None
        self.doc_store = []
        self.initialize_bm25()

        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        logging.basicConfig(
            filename=f'hybrid_search_{timestamp}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def initialize_bm25(self):
        """Initialize BM25 index with existing documents"""
        try:
            # Fetch all documents from vector store
            docs = self.vector_store.similarity_search_with_score("", k=10000)

            # Prepare documents for BM25
            tokenized_docs = []
            for doc, _ in docs:
                self.doc_store.append(doc)
                tokens = self._preprocess_text(doc.page_content)
                tokenized_docs.append(tokens)

            if tokenized_docs:
                # Create BM25 index only if there are documents
                self.bm25_index = BM25Okapi(tokenized_docs)
            else:
                logging.warning("BM25 index could not be initialized - no documents found.")

        except Exception as e:
            logging.error(f"Error initializing BM25: {str(e)}")
            raise

    def _preprocess_text(self, text: str) -> List[str]:
        """Preprocess text for BM25 indexing"""
        # Tokenize and remove stopwords
        stop_words = set(stopwords.words('english'))
        tokens = word_tokenize(text.lower())
        return [token for token in tokens if token.isalnum() and token not in stop_words]

    def hybrid_search(self,
                      query: str,
                      category_weights: Dict[str, float],
                      top_k: int = 5,
                      vector_weight: float = 0.7,
                      keyword_weight: float = 0.3) -> List[Dict]:
        """
        Perform hybrid search combining vector similarity and keyword matching

        Args:
            query: Search query
            category_weights: Dictionary of category weights
            top_k: Number of results to return
            vector_weight: Weight for vector similarity scores (0-1)
            keyword_weight: Weight for keyword matching scores (0-1)
        """
        try:
            # Validate weights
            if not np.isclose(vector_weight + keyword_weight, 1.0):
                raise ValueError("Vector and keyword weights must sum to 1.0")

            # Get more initial results for better hybrid ranking
            initial_k = min(top_k * 5, 100)

            # Vector search
            vector_results = self.vector_store.similarity_search_with_score(
                query=query,
                k=initial_k
            )

            # Keyword search
            preprocessed_query = self._preprocess_text(query)
            bm25_scores = self.bm25_index.get_scores(preprocessed_query)

            # Normalize BM25 scores
            if self.bm25_index is None or not bm25_scores.any():
                # Set BM25 scores to zero if no documents exist or scores are all zeros
                normalized_bm25_scores = np.zeros_like(bm25_scores)
            else:
                max_bm25_score = np.max(bm25_scores)
                if max_bm25_score > 0:
                    normalized_bm25_scores = bm25_scores / max_bm25_score
                else:
                    normalized_bm25_scores = np.zeros_like(bm25_scores)

            # Combine results
            hybrid_results = []
            for i, (doc, vector_score) in enumerate(vector_results):
                metadata = doc.metadata
                category = metadata.get('category', 'unknown')

                # Get BM25 score
                bm25_score = normalized_bm25_scores[self.doc_store.index(doc)]

                # Calculate hybrid score
                vector_similarity = 1 - vector_score  # Convert distance to similarity
                hybrid_score = (
                        vector_weight * vector_similarity +
                        keyword_weight * bm25_score
                )

                # Apply category weight
                category_weight = category_weights.get(category, 0.1)
                final_score = hybrid_score * category_weight

                hybrid_results.append({
                    'article_id': metadata.get('article_id'),
                    'title': metadata.get('title'),
                    'category': category,
                    'summary': metadata.get('summary'),
                    'vector_score': vector_similarity,
                    'keyword_score': bm25_score,
                    'hybrid_score': hybrid_score,
                    'category_weight': category_weight,
                    'final_score': final_score
                })

            # Sort by final score and return top_k results
            hybrid_results.sort(key=lambda x: x['final_score'], reverse=True)
            return hybrid_results[:top_k]

        except Exception as e:
            logging.error(f"Error in hybrid search: {str(e)}")
            return []

    def adjust_search_weights(self,
                              query: str,
                              results: List[Dict],
                              relevance_feedback: List[bool]) -> tuple:
        """
        Adjust search weights based on relevance feedback

        Args:
            query: Original search query
            results: Previous search results
            relevance_feedback: List of boolean values indicating relevance

        Returns:
            tuple: (new_vector_weight, new_keyword_weight)
        """
        try:
            if len(results) != len(relevance_feedback):
                raise ValueError("Results and feedback must have same length")

            relevant_results = [
                result for result, is_relevant in zip(results, relevance_feedback)
                if is_relevant
            ]

            if not relevant_results:
                return (0.7, 0.3)  # Default weights if no relevant results

            # Calculate average scores for relevant results
            avg_vector = np.mean([r['vector_score'] for r in relevant_results])
            avg_keyword = np.mean([r['keyword_score'] for r in relevant_results])

            # Adjust weights based on which method was more successful
            total = avg_vector + avg_keyword
            if total == 0:
                return (0.7, 0.3)

            vector_weight = avg_vector / total
            keyword_weight = avg_keyword / total

            return (vector_weight, keyword_weight)

        except Exception as e:
            logging.error(f"Error adjusting weights: {str(e)}")
            return (0.7, 0.3)


def main():
    """Example usage of HybridSearchEngine"""

    try:
        # Initialize search engine
        search_engine = HybridSearchEngine()

        # Example brand profile
        brand_profile = {
            "query": "AI-driven healthcare solutions for hospitals",
            "weights": {
                "healthcare": 1.0,
                "technology": 0.8,
                "science": 0.7,
                "business": 0.5
            }
        }

        # Perform initial search
        print("\nPerforming hybrid search...")
        results = search_engine.hybrid_search(
            query=brand_profile["query"],
            category_weights=brand_profile["weights"],
            top_k=3,
            vector_weight=0.7,
            keyword_weight=0.3
        )

        # Display results
        print("\nSearch Results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"Category: {result['category']}")
            print(f"Vector Score: {result['vector_score']:.4f}")
            print(f"Keyword Score: {result['keyword_score']:.4f}")
            print(f"Hybrid Score: {result['hybrid_score']:.4f}")
            print(f"Final Score: {result['final_score']:.4f}")

        # Example of weight adjustment based on feedback
        print("\nAdjusting weights based on feedback...")
        feedback = [True, True, False]  # Example relevance feedback
        new_weights = search_engine.adjust_search_weights(
            brand_profile["query"],
            results,
            feedback
        )
        print(f"Adjusted weights - Vector: {new_weights[0]:.2f}, Keyword: {new_weights[1]:.2f}")

    except Exception as e:
        print(f"Error in main: {str(e)}")


if __name__ == "__main__":
    main()

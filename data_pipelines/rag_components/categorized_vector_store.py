from langchain_community.vectorstores import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone as PineconeClient
from typing import List, Dict, Any
import logging
from datetime import datetime
from tqdm import tqdm
import os
from dotenv import load_dotenv

load_dotenv()


class CategorizedVectorStore:
    def __init__(self, index_name: str = "articles", namespace: str = "Whats-Good"):
        """
        Initialize Categorized Vector Store using LangChain and Pinecone
        """
        # Load environment variables
        load_dotenv()

        # Initialize Pinecone client
        self.pc = PineconeClient(api_key=os.getenv('PINECONE_API_KEY'))

        # Initialize embedding model using LangChain
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # Define available categories
        self.categories = [
            "technology", "healthcare", "lifestyle", "business",
            "finance", "entertainment", "sports", "science",
            "education", "environment"
        ]

        # Setup index
        self.index_name = index_name
        self.namespace = namespace  # Specify the namespace
        dimension = 384  # all-MiniLM-L6-v2 dimension

        # Check if the index exists; create it if not, in the specified namespace.
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric="cosine"
            )

        # Initialize LangChain's Pinecone vector store with the specified namespace
        self.vector_store = Pinecone.from_existing_index(
            index_name=self.index_name,
            embedding=self.embeddings,
            namespace=self.namespace  # Use the specified namespace here
        )

        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        logging.basicConfig(
            filename=f'vector_store_{timestamp}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def add_articles(self, articles: List[Dict[str, Any]]) -> None:
        """
        Add articles to Pinecone index with their categories in the specified namespace.
        """
        try:
            # Prepare texts and metadata for batch upsert
            texts = []
            metadatas = []
            ids = []

            for article in tqdm(articles, desc="Preparing articles"):
                summary = article.get('summarized', {}).get('content', '')
                if not summary:
                    continue

                metadata = {
                    'article_id': article['article_id'],
                    'title': article.get('cleaned', {}).get('title', ''),
                    'category': article.get('category', 'unknown'),
                    'summary': summary,
                    'original_word_count': article.get('summarized', {}).get('metadata', {}).get('original_word_count',
                                                                                                 0),
                    'summary_word_count': article.get('summarized', {}).get('metadata', {}).get('summary_word_count', 0)
                }

                texts.append(summary)
                metadatas.append(metadata)
                ids.append(article['article_id'])

            # Add to vector store in batches within the specified namespace
            batch_size = 100
            for i in tqdm(range(0, len(texts), batch_size), desc="Adding to vector store"):
                batch_texts = texts[i:i + batch_size]
                batch_metadata = metadatas[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]

                self.vector_store.add_texts(
                    texts=batch_texts,
                    metadatas=batch_metadata,
                    ids=batch_ids,
                    namespace=self.namespace  # Ensure to specify the namespace here as well
                )

        except Exception as e:
            logging.error(f"Error in add_articles: {str(e)}")
            raise

    def search_similar_articles(self,
                                brand_identity: str,
                                category_weights: Dict[str, float],
                                top_k: int = 5) -> List[Dict]:
        """
        Search for similar articles based on brand identity and dynamic category weights.
        """
        try:
            # Validate category weights
            for category in category_weights:
                if category not in self.categories:
                    raise ValueError(f"Invalid category: {category}")
                if not 0 <= category_weights[category] <= 1:
                    raise ValueError(f"Weight for {category} must be between 0 and 1")

            # Get more results initially for better filtering
            initial_k = min(top_k * 3, 100)

            # Perform similarity search within the specified namespace
            results = self.vector_store.similarity_search_with_score(
                query=brand_identity,
                k=initial_k,
                namespace=self.namespace  # Use the specified namespace here as well
            )

            # Process and weight results
            processed_results = []
            for doc, score in results:
                metadata = doc.metadata
                category = metadata.get('category', 'unknown')
                similarity_score = 1 - score  # Convert score to similarity (Pinecone returns distance)

                category_weight = category_weights.get(category, 0.1)
                weighted_score = similarity_score * category_weight

                processed_results.append({
                    'article_id': metadata.get('article_id'),
                    'title': metadata.get('title'),
                    'category': category,
                    'summary': metadata.get('summary'),
                    'similarity_score': similarity_score,
                    'category_weight': category_weight,
                    'weighted_score': weighted_score
                })

            processed_results.sort(key=lambda x: x['weighted_score'], reverse=True)
            return processed_results[:top_k]

        except Exception as e:
            logging.error(f"Error in search: {str(e)}")
            return []


if __name__ == '__main__':
    sample_articles = [
        {
            "article_id": "tech001",
            "cleaned": {"title": "AI Advances in 2024"},
            "summarized": {
                "content": "Recent developments in artificial intelligence show promising results in natural language processing and computer vision. Researchers have achieved breakthrough performance in multiple benchmarks.",
                "metadata": {"original_word_count": 500, "summary_word_count": 150}
            },
            "category": "technology"
        },
        {
            "article_id": "bus001",
            "cleaned": {"title": "Business Strategy Innovation"},
            "summarized": {
                "content": "Companies are adopting new business models integrating AI and data analytics. The transformation is leading to increased efficiency and market competitiveness.",
                "metadata": {"original_word_count": 450, "summary_word_count": 140}
            },
            "category": "business"
        },
        {
            "article_id": "health001",
            "cleaned": {"title": "Healthcare Innovation"},
            "summarized": {
                "content": "New medical devices and AI-driven diagnostics are revolutionizing patient care. Hospitals are seeing improved outcomes with these technologies.",
                "metadata": {"original_word_count": 400, "summary_word_count": 130}
            },
            "category": "healthcare"
        }
    ]

    try:
        # Initialize vector store with a specific namespace
        store = CategorizedVectorStore(namespace="Whats-Good")

        # Add sample articles
        print("Adding sample articles...")
        store.add_articles(sample_articles)

        # Test different brand profiles
        print("\nTesting different brand profiles...")

        brand_profiles = [
            {
                "identity": "We are a healthcare technology company focusing on AI-driven medical solutions",
                "weights": {
                    "healthcare": 1.0,
                    "technology": 0.8,
                    "science": 0.7,
                    "business": 0.5
                },
                "name": "HealthTech Company"
            },
        ]

        for profile in brand_profiles:
            print(f"\nSearching for {profile['name']}...")
            results = store.search_similar_articles(
                profile['identity'],
                profile['weights'],
                top_k=3
            )

            print(f"\nResults for {profile['name']}:")
            for r in results:
                print(f"\nArticle ID: {r['article_id']}")
                print(f"\nTitle: {r['title']}")
                print(f"Category: {r['category']}")
                print(f"Base Similarity: {r['similarity_score']:.4f}")
                print(f"Category Weight: {r['category_weight']:.4f}")
                print(f"Weighted Score: {r['weighted_score']:.4f}")

    except Exception as e:
        print(f"Error in main: {str(e)}")
from typing import List, Dict, Any, Optional
from hyde_retriever import HyDERetriever
from self_querying_retriever import SelfQueryingEngine
from dynamic_few_shot_learner import DynamicFewShotLearner
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

class AdaptiveRetrievalSystem:
    def __init__(self, index_name: str="articles", namespace: str="Whats-Good"):
        # Initialize base components
        self.hyde_retriever = HyDERetriever(index_name, namespace)
        self.self_query_engine = SelfQueryingEngine(index_name, namespace)
        self.few_shot_learner = DynamicFewShotLearner(index_name, namespace)

        # Strategy performance tracking
        self.strategy_performance = {
            'hyde': {'success_rate': 0.5, 'uses': 0},
            'self_query': {'success_rate': 0.5, 'uses': 0},
            'few_shot': {'success_rate': 0.5, 'uses': 0}
        }

        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        logging.basicConfig(
            filename=f'adaptive_retrieval_{timestamp}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def select_strategy(self, brand_description: str, category_weights: Dict[str, float]) -> str:
        """
        Select the best retrieval strategy based on context and past performance
        """

        try:
            scores = {
                'hyde': self._calculate_hyde_score(brand_description, category_weights),
                'self_query': self._calculate_self_query(brand_description, category_weights),
                'few_shot': self._calculate_few_shot_score(brand_description, category_weights)
            }

            strategy = max(scores.items(), key=lambda x: x[1])[0]
            logging.info(f"Selected strategy: {strategy} with scores {scores}")

            return strategy
        except Exception as e:
            logging.error(f"Error selecting strategy: {str(e)}")
            return 'self_query'

    def _calculate_hyde_score(self, brand_description: str, category_weights: Dict[str, float]) -> float:
        """Calculate score for HyDE strategy"""
        score = self.strategy_performance['hyde']['success_rate']

        # HyDE works well with detailed brand descriptions
        if len(brand_description.split()) > 50:
            score += 0.2

            # HyDE works well with multiple important categories
            important_categories = len([w for w in category_weights.values() if w > 0.7])
            if important_categories >= 2:
                score += 0.1

            return score

    def _calculate_self_query_score(self, brand_description: str, category_weights: Dict[str, float]) -> float:
        """Calculate score for Self-Query strategy"""
        score = self.strategy_performance['self_query']['success_rate']

        # Self-query works well with specific category focus
        if max(category_weights.values()) > 0.8:
            score += 0.2

        # Self-query works well with moderate description length
        if 20 <= len(brand_description.split()) <= 100:
            score += 0.1

        return score

    def _calculate_few_shot_score(self, brand_description: str, category_weights: Dict[str, float]) -> float:
        """Calculate score for Few-Shot strategy"""
        score = self.strategy_performance['few_shot']['success_rate']

        # Few-shot works better with more examples
        if len(self.few_shot_learner.examples) > 5:
            score += 0.2

        # Few-shot works well with balanced category weights
        weight_variance = self._calculate_weight_variance(category_weights)
        if weight_variance < 0.1:
            score += 0.1

        return score

    def _calculate_weight_variance(self, weights: Dict[str, float]) -> float:
        """Calculate variance of category weights"""
        values = list(weights.values())
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance

    def update_strategy_performance(self, strategy: str, success: bool):
        """Update strategy performance tracking"""
        perf = self.strategy_performance[strategy]
        perf['uses'] += 1
        perf['success_rate'] = (
                (perf['success_rate'] * (perf['uses'] - 1) + (1.0 if success else 0.0))
                / perf['uses']
        )

    def retrieve(self,
                 brand_description: str,
                 category_weights: Dict[str, float],
                 top_k: int = 3) -> List[Dict]:
        """
        Main retrieval method using adaptive strategy selection
        """
        try:
            strategy = self.select_strategy(brand_description, category_weights)
            logging.info(f"Using strategy: {strategy}")

            results = []
            if strategy == 'hyde':
                # Generate hypothetical documents and search
                hyde_doc = self.hyde_retriever.generate_hypothetical_document(
                    brand_description, category_weights
                )
                results = self.hyde_retriever.search_similar_articles(
                    hyde_doc, category_weights, top_k
                )

            elif strategy == 'self_query':
                # Use self-query engine
                query = self.self_query_engine.generate_structured_query(
                    brand_description, category_weights
                )
                results = self.self_query_engine.process_query(
                    query, category_weights, top_k
                )

            else:  # few_shot
                # Use few-shot learning
                results = self.few_shot_learner.search_with_learning(
                    brand_description, category_weights, top_k
                )

            # Add strategy information to results
            for result in results:
                result['retrieval_strategy'] = strategy

            return results

        except Exception as e:
            logging.error(f"Error in retrieval: {str(e)}")
            return []

    def provide_feedback(self, results: List[Dict], relevant_ids: List[str]):
        """
        Provide feedback on retrieval results
        """
        try:
            if not results:
                return

            # Calculate success rate
            relevant_count = sum(
                1 for r in results
                if r.get('article_id') in relevant_ids
            )
            success_rate = relevant_count / len(results)

            # Update strategy performance
            strategy = results[0].get('retrieval_strategy')
            if strategy:
                self.update_strategy_performance(strategy, success_rate > 0.5)

            # Add examples to few-shot learner if successful
            if success_rate > 0.7:
                for result in results:
                    if result.get('article_id') in relevant_ids:
                        self.few_shot_learner.add_example(
                            brand_description=result.get('brand_description', ''),
                            matched_content=result,
                            relevance_score=success_rate
                        )

        except Exception as e:
            logging.error(f"Error processing feedback: {str(e)}")


def main():
    """Example usage of Adaptive Retrieval System"""
    try:
        system = AdaptiveRetrievalSystem()

        # Test cases with different characteristics
        test_cases = [
            {
                "description": """
                We are a healthcare technology startup focusing on developing AI-powered diagnostic tools.
                Our main focus is on improving patient care through innovative technology solutions.
                We also provide data analytics services to healthcare providers for better decision making.
                """,
                "weights": {
                    "healthcare": 1.0,
                    "technology": 0.9,
                    "science": 0.7,
                    "business": 0.5
                }
            },
            {
                "description": "AI software company specializing in computer vision",
                "weights": {
                    "technology": 1.0,
                    "science": 0.8
                }
            }
        ]

        for i, case in enumerate(test_cases, 1):
            print(f"\nTest Case {i}:")
            print(f"Description: {case['description']}")

            # Get results
            results = system.retrieve(
                brand_description=case['description'],
                category_weights=case['weights']
            )

            # Display results
            print(f"\nFound {len(results)} results:")
            for j, result in enumerate(results, 1):
                print(f"\n{j}. {result['title']}")
                print(f"Category: {result['category']}")
                print(f"Strategy: {result['retrieval_strategy']}")
                print(f"Summary: {result['summary'][:200]}...")

            # Simulate feedback (mark first result as relevant)
            if results:
                system.provide_feedback(
                    results=results,
                    relevant_ids=[results[0]['article_id']]
                )

    except Exception as e:
        logging.error(f"Error in main: {str(e)}")


if __name__ == "__main__":
    main()

from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import (
    BrandContext, ArticleResponse, RetrievalResponse, fetch_articles_from_db, PineconeResult
)
from .strategies.hyde_strategy import HyDEStrategy
from .strategies.self_query_strategy import SelfQueryStrategy


class ArticleRetrievalService:
    def __init__(self,
                 index_name: str = "whats-good-articles",
                 namespace: str = "whats-good"):
        self.hyde_strategy = HyDEStrategy(index_name, namespace)
        self.self_query_strategy = SelfQueryStrategy(index_name, namespace)
        self.strategy_weights = {
            'hyde': 0.6,
            'self_query': 0.4
        }

    async def get_relevant_articles(
            self,
            brand_context: BrandContext,
            limit: int = 5,
            db: Optional[AsyncSession] = None
    ) -> RetrievalResponse:
        try:
            # Get results from both strategies
            hyde_results = await self.hyde_strategy.retrieve(
                brand_context=brand_context,
                limit=limit * 2
            )

            self_query_results = await self.self_query_strategy.retrieve(
                brand_context=brand_context,
                limit=limit * 2
            )

            # Convert PineconeResult objects to dicts for merging
            hyde_dicts = [result.to_dict() for result in hyde_results]
            self_query_dicts = [result.to_dict() for result in self_query_results]

            merged_results = self._merge_results(
                hyde_results=hyde_dicts,
                self_query_results=self_query_dicts,
                weights=self.strategy_weights,
                limit=limit
            )

            # Create scores map with consistent types
            scores_map = {
                result['article_id']: PineconeResult(
                    article_id=result['article_id'],
                    score=result['score'],
                    strategy=result['strategy']
                )
                for result in merged_results
            }

            articles = await fetch_articles_from_db(
                article_ids=list(scores_map.keys()),
                scores_map=scores_map,
                db=db
            )

            return RetrievalResponse(articles=articles, metrics=None)

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving articles: {str(e)}"
            )

    def _merge_results(
            self,
            hyde_results: List[dict],
            self_query_results: List[dict],
            weights: dict,
            limit: int
    ) -> List[dict]:
        seen_articles = set()
        merged = []

        for result in hyde_results:
            if result['article_id'] not in seen_articles:
                result['score'] *= weights['hyde']
                merged.append(result)
                seen_articles.add(result['article_id'])

        for result in self_query_results:
            if result['article_id'] not in seen_articles:
                result['score'] *= weights['self_query']
                merged.append(result)
                seen_articles.add(result['article_id'])

        merged.sort(key=lambda x: x['score'], reverse=True)
        return merged[:limit]
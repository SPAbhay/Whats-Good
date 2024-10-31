from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from ..db.base import get_db
from ..services.article_retrieval.core import ArticleRetrievalService
from ..services.article_retrieval.schemas import (
    BrandContext, RetrievalResponse
)
from ..models.brand import Brand
from ..services.brand_processor import BrandProcessor

router = APIRouter(prefix="/api/articles", tags=["articles"])
retrieval_service = ArticleRetrievalService()
brand_processor = BrandProcessor()


@router.get("/recommended/{brand_id}", response_model=RetrievalResponse)
async def get_recommended_articles(
        brand_id: int,
        limit: Optional[int] = 5,
        db: AsyncSession = Depends(get_db)
):
    try:
        # Debug log
        print(f"Fetching articles for brand {brand_id}")

        query = select(Brand).where(Brand.id == brand_id)
        result = await db.execute(query)
        brand = result.scalar_one_or_none()

        if not brand:
            print(f"Brand {brand_id} not found")
            return RetrievalResponse(articles=[], metrics=None)

        brand_context = BrandContext(
            brand_id=brand_id,
            industry=brand.processed_industry or "",
            values=brand.processed_brand_values or "",
            audience=brand.processed_target_audience or ""
        )

        print(f"Brand context: {brand_context}")

        response = await retrieval_service.get_relevant_articles(
            brand_context=brand_context,
            limit=limit,
            db=db
        )

        print(f"Found {len(response.articles)} articles")
        return response

    except Exception as e:
        print(f"Error retrieving articles: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving articles: {str(e)}"
        )


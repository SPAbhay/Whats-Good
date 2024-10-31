from ...services.brand_processor import ProcessedBrandProfile
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ...models.article import Article


class PineconeResult(BaseModel):
    """Internal model for Pinecone search results"""
    article_id: str
    score: float
    strategy: str

    def to_dict(self) -> dict:
        return {
            'article_id': self.article_id,
            'score': self.score,
            'strategy': self.strategy
        }


class ArticleResponse(BaseModel):
    article_id: str
    title: str
    summarized_content: str
    category: str
    author: Optional[str] = None
    publish_date: Optional[datetime] = None
    score: float
    retrieval_strategy: str
    matched_aspects: List[str] = Field(default_factory=list)
    topic_1: Optional[str] = None
    topic_2: Optional[str] = None
    topic_3: Optional[str] = None
    topic_4: Optional[str] = None
    topic_5: Optional[str] = None

    class Config:
        from_attributes = True


class BrandContext(BaseModel):
    """Unified brand context for retrieval"""
    brand_id: int
    industry: str = Field(description="Combined industry and focus")
    values: str = Field(description="Core brand values and USPs")
    audience: str = Field(description="Target audience information")

    @classmethod
    def from_processed_brand(cls, brand_id: int, processed: ProcessedBrandProfile) -> "BrandContext":
        return cls(
            brand_id=brand_id,
            industry=f"{processed.processed_industry}",
            values=processed.processed_brand_values,
            audience=processed.processed_target_audience
        )


class RetrievalResponse(BaseModel):
    articles: List[ArticleResponse]


async def fetch_articles_from_db(
    article_ids: List[str],
    scores_map: Dict[str, PineconeResult],
    db: AsyncSession
) -> List[ArticleResponse]:
    try:
        query = select(Article).where(Article.article_id.in_(article_ids))
        result = await db.execute(query)
        articles = result.scalars().all()

        return [
            ArticleResponse(
                article_id=article.article_id,
                title=article.title,
                summarized_content=article.summarized_content,
                category=article.category,
                author=getattr(article, 'author', None),
                publish_date=article.publish_date,
                score=scores_map[article.article_id].score if article.article_id in scores_map else 0.0,
                retrieval_strategy=scores_map[article.article_id].strategy if article.article_id in scores_map else "",
                matched_aspects=[],
                topic_1=article.topic_1,
                topic_2=article.topic_2,
                topic_3=article.topic_3,
                topic_4=article.topic_4,
                topic_5=article.topic_5,
            )
            for article in articles
            if hasattr(article, 'article_id')
        ]
    except Exception as e:
        logger.error(f"Error fetching articles from db: {str(e)}")
        return []
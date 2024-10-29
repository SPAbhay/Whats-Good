from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from backend.app.models.base import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    summarized_content = Column(Text)
    source_url = Column(String)
    brand_id = Column(Integer, ForeignKey("brands.id"))
    insights = Column(JSON, default=lambda: {
        "youtube": [],
        "reddit": []
    })
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    analytics_updated_at = Column(DateTime(timezone=True))
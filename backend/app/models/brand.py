from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from .base import Base
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    __table_args__ = {'extend_existing': True}

    # Raw responses directly from questionnaire
    raw_brand_name = Column(String, nullable=False)
    raw_industry_focus = Column(String, nullable=False)
    raw_target_audience = Column(String, nullable=False)
    raw_unique_value = Column(String, nullable=False)
    raw_social_platforms = Column(String)  # Nullable for first-time users
    raw_successful_content = Column(String)  # Nullable for first-time users

    # Processed responses (filled by LLM)
    processed_brand_name = Column(String)  # Cleaned/standardized brand name
    processed_industry = Column(String)  # Main industry category
    processed_industry_focus = Column(String)  # Specific focus area
    processed_target_audience = Column(String)  # Structured audience data
    processed_brand_values = Column(String)  # Core values and USPs
    processed_social_presence = Column(String)  # Structured social media data

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class BrandQuestionnaireResponse(BaseModel):
    raw_brand_name: str
    raw_industry_focus: str
    raw_target_audience: str
    raw_unique_value: str
    raw_social_platforms: Optional[str]
    raw_successful_content: Optional[str]

class BrandProcessedResponse(BaseModel):
    processed_brand_name: str
    processed_industry: str
    processed_industry_focus: str
    processed_target_audience: str
    processed_brand_values: str
    processed_social_presence: Optional[str]


class BrandResponse(BaseModel):
    id: int
    # Raw responses
    raw_brand_name: str
    raw_industry_focus: str
    raw_target_audience: str
    raw_unique_value: str
    raw_social_platforms: Optional[str]
    raw_successful_content: Optional[str]
    # Processed responses
    processed_brand_name: Optional[str]
    processed_industry: Optional[str]
    processed_industry_focus: Optional[str]
    processed_target_audience: Optional[str]
    processed_brand_values: Optional[str]
    processed_social_presence: Optional[str]
    # Metadata
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
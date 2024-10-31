from sqlalchemy import Column, String, Text, DateTime, JSON
from .base import Base

class Article(Base):
    __tablename__ = "articles"

    article_id = Column(String(255), primary_key=True)
    title = Column(Text)
    author = Column(String(255))
    source_url = Column(Text)
    content = Column(Text)
    publish_date = Column(DateTime)
    category = Column(String(255))
    cleaned_content = Column(Text)
    summarized_content = Column(Text)
    topic_1 = Column(String(255))
    topic_2 = Column(String(255))
    topic_3 = Column(String(255))
    topic_4 = Column(String(255))
    topic_5 = Column(String(255))
    insights = Column(JSON)
    created_at = Column(DateTime)
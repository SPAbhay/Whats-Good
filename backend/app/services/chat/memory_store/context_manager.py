from typing import Dict, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ....models.article import Article
from ....models.brand import Brand
from .redis_memory_store import RedisMemoryStore


class ChatContextManager:
    """
    Manages chat context operations and memory store integrations
    """

    def __init__(self, memory_store: RedisMemoryStore):
        self.memory_store = memory_store

    async def initialize_chat_context(
            self,
            db: AsyncSession,
            article_id: int,
            brand_id: int
    ) -> bool:
        """Initialize chat context with article and brand information"""
        try:
            # Fetch article and brand from database
            article_query = select(Article).where(and_(Article.id == article_id))
            brand_query = select(Brand).where(and_(Brand.id == brand_id))

            article_result = await db.execute(article_query)
            brand_result = await db.execute(brand_query)

            article = article_result.scalar_one_or_none()
            brand = brand_result.scalar_one_or_none()

            if not article or not brand:
                print(f"Failed to find {'article' if not article else 'brand'}")
                return False

            # Initialize context in Redis
            success = await self.memory_store.initialize_context(
                article=article,
                brand=brand
            )

            if not success:
                print("Failed to initialize Redis context")
                return False

            print(f"Successfully initialized context for article {article_id} and brand {brand_id}")
            return True

        except Exception as e:
            print(f"Error initializing chat context: {e}")
            return False

    async def add_message_to_context(
            self,
            article_id: int,
            brand_id: int,
            message: Dict,
            ttl: int = 3600
    ) -> bool:
        """Add a new message to the chat context"""
        try:
            return await self.memory_store.add_chat_memory(
                article_id=article_id,
                brand_id=brand_id,
                message=message,
                ttl=ttl
            )
        except Exception as e:
            print(f"Error adding message to context: {e}")
            return False

    async def get_chat_context(
            self,
            article_id: int,
            brand_id: int,
            include_chat: bool = True,
            max_messages: int = 10
    ) -> Dict:
        """Get complete chat context including article and chat history"""
        try:
            context = await self.memory_store.get_context(
                article_id=article_id,
                brand_id=brand_id,
                include_chat=include_chat,
                max_messages=max_messages
            )

            return self._enrich_context(context)
        except Exception as e:
            print(f"Error retrieving chat context: {e}")
            return {
                "article_content": None,
                "brand_identity": None,
                "chat_history": []
            }

    def _enrich_context(self, context: Dict) -> Dict:
        """Enrich context with additional information and analysis"""
        if not context:
            return context

        # Add metadata about context completeness
        context['metadata'] = {
            'has_article': bool(context.get('article_content')),
            'has_brand': bool(context.get('brand_identity')),
            'has_history': bool(context.get('chat_history')),
            'last_updated': datetime.now().isoformat()
        }

        # Add conversation summary if we have chat history
        if context.get('chat_history'):
            context['metadata']['conversation_summary'] = self._summarize_conversation(
                context['chat_history']
            )

        return context

    def _summarize_conversation(self, chat_history: List[Dict]) -> Dict:
        """Generate a summary of the conversation"""
        if not chat_history:
            return {"message_count": 0}

        return {
            "message_count": len(chat_history),
            "last_message_time": chat_history[-1].get('timestamp'),
            "topics_discussed": self._extract_topics(chat_history),
            "platforms_mentioned": self._extract_platforms(chat_history)
        }

    def _extract_topics(self, chat_history: List[Dict]) -> List[str]:
        """Extract main topics from chat history"""
        topics = set()

        for message in chat_history:
            content = message.get('content', '').lower()
            # Add basic topic extraction logic here
            if 'create' in content or 'make' in content:
                topics.add('content_creation')
            if 'brand' in content:
                topics.add('brand_discussion')
            if 'article' in content:
                topics.add('article_discussion')

        return list(topics)

    def _extract_platforms(self, chat_history: List[Dict]) -> List[str]:
        """Extract mentioned platforms from chat history"""
        platforms = set()
        platform_keywords = [
            'linkedin', 'twitter', 'instagram',
            'facebook', 'tiktok', 'youtube'
        ]

        for message in chat_history:
            content = message.get('content', '').lower()
            platforms.update(
                platform for platform in platform_keywords
                if platform in content
            )

        return list(platforms)

    async def clear_chat_context(
            self,
            article_id: int,
            brand_id: int
    ):
        """Clear chat context"""
        try:
            await self.memory_store.clear_context(
                article_id=article_id,
                brand_id=brand_id
            )
        except Exception as e:
            print(f"Error clearing chat context: {e}")
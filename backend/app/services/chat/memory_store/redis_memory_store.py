from typing import Dict, Optional, List
from datetime import datetime
import json
import zlib
from redis.asyncio import Redis
from ....models.article import Article
from ....models.brand import Brand
from ....core.config import Settings


class RedisMemoryStore:
    """
    Enhanced Redis-based memory store optimized for article-brand specific contexts
    """

    def __init__(
            self,
            settings: Settings,
            compression_threshold: int = 1000,
            prefix: str = "chat:memory:"
    ):
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            ssl=True,
            decode_responses=False
        )
        self.compression_threshold = compression_threshold
        self.prefix = prefix

    def _get_memory_key(self, article_id: str, brand_id: int, memory_type: str) -> str:
        return f"{self.prefix}{article_id}:{brand_id}:{memory_type}"

    def _compress_if_needed(self, data: str) -> bytes:
        """Compress data if it exceeds threshold"""
        encoded_data = data.encode() if isinstance(data, str) else data
        if len(encoded_data) > self.compression_threshold:
            return zlib.compress(encoded_data)
        return encoded_data

    def _decompress_if_needed(self, data: bytes) -> str:
        """Decompress data if it's compressed"""
        try:
            return zlib.decompress(data).decode()
        except (zlib.error, UnicodeDecodeError):
            return data.decode()

    async def initialize_context(
            self,
            article: Article,
            brand: Brand,
            ttl: int = 3600
    ) -> bool:
        try:
            # Store article content and insights
            content_key = self._get_memory_key(article.article_id, brand.id, "content")
            await self.redis.setex(
                content_key,
                ttl,
                self._compress_if_needed(json.dumps({
                    "content": article.content,
                    "summary": article.summarized_content,
                    "insights": article.insights if hasattr(article, 'insights') else {},
                    "timestamp": datetime.now().timestamp(),
                    "type": "article_content"
                }))
            )

            # Store brand identity
            brand_key = self._get_memory_key(article.article_id, brand.id, "brand")
            await self.redis.setex(
                brand_key,
                ttl,
                self._compress_if_needed(json.dumps({
                    "brand_identity": brand.brand_identity if hasattr(brand, 'brand_identity') else {},
                    "timestamp": datetime.now().timestamp(),
                    "type": "brand_identity"
                }))
            )

            return True
        except Exception as e:
            print(f"Error initializing context in Redis: {str(e)}")
            return False

    async def add_chat_memory(
            self,
            article_id: str,
            brand_id: int,
            message: Dict,
            ttl: int = 3600
    ) -> bool:
        """Add a chat message to memory"""
        try:
            chat_key = self._get_memory_key(
                article_id,
                brand_id,
                f"chat:{datetime.now().timestamp()}"
            )

            await self.redis.setex(
                chat_key,
                ttl,
                self._compress_if_needed(json.dumps({
                    "message": message,
                    "timestamp": datetime.now().timestamp(),
                    "type": "chat_message"
                }))
            )

            # Cleanup old messages if needed
            await self._cleanup_old_messages(article_id, brand_id)
            return True
        except Exception as e:
            print(f"Error adding chat memory: {e}")
            return False

    async def get_context(
            self,
            article_id: str,
            brand_id: int,
            include_chat: bool = True,
            max_messages: int = 10
    ) -> Dict:
        """Retrieve full context including article content and chat history"""
        context = {
            "article_content": None,
            "brand_identity": None,
            "chat_history": []
        }

        try:
            # Get article content and brand identity
            content_key = self._get_memory_key(article_id, brand_id, "content")
            brand_key = self._get_memory_key(article_id, brand_id, "brand")

            # Fetch article content
            content_data = await self.redis.get(content_key)
            if content_data:
                context["article_content"] = json.loads(
                    self._decompress_if_needed(content_data)
                )

            # Fetch brand identity
            brand_data = await self.redis.get(brand_key)
            if brand_data:
                context["brand_identity"] = json.loads(
                    self._decompress_if_needed(brand_data)
                )

            # Fetch chat history if requested
            if include_chat:
                pattern = f"{self.prefix}{article_id}:{brand_id}:chat:*"
                chat_keys = [key async for key in self.redis.scan_iter(pattern)]

                # Sort keys by timestamp
                chat_messages = []
                for key in chat_keys:
                    data = await self.redis.get(key)
                    if data:
                        message_data = json.loads(self._decompress_if_needed(data))
                        chat_messages.append(message_data)

                # Sort by timestamp and limit to max_messages
                chat_messages.sort(key=lambda x: x["timestamp"])
                context["chat_history"] = chat_messages[-max_messages:]

            return context

        except Exception as e:
            print(f"Error retrieving context: {e}")
            return context

    async def _cleanup_old_messages(
            self,
            article_id: str,
            brand_id: int,
            max_messages: int = 50
    ):
        """Clean up old chat messages if count exceeds threshold"""
        pattern = f"{self.prefix}{article_id}:{brand_id}:chat:*"
        chat_keys = await list(self.redis.scan_iter(pattern))

        if len(chat_keys) > max_messages:
            # Sort keys by timestamp
            key_times = []
            for key in chat_keys:
                try:
                    timestamp = float(key.split(":")[-1])
                    key_times.append((key, timestamp))
                except (ValueError, IndexError):
                    continue

            key_times.sort(key=lambda x: x[1])

            # Delete oldest messages
            for key, _ in key_times[:-max_messages]:
                await self.redis.delete(key)

    async def clear_context(self, article_id: str, brand_id: int):
        """Clear all context data for an article-brand combination"""
        pattern = f"{self.prefix}{article_id}:{brand_id}:*"
        keys = await list(self.redis.scan_iter(pattern))
        if keys:
            await self.redis.delete(*keys)
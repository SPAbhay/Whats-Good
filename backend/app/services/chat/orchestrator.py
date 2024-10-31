import asyncio
import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langchain_ollama import OllamaLLM
from langchain_openai import OpenAI

from .memory_store.context_manager import ChatContextManager
from .response_formatter import ResponseFormatter
from .content_analyzer import ContentAnalyzer


class AgentTransition(BaseModel):
    """Represents a transition between agents"""
    from_platform: Optional[str]
    to_platform: str
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)


class AgentResponse(BaseModel):
    """Standardized agent response"""
    content: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentContext(BaseModel):
    """Context for agent processing"""
    message: str
    article_content: Dict[str, Any]
    brand_identity: Dict[str, Any]
    platform: str
    chat_history: List[Dict]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MainOrchestrator:
    """
    Unified orchestrator for managing chat interactions across platforms
    """

    PLATFORM_PROFESSIONALS = {
        "LinkedIn": ("Leo", "Professional Growth Strategist"),
        "Twitter": ("Theo", "Viral Content Architect"),
        "Instagram": ("Iris", "Visual Story Expert"),
        "Facebook": ("Felix", "Community Engagement Specialist"),
        "TikTok": ("Tara", "Trend Dynamics Expert"),
        "YouTube": ("Yuri", "Video Strategy Specialist"),
        "General": ("Alex", "Content Expert")
    }

    PLATFORM_CHARACTERISTICS = {
        "LinkedIn": {
            "tone": "professional",
            "focus": "business insights and professional development",
            "content_type": "industry expertise and thought leadership",
            "engagement_style": "professional discussion"
        },
        "Twitter": {
            "tone": "concise and engaging",
            "focus": "trending topics and viral potential",
            "content_type": "short-form updates and trends",
            "engagement_style": "quick engagement and sharing"
        },
        "Instagram": {
            "tone": "visual and lifestyle",
            "focus": "visual storytelling and aesthetics",
            "content_type": "visual content and stories",
            "engagement_style": "visual engagement and community building"
        },
        "Facebook": {
            "tone": "conversational and community-focused",
            "focus": "community engagement and discussions",
            "content_type": "engaging posts and community content",
            "engagement_style": "community discussion and sharing"
        },
        "TikTok": {
            "tone": "entertaining and trendy",
            "focus": "trends and entertainment",
            "content_type": "short-form video content",
            "engagement_style": "creative engagement and trends"
        },
        "YouTube": {
            "tone": "informative and engaging",
            "focus": "in-depth content and education",
            "content_type": "long-form video content",
            "engagement_style": "detailed discussion and community"
        },
        "General": {
            "tone": "balanced and helpful",
            "focus": "comprehensive understanding",
            "content_type": "versatile content",
            "engagement_style": "helpful discussion"
        }
    }

    def __init__(
            self,
            context_manager: ChatContextManager,
            model_name: str = "mistral",
            temperature: float = 0.7
    ):
        self.context_manager = context_manager
        # self.llm = OllamaLLM(model=model_name, temperature=temperature)
        self.llm = OpenAI(model='gpt-3.5-turbo-instruct', api_key=os.getenv('OPENAI_API_KEY'), temperature=0.2)
        self.response_formatter = ResponseFormatter()
        self.content_analyzer = ContentAnalyzer()

    async def _analyze_context_needs(
            self,
            message: str,
            article_content: Dict,
            brand_identity: Dict,
            query_type: str
    ) -> Optional[AgentResponse]:
        """
        Intelligently analyze if we need more context based on the specific request
        Returns a response asking for more info if needed, None otherwise
        """
        message_lower = message.lower()

        # For content creation requests, analyze specific needs
        if query_type == "content_creation":
            needs = await self._identify_content_creation_needs(
                message, article_content, brand_identity
            )
            if needs:
                return AgentResponse(
                    content=f"I'll help you create that content! {needs}",
                    confidence_score=0.9,
                    metadata={"needs_more_info": True, "type": "content_creation"}
                )

        # For brand-related queries, check if we need specific brand details
        elif query_type == "brand_inquiry":
            if specific_brand_needs := self._check_specific_brand_needs(message, brand_identity):
                return AgentResponse(
                    content=specific_brand_needs,
                    confidence_score=0.9,
                    metadata={"needs_more_info": True, "type": "brand_details"}
                )

        # For article-related queries, check if we need more article context
        elif "article" in message_lower or query_type == "article_question":
            if specific_article_needs := await self._check_specific_article_needs(
                    message, article_content
            ):
                return AgentResponse(
                    content=specific_article_needs,
                    confidence_score=0.9,
                    metadata={"needs_more_info": True, "type": "article_details"}
                )

        return None

    def _has_audience_info(self, brand_identity: Dict) -> bool:
        """Check if brand identity contains audience information"""
        if not brand_identity:
            return False

        brand_text = brand_identity.get('brand_identity', '').lower()
        audience_indicators = [
            'audience', 'customer', 'client', 'user',
            'target', 'demographic', 'market', 'segment',
            'people', 'consumers', 'businesses', 'b2b', 'b2c'
        ]

        return any(indicator in brand_text for indicator in audience_indicators)

    async def _generate_youtube_idea(self, article_content: str, brand_identity: Dict) -> AgentResponse:
        prompt = f"""Based on this article content, suggest a YouTube video concept:

Article:
{article_content}

Brand Voice:
{brand_identity.get('brand_identity', 'Professional and informative')}

Generate a YouTube video concept that includes:
1. Compelling title
2. Brief description/outline
3. Key talking points
4. Target audience
5. Estimated video length
6. Type of video (tutorial, explanation, discussion, etc.)"""

        try:
            response = await self.llm.ainvoke(prompt)
            return AgentResponse(
                content=response,
                confidence_score=0.9,
                metadata={"platform": "YouTube"}
            )
        except Exception as e:
            print(f"Error generating YouTube idea: {e}")
            return AgentResponse(
                content="I apologize, but I'm having trouble generating a YouTube video concept. Could you try again?",
                confidence_score=0.5,
                metadata={"error": str(e)}
            )

    async def _generate_tweet(self, article_content: str, brand_identity: Dict) -> AgentResponse:
        prompt = f"""Based on this article content, create an engaging tweet:

Article:
{article_content}

Brand Voice:
{brand_identity.get('brand_identity', 'Professional and informative')}

Requirements:
1. Must be under 280 characters
2. Should be engaging and shareable
3. Include key article insights
4. Maintain brand voice
5. Optional: Include relevant hashtags

Generate a tweet that captures the main point while being engaging:"""

        try:
            response = await self.llm.ainvoke(prompt)
            return AgentResponse(
                content=response,
                confidence_score=0.9,
                metadata={"platform": "Twitter"}
            )
        except Exception as e:
            print(f"Error generating tweet: {e}")
            return AgentResponse(
                content="I apologize, but I'm having trouble generating a tweet. Could you try again?",
                confidence_score=0.5,
                metadata={"error": str(e)}
            )

    def _has_tone_info(self, brand_identity: Dict) -> bool:
        """Check if brand identity contains tone information"""
        if not brand_identity:
            return False

        brand_text = brand_identity.get('brand_identity', '').lower()
        tone_indicators = [
            'tone', 'voice', 'style', 'communication',
            'formal', 'casual', 'professional', 'friendly',
            'serious', 'playful', 'authoritative', 'conversational'
        ]

        return any(indicator in brand_text for indicator in tone_indicators)

    async def _identify_content_creation_needs(
            self,
            message: str,
            article_content: Dict,
            brand_identity: Dict
    ) -> Optional[str]:
        """
        Identify what additional information we need for content creation
        """
        message_lower = message.lower()
        needed_info = []

        # Extract request details
        platform_mentioned = any(platform.lower() in message_lower
                                 for platform in self.PLATFORM_CHARACTERISTICS.keys())
        wants_formal = "formal" in message_lower
        wants_casual = "casual" in message_lower
        wants_professional = "professional" in message_lower
        is_specific_request = any(word in message_lower for word
                                  in ["how to", "tutorial", "guide", "tips", "steps"])

        # Check brand voice needs
        if not brand_identity and (wants_formal or wants_casual or wants_professional):
            needed_info.append(
                "To maintain the right tone, could you tell me a bit about your brand's voice? "
                "For example, do you prefer a more formal or conversational style?"
            )

        # Check platform-specific needs
        if not platform_mentioned:
            needed_info.append(
                "Which platform would you like this content for? "
                "Each platform has its own best practices for engagement."
            )

        # Check for specific content type needs
        if is_specific_request and not self._has_sufficient_detail(article_content, message):
            needed_info.append(
                "To create detailed content about this topic, could you provide any specific "
                "points or aspects you'd like me to focus on?"
            )

        return " ".join(needed_info) if needed_info else None

    def _check_specific_brand_needs(
            self,
            message: str,
            brand_identity: Dict
    ) -> Optional[str]:
        """
        Check if we need specific brand information based on the query
        """
        message_lower = message.lower()

        if not brand_identity:
            return (
                "I see you're interested in brand-related content. "
                "Could you tell me about your brand's identity and values? "
                "This will help me provide more relevant assistance."
            )

        # Check for specific brand aspects
        if "tone" in message_lower and not self._has_tone_info(brand_identity):
            return "What tone do you typically use in your brand communications?"

        if "audience" in message_lower and not self._has_audience_info(brand_identity):
            return "Who is your target audience? This will help me tailor the content appropriately."

        return None

    async def _check_specific_article_needs(
            self,
            message: str,
            article_content: Dict
    ) -> Optional[str]:
        """
        Check if we need more article context based on the specific query
        """
        message_lower = message.lower()

        # Extract key topics from the query
        query_topics = await self._extract_query_topics(message)

        # Check if article contains sufficient information about these topics
        missing_info = self._identify_missing_article_info(
            query_topics,
            article_content
        )

        if missing_info:
            return (
                f"I notice you're asking about {', '.join(missing_info)}. "
                "Could you provide more context about these aspects? "
                "This will help me give you a more comprehensive response."
            )

        return None

    async def _send_status(self, context: Dict[str, Any], status: str):
        """Helper method to send status updates"""
        if "websocket" in context:
            try:
                await context["websocket"].send_json({
                    "type": "processing_status",
                    "status": status
                })
            except Exception as e:
                print(f"Error sending status update: {e}")

    async def process_message(
            self,
            message: str,
            context: Dict[str, Any]
    ) -> AgentResponse:
        try:
            print(f"Processing message: {message}")
            print(f"With context: {context}")

            # Validate context
            chat_context = context.get("chat_context")
            if not chat_context:
                print("No chat context found")
                return AgentResponse(
                    content="Sorry, I couldn't access the conversation context. Please try again.",
                    confidence_score=0.0,
                    metadata={"error": "Missing context"}
                )

            # Get article content
            article_content = chat_context.get("article_content", {})
            if not article_content:
                print("No article content found")
                return AgentResponse(
                    content="Sorry, I couldn't access the article content. Please try again.",
                    confidence_score=0.0,
                    metadata={"error": "Missing article"}
                )

            # Get brand identity
            brand_identity = chat_context.get("brand_identity", {})

            # Extract content safely
            article_text = article_content.get("content", "") if isinstance(article_content, dict) else ""
            if not article_text:
                print("No article text found")
                return AgentResponse(
                    content="Sorry, I couldn't find the article content. Please try again.",
                    confidence_score=0.0,
                    metadata={"error": "No content"}
                )

            # Process based on message type
            if "tweet" in message.lower() or "twitter" in message.lower():
                return await self._generate_tweet(article_text, brand_identity)
            elif "youtube" in message.lower() or "video" in message.lower():
                return await self._generate_youtube_idea(article_text, brand_identity)
            else:
                return await self._generate_contextual_response(
                    message=message,
                    article_text=article_text,
                    brand_identity=brand_identity,
                    context=context
                )

        except Exception as e:
            print(f"Error in process_message: {str(e)}")
            return AgentResponse(
                content="I apologize, but I encountered an error. Please try again.",
                confidence_score=0.0,
                metadata={"error": str(e)}
            )

    def _has_sufficient_detail(self, article_content: Dict, query: str) -> bool:
        """Check if article has sufficient detail for the specific query"""
        content = article_content.get('content', '')

        # Define detail requirements based on query type
        if "how to" in query.lower():
            # Check for step-by-step indicators
            has_steps = any(marker in content.lower()
                            for marker in ["step", "first", "then", "finally"])
            has_enough_detail = len(content.split()) >= 100  # Arbitrary threshold
            return has_steps and has_enough_detail

        if "tutorial" in query.lower() or "guide" in query.lower():
            # Check for detailed explanation indicators
            return (
                    "explain" in content.lower() or
                    "detail" in content.lower() or
                    len(content.split('.')) >= 5
            )

        return True  # Default to True for general queries

    async def _extract_query_topics(self, query: str) -> List[str]:
        """Extract main topics from the query that need to be addressed"""
        topic_prompt = f"""Extract key topics from this query:
        Query: {query}
        Return only the main topics, one per line."""

        try:
            response = await self.llm.invoke(topic_prompt)
            return [topic.strip() for topic in response.split('\n') if topic.strip()]
        except Exception:
            # Fallback to basic extraction
            return [word for word in query.lower().split()
                    if len(word) > 3 and word not in ['what', 'how', 'why', 'when', 'the']]

    async def _generate_contextual_response(
            self,
            message: str,
            article_text: str,
            brand_identity: Dict,
            context: Dict
    ) -> AgentResponse:
        try:
            print("Starting to generate response...")
            prompt = f"""Help create content based on this context:

    User Message: {message}

    Article Content:
    {article_text}

    Brand Identity:
    {brand_identity.get('brand_identity', '')}

    Please provide a helpful response that:
    1. Directly addresses the user's request
    2. Uses the article content appropriately
    3. Maintains brand voice
    4. Provides specific, actionable suggestions"""

            print("Sending prompt to Ollama...")
            response = await self.llm.ainvoke(prompt)
            print("Received response from Ollama:", response)

            # Send the response through websocket
            if "websocket" in context:
                try:
                    await context["websocket"].send_json({
                        "type": "message",
                        "content": response,
                        "metadata": {"platform": context.get("platform", "General")}
                    })
                    print("Response sent through websocket")
                except Exception as ws_error:
                    print(f"WebSocket send error: {ws_error}")

            return AgentResponse(
                content=response,
                confidence_score=0.9,
                metadata={"platform": context.get("platform", "General")}
            )
        except Exception as e:
            print(f"Error in _generate_contextual_response: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return AgentResponse(
                content="I apologize, but I'm having trouble generating a response. Could you rephrase your question?",
                confidence_score=0.5,
                metadata={"error": str(e)}
            )

    def _identify_missing_article_info(
            self,
            query_topics: List[str],
            article_content: Dict
    ) -> List[str]:
        """Identify which query topics aren't well-covered in the article"""
        content = article_content.get('content', '').lower()
        missing_topics = []

        for topic in query_topics:
            # Check if topic is mentioned with enough context
            topic_mentions = content.count(topic.lower())
            topic_context = len(content.split('.'))

            if topic_mentions == 0 or (topic_mentions == 1 and topic_context < 3):
                missing_topics.append(topic)

        return missing_topics

    def _get_persona_prefix(self, platform: str) -> str:
        """Get the platform-specific persona prefix"""
        name, title = self.PLATFORM_PROFESSIONALS.get(platform, self.PLATFORM_PROFESSIONALS["General"])
        return f"{name} ({title})"

    async def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from the article content"""
        key_points = []
        try:
            key_points_prompt = f"""Extract 3-5 key points from this content:
    {content}

    Return only the key points, one per line."""

            response = await self.llm.invoke(key_points_prompt)
            key_points = [point.strip() for point in response.split('\n') if point.strip()]
        except Exception:
            key_points = ["Main article point"]

        return key_points[:5]

    async def _generate_content_response(
            self,
            message: str,
            article_content: Dict,
            brand_identity: Dict,
            platform: str,
            context: Dict[str, Any]  # Add context parameter to access websocket
    ) -> AgentResponse:
        """Generate platform-specific content with detailed status updates"""

        async def update_status(status: str):
            if "websocket" in context:
                await context["websocket"].send_json({
                    "type": "processing_status",
                    "status": status
                })

        try:
            platform_chars = self.PLATFORM_CHARACTERISTICS.get(platform, self.PLATFORM_CHARACTERISTICS["General"])

            # Phase 1: Initial Analysis
            await update_status("📚 Reading and analyzing the article content...")
            await asyncio.sleep(0.5)  # Brief pause for UI update

            await update_status("🎯 Identifying key points and insights...")
            key_points = await self._extract_key_points(article_content.get('content', ''))
            await asyncio.sleep(0.5)

            # Phase 2: Brand Alignment
            await update_status("🎨 Analyzing brand voice and style preferences...")
            await asyncio.sleep(0.5)

            # Phase 3: Platform Optimization
            await update_status(f"✍️ Crafting content specifically for {platform}...")

            content_prompt = f"""Create {platform} content based on:

    Article Content: {article_content.get('content', '')}
    Brand Identity: {brand_identity.get('brand_identity', '')}

    Key Points Identified:
    {chr(10).join(f'- {point}' for point in key_points)}

    Requirements:
    - Tone: {platform_chars['tone']}
    - Focus: {platform_chars['focus']}
    - Style: {platform_chars['engagement_style']}

    Generate content that:
    1. Matches the brand's voice
    2. Is optimized for {platform}
    3. Engages the target audience
    4. Includes relevant calls-to-action"""

            await update_status("🔄 Generating your content...")
            content = await self.llm.invoke(content_prompt)

            # Phase 4: Final Polish
            await update_status("✨ Reviewing and polishing the content...")
            await asyncio.sleep(0.5)

            await update_status("🎉 Content ready! Here's what I've created...")

            return AgentResponse(
                content=content,
                confidence_score=0.9,
                metadata={
                    "platform": platform,
                    "content_type": platform_chars['content_type'],
                    "generation_steps": [
                        "article_analysis",
                        "brand_alignment",
                        "platform_optimization",
                        "final_polish"
                    ]
                }
            )
        except Exception as e:
            print(f"Error generating content: {e}")
            await update_status("❌ Encountered an error while generating content...")
            return AgentResponse(
                content="I apologize, but I encountered an error while creating your content. Could you try again?",
                confidence_score=0.5,
                metadata={"error": str(e)}
            )

    def _format_chat_history(self, history: List[Dict]) -> str:
        """Format chat history for context"""
        if not history:
            return "No previous messages"

        formatted = []
        for msg in history:
            role = msg.get('role', 'unknown').capitalize()
            content = msg.get('content', '')
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    def _explain_capabilities(self, has_brand_context: bool) -> AgentResponse:
        """Explain bot capabilities"""
        capabilities = [
            "Create personalized social media content for various platforms",
            "Adapt content to match your brand's voice and style",
            "Analyze articles and generate engaging posts",
            "Suggest platform-specific optimizations",
            "Help maintain consistent brand messaging"
        ]

        response = (
                "I'm your AI content assistant, specialized in helping you create "
                "engaging social media content. Here's what I can do:\n\n"
                + "\n".join(f"• {cap}" for cap in capabilities)
                + "\n\nWould you like me to help you create any specific type of content?"
        )

        if not has_brand_context:
            response += "\n\nNote: To provide more personalized assistance, "
            "I'd love to learn more about your brand's identity and goals."

        return AgentResponse(
            content=response,
            confidence_score=0.95,
            metadata={"type": "capabilities", "has_brand_context": has_brand_context}
        )
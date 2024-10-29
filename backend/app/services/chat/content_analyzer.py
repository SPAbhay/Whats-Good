from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
import re


class ContentTheme(BaseModel):
    """Content theme identification"""
    main_topic: str
    subtopics: List[str]
    tone: str
    target_audience: str


class ContentStructure(BaseModel):
    """Content structure analysis"""
    has_introduction: bool
    has_conclusion: bool
    sections: List[str]
    key_points: List[str]


class ContentInsight(BaseModel):
    """Individual content insight"""
    topic: str
    relevance: float
    context: str
    source: str


class AnalysisResult(BaseModel):
    """Complete content analysis result"""
    themes: ContentTheme
    structure: ContentStructure
    insights: List[ContentInsight]
    suggested_approaches: Dict[str, List[str]]


class ContentAnalyzer:
    """
    Analyzes content and queries to provide intelligent insights and responses
    """

    def __init__(self, model_name: str = "mistral", temperature: float = 0.7):
        self.llm = OllamaLLM(model=model_name, temperature=temperature)
        self._initialize_patterns()

    def _initialize_patterns(self):
        """Initialize regex patterns for content analysis"""
        self.patterns = {
            'question': r'\?$',
            'list_item': r'^\s*[-•*]\s',
            'heading': r'^#+\s',
            'url': r'https?://\S+',
            'emphasis': r'\*\*?[^*]+\*\*?|__[^_]+__',
        }

    async def analyze_query_type(self, message: str) -> str:
        """Analyze the type of user query"""
        message_lower = message.lower()

        # Check for direct content creation requests
        if any(verb in message_lower for verb in ['create', 'make', 'write', 'generate']):
            if any(platform in message_lower for platform in
                   ['linkedin', 'twitter', 'instagram', 'facebook', 'tiktok', 'youtube']):
                return 'content_creation'
            return 'content_request'

        # Check for brand-related queries
        if any(word in message_lower for word in ['brand', 'company', 'business', 'identity']):
            return 'brand_inquiry'

        # Check for capabilities questions
        if any(phrase in message_lower for phrase in [
            'what can you', 'what do you do', 'help me with', 'capabilities'
        ]):
            return 'capabilities'

        # Check for article-specific questions
        if any(word in message_lower for word in ['article', 'content', 'post']) and '?' in message:
            return 'article_question'

        # Check for help or guidance
        if any(word in message_lower for word in ['help', 'guide', 'how to', 'suggest']):
            return 'assistance'

        # Default to general inquiry
        return 'general_inquiry'

    async def analyze_content_needs(
            self,
            query: str,
            article_content: Optional[Dict] = None,
            brand_identity: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze what additional content or context might be needed
        """
        query_lower = query.lower()
        needs = {
            'needs_more_info': False,
            'missing_elements': [],
            'suggestions': []
        }

        # Check query complexity
        complexity_score = self._assess_query_complexity(query)

        # For complex queries, check if we have enough article detail
        if complexity_score > 0.7 and article_content:
            content_detail = self._assess_content_detail(
                article_content.get('content', ''),
                query
            )
            if content_detail < 0.6:
                needs['needs_more_info'] = True
                needs['missing_elements'].append('article_detail')
                needs['suggestions'].append(
                    "Could you specify which aspects you'd like me to focus on?"
                )

        # For branded content requests, check brand context
        if self._is_branded_request(query) and not brand_identity:
            needs['needs_more_info'] = True
            needs['missing_elements'].append('brand_identity')
            needs['suggestions'].append(
                "To better align with your brand, could you tell me more about your brand's voice and values?"
            )

        return needs

    def _assess_query_complexity(self, query: str) -> float:
        """
        Assess the complexity of a query
        Returns: float between 0 and 1
        """
        # Check for multiple questions
        question_count = query.count('?')

        # Check for specific detail requests
        detail_markers = ['specifically', 'detailed', 'explain', 'how', 'why']
        detail_count = sum(1 for marker in detail_markers if marker in query.lower())

        # Calculate complexity score
        base_score = min((question_count * 0.3) + (detail_count * 0.2), 1.0)

        # Adjust for query length
        length_factor = min(len(query.split()) / 20, 1.0)

        return (base_score + length_factor) / 2

    def _assess_content_detail(self, content: str, query: str) -> float:
        """
        Assess if content has enough detail for the query
        Returns: float between 0 and 1
        """
        # Extract key terms from query
        query_terms = set(query.lower().split()) - {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'
        }

        # Check content coverage
        content_lower = content.lower()
        term_coverage = sum(1 for term in query_terms if term in content_lower)
        coverage_score = term_coverage / len(query_terms) if query_terms else 1.0

        # Check content depth
        sentences = content.split('.')
        depth_score = min(len(sentences) / 10, 1.0)

        return (coverage_score + depth_score) / 2

    def _is_branded_request(self, query: str) -> bool:
        """Check if query implies need for brand context"""
        branded_indicators = [
            'brand', 'voice', 'tone', 'style', 'professional',
            'formal', 'company', 'our', 'we', 'representation'
        ]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in branded_indicators)

    async def extract_key_points(
            self,
            content: str,
            max_points: int = 5
    ) -> List[Dict[str, str]]:
        """Extract key points with explanations"""
        try:
            prompt = f"""Extract {max_points} key points from this content:

            {content}
            
            Format each point as:
            point||explanation||context
            One point per line."""

            response = await self.llm.invoke(prompt)
            points = []

            for line in response.strip().split('\n'):
                if '||' not in line:
                    continue
                point, explanation, context = line.split('||')
                points.append({
                    'point': point.strip(),
                    'explanation': explanation.strip(),
                    'context': context.strip()
                })

            return points[:max_points]
        except Exception:
            return [{'point': 'Error extracting points',
                     'explanation': 'Failed to process',
                     'context': 'Error'}]

    def analyze_tone_and_style(self, content: str) -> Dict[str, float]:
        """Analyze content tone and style characteristics"""
        tone_markers = {
            'professional': r'\b(professional|business|industry|expert)\b',
            'casual': r'\b(cool|awesome|great|nice)\b',
            'educational': r'\b(learn|understand|explain|know)\b',
            'promotional': r'\b(best|amazing|incredible|perfect)\b',
            'technical': r'\b(system|process|method|technical)\b'
        }

        content_lower = content.lower()
        scores = {}

        for tone, pattern in tone_markers.items():
            matches = len(re.findall(pattern, content_lower))
            # Normalize score between 0 and 1
            scores[tone] = min(matches / 10, 1.0)

        return scores
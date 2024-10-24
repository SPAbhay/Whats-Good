from typing import Dict, List
import json
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate


class InsightGenerator:
    def __init__(self):
        print("\nInitializing Insight Generator...")
        try:
            self.llm = OllamaLLM(model="mistral", temperature=0.2)
            print("✓ LLM initialized successfully")
        except Exception as e:
            print(f"✗ LLM initialization failed: {str(e)}")
            self.llm = None

        self.topic_analysis_prompt = PromptTemplate(
            input_variables=["topic", "keywords", "context"],
            template="""Analyze content for the following topic and its key aspects:

            Topic: {topic}
            Key Aspects: {keywords}

            Platform Data (YouTube and Reddit):
            {context}

            Provide a comprehensive analysis focused on:
            1. Main themes and patterns across keywords (with examples)
            2. Common questions/concerns from the audience
            3. Current trends and engagement patterns
            4. Content gaps and opportunities
            5. Audience sentiment and reactions

            Return ONLY a JSON object with this exact structure:
            {
                "themes": [
                    {{"theme": "theme1", "evidence": "evidence1"}}
                ],
                "questions": ["question1", "question2"],
                "trends": ["trend1", "trend2"],
                "opportunities": ["opportunity1", "opportunity2"],
                "audience_insights": {
                    "overall_sentiment": "sentiment",
                    "key_points": ["point1", "point2"]
                }
            }"""
        )

    def generate_insights(self, topic: str, keywords: List[str], analysis_data: Dict) -> Dict:
        """Generate insights from analysis data"""
        if not self.llm:
            return {"error": "LLM not available"}

        try:
            # Prepare context from analysis data
            context = self._prepare_context(analysis_data)

            # Get LLM analysis
            response = self.llm.invoke(
                self.topic_analysis_prompt.format(
                    topic=topic,
                    keywords=json.dumps(keywords),
                    context=json.dumps(context)
                )
            )

            # Parse response
            try:
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    return self._get_fallback_response("No valid JSON found in response")
            except json.JSONDecodeError:
                return self._get_fallback_response("Failed to parse LLM response")

        except Exception as e:
            return self._get_fallback_response(str(e))

    def _prepare_context(self, analysis_data: Dict) -> Dict:
        """Prepare context for LLM from analysis data"""
        context = {
            "platform_metrics": {
                "youtube": [],
                "reddit": []
            },
            "content_samples": {
                "youtube": [],
                "reddit": []
            }
        }

        # Process YouTube data
        for data in analysis_data["raw_data"]["youtube"]:
            context["platform_metrics"]["youtube"].append({
                "keyword": data["keyword"],
                "metrics": data["data"]["metrics"]
            })

            # Add sample comments
            context["content_samples"]["youtube"].extend([
                comment["text"][:200]
                for comment in data["data"].get("comments", [])[:3]
            ])

        # Process Reddit data
        for data in analysis_data["raw_data"]["reddit"]:
            context["platform_metrics"]["reddit"].append({
                "keyword": data["keyword"],
                "metrics": data["data"]["metrics"]
            })

            # Add sample posts and comments
            for post in data["data"].get("posts", [])[:2]:
                context["content_samples"]["reddit"].append({
                    "title": post["title"],
                    "text": post["selftext"][:200] if post.get("selftext") else "",
                    "comments": [
                        c["text"][:200]
                        for c in post.get("comments", [])[:2]
                    ]
                })

        return context

    def _get_fallback_response(self, error_msg: str) -> Dict:
        """Get fallback response structure"""
        return {
            "error": error_msg,
            "themes": [{"theme": "Analysis pending", "evidence": "Processing data"}],
            "questions": ["Analysis in progress"],
            "trends": ["Analysis pending"],
            "opportunities": ["Analysis pending"],
            "audience_insights": {
                "overall_sentiment": "Pending",
                "key_points": ["Analysis in progress"]
            }
        }

    def print_insights(self, insights: Dict):
        """Print insights in a readable format"""
        print("\nInsight Analysis Results:")
        print("=" * 50)

        if "error" in insights:
            print(f"Error: {insights['error']}")
            return

        if "themes" in insights:
            print("\nMain Themes:")
            for theme in insights["themes"]:
                print(f"• {theme.get('theme', 'No theme')}")
                if evidence := theme.get('evidence'):
                    print(f"  Evidence: {evidence[:200]}...")

        if "questions" in insights:
            print("\nKey Questions:")
            for q in insights["questions"]:
                print(f"• {q}")

        if "trends" in insights:
            print("\nTrends:")
            for trend in insights["trends"]:
                print(f"• {trend}")

        if "opportunities" in insights:
            print("\nOpportunities:")
            for opp in insights["opportunities"]:
                print(f"• {opp}")

        if "audience_insights" in insights:
            print("\nAudience Insights:")
            ai = insights["audience_insights"]
            print(f"Overall Sentiment: {ai.get('overall_sentiment', 'Unknown')}")
            if "key_points" in ai:
                print("Key Points:")
                for point in ai["key_points"]:
                    print(f"• {point}")
import os
from typing import Dict, List
from datetime import datetime
import json
import numpy as np
from textblob import TextBlob
from temp.youtube_scraper import YouTubeScraper
from temp.reddit_scraper import RedditScraper


class ContentAnalyzer:
    def __init__(
            self,
            youtube_api_key: str,
            reddit_client_id: str,
            reddit_client_secret: str,
            reddit_user_agent: str
    ):
        print("\nInitializing Content Analyzer...")

        # Initialize scrapers
        print("1. Setting up YouTube scraper...")
        self.youtube_scraper = YouTubeScraper(youtube_api_key)

        print("2. Setting up Reddit scraper...")
        self.reddit_scraper = RedditScraper(
            reddit_client_id,
            reddit_client_secret,
            reddit_user_agent
        )

    def analyze_topic_content(self, topic: str, keywords: List[str]) -> Dict:
        """Analyze content for a topic using multiple keywords"""
        print(f"\nAnalyzing topic: '{topic}'")
        print(f"Keywords: {', '.join(keywords)}")

        all_data = {
            "youtube": [],
            "reddit": []
        }

        keyword_results = []

        # Gather data for each keyword
        for keyword in keywords:
            print(f"\nGathering data for keyword: '{keyword}'")
            try:
                youtube_data = self.youtube_scraper.get_videos_data(keyword)
                reddit_data = self.reddit_scraper.get_topic_data(keyword)

                if youtube_data["success"]:
                    all_data["youtube"].append({
                        "keyword": keyword,
                        "data": youtube_data
                    })

                if reddit_data["success"]:
                    all_data["reddit"].append({
                        "keyword": keyword,
                        "data": reddit_data
                    })

                # Calculate individual metrics
                result = {
                    "keyword": keyword,
                    "popularity": self.calculate_popularity_score(
                        youtube_data.get("metrics", {}),
                        reddit_data.get("metrics", {})
                    ),
                    "sentiment": self.analyze_sentiment(
                        youtube_data.get("comments", []),
                        reddit_data.get("posts", [])
                    ),
                    "data_points": {
                        "youtube": len(youtube_data.get("videos", [])),
                        "reddit": len(reddit_data.get("posts", []))
                    }
                }
                keyword_results.append(result)

            except Exception as e:
                print(f"Error processing keyword '{keyword}': {str(e)}")

        return {
            "success": True,
            "topic": topic,
            "keywords_analyzed": keywords,
            "timestamp": datetime.now().isoformat(),
            "keyword_metrics": keyword_results,
            "raw_data": all_data,
            "data_summary": {
                "youtube_videos": sum(len(d["data"].get("videos", []))
                                      for d in all_data["youtube"]),
                "youtube_comments": sum(len(d["data"].get("comments", []))
                                        for d in all_data["youtube"]),
                "reddit_posts": sum(len(d["data"].get("posts", []))
                                    for d in all_data["reddit"]),
                "reddit_comments": sum(
                    sum(len(post.get("comments", []))
                        for post in d["data"].get("posts", []))
                    for d in all_data["reddit"]
                )
            }
        }

    def calculate_popularity_score(self, youtube_metrics: Dict, reddit_metrics: Dict) -> float:
        """Calculate overall popularity score (0-100)"""
        score = 0

        # YouTube component (60%)
        if youtube_metrics:
            view_score = min(1.0, youtube_metrics.get("total_views", 0) / 1000000)
            engagement_score = min(1.0, youtube_metrics.get("engagement_rate", 0) / 0.1)
            velocity_score = min(1.0, youtube_metrics.get("avg_view_velocity", 0) / 10000)

            youtube_score = (
                    view_score * 30 +
                    engagement_score * 20 +
                    velocity_score * 10
            )
            score += youtube_score

        # Reddit component (40%)
        if reddit_metrics:
            post_score = min(1.0, reddit_metrics.get("avg_score_per_post", 0) / 1000)
            comment_score = min(1.0, reddit_metrics.get("avg_comments_per_post", 0) / 100)
            reddit_score = (post_score + comment_score) * 20
            score += reddit_score

        return min(100, score)

    def analyze_sentiment(self, youtube_comments: List[Dict], reddit_posts: List[Dict]) -> Dict:
        """Analyze sentiment across platforms"""
        sentiments = []

        # Process YouTube comments
        for comment in youtube_comments:
            if text := comment.get("text"):
                blob = TextBlob(text)
                sentiments.append(blob.sentiment.polarity)

        # Process Reddit content
        for post in reddit_posts:
            if title := post.get("title"):
                blob = TextBlob(title)
                sentiments.append(blob.sentiment.polarity)

            if text := post.get("selftext"):
                blob = TextBlob(text)
                sentiments.append(blob.sentiment.polarity)

            for comment in post.get("comments", []):
                if comment_text := comment.get("text"):
                    blob = TextBlob(comment_text)
                    sentiments.append(blob.sentiment.polarity)

        if not sentiments:
            return {"score": 0, "category": "Neutral", "confidence": 0}

        avg_sentiment = np.mean(sentiments)

        # Categorize sentiment
        if avg_sentiment >= 0.3:
            category = "Very Positive"
        elif avg_sentiment >= 0.1:
            category = "Positive"
        elif avg_sentiment <= -0.3:
            category = "Very Negative"
        elif avg_sentiment <= -0.1:
            category = "Negative"
        else:
            category = "Neutral"

        return {
            "score": avg_sentiment,
            "category": category,
            "confidence": min(1.0, len(sentiments) / 100),
            "samples_analyzed": len(sentiments)
        }

    def save_result(self, result: Dict, filename: str):
        """Save analysis result to file"""
        if result["success"]:
            output_dir = "analysis_resultss"
            os.makedirs(output_dir, exist_ok=True)

            filepath = f"{output_dir}/{filename}"
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            print(f"Results saved to: {filepath}")


def main():
    from dotenv import load_dotenv
    load_dotenv()

    analyzer = ContentAnalyzer(
        youtube_api_key=os.getenv('YOUTUBE_API_KEY'),
        reddit_client_id=os.getenv('REDDIT_CLIENT_ID'),
        reddit_client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        reddit_user_agent=os.getenv('REDDIT_USER_AGENT')
    )

    # Test with sample topic
    topic = "Impact of AI on Healthcare"
    keywords = [
        "AI healthcare diagnosis",
        "medical artificial intelligence",
        "healthcare automation"
    ]

    result = analyzer.analyze_topic_content(topic, keywords)

    # Print summary
    if result["success"]:
        print("\nAnalysis Summary:")
        print("=" * 50)
        print(f"Topic: {result['topic']}")
        print(f"Keywords Analyzed: {', '.join(result['keywords_analyzed'])}")
        print("\nData Collected:")
        print(f"- YouTube: {result['data_summary']['youtube_videos']} videos, "
              f"{result['data_summary']['youtube_comments']} comments")
        print(f"- Reddit: {result['data_summary']['reddit_posts']} posts, "
              f"{result['data_summary']['reddit_comments']} comments")

        filename = f"base_analysis_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        analyzer.save_result(result, filename)

    else:
        print(f"Analysis failed: {result.get('error', 'Unknown error')}")




if __name__ == "__main__":
    main()
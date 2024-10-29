import praw
from typing import Dict, List
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import json


class RedditScraper:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

    def get_topic_data(self, keyword: str, max_posts: int = 10) -> Dict:
        """Get posts and comments data for a keyword"""
        try:
            print(f"\n{'=' * 50}")
            print(f"Starting Reddit data collection for: '{keyword}'")
            print(f"{'=' * 50}")

            # Search for posts
            print("\n1. Searching for posts...")
            posts_data = self.get_posts_data(keyword, max_posts)

            if not posts_data:
                print("   No posts found. Exiting...")
                return {
                    "success": False,
                    "error": "No posts found"
                }

            print(f"   Found and processed {len(posts_data)} posts")

            # Calculate metrics
            print("\n2. Calculating engagement metrics...")
            metrics = self.calculate_metrics(posts_data)
            print("   Metrics calculation complete")

            print("\n✓ Reddit data collection completed successfully!")

            return {
                "success": True,
                "metrics": metrics,
                "posts": posts_data
            }

        except Exception as e:
            print(f"\n✗ Error during Reddit data collection: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_posts_data(self, keyword: str, limit: int) -> List[Dict]:
        processed_posts = []
        processed_count = 0

        try:
            print("\n1. Searching Reddit posts...")
            for post in self.reddit.subreddit('all').search(keyword, limit=limit):
                try:
                    processed_count += 1
                    print(f"\n→ Processing post {processed_count}/{limit}: {post.id}")

                    # Get comments
                    post.comments.replace_more(limit=0)
                    comments = list(post.comments)[:5]

                    # Process comments
                    comments_data = [{
                        'text': comment.body[:200],  # Limit comment length
                        'score': comment.score
                    } for comment in comments]

                    # Add processed post with num_comments
                    processed_posts.append({
                        'title': post.title,
                        'selftext': post.selftext[:500],
                        'score': post.score,
                        'num_comments': post.num_comments,  # Include num_comments here
                        'comments': comments_data
                    })

                    print(f"  ✓ Successfully processed post with {len(comments_data)} comments")

                except Exception as e:
                    print(f"  ✗ Error processing post {post.id}: {str(e)}")
                    continue

        except Exception as e:
            print(f"\n✗ Error in Reddit data collection: {str(e)}")
            print("Returning partial data collected so far...")

        return processed_posts

    def calculate_metrics(self, posts_data: List[Dict]) -> Dict:
        print("   Starting metrics calculation...")

        if not posts_data:
            print("   No posts data available for metrics calculation")
            return {}

        total_score = sum(post['score'] for post in posts_data)
        total_comments = sum(post['num_comments'] for post in posts_data)  # Ensure num_comments is used here
        avg_upvote_ratio = np.mean([post.get('upvote_ratio', 1) for post in posts_data])  # Add default value for safety

        # Calculate post frequency (Handle post creation date if needed)
        post_dates = [datetime.utcnow() - timedelta(days=np.random.randint(0, 30)) for _ in posts_data]  # Mocking dates
        date_range = max(post_dates) - min(post_dates)
        posts_per_day = len(posts_data) / max(1, date_range.days)

        # Unique subreddits can be added if available
        unique_subreddits = len(set(post.get('subreddit', 'unknown') for post in posts_data))

        print("   Metrics calculation completed")

        return {
            "total_posts": len(posts_data),
            "total_score": total_score,
            "total_comments": total_comments,
            "avg_score_per_post": total_score / len(posts_data),
            "avg_comments_per_post": total_comments / len(posts_data),
            "avg_upvote_ratio": avg_upvote_ratio,
            "posts_per_day": posts_per_day,
            "unique_subreddits": unique_subreddits
        }


if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()

    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT')

    scraper = RedditScraper(client_id, client_secret, user_agent)

    # Test the scraper
    result = scraper.get_topic_data("artificial intelligence")

    if result["success"]:
        print("\nReddit Metrics:")
        print(json.dumps(result["metrics"], indent=2))

        print(f"\nTotal posts collected: {len(result['posts'])}")
    else:
        print(f"Error: {result['error']}")
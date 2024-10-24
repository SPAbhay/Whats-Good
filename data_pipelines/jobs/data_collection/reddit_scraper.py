import praw
import json
from typing import List, Dict
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

class RedditConfig:
    def __init__(self, client_id: str, client_secret: str, user_agent: str, output_file: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.output_file = output_file

class RedditConfig:
    def __init__(self, client_id: str, client_secret: str, user_agent: str, output_file: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.output_file = output_file

class RedditScraper:
    def __init__(self, config: RedditConfig):
        self.config = config
        self.reddit = praw.Reddit(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            user_agent=self.config.user_agent
        )

    def scrape_subreddit(self, subreddit_name: str, time_filter: str = 'week', limit: int = 100) -> List[Dict]:
        """
        Scrape posts from a specified subreddit.
        """
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []

        for post in subreddit.top(time_filter=time_filter, limit=limit):
            post_data = {
                'title': post.title,
                'author': str(post.author),
                'created_utc': datetime.fromtimestamp(post.created_utc).isoformat(),
                'score': post.score,
                'url': post.url,
                'selftext': post.selftext,
                'num_comments': post.num_comments,
                'comments': self.get_top_comments(post, 5)
            }
            posts.append(post_data)

        return posts

    def get_top_comments(self, post: praw.models.Submission, limit: int = 5) -> List[Dict]:
        """
        Get top comments for a post.
        """
        post.comment_sort = 'top'
        post.comments.replace_more(limit=0)
        return [{
            'author': str(comment.author),
            'body': comment.body,
            'score': comment.score,
            'created_utc': datetime.fromtimestamp(comment.created_utc).isoformat()
        } for comment in post.comments[:limit]]

    def scrape_multiple_subreddits(self, subreddit_list: List[str], time_filter: str = 'week', limit: int = 100) -> Dict[str, List[Dict]]:
        """
        Scrape posts from multiple subreddits using parallel processing.
        """
        all_posts = {}
        with ThreadPoolExecutor(max_workers=min(len(subreddit_list), 10)) as executor:
            future_to_subreddit = {executor.submit(self.scrape_subreddit, subreddit, time_filter, limit): subreddit for subreddit in subreddit_list}
            for future in as_completed(future_to_subreddit):
                subreddit = future_to_subreddit[future]
                try:
                    all_posts[subreddit] = future.result()
                    print(f"Finished scraping r/{subreddit}")
                except Exception as e:
                    print(f"Error scraping r/{subreddit}: {e}")
        return all_posts

    def save_to_json(self, articles: List[Dict]):
        output_file_path = os.path.join('..', '..', 'data/', self.config.output_file)

        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(articles, json_file, ensure_ascii=False, indent=4)
        print(f"Articles saved to {self.config.output_file}")

    def run(self, subreddit_list: List[str], time_filter: str = 'week', limit: int = 100):
        """
        Run the Reddit scraper for the given subreddits.
        """
        all_posts = self.scrape_multiple_subreddits(subreddit_list, time_filter, limit)
        self.save_to_json(all_posts)

if __name__ == '__main__':
    config = RedditConfig(
        client_id=os.environ['REDDIT_CLIENT_ID'],
        client_secret=os.environ['REDDIT_CLIENT_SECRET'],
        user_agent=os.environ['REDDIT_USER_AGENT'],
        output_file="../../data/reddit_api_posts_raw.json"
    )

    scraper = RedditScraper(config)
    subreddits_to_scrape = ['technology', 'AskReddit']
    scraper.run(subreddits_to_scrape, time_filter='week', limit=50)
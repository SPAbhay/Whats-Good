# !pip install -r /Workspace/Users/tisha.chordia@epsilon.com/Whats-Good/requirements.txt
# dbutils.library.restartPython()

import praw
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

class RedditCollector:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )

    def get_trending_topics(self, subreddit: str = 'all', limit: int = 10) -> List[Dict]:
        trending_topics = []
        for submission in self.reddit.subreddit(subreddit).hot(limit=limit):
            trending_topics.append({
                'title': submission.title,
                'score': submission.score,
                'url': submission.url,
                'subreddit': submission.subreddit.display_name
            })
        return trending_topics
    
if __name__ == "__main__":
    collector = RedditCollector()
    trends = collector.get_trending_topics()
    print(trends)
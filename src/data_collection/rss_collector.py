# !pip install -r /Workspace/Users/tisha.chordia@epsilon.com/Whats-Good/requirements.txt
# dbutils.library.restartPython()

import feedparser
from typing import List, Dict
from datetime import datetime, timezone
from dotenv import load_dotenv
from dateutil import parser

load_dotenv()

class RSSCollector:
    def __init__(self, feed_urls: List[str]):
        self.feed_urls = feed_urls

    def get_recent_entries(self, max_entries: int = 10) -> List[Dict]:
        all_entries = []
        for url in self.feed_urls:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_entries]:
                all_entries.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.get('published', 'N/A'),
                    'summary': entry.get('summary', 'N/A'),
                    'source': feed.feed.title
                })
        # Sort by published date, most recent first
        all_entries.sort(
            key=lambda article: parser.parse(article['published']) if article['published'] != 'N/A' else datetime(1970, 1, 1, tzinfo=timezone.utc),
            reverse=True
        )
        
        return all_entries[:max_entries]

if __name__ == "__main__":
    feed_urls = [
        'http://rss.cnn.com/rss/cnn_topstories.rss',
        'http://feeds.bbci.co.uk/news/rss.xml',
        'https://www.techcrunch.com/feed/'
    ]
    collector = RSSCollector(feed_urls)
    recent_news = collector.get_recent_entries()
    print(recent_news)

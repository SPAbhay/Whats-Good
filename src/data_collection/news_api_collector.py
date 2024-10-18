# !pip install -r /Workspace/Users/tisha.chordia@epsilon.com/Whats-Good/requirements.txt
# dbutils.library.restartPython()

from newsapi import NewsApiClient
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

class NewsAPICollector:
    def __init__(self):
        api_key = os.environ.get('NEWSAPI_API_KEY')
        self.newsapi = NewsApiClient(api_key=api_key)

    def get_top_headlines(self, country: str = 'us', category: str = 'general', page_size: int = 10) -> List[Dict]:
        top_headlines = self.newsapi.get_top_headlines(country=country, 
                                                       category=category, 
                                                       page_size=page_size)
        
        return [{
            'title': article['title'],
            'source': article['source']['name'],
            'published_at': article['publishedAt']
        } for article in top_headlines['articles']]

# Usage
if __name__ == "__main__":
    collector = NewsAPICollector()
    headlines = collector.get_top_headlines()
    print(headlines)
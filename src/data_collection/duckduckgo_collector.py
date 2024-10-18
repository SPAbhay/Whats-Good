from duckduckgo_search import DDGS
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class DuckDuckGoCollector:
    def __init__(self):
        pass

    def search_recent_news(self, query: str, num_results: int = 10) -> List[Dict]:
        with DDGS() as ddgs:
            results = ddgs.news(query, max_results=num_results)
            return [
                {
                    'title': result['title'],
                    'url': result['url'],
                    'snippet': result['body'],
                    'source': result['source'],
                }
                for result in results
            ]

    def enrich_trend_info(self, trend: str) -> Dict:
        search_results = self.search_recent_news(trend, num_results=5)
        return {
            'trend': trend,
            'recent_articles': search_results
        }

if __name__ == "__main__":
    collector = DuckDuckGoCollector()
    trend_info = collector.enrich_trend_info("AI in healthcare")
    print(trend_info)
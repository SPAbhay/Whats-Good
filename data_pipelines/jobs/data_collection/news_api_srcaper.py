import requests
import json
from typing import List, Dict
from datetime import datetime, timedelta
from newspaper import Article
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from dotenv import load_dotenv

load_dotenv()

class NewsAPIConfig:
    def __init__(self, api_key: str, output_file: str):
        self.api_key = api_key
        self.output_file = output_file
        self.base_url = "https://newsapi.org/v2/everything"

class NewsAPIScraper:
    def __init__(self, config: NewsAPIConfig):
        self.config = config

    def fetch_articles(self, query: str, from_date: str, to_date: str, language: str = 'en') -> List[Dict]:
        """
        Fetch articles from News API based on the given parameters.
        """
        params = {
            'q': query,
            'from': from_date,
            'to': to_date,
            'language': language,
            'sortBy': 'publishedAt',
            'apiKey': self.config.api_key
        }

        response = requests.get(self.config.base_url, params=params)
        if response.status_code == 200:
            return response.json()['articles']
        else:
            print(f"Error fetching articles: {response.status_code}")
            return []

    def scrape_full_article(self, url: str) -> str:
        """
        Scrape the full article content from the given URL.
        """
        try:
            article = Article(url)
            article.download()
            article.parse()
            return article.text
        except Exception as e:
            print(f"Error scraping article from {url}: {e}")
            return ""

    def process_articles(self, articles: List[Dict], category: str) -> List[Dict]:
        """
        Process the fetched articles to extract relevant information and scrape full content.
        """
        processed_articles = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_article = {executor.submit(self.scrape_full_article, article['url']): article for article in articles}
            for future in as_completed(future_to_article):
                article = future_to_article[future]
                try:
                    full_content = future.result()
                    processed_article = {
                        'title': article['title'],
                        'author': article['author'],
                        'source': article['source']['name'],
                        'publish_date': article['publishedAt'],
                        'content': full_content,
                        'category': category
                    }
                    processed_articles.append(processed_article)
                except Exception as e:
                    print(f"Error processing article {article['url']}: {e}")
        return processed_articles

    def save_to_json(self, articles: List[Dict]):
        output_file_path = os.path.join('..', '..', 'data/', self.config.output_file)

        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(articles, json_file, ensure_ascii=False, indent=4)
        print(f"Articles saved to {self.config.output_file}")

    def run(self, queries: List[str], days_back: int = 7):
        to_date = datetime.now().strftime('%Y-%m-%d')
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        all_processed_articles = []
        for query in queries:
            print(f"Fetching articles for category: {query}")
            fetched_articles = self.fetch_articles(query, from_date, to_date)
            processed_articles = self.process_articles(fetched_articles, category=query)
            all_processed_articles.extend(processed_articles)

        self.save_to_json(all_processed_articles)

if __name__ == "__main__":
    config = NewsAPIConfig(
        api_key=os.environ['NEWSAPI_API_KEY'],
        output_file="newsapi_api_articles_raw.json"
    )

    scraper = NewsAPIScraper(config)
    scraper.run(["technology", "sports"], days_back=3)


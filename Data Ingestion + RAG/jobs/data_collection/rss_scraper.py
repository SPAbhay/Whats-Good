import feedparser
import newspaper
import json
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

class RSSScraperConfig:
    def __init__(self, rss_feeds: Dict[str, List[str]], output_file: str):
        self.rss_feeds = rss_feeds
        self.output_file = output_file

class ArticleScraper:
    @staticmethod
    def scrape_article_content(article_url: str, category: str) -> Dict:
        """Extracts article content using Newspaper3k."""
        article = newspaper.Article(article_url)
        article.download()
        article.parse()
        return {
            'title': article.title,
            'author': article.authors,
            'source': article_url,
            'publish_date': str(article.publish_date),
            'content': article.text,
            'category': category

        }

class RSSFeedScraper:
    def __init__(self, feed_url: str, category: str):
        self.feed_url = feed_url
        self.category = category

    def scrape(self) -> List[Dict]:
        """Scrapes articles from the RSS feed URL."""
        feed = feedparser.parse(self.feed_url)
        articles = []
        for entry in feed.entries:
            try:
                article_data = ArticleScraper.scrape_article_content(entry.link, self.category)
                article_data['category'] = self.category  # Add category to the article data
                articles.append(article_data)
            except Exception as e:
                print(f"Error processing {entry.link}: {e}")
        return articles

class RSSScraperOrchestrator:
    def __init__(self, config: RSSScraperConfig):
        self.config = config

    def scrape_all_feeds(self) -> List[Dict]:
        all_articles = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for category, urls in self.config.rss_feeds.items():
                for url in urls:
                    futures.append(executor.submit(RSSFeedScraper(url, category).scrape))

            for future in as_completed(futures):
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                    print(f"Scraped {len(articles)} articles from from {url} (Category: {category})")
                except Exception as e:
                    print(f"Error during scraping: {e}")
        return all_articles

    def save_to_json(self, articles: List[Dict]):
        output_file_path = os.path.join('..', '..', 'data/', self.config.output_file)

        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(articles, json_file, ensure_ascii=False, indent=4)
        print(f"Articles saved to {self.config.output_file}")

    def run(self):
        articles = self.scrape_all_feeds()
        self.save_to_json(articles)

if __name__ == '__main__':
    config = RSSScraperConfig(
        rss_feeds={
            'category1': [
                'https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID'
            ]
        },
        output_file='rss_api_articles_raw.json'
    )

    orchestrator = RSSScraperOrchestrator(config)
    orchestrator.run()
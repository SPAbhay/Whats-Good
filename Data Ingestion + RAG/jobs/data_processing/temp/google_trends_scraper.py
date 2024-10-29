from pytrends.request import TrendReq
import pandas as pd
import json
from typing import List, Dict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

class GoogleTrendsConfig:
    def __init__(self, hl: str, tz: int, output_file: str):
        self.hl = hl  # Language for Google Trends
        self.tz = tz  # Timezone offset
        self.output_file = output_file


class GoogleTrendsScraper:
    def __init__(self, config: GoogleTrendsConfig):
        self.config = config
        self.pytrends = TrendReq(hl=self.config.hl, tz=self.config.tz)

    def fetch_interest_over_time(self, keyword: str, timeframe: str = 'today 3-m') -> Dict:
        self.pytrends.build_payload([keyword], timeframe=timeframe)
        interest_over_time_df = self.pytrends.interest_over_time()

        if interest_over_time_df.empty:
            return {"error": f"No data available for keyword: {keyword}"}

        return {
            "keyword": keyword,
            "data": interest_over_time_df[keyword].to_dict()
        }

    def fetch_related_queries(self, keyword: str) -> Dict:
        self.pytrends.build_payload([keyword])
        related_queries = self.pytrends.related_queries()

        if not related_queries[keyword]:
            return {"error": f"No related queries available for keyword: {keyword}"}

        return {
            "keyword": keyword,
            "top": related_queries[keyword]['top'].to_dict() if related_queries[keyword]['top'] is not None else {},
            "rising": related_queries[keyword]['rising'].to_dict() if related_queries[keyword][
                                                                          'rising'] is not None else {}
        }

    def fetch_trending_searches(self, country: str = 'united_states') -> List[str]:
        trending_searches_df = self.pytrends.trending_searches(pn=country)
        return trending_searches_df[0].tolist()

    def scrape_multiple_keywords(self, keywords: List[str], timeframe: str = 'today 3-m') -> Dict[str, Dict]:
        all_trend_data = {}
        with ThreadPoolExecutor(max_workers=min(len(keywords), 5)) as executor:
            future_to_keyword = {
                executor.submit(self.fetch_interest_over_time, keyword, timeframe): keyword for keyword in keywords
            }
            future_to_keyword.update({
                executor.submit(self.fetch_related_queries, keyword): keyword for keyword in keywords
            })

            for future in as_completed(future_to_keyword):
                keyword = future_to_keyword[future]
                try:
                    result = future.result()
                    if keyword not in all_trend_data:
                        all_trend_data[keyword] = {}
                    if "data" in result:
                        all_trend_data[keyword]["interest_over_time"] = result
                    elif "top" in result:
                        all_trend_data[keyword]["related_queries"] = result
                    print(f"Finished scraping trend data for keyword: {keyword}")
                except Exception as e:
                    print(f"Error scraping trend data for keyword {keyword}: {e}")

        return all_trend_data

    def save_to_json(self, articles: List[Dict]):
        output_file_path = os.path.join('..', '..', 'data/', self.config.output_file)

        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(articles, json_file, ensure_ascii=False, indent=4)
        print(f"Articles saved to {self.config.output_file}")

    def run(self, keywords: List[str], timeframe: str = 'today 3-m'):
        all_trend_data = self.scrape_multiple_keywords(keywords, timeframe)

        # Fetch trending searches
        trending_searches = self.fetch_trending_searches()
        all_trend_data["trending_searches"] = trending_searches

        self.save_to_json(all_trend_data)

if __name__ == '__main__':
    config = GoogleTrendsConfig(
        hl='en-US',
        tz=360,
        output_file="google_trends_api_raw.json"
    )

    scraper = GoogleTrendsScraper(config)
    keywords_to_scrape = ['technology']
    scraper.run(keywords_to_scrape, timeframe='today 3-d')
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
from typing import List, Dict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from dotenv import load_dotenv

load_dotenv()

class YouTubeConfig:
    def __init__(self, api_key: str, output_file: str):
        self.api_key = api_key
        self.output_file = output_file

class YouTubeScraper:
    def __init__(self, config: YouTubeConfig):
        self.config = config
        self.youtube = build('youtube', 'v3', developerKey=self.config.api_key)

    def search_videos(self, query: str, max_results: int = 50) -> List[Dict]:
        """
        Search for videos based on a query.
        """
        try:
            search_response = self.youtube.search().list(
                q=query,
                type='video',
                part='id,snippet',
                maxResults=max_results
            ).execute()

            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            return self.get_video_details(video_ids)
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return []

    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """
        Get detailed information for a list of video IDs.
        """
        try:
            videos_response = self.youtube.videos().list(
                id=','.join(video_ids),
                part='snippet,statistics'
            ).execute()

            return [self.process_video_item(item) for item in videos_response.get('items', [])]
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return []

    def process_video_item(self, item: Dict) -> Dict:
        """
        Process a single video item to extract relevant information.
        """
        snippet = item['snippet']
        statistics = item['statistics']
        return {
            'title': snippet['title'],
            'description': snippet['description'],
            'publishedAt': snippet['publishedAt'],
            'channelTitle': snippet['channelTitle'],
            'viewCount': statistics.get('viewCount', 0),
            'likeCount': statistics.get('likeCount', 0),
            'commentCount': statistics.get('commentCount', 0),
            'videoId': item['id']
        }

    def get_video_comments(self, video_id: str, max_results: int = 100) -> List[Dict]:
        """
        Get comments for a specific video.
        """
        try:
            comments_response = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=max_results
            ).execute()

            return [{
                'author': item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                'text': item['snippet']['topLevelComment']['snippet']['textDisplay'],
                'likeCount': item['snippet']['topLevelComment']['snippet']['likeCount'],
                'publishedAt': item['snippet']['topLevelComment']['snippet']['publishedAt']
            } for item in comments_response.get('items', [])]
        except HttpError as e:
            print(f"An HTTP error {e.resp.status} occurred: {e.content}")
            return []

    def scrape_multiple_queries(self, queries: List[str], max_results_per_query: int = 50) -> Dict[str, List[Dict]]:
        """
        Scrape videos for multiple queries using parallel processing.
        """
        all_videos = {}
        with ThreadPoolExecutor(max_workers=min(len(queries), 5)) as executor:
            future_to_query = {executor.submit(self.search_videos, query, max_results_per_query): query for query in queries}
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    all_videos[query] = future.result()
                    print(f"Finished scraping videos for query: {query}")
                except Exception as e:
                    print(f"Error scraping videos for query {query}: {e}")
        return all_videos

    def save_to_json(self, articles: List[Dict]):
        output_file_path = os.path.join('..', '..', 'data/', self.config.output_file)

        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        with open(output_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(articles, json_file, ensure_ascii=False, indent=4)
        print(f"Articles saved to {self.config.output_file}")

    def run(self, queries: List[str], max_results_per_query: int = 50):
        """
        Run the YouTube scraper for the given queries.
        """
        all_videos = self.scrape_multiple_queries(queries, max_results_per_query)
        self.save_to_json(all_videos)

if __name__ == "__main__":
    config = YouTubeConfig(
        api_key=os.environ['YOUTUBE_API_KEY'],
        output_file="youtube_api_raw.json"
    )

    scraper = YouTubeScraper(config)
    queries_to_scrape = ['machine learning', 'artificial intelligence']
    scraper.run(queries_to_scrape, max_results_per_query=30)
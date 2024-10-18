from googleapiclient.discovery import build
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

class YouTubeCollector:
    def __init__(self):
        api_key = os.environ.get('YOUTUBE_API_KEY')
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def get_trending_videos(self, region_code: str = 'US', max_results: int = 10) -> List[Dict]:
        request = self.youtube.videos().list(
            part='snippet',
            chart='mostPopular',
            regionCode=region_code,
            maxResults=max_results
        )
        response = request.execute()

        trending_videos = []
        for item in response['items']:
            trending_videos.append({
                'title': item['snippet']['title'],
                'channel': item['snippet']['channelTitle'],
                'publish_time': item['snippet']['publishedAt']
            })
        return trending_videos

if __name__ == "__main__":
    collector = YouTubeCollector()
    trends = collector.get_trending_videos()
    print(trends)
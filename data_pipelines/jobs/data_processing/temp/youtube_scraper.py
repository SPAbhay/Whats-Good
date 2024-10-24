from googleapiclient.discovery import build
from typing import Dict, List
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import json

class YouTubeScraper:
    def __init__(self, api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def get_videos_data(self, keyword: str, max_results: int = 8) -> Dict:
        """Get video data and comments for a keyword"""
        try:
            print(f"\n{'=' * 50}")
            print(f"Starting YouTube data collection for: '{keyword}'")
            print(f"{'=' * 50}")

            # Search for videos
            print("\n1. Searching for videos...")
            search_response = self.youtube.search().list(
                q=keyword,
                type='video',
                part='id',
                maxResults=max_results,
                order='relevance'
            ).execute()

            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            print(f"   Found {len(video_ids)} videos")

            if not video_ids:
                print("   No videos found. Exiting...")
                return {
                    "success": False,
                    "error": "No videos found"
                }

            # Get video details
            print("\n2. Fetching video details...")
            videos_data = self.get_videos_details(video_ids)
            print(f"   Processed details for {len(videos_data)} videos")

            # Get comments
            print("\n3. Fetching video comments...")
            comments_data = self.get_videos_comments(video_ids[:10])
            print(f"   Collected {len(comments_data)} comments from top videos")

            # Calculate metrics
            print("\n4. Calculating engagement metrics...")
            metrics = self.calculate_metrics(videos_data)
            print("   Metrics calculation complete")

            print("\n✓ YouTube data collection completed successfully!")

            return {
                "success": True,
                "metrics": metrics,
                "videos": videos_data,
                "comments": comments_data
            }

        except Exception as e:
            print(f"\n✗ Error during YouTube data collection: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_videos_details(self, video_ids: List[str]) -> List[Dict]:
        """Get detailed information for videos"""
        videos_response = self.youtube.videos().list(
            id=','.join(video_ids),
            part='snippet,statistics'
        ).execute()

        return [{
            'video_id': item['id'],
            'title': item['snippet']['title'],
            'views': int(item['statistics'].get('viewCount', 0)),
            'likes': int(item['statistics'].get('likeCount', 0)),
            'comments_count': int(item['statistics'].get('commentCount', 0)),
            'publish_date': item['snippet']['publishedAt'],
            'description': item['snippet']['description']
        } for item in videos_response.get('items', [])]

    def get_videos_comments(self, video_ids: List[str], comments_per_video: int = 50) -> List[Dict]:
        """Get comments for videos"""
        all_comments = []

        for i, video_id in enumerate(video_ids, 1):
            try:
                print(f"   Processing comments for video {i}/{len(video_ids)}")
                comments_response = self.youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=comments_per_video,
                    order='relevance'
                ).execute()

                video_comments = [{
                    'video_id': video_id,
                    'text': item['snippet']['topLevelComment']['snippet']['textDisplay'],
                    'likes': item['snippet']['topLevelComment']['snippet']['likeCount'],
                    'publish_date': item['snippet']['topLevelComment']['snippet']['publishedAt']
                } for item in comments_response.get('items', [])]

                all_comments.extend(video_comments)
                print(f"      Retrieved {len(video_comments)} comments")

            except Exception as e:
                print(f"      ✗ Error getting comments for video {video_id}: {str(e)}")
                continue

        return all_comments

    def calculate_metrics(self, videos_data: List[Dict]) -> Dict:
        """Calculate engagement metrics"""
        if not videos_data:
            return {}

        total_views = sum(video['views'] for video in videos_data)
        total_likes = sum(video['likes'] for video in videos_data)
        total_comments = sum(video['comments_count'] for video in videos_data)

        # Calculate engagement rate
        engagement_rate = ((total_likes + total_comments) / total_views) if total_views > 0 else 0

        # Calculate view velocity (views per day since publish)
        current_time = datetime.utcnow()

        view_velocities = []
        for video in videos_data:
            publish_date = datetime.strptime(video['publish_date'], '%Y-%m-%dT%H:%M:%SZ')
            days_since_publish = max(1, (current_time - publish_date).days)
            view_velocity = video['views'] / days_since_publish
            view_velocities.append(view_velocity)

        avg_view_velocity = np.mean(view_velocities) if view_velocities else 0

        return {
            "total_videos": len(videos_data),
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "engagement_rate": engagement_rate,
            "avg_view_velocity": avg_view_velocity,
            "avg_views_per_video": total_views / len(videos_data),
            "avg_likes_per_video": total_likes / len(videos_data),
            "avg_comments_per_video": total_comments / len(videos_data)
        }


if __name__ == "__main__":
    from dotenv import load_dotenv
    import os

    load_dotenv()

    api_key = os.getenv('YOUTUBE_API_KEY')
    scraper = YouTubeScraper(api_key)

    # Test the scraper
    result = scraper.get_videos_data("artificial intelligence")

    if result["success"]:
        print("\nYouTube Metrics:")
        print(json.dumps(result["metrics"], indent=2))

        print(f"\nTotal comments collected: {len(result['comments'])}")
    else:
        print(f"Error: {result['error']}")
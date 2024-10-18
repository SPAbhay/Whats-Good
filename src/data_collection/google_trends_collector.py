# !pip install -r /Workspace/Users/tisha.chordia@epsilon.com/Whats-Good/requirements.txt
# dbutils.library.restartPython()

from pytrends.request import TrendReq
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class GoogleTrendsCollector:
    def __init__(self):
        self.pytrends = TrendReq(hl='en-US', tz=360)

    def get_trending_topics(self, geo: str = 'united_states') -> List[Dict]:
        trending_searches = self.pytrends.trending_searches(pn=geo)
        return [{'topic': topic} for topic in trending_searches[0].tolist()]

# Usage
if __name__ == "__main__":
    collector = GoogleTrendsCollector()
    trends = collector.get_trending_topics()
    print(trends)
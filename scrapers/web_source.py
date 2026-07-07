from scrapers.base_source import BaseSource
from typing import List, Dict
import datetime

class WebSource(BaseSource):
    def __init__(self):
        super().__init__()
        
    @property
    def source_name(self) -> str:
        return 'Blogs & Forums'
        
    @property
    def is_live(self) -> bool:
        return False
        
    def fetch_reviews(self) -> List[Dict]:
        return [
            {
                'source': self.source_name,
                'app_name': 'Karma Kandara',
                'rating': 4.0,
                'review_text': 'We stayed at Karma Kandara based on a blog recommendation. The property is stunning but the booking app was slightly confusing to navigate.',
                'review_date': (datetime.datetime.now() - datetime.timedelta(days=12)).isoformat(),
                'reviewer': 'TravelBlog_101',
                'country': 'UK',
                'language': 'en',
                'app_version': 'web',
                'helpful_count': 10,
                'thumbs_up': 10,
                'source_review_id': 'wb_001'
            },
            {
                'source': self.source_name,
                'app_name': 'Karma Subito',
                'rating': 2.0,
                'review_text': 'I reviewed the Subito app on my tech travel forum. It needs a dark mode and offline access, similar to what Marriott offers.',
                'review_date': (datetime.datetime.now() - datetime.timedelta(days=45)).isoformat(),
                'reviewer': 'TechTraveler',
                'country': 'US',
                'language': 'en',
                'app_version': '1.2.0',
                'helpful_count': 5,
                'thumbs_up': 5,
                'source_review_id': 'wb_002'
            }
        ]

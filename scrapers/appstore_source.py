import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scrapers.base_source import BaseSource
from typing import List, Dict
import requests
from datetime import datetime

class AppStoreSource(BaseSource):
    def __init__(self, app_id: str = '6737755581', app_name: str = 'Karma Subito'):
        super().__init__()
        self.app_id = app_id
        self.app_name = app_name
        
    @property
    def source_name(self) -> str:
        return 'Apple App Store'
        
    @property
    def is_live(self) -> bool:
        return True
        
    def fetch_reviews(self) -> List[Dict]:
        reviews = []
        try:
            # Fallback to Apple RSS feed since app-store-scraper has dependency conflicts
            url = f"https://itunes.apple.com/us/rss/customerreviews/id={self.app_id}/sortBy=mostRecent/json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                entries = data.get('feed', {}).get('entry', [])
                # The first entry is often metadata about the app
                for entry in entries[1:]:
                    review_text = entry.get('content', {}).get('label', '')
                    title = entry.get('title', {}).get('label', '')
                    full_text = f"{title} - {review_text}"
                    
                    rating = float(entry.get('im:rating', {}).get('label', '0'))
                    reviewer = entry.get('author', {}).get('name', {}).get('label', 'Unknown')
                    review_id = entry.get('id', {}).get('label', '')
                    app_version = entry.get('im:version', {}).get('label', 'Unknown')
                    
                    # RSS feed doesn't provide exact date reliably in this format, use current
                    review_date = datetime.now().isoformat()
                    
                    reviews.append({
                        'source': self.source_name,
                        'app_name': self.app_name,
                        'rating': rating,
                        'review_text': full_text,
                        'review_date': review_date,
                        'reviewer': reviewer,
                        'country': 'US',
                        'language': 'en',
                        'app_version': app_version,
                        'helpful_count': 0,
                        'thumbs_up': 0,
                        'source_review_id': f"as_{review_id}"
                    })
        except Exception as e:
            print(f"Error fetching from App Store RSS: {e}")
            
        return reviews

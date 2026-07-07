"""
Google Play Store review scraper for Karma Group apps.
Uses google-play-scraper to fetch real reviews from the Play Store.
"""
import logging
from typing import List, Dict
from datetime import datetime

from scrapers.base_source import BaseSource

logger = logging.getLogger(__name__)

# App ID to friendly name mapping
APP_ID_MAP = {
    "com.karmaclub": "Karma Subito",
    "com.kg.pitchbook": "Karma Group Portfolio",
    "com.redlamp.handigo.karmakandara": "Karma Kandara",
}

REVIEWS_PER_APP = 500


class PlayStoreSource(BaseSource):
    """Fetches real reviews from Google Play Store for Karma Group apps."""

    @property
    def source_name(self) -> str:
        return "Google Play Store"

    @property
    def is_live(self) -> bool:
        return True

    def fetch_reviews(self) -> List[Dict]:
        """Fetch up to 500 reviews per app across all sort orders."""
        try:
            from google_play_scraper import reviews, Sort
        except ImportError:
            logger.error(
                "google-play-scraper is not installed. "
                "Run: pip install google-play-scraper"
            )
            return []

        all_reviews: List[Dict] = []

        for app_id, app_name in APP_ID_MAP.items():
            for sort_order in (Sort.NEWEST, Sort.MOST_RELEVANT):
                try:
                    result, _ = reviews(
                        app_id,
                        lang="en",
                        country="us",
                        sort=sort_order,
                        count=REVIEWS_PER_APP,
                    )
                    for r in result:
                        review_date = r.get("at")
                        if isinstance(review_date, datetime):
                            review_date_str = review_date.isoformat()
                        elif review_date is not None:
                            review_date_str = str(review_date)
                        else:
                            review_date_str = None

                        mapped = {
                            "source": self.source_name,
                            "app_name": app_name,
                            "rating": r.get("score"),
                            "review_text": r.get("content", ""),
                            "review_date": review_date_str,
                            "reviewer": r.get("userName", "Anonymous"),
                            "country": "US",
                            "language": "en",
                            "app_version": r.get("reviewCreatedVersion"),
                            "helpful_count": r.get("thumbsUpCount", 0),
                            "source_review_id": r.get("reviewId"),
                        }
                        all_reviews.append(mapped)

                    logger.info(
                        "Fetched %d reviews for %s (sort=%s)",
                        len(result),
                        app_name,
                        sort_order.name if hasattr(sort_order, "name") else sort_order,
                    )

                except Exception as exc:
                    logger.warning(
                        "Failed to fetch reviews for %s (%s, sort=%s): %s",
                        app_name,
                        app_id,
                        sort_order,
                        exc,
                    )
                    continue

        # Deduplicate by reviewId (same review may appear in multiple sort orders)
        seen_ids: set = set()
        unique_reviews: List[Dict] = []
        for rev in all_reviews:
            rid = rev.get("source_review_id")
            if rid and rid in seen_ids:
                continue
            if rid:
                seen_ids.add(rid)
            unique_reviews.append(rev)

        logger.info(
            "PlayStoreSource: total unique reviews fetched = %d", len(unique_reviews)
        )
        self._reviews = unique_reviews
        return unique_reviews

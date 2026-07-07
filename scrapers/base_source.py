"""
Abstract base class for all review sources in KAIP.
Every scraper/source must inherit from BaseSource and implement
the required properties and methods.
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class BaseSource(ABC):
    """Abstract base class for all review sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the review source."""
        pass

    @property
    def is_live(self) -> bool:
        """Whether this source fetches live data."""
        return False

    @abstractmethod
    def fetch_reviews(self) -> List[Dict]:
        """Fetch reviews from this source.

        Returns list of dicts with keys:
            source, app_name, rating, review_text, review_date,
            reviewer, country, language, app_version,
            helpful_count, thumbs_up, source_review_id
        """
        pass

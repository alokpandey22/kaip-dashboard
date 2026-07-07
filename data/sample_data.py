import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.database import insert_review, insert_classification
from scrapers.playstore_source import PlayStoreSource
from scrapers.appstore_source import AppStoreSource
from scrapers.trustpilot_source import TrustpilotSource
from scrapers.tripadvisor_source import TripAdvisorSource
from scrapers.reddit_source import RedditSource
from scrapers.google_reviews_source import GoogleReviewsSource
from scrapers.social_source import SocialMediaSource
from scrapers.youtube_source import YouTubeSource
from scrapers.web_source import WebSource
from ai.classifier import classify_reviews
import streamlit as st

def generate_all_samples():
    """Generates sample data from all configured stubs and inserts into DB."""
    sources = [
        TrustpilotSource(),
        TripAdvisorSource(),
        RedditSource(),
        GoogleReviewsSource(),
        SocialMediaSource(),
        YouTubeSource(),
        WebSource()
    ]
    
    all_reviews = []
    for source in sources:
        try:
            reviews = source.fetch_reviews()
            all_reviews.extend(reviews)
        except Exception as e:
            print(f"Error fetching from {source.source_name}: {e}")

    # Generate some dummy PlayStore and AppStore ones for completeness in the sample
    # if live isn't used
    all_reviews.extend([
        {
            'source': 'Google Play Store', 'app_name': 'Karma Subito', 'rating': 3.0,
            'review_text': 'App crashes sometimes when booking a resort.', 'review_date': '2026-06-15',
            'reviewer': 'John Doe', 'country': 'US', 'language': 'en', 'app_version': '1.0',
            'helpful_count': 2, 'thumbs_up': 2, 'source_review_id': 'ps_dummy_1'
        },
        {
            'source': 'Apple App Store', 'app_name': 'Karma Subito', 'rating': 1.0,
            'review_text': 'Cannot login, it keeps saying invalid password even after reset.', 'review_date': '2026-06-18',
            'reviewer': 'Jane D', 'country': 'UK', 'language': 'en', 'app_version': '1.1',
            'helpful_count': 5, 'thumbs_up': 5, 'source_review_id': 'as_dummy_1'
        },
        {
            'source': 'Google Play Store', 'app_name': 'Karma Kandara', 'rating': 5.0,
            'review_text': 'Beautiful resort and the app made it so easy to request room service.', 'review_date': '2026-07-01',
            'reviewer': 'Traveler99', 'country': 'AU', 'language': 'en', 'app_version': '2.0',
            'helpful_count': 1, 'thumbs_up': 1, 'source_review_id': 'ps_dummy_2'
        }
    ])

    # Insert into DB
    for review in all_reviews:
        review_id = insert_review(review)
        if review_id:
            # For sample data, we can pre-classify to save Gemini API calls during demo
            # We'll just generate some logical defaults based on the rating and text
            sentiment = 'positive' if review['rating'] >= 4 else ('negative' if review['rating'] <= 2 else 'mixed')
            
            # Simple keyword matching for category/feature area
            text = review['review_text'].lower()
            category = 'general_feedback'
            feature_area = 'general'
            intent = 'praise' if sentiment == 'positive' else 'complaint'
            
            if 'bug' in text or 'crash' in text or 'error' in text:
                category = 'bug'
                intent = 'bug_report'
            elif 'feature' in text or 'add' in text or 'wish' in text:
                category = 'feature_request'
                intent = 'feature_request'
            elif 'slow' in text or 'lag' in text:
                category = 'performance'
            elif 'confus' in text or 'hard to' in text or 'ui' in text:
                category = 'ux_friction'
            elif 'price' in text or 'expensive' in text or 'cost' in text:
                category = 'pricing'
                feature_area = 'pricing'
            
            if 'book' in text or 'reservation' in text:
                feature_area = 'booking_flow'
            elif 'login' in text or 'password' in text:
                feature_area = 'login_auth'
            elif 'pay' in text or 'card' in text:
                feature_area = 'payments'
            
            severity = 'low'
            if sentiment == 'negative':
                severity = 'critical' if category == 'bug' else 'high'
            
            competitor_mention = 'Airbnb' if 'airbnb' in text else ('Marriott' if 'marriott' in text else None)
            
            classification = {
                'sentiment': sentiment,
                'category': category,
                'feature_area': feature_area,
                'severity': severity,
                'intent': intent,
                'pain_point': review['review_text'][:150] + '...' if sentiment != 'positive' else None,
                'competitor_mention': competitor_mention,
                'one_line_summary': f"User thinks: {review['review_text'][:40]}..."
            }
            
            insert_classification(review_id, classification)

if __name__ == '__main__':
    generate_all_samples()
    print("Sample data generated successfully!")

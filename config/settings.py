import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
import streamlit as st
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except (FileNotFoundError, KeyError):
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

# App IDs to scrape
PLAYSTORE_APPS = {
    'com.karmaclub': 'Karma Subito',
    'com.kg.pitchbook': 'Karma Group Portfolio',
    'com.redlamp.handigo.karmakandara': 'Karma Kandara'
}

APPSTORE_APPS = {
    '6737755581': 'Karma Subito'
}

# Database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'kaip.db')

# AI Settings
GROQ_MODEL = 'llama-3.3-70b-versatile'
BATCH_SIZE = 10  # reviews per API call

# Source names
SOURCE_PLAYSTORE = 'Google Play Store'
SOURCE_APPSTORE = 'Apple App Store'
SOURCE_TRUSTPILOT = 'Trustpilot'
SOURCE_TRIPADVISOR = 'TripAdvisor'
SOURCE_REDDIT = 'Reddit'
SOURCE_GOOGLE_REVIEWS = 'Google Reviews'
SOURCE_LINKEDIN = 'LinkedIn'
SOURCE_FACEBOOK = 'Facebook'
SOURCE_TWITTER = 'Twitter/X'
SOURCE_YOUTUBE = 'YouTube'
SOURCE_BLOGS = 'Blogs & News'
SOURCE_FORUMS = 'Travel Forums'

ALL_SOURCES = [
    SOURCE_PLAYSTORE, SOURCE_APPSTORE, SOURCE_TRUSTPILOT,
    SOURCE_TRIPADVISOR, SOURCE_REDDIT, SOURCE_GOOGLE_REVIEWS,
    SOURCE_LINKEDIN, SOURCE_FACEBOOK, SOURCE_TWITTER,
    SOURCE_YOUTUBE, SOURCE_BLOGS, SOURCE_FORUMS
]

LIVE_SOURCES = [SOURCE_PLAYSTORE, SOURCE_APPSTORE]

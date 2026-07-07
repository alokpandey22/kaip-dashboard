import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import pandas as pd
from data.database import get_all_classified, init_db

st.set_page_config(page_title='KAIP | Review Explorer', page_icon='🔍', layout='wide')

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.css')
if os.path.exists(css_path):
    with open(css_path, encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.markdown('# 🔍 Review Explorer')
st.markdown('Search, filter, and explore all AI-classified customer feedback')

init_db()
df = get_all_classified()

if df.empty:
    st.warning('No classified data yet. Go to the home page and load data first.')
    st.stop()

# Filters
st.sidebar.header('Filters')
sources = st.sidebar.multiselect('Source', options=df['source'].unique(), default=list(df['source'].unique()))
apps = st.sidebar.multiselect('App', options=df['app_name'].unique(), default=list(df['app_name'].unique()))

ratings = st.sidebar.slider('Rating Range', 1, 5, (1, 5))

if 'sentiment' in df.columns:
    sentiments = st.sidebar.multiselect('Sentiment', options=df['sentiment'].dropna().unique(), default=list(df['sentiment'].dropna().unique()))
else:
    sentiments = []

if 'category' in df.columns:
    categories = st.sidebar.multiselect('Category', options=df['category'].dropna().unique(), default=list(df['category'].dropna().unique()))
else:
    categories = []

if 'feature_area' in df.columns:
    features = st.sidebar.multiselect('Feature Area', options=df['feature_area'].dropna().unique(), default=list(df['feature_area'].dropna().unique()))
else:
    features = []

search_term = st.sidebar.text_input('Search Text')

# Apply filters
filtered_df = df.copy()
filtered_df = filtered_df[filtered_df['source'].isin(sources)]
filtered_df = filtered_df[filtered_df['app_name'].isin(apps)]
filtered_df = filtered_df[(filtered_df['rating'] >= ratings[0]) & (filtered_df['rating'] <= ratings[1])]

if sentiments:
    filtered_df = filtered_df[filtered_df['sentiment'].isin(sentiments)]
if categories:
    filtered_df = filtered_df[filtered_df['category'].isin(categories)]
if features:
    filtered_df = filtered_df[filtered_df['feature_area'].isin(features)]

if search_term:
    search_mask = filtered_df['review_text'].str.contains(search_term, case=False, na=False) | \
                  filtered_df['one_line_summary'].str.contains(search_term, case=False, na=False) | \
                  filtered_df['pain_point'].str.contains(search_term, case=False, na=False)
    filtered_df = filtered_df[search_mask]

st.markdown(f"**Showing {len(filtered_df):,} of {len(df):,} reviews**")

if filtered_df.empty:
    st.info('No reviews match your filters.')
else:
    display_cols = ['review_date', 'source', 'app_name', 'rating', 'sentiment', 'category', 'severity', 'one_line_summary']
    available_cols = [c for c in display_cols if c in filtered_df.columns]
    
    st.dataframe(filtered_df[available_cols], use_container_width=True)
    
    st.markdown('### Detailed View')
    for _, row in filtered_df.head(50).iterrows():
        title = f"{'⭐'*int(row['rating'])} | {row.get('sentiment', 'Unknown').title()} | {row.get('category', 'Unknown').title()} | {row.get('one_line_summary', 'No summary')}"
        with st.expander(title):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Source:** {row['source']}")
                st.markdown(f"**App:** {row['app_name']}")
                st.markdown(f"**Date:** {row['review_date']}")
                st.markdown(f"**Feature Area:** {row.get('feature_area', 'N/A')}")
                st.markdown(f"**Pain Point:** {row.get('pain_point', 'N/A')}")
            with c2:
                st.markdown(f"**Sentiment:** {row.get('sentiment', 'N/A')}")
                st.markdown(f"**Category:** {row.get('category', 'N/A')}")
                st.markdown(f"**Severity:** {row.get('severity', 'N/A')}")
                st.markdown(f"**Intent:** {row.get('intent', 'N/A')}")
                st.markdown(f"**Competitor Mention:** {row.get('competitor_mention', 'None')}")
            
            st.markdown('**Original Review:**')
            st.info(row['review_text'])
    
    if len(filtered_df) > 50:
        st.caption(f'Showing first 50 detailed views out of {len(filtered_df)}. Use filters to narrow down.')

    # Download button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name="kaip_reviews.csv", mime="text/csv")

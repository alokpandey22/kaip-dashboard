import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import pandas as pd
import plotly.express as px
from data.database import get_all_classified, init_db
from analytics.trends import (
    get_sentiment_over_time, get_rating_over_time,
    get_category_over_time, get_review_volume_over_time,
    detect_emerging_issues
)

st.set_page_config(page_title='KAIP | Trend Analysis', page_icon='📈', layout='wide')

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.css')
if os.path.exists(css_path):
    with open(css_path, encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.markdown('# 📈 Trend Analysis')
st.markdown('Track how customer feedback evolves over time')

init_db()
df = get_all_classified()

if df.empty:
    st.warning('No classified data yet. Go to the home page and load data first.')
    st.stop()

# Frequency toggle
freq_map = {'Monthly': 'M', 'Weekly': 'W', 'Daily': 'D'}
freq_label = st.radio('Time Frequency', list(freq_map.keys()), horizontal=True)
freq = freq_map[freq_label]

col1, col2 = st.columns(2)

with col1:
    st.subheader('Sentiment Over Time')
    sentiment_trends = get_sentiment_over_time(df, freq)
    if not sentiment_trends.empty:
        colors = {'positive': '#66bb6a', 'neutral': '#ffb74d', 'negative': '#ef5350', 'mixed': '#ab47bc'}
        fig = px.area(sentiment_trends.reset_index(), x='period', y=sentiment_trends.columns,
                     color_discrete_map=colors)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white',
                         xaxis_title='Date', yaxis_title='Number of Reviews')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info('Not enough date information for sentiment trends.')

with col2:
    st.subheader('Rating Over Time (by App)')
    rating_trends = get_rating_over_time(df, freq)
    if not rating_trends.empty:
        fig = px.line(rating_trends.reset_index(), x='period', y=rating_trends.columns, markers=True)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white',
                         xaxis_title='Date', yaxis_title='Average Rating')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info('Not enough date information for rating trends.')

st.markdown('---')
col1, col2 = st.columns(2)

with col1:
    st.subheader('Issue Categories Over Time')
    cat_trends = get_category_over_time(df, freq)
    if not cat_trends.empty:
        fig = px.area(cat_trends.reset_index(), x='period', y=cat_trends.columns)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white',
                         xaxis_title='Date', yaxis_title='Number of Issues')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info('Not enough data for category trends.')

with col2:
    st.subheader('Review Volume by Source')
    vol_trends = get_review_volume_over_time(df, freq)
    if not vol_trends.empty:
        fig = px.bar(vol_trends.reset_index(), x='period', y=vol_trends.columns)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white',
                         xaxis_title='Date', yaxis_title='Review Count', barmode='stack')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info('Not enough data for volume trends.')

st.markdown('---')
st.subheader('🚨 Emerging Issues (Last 30 Days)')
st.markdown('Complaints that are new or rapidly increasing compared to the previous period.')
emerging = detect_emerging_issues(df, lookback_days=30)

if not emerging.empty:
    def format_status(status):
        if status == 'NEW':
            return "<span style='background:#ef5350;padding:2px 8px;border-radius:4px;color:white;font-size:12px;font-weight:bold;'>NEW</span>"
        elif status == 'INCREASING':
            return "<span style='background:#ffb74d;padding:2px 8px;border-radius:4px;color:white;font-size:12px;font-weight:bold;'>INCREASING</span>"
        return status
        
    emerging_html = emerging.copy()
    emerging_html['status'] = emerging_html['status'].apply(format_status)
    emerging_html['change_pct'] = emerging_html['change_pct'].apply(lambda x: f"+{x}%" if isinstance(x, (int, float)) else x)
    st.write(emerging_html.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.success('No emerging issues detected in the last 30 days. Things are stable!')

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from data.database import get_all_classified, init_db
from analytics.aggregator import (
    get_overview_metrics, get_sentiment_distribution, 
    get_rating_distribution, get_source_distribution,
    get_app_distribution, get_feature_area_breakdown
)
from ai.executive_summary import generate_executive_summary
from analytics.aggregator import prepare_recommendation_input

st.set_page_config(page_title='KAIP | Executive Overview', page_icon='📊', layout='wide')

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.css')
if os.path.exists(css_path):
    with open(css_path, encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.markdown('# 📊 Executive Overview')
st.markdown('Real-time product intelligence at a glance')

init_db()
df = get_all_classified()

if df.empty:
    st.warning('No classified data yet. Go to the home page and load data first.')
    st.stop()

metrics = get_overview_metrics(df)

# Row 1: KPI Cards
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.metric('Total Reviews', f"{metrics['total_reviews']:,}")
with col2:
    st.metric('Avg Rating', f"⭐ {metrics['avg_rating']}", delta=f"{metrics['rating_trend']:+.2f}")
with col3:
    st.metric('Positive', f"{metrics['positive_pct']}%", delta_color='normal')
with col4:
    st.metric('Negative', f"{metrics['negative_pct']}%", delta_color='inverse')
with col5:
    st.metric('Sources', metrics['total_sources'])
with col6:
    st.metric('Apps Tracked', metrics['total_apps'])

st.markdown('---')

# Row 2: Key Insights Cards
col1, col2 = st.columns(2)
with col1:
    st.markdown(f"""
<div style='background: linear-gradient(135deg, #1a1f2e 0%, #2d1f3d 100%); padding: 20px; border-radius: 12px; border: 1px solid #ef535030;'>
<h3 style='color: #ef5350; margin: 0;'>🚨 Top Complaint</h3>
<p style='color: #ffffff; font-size: 18px; margin-top: 8px;'>{metrics['top_complaint']}</p>
</div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown(f"""
<div style='background: linear-gradient(135deg, #1a1f2e 0%, #1f2d3d 100%); padding: 20px; border-radius: 12px; border: 1px solid #4fc3f730;'>
<h3 style='color: #4fc3f7; margin: 0;'>💡 Top Feature Request</h3>
<p style='color: #ffffff; font-size: 18px; margin-top: 8px;'>{metrics['top_feature_request']}</p>
</div>
    """, unsafe_allow_html=True)

st.markdown('')

# Row 3: Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader('Sentiment Distribution')
    sentiment_data = get_sentiment_distribution(df)
    if sentiment_data:
        colors = {'positive': '#66bb6a', 'neutral': '#ffb74d', 'negative': '#ef5350', 'mixed': '#ab47bc'}
        fig = px.pie(
            values=list(sentiment_data.values()),
            names=list(sentiment_data.keys()),
            color=list(sentiment_data.keys()),
            color_discrete_map=colors,
            hole=0.4
        )
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader('Rating Distribution')
    rating_data = get_rating_distribution(df)
    if rating_data:
        colors_list = ['#ef5350', '#ff7043', '#ffb74d', '#aed581', '#66bb6a']
        fig = px.bar(
            x=[str(int(k)) + '⭐' for k in sorted(rating_data.keys())],
            y=[rating_data[k] for k in sorted(rating_data.keys())],
            color=[str(int(k)) for k in sorted(rating_data.keys())],
            color_discrete_sequence=colors_list
        )
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                         font_color='white', showlegend=False,
                         xaxis_title='Rating', yaxis_title='Count')
        st.plotly_chart(fig, use_container_width=True)

# Row 4: Source & App Distribution
col1, col2 = st.columns(2)

with col1:
    st.subheader('Reviews by Source')
    source_data = get_source_distribution(df)
    if source_data:
        fig = px.bar(x=list(source_data.keys()), y=list(source_data.values()),
                    color_discrete_sequence=['#4fc3f7'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                         font_color='white', showlegend=False,
                         xaxis_title='Source', yaxis_title='Reviews')
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader('Reviews by App')
    app_data = get_app_distribution(df)
    if app_data:
        fig = px.bar(x=list(app_data.keys()), y=list(app_data.values()),
                    color_discrete_sequence=['#66bb6a'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                         font_color='white', showlegend=False,
                         xaxis_title='App', yaxis_title='Reviews')
        st.plotly_chart(fig, use_container_width=True)

# Row 5: Feature Area Priority Breakdown
st.subheader('🎯 Issue Priority by Feature Area')
fab = get_feature_area_breakdown(df)
if not fab.empty:
    fig = px.bar(fab, x='feature_area', y='priority_score', 
                color='most_common_severity',
                color_discrete_map={'critical': '#ef5350', 'high': '#ff7043', 'medium': '#ffb74d', 'low': '#aed581'},
                hover_data=['frequency', 'avg_rating', 'sample_complaints'])
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                     font_color='white', xaxis_title='Feature Area', yaxis_title='Priority Score')
    st.plotly_chart(fig, use_container_width=True)

# Row 6: AI Executive Summary
st.markdown('---')
st.subheader('🤖 AI Executive Summary')
if st.button('Generate Executive Summary', key='gen_exec_summary'):
    with st.spinner('AI is analyzing your data...'):
        data_summary = prepare_recommendation_input(df)
        summary = generate_executive_summary(data_summary)
        st.markdown(summary)
        st.session_state['executive_summary'] = summary
elif 'executive_summary' in st.session_state:
    st.markdown(st.session_state['executive_summary'])

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import pandas as pd
import plotly.express as px
from data.database import get_all_classified, init_db
from analytics.aggregator import (
    get_top_feature_requests, get_top_bugs, get_most_loved_features,
    get_churn_drivers, get_competitor_mentions, get_feature_area_breakdown
)

st.set_page_config(page_title='KAIP | AI Insights', page_icon='🎯', layout='wide')

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.css')
if os.path.exists(css_path):
    with open(css_path, encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.markdown('# 🎯 AI Insights')
st.markdown('Deep dive into categorized product feedback')

init_db()
df = get_all_classified()

if df.empty:
    st.warning('No classified data yet. Go to the home page and load data first.')
    st.stop()

def get_severity_badge(severity):
    colors = {'critical': '#ef5350', 'high': '#ff7043', 'medium': '#ffb74d', 'low': '#aed581'}
    color = colors.get(str(severity).lower(), '#888')
    return f"<span style='background:{color};padding:2px 8px;border-radius:4px;color:white;font-size:12px;font-weight:bold;'>{str(severity).title()}</span>"

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    'Top Requests', 'Top Bugs', 'Most Loved', 'Churn Drivers', 'Competitors', 'Pain Points'
])

with tab1:
    st.subheader('💡 Top Feature Requests')
    features = get_top_feature_requests(df, 15)
    if not features.empty:
        st.dataframe(features, use_container_width=True)
    else:
        st.info('No feature requests found.')

with tab2:
    st.subheader('🐛 Top Bugs & UX Friction')
    bugs = get_top_bugs(df, 15)
    if not bugs.empty:
        bugs_html = bugs.copy()
        bugs_html['severity'] = bugs_html['severity'].apply(get_severity_badge)
        st.write(bugs_html.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.info('No bugs found.')

with tab3:
    st.subheader('❤️ Most Loved Features')
    loved = get_most_loved_features(df, 10)
    if not loved.empty:
        st.dataframe(loved, use_container_width=True)
    else:
        st.info('No positive feedback found.')

with tab4:
    st.subheader('⚠️ Churn Drivers (1-2 Star Reviews)')
    churn = get_churn_drivers(df, 15)
    if not churn.empty:
        churn_html = churn.copy()
        churn_html['severity'] = churn_html['severity'].apply(get_severity_badge)
        st.write(churn_html.to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.info('No churn drivers found.')

with tab5:
    st.subheader('🆚 Competitor Mentions')
    comps = get_competitor_mentions(df)
    if not comps.empty:
        st.dataframe(comps, use_container_width=True)
    else:
        st.info('No competitor mentions found.')

with tab6:
    st.subheader('🎯 Feature Area Priority Breakdown')
    fab = get_feature_area_breakdown(df)
    if not fab.empty:
        fig = px.bar(fab, x='priority_score', y='feature_area', orientation='h',
                    color='most_common_severity',
                    color_discrete_map={'critical': '#ef5350', 'high': '#ff7043', 'medium': '#ffb74d', 'low': '#aed581'},
                    hover_data=['frequency', 'avg_rating'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                         font_color='white', yaxis={'categoryorder':'total ascending'},
                         xaxis_title='Priority Score', yaxis_title='Feature Area')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(fab, use_container_width=True)
    else:
        st.info('No negative/mixed feedback to analyze.')

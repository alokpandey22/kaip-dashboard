import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import pandas as pd
import plotly.express as px
from data.database import get_all_classified, init_db
from analytics.aggregator import prepare_recommendation_input
from ai.recommender import generate_recommendations

st.set_page_config(page_title='KAIP | AI Recommendations', page_icon='🤖', layout='wide')

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.css')
if os.path.exists(css_path):
    with open(css_path, encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.markdown('# 🤖 AI Recommendations')
st.markdown('Data-driven product feature and fix recommendations')

init_db()
df = get_all_classified()

if df.empty:
    st.warning('No classified data yet. Go to the home page and load data first.')
    st.stop()

if st.button('Generate AI Recommendations', type='primary'):
    with st.spinner('AI is generating product recommendations based on data...'):
        agg_data = prepare_recommendation_input(df)
        recs = generate_recommendations(agg_data)
        st.session_state['recommendations'] = recs

if 'recommendations' not in st.session_state or not st.session_state['recommendations']:
    st.info('Click the button above to generate recommendations.')
    st.stop()

recs = st.session_state['recommendations']
recs_df = pd.DataFrame(recs)

# Ensure required columns exist in case the LLM misses some
for col in ['category', 'feature', 'priority', 'why', 'expected_impact', 'estimated_effort', 'confidence']:
    if col not in recs_df.columns:
        recs_df[col] = 'Unknown'

# Optional Scatter Plot / Priority Matrix
st.subheader('Priority Matrix')
# Create a dummy frequency and severity numeric scale for plotting just to visualize priority
priority_map = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
recs_df['priority_val'] = recs_df['priority'].map(lambda x: priority_map.get(str(x).capitalize(), 2))
# Add some jitter to x for visualization
import numpy as np
recs_df['x_val'] = np.random.uniform(1, 10, size=len(recs_df))

fig = px.scatter(recs_df, x='x_val', y='priority_val', text='feature', color='category',
                 color_discrete_map={'Fix Now': '#ef5350', 'Improve': '#ffb74d', 'Consider Building': '#66bb6a'},
                 size='priority_val', size_max=20)
fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white',
                  xaxis={'visible': False}, yaxis={'tickvals': [1,2,3,4], 'ticktext': ['Low', 'Medium', 'High', 'Critical']},
                  title="Recommendation Landscape")
fig.update_traces(textposition='top center')
st.plotly_chart(fig, use_container_width=True)

st.markdown('---')

def render_rec_card(rec, color, border_color):
    priority_colors = {'Critical': '#ef5350', 'High': '#ff7043', 'Medium': '#ffb74d', 'Low': '#aed581'}
    p_color = priority_colors.get(str(rec.get('priority')).capitalize(), '#888')
    
    html = f"""
<div style='background: #1a1f2e; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 5px solid {border_color};'>
<div style='display: flex; justify-content: space-between; align-items: start;'>
<h3 style='margin-top:0; color: white;'>{rec.get('feature', 'Unknown Feature')}</h3>
<span style='background: {p_color}; padding: 4px 10px; border-radius: 4px; color: white; font-weight: bold;'>{rec.get('priority', 'Medium')}</span>
</div>
<p style='color: #b0bec5;'><strong>Why:</strong> {rec.get('why', '')}</p>
<div style='display: flex; gap: 20px; margin-top: 15px;'>
<div><span style='color: #4fc3f7;'>Expected Impact:</span> <span style='color: white;'>{rec.get('expected_impact', '')}</span></div>
<div><span style='color: #4fc3f7;'>Effort:</span> <span style='color: white;'>{rec.get('estimated_effort', '')}</span></div>
<div><span style='color: #4fc3f7;'>Confidence:</span> <span style='color: white;'>{rec.get('confidence', '')}</span></div>
</div>
</div>
    """
    st.markdown(html, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("<h2 style='color:#ef5350;'>🔴 Fix Now</h2>", unsafe_allow_html=True)
    fix_now = recs_df[recs_df['category'].str.contains('Fix', case=False, na=False)]
    for _, rec in fix_now.iterrows():
        render_rec_card(rec, '#ef5350', '#ef5350')

with col2:
    st.markdown("<h2 style='color:#ffb74d;'>🟡 Improve</h2>", unsafe_allow_html=True)
    improve = recs_df[recs_df['category'].str.contains('Improve', case=False, na=False)]
    for _, rec in improve.iterrows():
        render_rec_card(rec, '#ffb74d', '#ffb74d')

with col3:
    st.markdown("<h2 style='color:#66bb6a;'>🟢 Consider Building</h2>", unsafe_allow_html=True)
    build = recs_df[recs_df['category'].str.contains('Build', case=False, na=False)]
    for _, rec in build.iterrows():
        render_rec_card(rec, '#66bb6a', '#66bb6a')

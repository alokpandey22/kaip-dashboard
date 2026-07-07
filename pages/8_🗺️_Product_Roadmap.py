import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import pandas as pd
from analytics.roadmap import generate_roadmap

st.set_page_config(page_title='KAIP | Product Roadmap', page_icon='🗺️', layout='wide')

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.css')
if os.path.exists(css_path):
    with open(css_path, encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.markdown('# 🗺️ AI Product Roadmap')
st.markdown('Quarterly roadmap automatically generated from prioritized product recommendations.')

recs = st.session_state.get('recommendations', [])

if not recs:
    st.info('No recommendations available to generate a roadmap. Please visit the "AI Recommendations" page first.')
    st.stop()

if st.button('Generate AI Roadmap', type='primary'):
    with st.spinner('Generating strategic quarterly roadmap...'):
        st.session_state['roadmap'] = generate_roadmap(recs)

roadmap = st.session_state.get('roadmap', {})

st.markdown('---')

# Visual Timeline layout
cols = st.columns(4)
quarters = ['Q3_2026', 'Q4_2026', 'Q1_2027', 'Q2_2027']
q_names = ['Q3 2026', 'Q4 2026', 'Q1 2027', 'Q2 2027']

def get_type_color(item_type):
    t = str(item_type).lower()
    if 'bug' in t: return '#ef5350'
    if 'feature' in t: return '#4fc3f7'
    return '#ffb74d'

for i, q in enumerate(quarters):
    with cols[i]:
        items = roadmap.get(q, [])
        items_html = ""
        for item in items:
            t_color = get_type_color(item.get('type', ''))
            items_html += f"""
<div style='background: #0e111720; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid {t_color};'>
<strong style='color: white;'>{item.get('item', 'Unknown')}</strong><br>
<span style='background: {t_color}30; color: {t_color}; padding: 2px 6px; border-radius: 4px; font-size: 11px;'>{item.get('type', '')}</span>
<span style='background: #ffffff20; color: #ddd; padding: 2px 6px; border-radius: 4px; font-size: 11px;'>{item.get('priority', '')}</span>
<p style='color: #999; font-size: 13px; margin-top: 6px; line-height: 1.2;'>{item.get('rationale', '')}</p>
</div>
            """
            
        html = f"""
<div style='background: linear-gradient(180deg, #1a1f2e 0%, #262c3a 100%); padding: 16px; border-radius: 12px; border: 1px solid #ffffff10; min-height: 400px;'>
<h3 style='color: #4fc3f7; text-align: center; margin-top: 0;'>{q_names[i]}</h3>
            {items_html}
</div>
        """
        st.markdown(html, unsafe_allow_html=True)

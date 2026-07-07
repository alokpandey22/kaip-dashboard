import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import pandas as pd
from ai.prd_generator import generate_prd

st.set_page_config(page_title='KAIP | PRD Generator', page_icon='📋', layout='wide')

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.css')
if os.path.exists(css_path):
    with open(css_path, encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.markdown('# 📋 PRD Generator')
st.markdown('Automatically draft Product Requirements Documents from data insights')

recs = st.session_state.get('recommendations', [])
rec_options = [r.get('feature', 'Unknown') for r in recs]

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('### Input Parameters')
    
    selected_feature = None
    if rec_options:
        sel_idx = st.selectbox('Select from AI Recommendations:', ['-- Custom Entry --'] + rec_options)
        if sel_idx != '-- Custom Entry --':
            selected_rec = next((r for r in recs if r.get('feature') == sel_idx), None)
            if selected_rec:
                selected_feature = selected_rec.get('feature')
                def_justification = selected_rec.get('why', '')
                def_priority = selected_rec.get('priority', 'Medium')
                def_supporting = f"Expected Impact: {selected_rec.get('expected_impact', '')}\nConfidence: {selected_rec.get('confidence', '')}\nEffort: {selected_rec.get('estimated_effort', '')}"
    
    if not selected_feature:
        selected_feature = ''
        def_justification = ''
        def_priority = 'Medium'
        def_supporting = ''
        
    feature_name = st.text_input('Feature Name', value=selected_feature)
    justification = st.text_area('Justification', value=def_justification, height=100)
    priority = st.selectbox('Priority', ['Critical', 'High', 'Medium', 'Low'], index=['Critical', 'High', 'Medium', 'Low'].index(str(def_priority).capitalize()) if str(def_priority).capitalize() in ['Critical', 'High', 'Medium', 'Low'] else 2)
    supporting_data = st.text_area('Supporting Data', value=def_supporting, height=150)
    
    if st.button('Generate PRD', type='primary'):
        if not feature_name:
            st.error('Feature name is required.')
        else:
            with st.spinner('Generating PRD... This takes about 10-15 seconds.'):
                prd_content = generate_prd(feature_name, justification, priority, supporting_data)
                st.session_state['generated_prd'] = prd_content
                st.session_state['generated_prd_name'] = feature_name

with col2:
    st.markdown('### Generated PRD')
    if 'generated_prd' in st.session_state:
        st.download_button(
            label="Download as Markdown",
            data=st.session_state['generated_prd'],
            file_name=f"PRD_{st.session_state.get('generated_prd_name', 'Feature').replace(' ', '_')}.md",
            mime="text/markdown"
        )
        st.markdown(
            f"""<div style='background: #1a1f2e; padding: 30px; border-radius: 8px; border: 1px solid #ffffff20; height: 600px; overflow-y: auto;'>
            {st.session_state['generated_prd']}
</div>""",
            unsafe_allow_html=True
        )
    else:
        st.info('Fill out the parameters and click Generate PRD to see the result here.')

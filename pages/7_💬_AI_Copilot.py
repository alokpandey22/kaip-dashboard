import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
from data.database import get_all_classified, init_db
from ai.copilot import query as copilot_query

st.set_page_config(page_title='KAIP | AI Copilot', page_icon='💬', layout='wide')

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.css')
if os.path.exists(css_path):
    with open(css_path, encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.markdown('# 💬 AI Product Copilot')
st.markdown('Ask questions about your product data and get AI-powered answers grounded in real customer feedback.')

init_db()
df = get_all_classified()

if df.empty:
    st.warning('No data loaded. Please load data from the home page first.')
    st.stop()

# Initialize chat history
if 'copilot_messages' not in st.session_state:
    st.session_state.copilot_messages = [
        {'role': 'assistant', 'content': '👋 Hi! I\'m your AI Product Copilot. I can analyze customer feedback and help you make data-driven product decisions. Try asking me:\n\n• What should we build next?\n• What\'s our biggest bug?\n• How do customers feel about booking?\n• What are competitors doing better?'}
    ]

# Quick question buttons
st.markdown('**Quick Questions:**')
quick_cols = st.columns(3)
quick_questions = [
    'What should we build next?',
    'What is our biggest bug?', 
    'How do customers feel about booking?',
    'What are competitors doing better?',
    'Generate a sprint priority list',
    'What features should we NOT build?'
]
for i, q in enumerate(quick_questions):
    with quick_cols[i % 3]:
        if st.button(q, key=f'quick_{i}'):
            st.session_state.copilot_input = q

st.markdown('---')

# Display chat history
for msg in st.session_state.copilot_messages:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

# Handle input
prompt = st.chat_input('Ask me anything about your product...')
if hasattr(st.session_state, 'copilot_input') and st.session_state.copilot_input:
    prompt = st.session_state.copilot_input
    st.session_state.copilot_input = None

if prompt:
    st.session_state.copilot_messages.append({'role': 'user', 'content': prompt})
    with st.chat_message('user'):
        st.markdown(prompt)
    
    with st.chat_message('assistant'):
        with st.spinner('Analyzing your data...'):
            try:
                response = copilot_query(prompt, df)
                st.markdown(response)
                st.session_state.copilot_messages.append({'role': 'assistant', 'content': response})
            except Exception as e:
                error_msg = f'Sorry, I encountered an error: {str(e)}'
                st.error(error_msg)
                st.session_state.copilot_messages.append({'role': 'assistant', 'content': error_msg})

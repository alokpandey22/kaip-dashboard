import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import streamlit as st
import pandas as pd
from data.database import get_all_classified, init_db

st.set_page_config(page_title='KAIP | AI Opportunity Hub', page_icon='🏢', layout='wide')

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'style.css')
if os.path.exists(css_path):
    with open(css_path, encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.markdown('# 🏢 AI Opportunity Hub')
st.markdown('Cross-organizational AI opportunities based on customer feedback patterns.')

init_db()
df = get_all_classified()

# Pre-populated defaults
opportunities = [
    {
        'Team': 'Customer Support',
        'Opportunity': 'Repeated booking queries and slow responses',
        'AI Suggestion': 'AI Support Copilot',
        'Expected Benefit': 'Faster response time, lower support cost',
        'Data Signal': 'General pattern'
    },
    {
        'Team': 'Marketing',
        'Opportunity': 'Repetitive campaign content',
        'AI Suggestion': 'AI Content Generation',
        'Expected Benefit': 'Higher productivity, A/B test variations',
        'Data Signal': 'General pattern'
    },
    {
        'Team': 'Design/UX',
        'Opportunity': 'Repeated UI navigation complaints',
        'AI Suggestion': 'AI-Assisted UX Insights',
        'Expected Benefit': 'Better usability, reduced friction',
        'Data Signal': 'General pattern'
    },
    {
        'Team': 'Operations',
        'Opportunity': 'Property maintenance and amenity mentions',
        'AI Suggestion': 'Predictive Maintenance AI',
        'Expected Benefit': 'Reduced downtime, better guest experience',
        'Data Signal': 'General pattern'
    },
    {
        'Team': 'Sales',
        'Opportunity': 'Membership value questions',
        'AI Suggestion': 'AI Sales Assistant',
        'Expected Benefit': 'Better conversion rates',
        'Data Signal': 'General pattern'
    },
    {
        'Team': 'Product',
        'Opportunity': 'Feature request overload',
        'AI Suggestion': 'AI Product Prioritization (KAIP)',
        'Expected Benefit': 'Faster decisions, data-backed roadmap',
        'Data Signal': 'General pattern'
    },
    {
        'Team': 'Revenue',
        'Opportunity': 'Pricing and value complaints',
        'AI Suggestion': 'Dynamic Pricing AI',
        'Expected Benefit': 'Optimized revenue, higher occupancy',
        'Data Signal': 'General pattern'
    },
    {
        'Team': 'Guest Experience',
        'Opportunity': 'Concierge limitations',
        'AI Suggestion': 'AI Digital Concierge',
        'Expected Benefit': '24/7 personalized service',
        'Data Signal': 'General pattern'
    }
]

# If we have data, try to inject actual numbers
if not df.empty:
    support_complaints = len(df[df['feature_area'] == 'customer_support'])
    if support_complaints > 0:
        opportunities[0]['Data Signal'] = f"{support_complaints} support complaints"
        
    ux_complaints = len(df[df['feature_area'] == 'ui_navigation'])
    if ux_complaints > 0:
        opportunities[2]['Data Signal'] = f"{ux_complaints} UI/UX complaints"
        
    prop_complaints = len(df[df['feature_area'] == 'property_experience'])
    if prop_complaints > 0:
        opportunities[3]['Data Signal'] = f"{prop_complaints} property mentions"
        
    pricing_complaints = len(df[df['feature_area'] == 'pricing'])
    if pricing_complaints > 0:
        opportunities[6]['Data Signal'] = f"{pricing_complaints} pricing mentions"

opp_df = pd.DataFrame(opportunities)

# Custom styled dataframe rendering
st.markdown('''
<style>
.opp-table {width: 100%; border-collapse: collapse; margin-top: 20px;}
.opp-table th {background: #1a1f2e; padding: 12px; text-align: left; color: #4fc3f7; border-bottom: 1px solid #333;}
.opp-table td {padding: 12px; border-bottom: 1px solid #333; color: #eee;}
.team-badge {background: #333; padding: 4px 8px; border-radius: 4px; font-weight: 500;}
</style>
''', unsafe_allow_html=True)

html = "<table class='opp-table'><tr><th>Team</th><th>Opportunity</th><th>AI Suggestion</th><th>Expected Benefit</th><th>Data Signal</th></tr>"
for _, row in opp_df.iterrows():
    html += f"""
<tr>
<td><span class='team-badge'>{row['Team']}</span></td>
<td>{row['Opportunity']}</td>
<td><strong style='color:#66bb6a;'>{row['AI Suggestion']}</strong></td>
<td>{row['Expected Benefit']}</td>
<td style='color:#ffb74d;'>{row['Data Signal']}</td>
</tr>
    """
html += "</table>"

st.markdown(html, unsafe_allow_html=True)

st.markdown('---')
st.markdown('### Return on AI Investment')
c1, c2, c3 = st.columns(3)
c1.metric('Estimated Eng Hours Saved', '120 hrs/mo')
c2.metric('Support Ticket Deflection', '22%')
c3.metric('Roadmap Planning Velocity', '3x Faster')

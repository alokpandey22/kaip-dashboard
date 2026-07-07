import json
import groq
from config.settings import GROQ_API_KEY, GROQ_MODEL
from ai.prompts import EXECUTIVE_SUMMARY_PROMPT

def generate_executive_summary(data_summary: dict) -> str:
    client = groq.Groq(api_key=GROQ_API_KEY)
    
    prompt = EXECUTIVE_SUMMARY_PROMPT.format(data_json=json.dumps(data_summary, default=str))
    
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating executive summary: {e}"

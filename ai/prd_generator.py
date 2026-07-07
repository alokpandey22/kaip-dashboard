import groq
from config.settings import GROQ_API_KEY, GROQ_MODEL
from ai.prompts import PRD_PROMPT

def generate_prd(feature_name: str, justification: str, priority: str, supporting_data: str = None) -> str:
    client = groq.Groq(api_key=GROQ_API_KEY)
    prompt = PRD_PROMPT.format(
        feature_name=feature_name,
        justification=justification,
        priority=priority,
        supporting_data=supporting_data or "None"
    )
    
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4096
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating PRD: {e}"

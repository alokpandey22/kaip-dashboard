import json
import groq
from config.settings import GROQ_API_KEY, GROQ_MODEL
from ai.prompts import RECOMMENDATION_PROMPT

def generate_recommendations(data_summary: dict) -> list:
    client = groq.Groq(api_key=GROQ_API_KEY)
    
    prompt = RECOMMENDATION_PROMPT.format(data_json=json.dumps(data_summary, default=str))
    
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        parsed = json.loads(response.choices[0].message.content)
        if isinstance(parsed, dict):
            for k in parsed.keys():
                if isinstance(parsed[k], list):
                    return parsed[k]
        if isinstance(parsed, list):
            return parsed
        return [parsed]
    except Exception as e:
        return [{"feature": "Error generating recommendations", "why": str(e), "priority": "Low", "effort": "Medium", "expected_impact": "None"}]

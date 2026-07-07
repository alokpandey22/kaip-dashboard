import json
import logging
import time
from typing import List, Dict, Optional, Callable
import groq
from config.settings import GROQ_API_KEY, GROQ_MODEL, BATCH_SIZE
from ai.prompts import CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)

def classify_reviews(reviews: List[Dict], progress_callback=None, batch_size=BATCH_SIZE) -> List[Dict]:
    if not reviews: return []
    client = groq.Groq(api_key=GROQ_API_KEY)
    results = []
    
    for i in range(0, len(reviews), batch_size):
        batch = reviews[i:i+batch_size]
        if progress_callback:
            progress_callback(i/len(reviews), f"Classifying {i} to {i+len(batch)}")
            
        reviews_for_prompt = [{"index": idx, "text": r.get("text", r.get("content", r.get("review_text", "")))} for idx, r in enumerate(batch)]
        prompt = CLASSIFICATION_PROMPT.format(reviews_json=json.dumps(reviews_for_prompt))
        
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            parsed = json.loads(content)
            
            if isinstance(parsed, dict):
                for k in parsed.keys():
                    if isinstance(parsed[k], list):
                        parsed = parsed[k]
                        break
            if not isinstance(parsed, list):
                parsed = [parsed]
                
            while len(parsed) < len(batch):
                parsed.append({"sentiment": "neutral", "category": "general_feedback", "feature_area": "general", "severity": "low", "intent": "suggestion", "pain_point": None, "competitor_mention": None, "one_line_summary": "Failed to parse"})
            results.extend(parsed[:len(batch)])
        except Exception as e:
            logger.error(f"Error classifying batch: {e}")
            results.extend([{"sentiment": "neutral", "category": "general_feedback", "feature_area": "general", "severity": "low", "intent": "suggestion", "pain_point": None, "competitor_mention": None, "one_line_summary": "API Error"}] * len(batch))
            
        time.sleep(1) # rate limit protection
            
    if progress_callback: progress_callback(1.0, "Classification complete.")
    return results

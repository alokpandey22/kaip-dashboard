import groq
from config.settings import GROQ_API_KEY, GROQ_MODEL
from ai.prompts import COPILOT_SYSTEM_PROMPT

def query(question: str, df, top_k=5) -> str:
    client = groq.Groq(api_key=GROQ_API_KEY)
    
    if "review_text" in df.columns:
        text_col = "review_text"
    elif "text" in df.columns:
        text_col = "text"
    elif "content" in df.columns:
        text_col = "content"
    else:
        text_col = df.columns[0]
        
    context = "\n".join(df[text_col].dropna().astype(str).head(top_k).tolist())
    
    system_msg = COPILOT_SYSTEM_PROMPT.format(context=context)
    
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": question}
            ],
            temperature=0.5,
            max_tokens=2048
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error querying copilot: {e}"

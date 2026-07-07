"""
KAIP Analytics Roadmap Generator
Generates a quarterly product roadmap from prioritised recommendations
using Groq AI, with a deterministic fallback.
"""

import json
import os
import sys
from typing import Dict, List, Any

import groq

# Resolve project root for reliable imports regardless of CWD
_PROJECT_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from config.settings import GROQ_API_KEY, GROQ_MODEL  # noqa: E402
from ai.prompts import ROADMAP_PROMPT  # noqa: E402


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_roadmap(recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
    """Generate a quarterly product roadmap from a list of recommendations.

    Each recommendation dict is expected to have at least:
        feature, category, priority, why

    Returns a dict keyed by quarter strings (e.g. "Q3_2026") whose values
    are lists of roadmap items.  Falls back to ``_fallback_roadmap`` when
    the Groq API key is absent or the call fails.
    """
    if not recommendations:
        return _empty_roadmap()

    if not GROQ_API_KEY:
        return _fallback_roadmap(recommendations)

    try:
        client = groq.Groq(api_key=GROQ_API_KEY)

        prompt = ROADMAP_PROMPT.format(
            recommendations=json.dumps(recommendations, indent=2, default=str)
        )

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Validate that result has the expected quarter keys
        if not isinstance(result, dict):
            return _fallback_roadmap(recommendations)

        return result

    except Exception as e:  # noqa: BLE001
        print(f"[KAIP] Roadmap generation error: {e}")
        return _fallback_roadmap(recommendations)


# ---------------------------------------------------------------------------
# Fallback / rule-based roadmap
# ---------------------------------------------------------------------------

_QUARTER_KEYS = ("Q3_2026", "Q4_2026", "Q1_2027", "Q2_2027")


def _empty_roadmap() -> Dict[str, List]:
    """Return an empty roadmap scaffold."""
    return {q: [] for q in _QUARTER_KEYS}


def _fallback_roadmap(recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
    """Simple deterministic roadmap when Groq is unavailable.

    Sorting logic:
    * "Fix Now" items → Q3 (immediate)
    * "Improve"  items → Q3–Q4
    * "Consider Building" items → Q1 next year
    * Everything else → Q2 next year
    """
    roadmap: Dict[str, List[Dict]] = _empty_roadmap()
    quarters = list(_QUARTER_KEYS)

    for i, rec in enumerate(recommendations[:12]):
        category = str(rec.get("category", "Improve")).strip()

        if category == "Fix Now":
            quarter_idx = 0
        elif category == "Improve":
            quarter_idx = min(i // 3, 1)
        elif category == "Consider Building":
            quarter_idx = min(i // 3, 2)
        else:
            quarter_idx = min(i // 3, 3)

        # Determine item type from category
        if category == "Fix Now":
            item_type = "Bug Fix"
        elif category == "Consider Building":
            item_type = "Feature"
        else:
            item_type = "Improvement"

        roadmap[quarters[quarter_idx]].append(
            {
                "item": rec.get("feature", rec.get("item", "Unknown")),
                "type": item_type,
                "priority": rec.get("priority", "Medium"),
                "rationale": rec.get("why", rec.get("rationale", "")),
                "dependencies": rec.get("dependencies", "None identified"),
            }
        )

    return roadmap

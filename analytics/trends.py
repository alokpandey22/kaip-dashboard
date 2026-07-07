"""
KAIP Analytics Trends
Time-series analysis for trend charts and emerging issue detection.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _prepare_dated(
    df: pd.DataFrame,
    date_col: str = "review_date",
) -> pd.DataFrame:
    """Return a copy with *date_col* coerced to datetime, rows with NaT dropped."""
    if df.empty or date_col not in df.columns:
        return pd.DataFrame()

    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col], errors="coerce")
    out = out.dropna(subset=[date_col])
    return out


def _add_period(
    df: pd.DataFrame,
    freq: str,
    date_col: str = "review_date",
) -> pd.DataFrame:
    """Add a 'period' column derived from *date_col* at the given frequency."""
    out = df.copy()
    out["period"] = out[date_col].dt.to_period(freq)
    return out


# ---------------------------------------------------------------------------
# Sentiment over time
# ---------------------------------------------------------------------------

def get_sentiment_over_time(
    df: pd.DataFrame,
    freq: str = "M",
) -> pd.DataFrame:
    """Sentiment distribution over time.

    Returns a DataFrame with a DatetimeIndex and one column per sentiment
    label (positive, negative, neutral, mixed).  Counts are filled with 0
    for periods with no data.
    """
    prepared = _prepare_dated(df)
    if prepared.empty or "sentiment" not in prepared.columns:
        return pd.DataFrame()

    prepared = _add_period(prepared, freq)
    pivot = (
        prepared.groupby(["period", "sentiment"])
        .size()
        .unstack(fill_value=0)
    )
    pivot.index = pivot.index.to_timestamp()
    return pivot


# ---------------------------------------------------------------------------
# Rating over time
# ---------------------------------------------------------------------------

def get_rating_over_time(
    df: pd.DataFrame,
    freq: str = "M",
) -> pd.DataFrame:
    """Average rating over time, broken out per app.

    Returns a DataFrame with DatetimeIndex and one column per app_name.
    """
    prepared = _prepare_dated(df)
    if prepared.empty or "rating" not in prepared.columns:
        return pd.DataFrame()

    prepared = _add_period(prepared, freq)

    if "app_name" in prepared.columns:
        pivot = (
            prepared.groupby(["period", "app_name"])["rating"]
            .mean()
            .unstack(fill_value=None)
        )
    else:
        pivot = (
            prepared.groupby("period")["rating"]
            .mean()
            .to_frame(name="avg_rating")
        )

    pivot.index = pivot.index.to_timestamp()
    return pivot


# ---------------------------------------------------------------------------
# Issue category volume over time
# ---------------------------------------------------------------------------

def get_category_over_time(
    df: pd.DataFrame,
    freq: str = "M",
) -> pd.DataFrame:
    """Issue-category (feature_area) volume over time.

    Only negative/mixed sentiment reviews are included.
    Returns a DataFrame with DatetimeIndex and one column per feature_area.
    """
    prepared = _prepare_dated(df)
    if prepared.empty or "sentiment" not in prepared.columns or "feature_area" not in prepared.columns:
        return pd.DataFrame()

    issues = prepared[prepared["sentiment"].isin(["negative", "mixed"])].copy()
    if issues.empty:
        return pd.DataFrame()

    issues = _add_period(issues, freq)
    pivot = (
        issues.groupby(["period", "feature_area"])
        .size()
        .unstack(fill_value=0)
    )
    pivot.index = pivot.index.to_timestamp()
    return pivot


# ---------------------------------------------------------------------------
# Review volume over time
# ---------------------------------------------------------------------------

def get_review_volume_over_time(
    df: pd.DataFrame,
    freq: str = "M",
) -> pd.DataFrame:
    """Total review volume over time, split by source.

    Returns a DataFrame with DatetimeIndex and one column per source.
    """
    prepared = _prepare_dated(df)
    if prepared.empty:
        return pd.DataFrame()

    prepared = _add_period(prepared, freq)

    if "source" in prepared.columns:
        pivot = (
            prepared.groupby(["period", "source"])
            .size()
            .unstack(fill_value=0)
        )
    else:
        pivot = (
            prepared.groupby("period")
            .size()
            .to_frame(name="review_count")
        )

    pivot.index = pivot.index.to_timestamp()
    return pivot


# ---------------------------------------------------------------------------
# Emerging issue detection
# ---------------------------------------------------------------------------

def detect_emerging_issues(
    df: pd.DataFrame,
    lookback_days: int = 30,
) -> pd.DataFrame:
    """Detect new or rapidly increasing complaints.

    Compares pain-point counts in the most recent *lookback_days* window
    against the immediately preceding window of the same length.

    Returns a DataFrame with columns:
        pain_point, recent_count, previous_count, change_pct, status

    *status* is one of:
        • NEW — not seen in the previous window
        • INCREASING — ≥50 % increase
    """
    prepared = _prepare_dated(df)
    if prepared.empty or "sentiment" not in prepared.columns or "pain_point" not in prepared.columns:
        return pd.DataFrame()

    now = pd.Timestamp.now()
    cutoff_recent = now - pd.Timedelta(days=lookback_days)
    cutoff_older = now - pd.Timedelta(days=lookback_days * 2)

    recent = prepared[prepared["review_date"] >= cutoff_recent]
    older = prepared[
        (prepared["review_date"] < cutoff_recent)
        & (prepared["review_date"] >= cutoff_older)
    ]

    if recent.empty:
        return pd.DataFrame()

    recent_issues = recent[recent["sentiment"].isin(["negative", "mixed"])]
    older_issues = older[older["sentiment"].isin(["negative", "mixed"])]

    recent_counts = (
        recent_issues["pain_point"]
        .dropna()
        .loc[lambda s: s.astype(str).str.strip() != ""]
        .value_counts()
    )
    older_counts = (
        older_issues["pain_point"]
        .dropna()
        .loc[lambda s: s.astype(str).str.strip() != ""]
        .value_counts()
    )

    if recent_counts.empty:
        return pd.DataFrame()

    emerging: List[Dict] = []
    for pain_point, count in recent_counts.items():
        old_count = older_counts.get(pain_point, 0)
        if old_count == 0:
            change_pct = "New"
            status = "NEW"
        else:
            change_val = (count - old_count) / old_count * 100
            change_pct = round(float(change_val), 1)
            status = "INCREASING" if change_val > 50 else "STABLE"

        if status in ("NEW", "INCREASING"):
            emerging.append(
                {
                    "pain_point": pain_point,
                    "recent_count": int(count),
                    "previous_count": int(old_count),
                    "change_pct": change_pct,
                    "status": status,
                }
            )

    if not emerging:
        return pd.DataFrame()

    result = pd.DataFrame(emerging)
    return result.sort_values("recent_count", ascending=False).reset_index(drop=True)

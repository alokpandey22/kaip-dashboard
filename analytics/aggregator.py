"""
KAIP Analytics Aggregator
Core analytics engine that transforms classified review data into product intelligence.
Computes priority scores, overview metrics, feature area breakdowns, and more.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional


# ---------------------------------------------------------------------------
# Helper: safe column access
# ---------------------------------------------------------------------------

def _safe_col(df: pd.DataFrame, col: str) -> pd.Series:
    """Return a column as a Series, or an empty Series if it doesn't exist."""
    if col in df.columns:
        return df[col]
    return pd.Series(dtype="object", name=col)


def _ensure_datetime(df: pd.DataFrame, col: str = "review_date") -> pd.DataFrame:
    """Return a copy with *col* coerced to datetime (NaT on failure)."""
    out = df.copy()
    if col in out.columns:
        out[col] = pd.to_datetime(out[col], errors="coerce")
    return out


# ---------------------------------------------------------------------------
# Priority scoring
# ---------------------------------------------------------------------------

def compute_priority_score(
    frequency: int,
    severity: str,
    avg_days_ago: float,
) -> float:
    """Compute priority score using RICE-style logic.

    Score = frequency × severity_weight × recency_weight

    * severity_weight maps critical→4, high→3, medium→2, low→1
    * recency_weight is higher for recent issues (linear decay over 365 days,
      floored at 0.1 so old issues don't vanish).
    """
    severity_weights: Dict[str, int] = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1,
    }
    severity_w = severity_weights.get(str(severity).lower().strip(), 1)

    # Clamp avg_days_ago to non-negative
    avg_days_ago = max(0.0, float(avg_days_ago) if pd.notna(avg_days_ago) else 180.0)
    recency_w = max(0.1, 1.0 - (avg_days_ago / 365.0))

    return round(frequency * severity_w * recency_w, 2)


# ---------------------------------------------------------------------------
# Executive overview
# ---------------------------------------------------------------------------

def get_overview_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Get executive overview metrics from the full classified review set."""
    empty_result: Dict[str, Any] = {
        "total_reviews": 0,
        "avg_rating": 0.0,
        "positive_pct": 0.0,
        "negative_pct": 0.0,
        "neutral_pct": 0.0,
        "mixed_pct": 0.0,
        "top_complaint": "N/A",
        "top_feature_request": "N/A",
        "total_sources": 0,
        "total_apps": 0,
        "reviews_last_30_days": 0,
        "rating_trend": 0.0,
    }
    if df.empty:
        return empty_result

    total = len(df)

    # Sentiment percentages (safe even if column is missing)
    if "sentiment" in df.columns:
        sentiment_counts = df["sentiment"].value_counts(normalize=True) * 100
    else:
        sentiment_counts = pd.Series(dtype="float64")

    # Top complaint -------------------------------------------------------
    top_complaint = "N/A"
    if "sentiment" in df.columns and "pain_point" in df.columns:
        negatives = df[df["sentiment"].isin(["negative", "mixed"])]
        pain_vals = negatives["pain_point"].dropna()
        pain_vals = pain_vals[pain_vals.astype(str).str.strip() != ""]
        if not pain_vals.empty:
            top_complaint = pain_vals.value_counts().index[0]

    # Top feature request --------------------------------------------------
    top_feature_request = "N/A"
    if "category" in df.columns and "feature_area" in df.columns:
        feature_reqs = df[df["category"] == "feature_request"]
        fa_vals = feature_reqs["feature_area"].dropna()
        fa_vals = fa_vals[fa_vals.astype(str).str.strip() != ""]
        if not fa_vals.empty:
            top_feature_request = fa_vals.value_counts().index[0]

    # Rating trend (last 30 days vs previous 30 days) ----------------------
    trend: float = 0.0
    reviews_last_30 = 0
    if "review_date" in df.columns and "rating" in df.columns:
        df_dated = _ensure_datetime(df)
        now = pd.Timestamp.now()
        last_30 = df_dated[df_dated["review_date"] >= now - pd.Timedelta(days=30)]
        prev_30 = df_dated[
            (df_dated["review_date"] >= now - pd.Timedelta(days=60))
            & (df_dated["review_date"] < now - pd.Timedelta(days=30))
        ]
        reviews_last_30 = len(last_30)
        if len(last_30) > 0 and len(prev_30) > 0:
            trend = float(last_30["rating"].mean() - prev_30["rating"].mean())
        else:
            trend = 0.0

    # Average rating -------------------------------------------------------
    avg_rating = 0.0
    if "rating" in df.columns and not df["rating"].dropna().empty:
        avg_rating = round(float(df["rating"].mean()), 2)

    return {
        "total_reviews": total,
        "avg_rating": avg_rating,
        "positive_pct": round(float(sentiment_counts.get("positive", 0)), 1),
        "negative_pct": round(float(sentiment_counts.get("negative", 0)), 1),
        "neutral_pct": round(float(sentiment_counts.get("neutral", 0)), 1),
        "mixed_pct": round(float(sentiment_counts.get("mixed", 0)), 1),
        "top_complaint": top_complaint,
        "top_feature_request": top_feature_request,
        "total_sources": int(df["source"].nunique()) if "source" in df.columns else 0,
        "total_apps": int(df["app_name"].nunique()) if "app_name" in df.columns else 0,
        "reviews_last_30_days": reviews_last_30,
        "rating_trend": round(trend, 2) if not np.isnan(trend) else 0.0,
    }


# ---------------------------------------------------------------------------
# Feature area breakdown (with priority scores)
# ---------------------------------------------------------------------------

def get_feature_area_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Break issues down by feature_area with priority scores.

    Only considers negative/mixed sentiment reviews.  Returns a DataFrame
    sorted by descending priority score.
    """
    required_cols = {"sentiment", "feature_area", "rating", "severity", "one_line_summary"}
    if df.empty or not required_cols.issubset(df.columns):
        return pd.DataFrame()

    issues = df[df["sentiment"].isin(["negative", "mixed"])].copy()
    if issues.empty:
        return pd.DataFrame()

    grouped = (
        issues.groupby("feature_area")
        .agg(
            frequency=("feature_area", "count"),
            avg_rating=("rating", "mean"),
            most_common_severity=(
                "severity",
                lambda x: x.mode().iloc[0] if not x.mode().empty else "medium",
            ),
            sample_complaints=(
                "one_line_summary",
                lambda x: " | ".join(x.dropna().head(3).tolist()),
            ),
        )
        .reset_index()
    )

    # Compute recency (avg days ago) per feature area ----------------------
    if "review_date" in df.columns:
        now = pd.Timestamp.now()
        issues_dated = _ensure_datetime(issues)
        avg_days = (
            issues_dated.groupby("feature_area")["review_date"]
            .apply(
                lambda x: (now - x.dropna()).dt.days.mean()
                if not x.dropna().empty
                else 180.0
            )
            .reset_index(name="avg_days_ago")
        )
        grouped = grouped.merge(avg_days, on="feature_area", how="left")
        grouped["avg_days_ago"] = grouped["avg_days_ago"].fillna(180.0)
    else:
        grouped["avg_days_ago"] = 180.0

    grouped["priority_score"] = grouped.apply(
        lambda r: compute_priority_score(
            r["frequency"], r["most_common_severity"], r["avg_days_ago"]
        ),
        axis=1,
    )

    return grouped.sort_values("priority_score", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Top bugs
# ---------------------------------------------------------------------------

def get_top_bugs(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top bugs ranked by frequency. Includes bug, ux_friction, performance."""
    required_cols = {"category", "feature_area", "pain_point", "rating", "severity", "source"}
    if df.empty or not required_cols.issubset(df.columns):
        return pd.DataFrame()

    bugs = df[df["category"].isin(["bug", "ux_friction", "performance"])].copy()
    if bugs.empty:
        return pd.DataFrame()

    # Drop rows where pain_point is missing — can't group on it otherwise
    bugs = bugs.dropna(subset=["pain_point"])
    bugs = bugs[bugs["pain_point"].astype(str).str.strip() != ""]
    if bugs.empty:
        return pd.DataFrame()

    grouped = (
        bugs.groupby(["feature_area", "pain_point"])
        .agg(
            count=("pain_point", "count"),
            avg_rating=("rating", "mean"),
            severity=(
                "severity",
                lambda x: x.mode().iloc[0] if not x.mode().empty else "medium",
            ),
            sources=("source", lambda x: ", ".join(x.unique())),
        )
        .reset_index()
        .sort_values("count", ascending=False)
        .head(n)
    )

    return grouped.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Top feature requests
# ---------------------------------------------------------------------------

def get_top_feature_requests(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Most requested features based on category == 'feature_request'."""
    required_cols = {"category", "feature_area", "one_line_summary", "rating", "source"}
    if df.empty or not required_cols.issubset(df.columns):
        return pd.DataFrame()

    features = df[df["category"] == "feature_request"].copy()
    if features.empty:
        return pd.DataFrame()

    features = features.dropna(subset=["one_line_summary"])
    if features.empty:
        return pd.DataFrame()

    grouped = (
        features.groupby(["feature_area", "one_line_summary"])
        .agg(
            mentions=("one_line_summary", "count"),
            avg_rating=("rating", "mean"),
            sources=("source", lambda x: ", ".join(x.unique())),
        )
        .reset_index()
        .sort_values("mentions", ascending=False)
        .head(n)
    )

    return grouped.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Most loved features
# ---------------------------------------------------------------------------

def get_most_loved_features(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Features with the most positive mentions."""
    required_cols = {"sentiment", "feature_area", "rating", "one_line_summary"}
    if df.empty or not required_cols.issubset(df.columns):
        return pd.DataFrame()

    praise = df[df["sentiment"] == "positive"].copy()
    if praise.empty:
        return pd.DataFrame()

    grouped = (
        praise.groupby("feature_area")
        .agg(
            positive_mentions=("feature_area", "count"),
            avg_rating=("rating", "mean"),
            sample_praise=(
                "one_line_summary",
                lambda x: " | ".join(x.dropna().head(3).tolist()),
            ),
        )
        .reset_index()
        .sort_values("positive_mentions", ascending=False)
        .head(n)
    )

    return grouped.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Churn drivers (1-2 star reviews)
# ---------------------------------------------------------------------------

def get_churn_drivers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Issues driving 1–2 star reviews (strongest churn signals)."""
    required_cols = {"rating", "feature_area", "pain_point", "severity"}
    if df.empty or not required_cols.issubset(df.columns):
        return pd.DataFrame()

    churn = df[df["rating"] <= 2].copy()
    if churn.empty:
        return pd.DataFrame()

    churn = churn.dropna(subset=["pain_point"])
    churn = churn[churn["pain_point"].astype(str).str.strip() != ""]
    if churn.empty:
        return pd.DataFrame()

    grouped = (
        churn.groupby(["feature_area", "pain_point"])
        .agg(
            count=("pain_point", "count"),
            avg_rating=("rating", "mean"),
            severity=(
                "severity",
                lambda x: x.mode().iloc[0] if not x.mode().empty else "high",
            ),
        )
        .reset_index()
        .sort_values("count", ascending=False)
        .head(n)
    )

    return grouped.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Competitor mentions
# ---------------------------------------------------------------------------

def get_competitor_mentions(df: pd.DataFrame) -> pd.DataFrame:
    """Extract and aggregate competitor mentions from reviews."""
    if df.empty or "competitor_mention" not in df.columns:
        return pd.DataFrame()

    comps = df[
        df["competitor_mention"].notna()
        & (df["competitor_mention"].astype(str).str.strip() != "")
    ].copy()
    if comps.empty:
        return pd.DataFrame()

    summary_col = "one_line_summary" if "one_line_summary" in comps.columns else None

    if summary_col:
        grouped = (
            comps.groupby("competitor_mention")
            .agg(
                mentions=("competitor_mention", "count"),
                context=(
                    summary_col,
                    lambda x: " | ".join(x.dropna().head(3).tolist()),
                ),
            )
            .reset_index()
            .sort_values("mentions", ascending=False)
        )
    else:
        grouped = (
            comps.groupby("competitor_mention")
            .agg(mentions=("competitor_mention", "count"))
            .reset_index()
            .sort_values("mentions", ascending=False)
        )

    return grouped.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Distribution helpers (for charts)
# ---------------------------------------------------------------------------

def get_sentiment_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """Sentiment value counts → dict."""
    if df.empty or "sentiment" not in df.columns:
        return {}
    return df["sentiment"].value_counts().to_dict()


def get_rating_distribution(df: pd.DataFrame) -> Dict[int, int]:
    """Rating value counts → dict (sorted by rating)."""
    if df.empty or "rating" not in df.columns:
        return {}
    return df["rating"].value_counts().sort_index().to_dict()


def get_source_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """Review count per source."""
    if df.empty or "source" not in df.columns:
        return {}
    return df["source"].value_counts().to_dict()


def get_app_distribution(df: pd.DataFrame) -> Dict[str, int]:
    """Review count per app."""
    if df.empty or "app_name" not in df.columns:
        return {}
    return df["app_name"].value_counts().to_dict()


# ---------------------------------------------------------------------------
# Recommendation engine input
# ---------------------------------------------------------------------------

def prepare_recommendation_input(df: pd.DataFrame) -> Dict[str, Any]:
    """Prepare a consolidated data dict for the AI recommendation engine.

    Returns a dictionary that can be JSON-serialised and passed into the
    Gemini recommendation prompt.
    """
    if df.empty:
        return {
            "overview": get_overview_metrics(df),
            "top_bugs": [],
            "top_feature_requests": [],
            "churn_drivers": [],
            "most_loved": [],
            "competitor_mentions": [],
            "feature_area_breakdown": [],
            "total_reviews": 0,
            "date_range": "N/A",
        }

    bugs_df = get_top_bugs(df)
    features_df = get_top_feature_requests(df)
    churn_df = get_churn_drivers(df)
    loved_df = get_most_loved_features(df)
    comp_df = get_competitor_mentions(df)
    farea_df = get_feature_area_breakdown(df)

    # Date range -----------------------------------------------------------
    date_range = "N/A"
    if "review_date" in df.columns:
        dated = _ensure_datetime(df)
        valid_dates = dated["review_date"].dropna()
        if not valid_dates.empty:
            date_range = f"{valid_dates.min().date()} to {valid_dates.max().date()}"

    return {
        "overview": get_overview_metrics(df),
        "top_bugs": bugs_df.to_dict("records") if not bugs_df.empty else [],
        "top_feature_requests": features_df.to_dict("records") if not features_df.empty else [],
        "churn_drivers": churn_df.to_dict("records") if not churn_df.empty else [],
        "most_loved": loved_df.to_dict("records") if not loved_df.empty else [],
        "competitor_mentions": comp_df.to_dict("records") if not comp_df.empty else [],
        "feature_area_breakdown": farea_df.to_dict("records") if not farea_df.empty else [],
        "total_reviews": len(df),
        "date_range": date_range,
    }

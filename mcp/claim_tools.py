"""
Claim MCP (Model Context Protocol) Tools
Extended with trading data analysis using Pandas
"""

from datetime import datetime
from typing import List, Dict
import re
import pandas as pd


# -------------------------------------------------------------------
# 1. Extract dates from retrieved claim text
# -------------------------------------------------------------------
def extract_dates_from_text(text: str) -> List[str]:
    """Extract ISO-formatted dates (YYYY-MM-DD) from text."""
    pattern = r"\b\d{4}-\d{2}-\d{2}\b"
    return re.findall(pattern, text)


# -------------------------------------------------------------------
# 2. Compute claim duration from extracted dates
# -------------------------------------------------------------------
def compute_claim_duration(dates: List[str]) -> int:
    """Compute claim duration in days based on a list of ISO dates."""
    if len(dates) < 2:
        return -1
    parsed = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
    return (max(parsed) - min(parsed)).days


# -------------------------------------------------------------------
# 3. Validate presence of required claim documents
# -------------------------------------------------------------------
def validate_required_documents(
    text: str, required_documents: List[str]
) -> Dict[str, bool]:
    """Check whether required document names appear in the retrieved text."""
    text_lower = text.lower()
    return {doc: (doc.lower() in text_lower) for doc in required_documents}


# -------------------------------------------------------------------
# 4. High-level MCP helper for timeline analysis
# -------------------------------------------------------------------
def analyze_claim_timeline(text: str) -> Dict[str, object]:
    """Extract dates and compute duration."""
    dates = extract_dates_from_text(text)
    duration = compute_claim_duration(dates)
    return {"dates_found": dates, "claim_duration_days": duration}


# -------------------------------------------------------------------
# 5. Extract price range from trading data
# -------------------------------------------------------------------
def extract_price_range(text: str) -> Dict[str, float]:
    """Extract high and low prices from trading text."""
    price_pattern = r"\$?(\d+\.?\d*)"
    prices = [float(m) for m in re.findall(price_pattern, text)]

    if prices:
        return {
            "high": max(prices),
            "low": min(prices),
        }

    return {"high": None, "low": None}


# -------------------------------------------------------------------
# 6. Analyze trading patterns with Pandas
# -------------------------------------------------------------------
def analyze_trading_patterns(text: str) -> Dict[str, any]:
    """
    Use Pandas to analyze trading patterns from retrieved text.
    Extracts structured data and performs statistical analysis.
    """
    try:
        lines = text.split("\n")
        data_rows = []

        for line in lines:
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", line)
            price_match = re.search(r"(\d+\.\d{2})", line)

            if date_match and price_match:
                data_rows.append(
                    {"date": date_match.group(1), "price": float(price_match.group(1))}
                )

        if not data_rows:
            return {"error": "No trading data found"}

        df = pd.DataFrame(data_rows)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        stats = {
            "total_days": len(df),
            "avg_price": round(df["price"].mean(), 2),
            "price_std": round(df["price"].std(), 2),
            "price_volatility": round(
                (df["price"].std() / df["price"].mean()) * 100, 2
            ),
            "max_price": round(df["price"].max(), 2),
            "min_price": round(df["price"].min(), 2),
            "price_change_pct": (
                round(
                    ((df["price"].iloc[-1] - df["price"].iloc[0]) / df["price"].iloc[0])
                    * 100,
                    2,
                )
                if len(df) > 1
                else 0
            ),
        }

        return stats

    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}


# -------------------------------------------------------------------
# 7. Calculate moving averages
# -------------------------------------------------------------------
def calculate_moving_average(text: str, window: int = 5) -> Dict[str, any]:
    """
    Calculate moving average of prices using Pandas.
    """
    try:
        price_pattern = r"(\d+\.\d{2})"
        prices = [float(m) for m in re.findall(price_pattern, text)]

        if len(prices) < window:
            return {
                "error": f"Not enough data points (need {window}, got {len(prices)})"
            }

        df = pd.DataFrame({"price": prices})

        df["ma"] = df["price"].rolling(window=window).mean()

        latest_ma = df["ma"].iloc[-1]
        latest_price = df["price"].iloc[-1]

        return {
            "latest_price": round(latest_price, 2),
            "moving_average": round(latest_ma, 2),
            "above_ma": latest_price > latest_ma,
            "window": window,
        }

    except Exception as e:
        return {"error": f"Moving average calculation failed: {str(e)}"}

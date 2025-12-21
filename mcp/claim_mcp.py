from typing import List
from langchain_core.tools import Tool
import json
from mcp.claim_tools import (
    analyze_claim_timeline,
    validate_required_documents,
    extract_price_range,
    analyze_trading_patterns,
    calculate_moving_average,
)


def timeline_tool(text: str) -> str:
    result = analyze_claim_timeline(text)
    return json.dumps(
        {
            "dates_found": len(result["dates_found"]),
            "duration_days": result["claim_duration_days"],
            "first_date": result["dates_found"][0] if result["dates_found"] else None,
            "last_date": result["dates_found"][-1] if result["dates_found"] else None,
        }
    )


def validation_tool(text: str) -> str:
    result = validate_required_documents(
        text, ["OHLCV data", "price", "volume", "date"]
    )
    missing = [k for k, v in result.items() if not v]
    return json.dumps({"missing_fields": missing, "all_present": len(missing) == 0})


def price_range_tool(text: str) -> str:
    result = extract_price_range(text)
    return json.dumps(
        {
            "high": result["high"],
            "low": result["low"],
            "range": (
                result["high"] - result["low"]
                if result["high"] and result["low"]
                else None
            ),
        }
    )


def patterns_tool(text: str) -> str:
    result = analyze_trading_patterns(text)
    if "error" in result:
        return json.dumps({"error": result["error"]})
    return json.dumps(
        {
            "avg_price": result["avg_price"],
            "volatility": result["price_volatility"],
            "price_change_pct": result["price_change_pct"],
            "max_price": result["max_price"],
            "min_price": result["min_price"],
        }
    )


def moving_average_tool(text: str) -> str:
    result = calculate_moving_average(text, window=5)
    if "error" in result:
        return json.dumps({"error": result["error"]})
    return json.dumps(
        {
            "latest_price": result["latest_price"],
            "moving_average": result["moving_average"],
            "signal": "BULLISH" if result["above_ma"] else "BEARISH",
        }
    )


class ClaimMCP:
    def __init__(self):
        self.tools = [
            Tool(
                name="GetTimeline",
                func=timeline_tool,
                description="Extract timeline dates and calculate duration from trading data text",
            ),
            Tool(
                name="ValidateData",
                func=validation_tool,
                description="Check if required trading data fields (OHLCV, price, volume, date) are present",
            ),
            Tool(
                name="GetPriceRange",
                func=price_range_tool,
                description="Extract high and low prices from trading data",
            ),
            Tool(
                name="AnalyzePatterns",
                func=patterns_tool,
                description="Calculate trading statistics: average price, volatility, price changes",
            ),
            Tool(
                name="CalculateMA",
                func=moving_average_tool,
                description="Calculate 5-day moving average and determine bullish/bearish signal",
            ),
        ]

    def get_tools(self) -> List[Tool]:
        return self.tools

    def run(self, query: str, contexts: list[str]):
        text = "\n".join(contexts)
        q = query.lower()

        if "timeline" in q or "duration" in q:
            return timeline_tool(text)
        elif "missing" in q or "validate" in q:
            return validation_tool(text)
        elif "range" in q or ("high" in q and "low" in q):
            return price_range_tool(text)
        elif "pattern" in q or "statistics" in q:
            return patterns_tool(text)
        elif "moving average" in q or "trend" in q:
            return moving_average_tool(text)

        return None

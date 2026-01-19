"""
Financial MCP (Model Context Protocol)

- Actually uses all financial tools
- Smart tool selection based on query
- Formatted output
"""

from typing import List, Dict
from langchain_core.tools import Tool
import re
from mcp.financial_tools import (
    extract_dollar_amounts,
    extract_percentages,
    analyze_profitability,
    extract_risk_keywords,
    analyze_financial_health,
)


class FinancialMCP:
    """
    MCP Tool Provider for Financial Analysis.
    
    Uses specialized tools to extract and analyze financial data:
    - Dollar amounts extraction
    - Percentage extraction
    - Fiscal period detection
    - Profitability analysis
    - Risk keyword detection
    - Overall financial health assessment
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.tools = self._create_tools() if enabled else []

    def _create_tools(self) -> list:
        """Create LangChain-compatible tools."""
        return [
            Tool(
                name="ExtractDollarAmounts",
                func=self._extract_amounts_tool,
                description="Extract and rank dollar amounts from financial text"
            ),
            Tool(
                name="ExtractPercentages",
                func=self._extract_percentages_tool,
                description="Extract percentage values from financial text"
            ),
            Tool(
                name="AnalyzeProfitability",
                func=self._analyze_profitability_tool,
                description="Determine if company is profitable or reporting losses"
            ),
            Tool(
                name="ExtractRiskKeywords",
                func=self._extract_risks_tool,
                description="Identify risk-related keywords and concerns"
            ),
            Tool(
                name="AnalyzeFinancialHealth",
                func=self._analyze_health_tool,
                description="Comprehensive financial health assessment"
            ),
        ]

    def _extract_amounts_tool(self, text: str) -> str:
        results = extract_dollar_amounts(text)
        return self._format_amounts(results)
    
    def _extract_percentages_tool(self, text: str) -> str:
        results = extract_percentages(text)
        return self._format_percentages(results)
    
    def _analyze_profitability_tool(self, text: str) -> str:
        result = analyze_profitability(text)
        return self._format_profitability(result)
    
    def _extract_risks_tool(self, text: str) -> str:
        keywords = extract_risk_keywords(text)
        return self._format_risks(keywords)
    
    def _analyze_health_tool(self, text: str) -> str:
        result = analyze_financial_health(text)
        return self._format_health(result)

    def _format_amounts(self, results: list) -> str:
        """Format top dollar amounts."""
        if not results:
            return ""
        
        seen = set()
        top = []
        for r in sorted(results, key=lambda x: x.get("amount", 0), reverse=True):
            formatted = r.get("formatted", "")
            if formatted and formatted not in seen and len(top) < 5:
                seen.add(formatted)
                top.append(r)
        
        if not top:
            return ""
        
        lines = ["**📊 Key Financial Figures:**"]
        for item in top:
            context = item.get("context", "")[:50]
            lines.append(f"• {item['formatted']} - {context}...")
        
        return "\n".join(lines)

    def _format_percentages(self, results: list) -> str:
        """Format key percentages."""
        if not results:
            return ""
        
        seen = set()
        unique = []
        for r in results:
            formatted = r.get("formatted", "")
            if formatted and formatted not in seen and len(unique) < 5:
                seen.add(formatted)
                unique.append(r)
        
        if not unique:
            return ""
        
        lines = ["**📈 Key Percentages:**"]
        for item in unique:
            context = item.get("context", "")[:40]
            lines.append(f"• {item['formatted']} - {context}...")
        
        return "\n".join(lines)

    def _format_profitability(self, result: dict) -> str:
        """Format profitability status."""
        status = result.get("status", "unknown")
        
        if status == "loss":
            indicators = result.get("loss_indicators", [])
            msg = "⚠️ **Profitability Status:** NET LOSS"
            if indicators:
                msg += f"\n   Indicators: {', '.join(indicators[:3])}"
            return msg
        elif status == "profit":
            indicators = result.get("profit_indicators", [])
            msg = "✅ **Profitability Status:** PROFITABLE"
            if indicators:
                msg += f"\n   Indicators: {', '.join(indicators[:3])}"
            return msg
        else:
            return "⚪ **Profitability Status:** Unable to determine"

    def _format_risks(self, keywords: list) -> str:
        """Format risk indicators."""
        if not keywords:
            return ""
        
        lines = ["**⚠️ Risk Indicators Detected:**"]
        for kw in keywords[:7]:
            lines.append(f"• {kw}")
        
        return "\n".join(lines)

    def _format_health(self, result: dict) -> str:
        """Format financial health assessment."""
        if not result:
            return ""
        
        lines = ["**🏥 Financial Health Assessment:**"]
        
        # Overall score
        score = result.get("overall_score", 0)
        if score >= 7:
            lines.append(f"• Overall: 🟢 Strong ({score}/10)")
        elif score >= 5:
            lines.append(f"• Overall: 🟡 Moderate ({score}/10)")
        else:
            lines.append(f"• Overall: 🔴 Weak ({score}/10)")
        
        # Key metrics
        if result.get("has_cash"):
            lines.append("• Cash Position: ✓ Adequate")
        if result.get("has_revenue"):
            lines.append("• Revenue: ✓ Present")
        if result.get("high_debt"):
            lines.append("• Debt Level: ⚠️ High")
        if result.get("going_concern"):
            lines.append("• Going Concern: 🔴 Warning Present")
        
        return "\n".join(lines)

    def get_tools(self) -> List[Tool]:
        """Return LangChain tools."""
        return self.tools

    def run(self, query: str, contexts: List[str]) -> str:
        """
        Run appropriate analysis based on query type.
        
        Automatically selects which tools to use based on query keywords.
        """
        if not self.enabled or not contexts:
            return ""
        
        text = "\n".join(contexts)
        query_lower = query.lower()
        
        outputs = []
        
        # Revenue/Income/Financial figures
        if any(w in query_lower for w in ["revenue", "income", "cash", "debt", "assets", "amount", "how much", "total"]):
            amounts = self._format_amounts(extract_dollar_amounts(text))
            if amounts:
                outputs.append(amounts)
        
        # Profitability
        if any(w in query_lower for w in ["profit", "loss", "profitable", "earnings", "net income"]):
            profitability = self._format_profitability(analyze_profitability(text))
            if profitability:
                outputs.append(profitability)
        
        # Margins/Growth/Percentages
        if any(w in query_lower for w in ["margin", "growth", "percent", "rate", "ratio", "%"]):
            percentages = self._format_percentages(extract_percentages(text))
            if percentages:
                outputs.append(percentages)
        
        # Risk analysis
        if any(w in query_lower for w in ["risk", "concern", "warning", "challenge", "threat"]):
            risks = self._format_risks(extract_risk_keywords(text))
            if risks:
                outputs.append(risks)
        
        # Financial health / Overview
        if any(w in query_lower for w in ["health", "overview", "summary", "position", "status", "condition"]):
            health = self._format_health(analyze_financial_health(text))
            if health:
                outputs.append(health)
        
        # Join outputs with separator
        if outputs:
            return "\n\n---\n**MCP Analysis:**\n" + "\n\n".join(outputs)
        
        return ""


# Alias for backward compatibility
ClaimMCP = FinancialMCP
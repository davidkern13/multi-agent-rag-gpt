"""
Financial Analysis Tools (MCP)

Tools for SEC filing analysis
"""

from datetime import datetime
from typing import List, Dict
import re


def extract_dollar_amounts(text: str) -> List[Dict]:
    """
    Extract dollar amounts from text.
    
    Returns:
        List of {amount, context} dicts
    """
    patterns = [
        r'\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion|thousand)?',
        r'([\d,]+(?:\.\d+)?)\s*(million|billion|thousand)?\s*(?:dollars|\$)',
    ]
    
    results = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            amount_str = match.group(1).replace(',', '')
            multiplier_str = match.group(2) if match.group(2) else ''
            
            try:
                amount = float(amount_str)
                
                if 'billion' in multiplier_str.lower():
                    amount *= 1_000_000_000
                elif 'million' in multiplier_str.lower():
                    amount *= 1_000_000
                elif 'thousand' in multiplier_str.lower():
                    amount *= 1_000
                
                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()
                
                results.append({
                    "amount": amount,
                    "formatted": f"${amount:,.2f}",
                    "context": context
                })
            except ValueError:
                continue
    
    return results


def extract_percentages(text: str) -> List[Dict]:
    """
    Extract percentage values from text.
    
    Returns:
        List of {value, context} dicts
    """
    pattern = r'([-+]?\d+(?:\.\d+)?)\s*%'
    
    results = []
    for match in re.finditer(pattern, text):
        try:
            value = float(match.group(1))
            
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()
            
            results.append({
                "value": value,
                "formatted": f"{value:+.2f}%" if value >= 0 else f"{value:.2f}%",
                "context": context
            })
        except ValueError:
            continue
    
    return results


def extract_fiscal_periods(text: str) -> List[str]:
    """
    Extract fiscal periods mentioned in text.
    
    Returns:
        List of period strings (e.g., ["Q4 2024", "FY 2023"])
    """
    patterns = [
        r'Q[1-4]\s*20\d{2}',
        r'(?:FY|fiscal year)\s*20\d{2}',
        r'(?:first|second|third|fourth)\s+quarter\s+(?:of\s+)?20\d{2}',
        r'(?:year|twelve months)\s+ended\s+\w+\s+\d{1,2},?\s+20\d{2}',
        r'(?:three|six|nine|twelve)\s+months\s+ended',
    ]
    
    results = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        results.extend(matches)
    
    return list(set(results))


def analyze_profitability(text: str) -> Dict:
    """
    Analyze profitability indicators in text.
    
    Returns:
        Dict with profitability assessment
    """
    text_lower = text.lower()
    
    # Check for loss indicators
    loss_indicators = [
        'net loss', 'operating loss', 'loss from operations',
        'accumulated deficit', 'negative cash flow'
    ]
    
    # Check for profit indicators
    profit_indicators = [
        'net income', 'net profit', 'operating income',
        'positive cash flow', 'profitable'
    ]
    
    losses_found = [ind for ind in loss_indicators if ind in text_lower]
    profits_found = [ind for ind in profit_indicators if ind in text_lower]
    
    # Determine status
    if losses_found and not profits_found:
        status = "UNPROFITABLE"
        assessment = "Company is reporting losses"
    elif profits_found and not losses_found:
        status = "PROFITABLE"
        assessment = "Company is reporting profits"
    elif losses_found and profits_found:
        status = "MIXED"
        assessment = "Company has both profitable and unprofitable segments/periods"
    else:
        status = "UNKNOWN"
        assessment = "Profitability status unclear from text"
    
    return {
        "status": status,
        "assessment": assessment,
        "loss_indicators": losses_found,
        "profit_indicators": profits_found
    }


def extract_risk_keywords(text: str) -> List[str]:
    """
    Extract risk-related keywords from text.
    
    Returns:
        List of risk keywords found
    """
    risk_keywords = [
        'risk', 'uncertainty', 'challenge', 'competition',
        'regulatory', 'compliance', 'litigation', 'lawsuit',
        'debt', 'leverage', 'liquidity', 'going concern',
        'material weakness', 'impairment', 'restructuring',
        'concentration', 'dependency', 'cybersecurity',
        'volatility', 'inflation', 'recession', 'downturn'
    ]
    
    text_lower = text.lower()
    return [kw for kw in risk_keywords if kw in text_lower]


def calculate_growth_rate(current: float, previous: float) -> Dict:
    """
    Calculate growth rate between two values.
    
    Returns:
        Dict with growth analysis
    """
    if previous == 0:
        return {"error": "Cannot calculate: previous value is zero"}
    
    change = current - previous
    rate = (change / abs(previous)) * 100
    
    return {
        "current": current,
        "previous": previous,
        "change": change,
        "growth_rate": round(rate, 2),
        "formatted": f"{rate:+.2f}%",
        "direction": "increase" if rate > 0 else "decrease" if rate < 0 else "unchanged"
    }


def analyze_financial_health(text: str) -> Dict:
    """
    Comprehensive financial health analysis.
    
    Returns:
        Dict with health assessment
    """
    profitability = analyze_profitability(text)
    risks = extract_risk_keywords(text)
    amounts = extract_dollar_amounts(text)
    periods = extract_fiscal_periods(text)
    
    # Count red flags
    red_flags = []
    
    if profitability["status"] == "UNPROFITABLE":
        red_flags.append("Company reporting losses")
    
    if "going concern" in risks:
        red_flags.append("Going concern warning")
    
    if "material weakness" in risks:
        red_flags.append("Material weakness in controls")
    
    if len(risks) > 5:
        red_flags.append("Multiple risk factors identified")
    
    # Health score (simple heuristic)
    health_score = 100
    health_score -= len(red_flags) * 20
    health_score -= len(risks) * 2
    health_score = max(0, min(100, health_score))
    
    return {
        "profitability": profitability,
        "risk_keywords": risks,
        "red_flags": red_flags,
        "health_score": health_score,
        "fiscal_periods": periods,
        "amounts_found": len(amounts)
    }
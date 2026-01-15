"""
Metadata Extractor - Financial Reports

- SEC filing metadata extraction
- Financial document classification
"""

import re
from dateutil import parser
from collections import Counter


def extract_timestamp(text: str):
    """Extract the first date found in text."""
    match = re.search(r"\b(?:\d{4}-\d{2}-\d{2}|\w{3,9} \d{1,2}, \d{4})\b", text)
    if match:
        try:
            return str(parser.parse(match.group(0)).date())
        except Exception:
            return None
    return None


def extract_entities_from_text(text: str, top_n: int = 10):
    """
    Extract entities from financial text.

    Returns:
        List of tuples: [(entity, count), ...]
    """
    # Stock tickers
    stock_tickers = re.findall(r"\b[A-Z]{1,5}\b", text)

    # Capitalized words (company names, etc.)
    capitalized = re.findall(r"\b[A-Z][a-z]+\b", text)

    # Financial terms
    financial_terms = [
        "revenue", "profit", "loss", "earnings", "guidance", "forecast",
        "quarter", "annual", "shares", "stock", "dividend", "market",
        "assets", "liabilities", "equity", "cash", "debt", "margin",
        "income", "expense", "operating", "gross", "net", "ebitda",
        "eps", "gaap", "non-gaap", "fiscal", "segment", "backlog",
        "contract", "customer", "acquisition", "restructuring",
        "impairment", "depreciation", "amortization", "goodwill",
        "risk", "compliance", "regulatory", "sec", "filing",
    ]

    found_terms = [term for term in financial_terms if term.lower() in text.lower()]

    all_entities = stock_tickers + capitalized + found_terms

    stopwords = {
        "The", "This", "That", "With", "From", "Were", "Have", "More",
        "Been", "Their", "About", "Other", "These", "Which", "Would",
        "Could", "Should", "Company", "December", "January", "February",
    }
    filtered = [e for e in all_entities if e not in stopwords and len(e) > 1]

    counter = Counter(filtered)
    return counter.most_common(top_n)


def extract_financial_values(text: str, max_values: int = 10):
    """
    Extract dollar amounts and percentages from text.

    Returns:
        List of value strings
    """
    values = re.findall(r"\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|thousand))?|\d+\.?\d*%", text, re.IGNORECASE)
    return values[:max_values]


def extract_fiscal_period(text: str) -> str:
    """
    Extract fiscal period from text.
    
    Returns:
        Period string (e.g., "Q4 2024", "FY 2024")
    """
    # Look for quarter references
    quarter_match = re.search(r"Q[1-4]\s*20\d{2}", text, re.IGNORECASE)
    if quarter_match:
        return quarter_match.group(0).upper()
    
    # Look for fiscal year
    fy_match = re.search(r"(?:FY|fiscal\s*year)\s*20\d{2}", text, re.IGNORECASE)
    if fy_match:
        return fy_match.group(0).upper()
    
    # Look for year ended
    year_match = re.search(r"(?:year|twelve months)\s+ended\s+\w+\s+\d{1,2},?\s+(20\d{2})", text, re.IGNORECASE)
    if year_match:
        return f"FY {year_match.group(1)}"
    
    return None


def extract_doc_type(text: str) -> str:
    """
    Determine document type based on content.
    """
    text_lower = text.lower()

    # SEC Filing types
    if any(term in text_lower for term in ["10-k", "annual report", "form 10-k"]):
        return "sec_10k"
    elif any(term in text_lower for term in ["10-q", "quarterly report", "form 10-q"]):
        return "sec_10q"
    elif any(term in text_lower for term in ["8-k", "current report", "form 8-k"]):
        return "sec_8k"
    elif any(term in text_lower for term in ["proxy", "def 14a"]):
        return "sec_proxy"
    
    # Financial sections
    elif any(term in text_lower for term in ["risk factor", "risks"]):
        return "risk_factors"
    elif any(term in text_lower for term in ["management discussion", "md&a", "management's discussion"]):
        return "mda_section"
    elif any(term in text_lower for term in ["financial statement", "balance sheet", "income statement"]):
        return "financial_statements"
    elif any(term in text_lower for term in ["notes to", "footnote"]):
        return "financial_notes"
    elif any(term in text_lower for term in ["business overview", "description of business"]):
        return "business_description"
    elif any(term in text_lower for term in ["forward-looking", "outlook", "guidance"]):
        return "forward_looking"
    
    return "general_section"


def extract_section_title(text: str) -> str:
    """
    Extract section title from text.
    """
    lines = text.strip().splitlines()
    
    # Common SEC section headers
    sec_headers = [
        "RISK FACTORS", "BUSINESS", "MANAGEMENT'S DISCUSSION",
        "FINANCIAL STATEMENTS", "NOTES TO", "PROPERTIES",
        "LEGAL PROCEEDINGS", "MARKET FOR", "SELECTED FINANCIAL",
        "DIRECTORS", "EXECUTIVE COMPENSATION", "SECURITY OWNERSHIP",
        "PART I", "PART II", "PART III", "PART IV", "ITEM",
    ]
    
    for line in lines:
        line = line.strip()
        if line and len(line) < 100:
            # Check if it's a SEC header
            line_upper = line.upper()
            if any(header in line_upper for header in sec_headers):
                return line
            # Check if it looks like a title
            if line.isupper() or (line[0].isupper() and line.count(".") < 2):
                return line

    # Fallback: first non-empty line
    for line in lines:
        if line.strip():
            return line.strip()[:100]

    return "Untitled Section"


def extract_metadata_summary(text: str) -> dict:
    """
    Extract comprehensive metadata from SEC filing text.

    Returns:
        Dictionary with all extracted metadata
    """
    return {
        "doc_type": extract_doc_type(text),
        "timestamp": extract_timestamp(text),
        "fiscal_period": extract_fiscal_period(text),
        "entities": extract_entities_from_text(text, top_n=10),
        "financial_values": extract_financial_values(text, max_values=10),
        "section_title": extract_section_title(text),
        "text_length": len(text),
        "has_financial_data": any(
            term in text.lower() for term in ["$", "revenue", "income", "loss", "margin"]
        ),
        "has_risk_factors": "risk" in text.lower(),
        "has_forward_looking": any(
            term in text.lower() for term in ["forward-looking", "outlook", "expects", "anticipates"]
        ),
    }


# Backward compatibility
def extract_entities(text: str):
    return extract_entities_from_text(text, top_n=10)


def extract_price_contexts(text: str, max_prices: int = 5):
    return extract_financial_values(text, max_values=max_prices)
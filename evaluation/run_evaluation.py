"""
SEC Filing Evaluation System - BigBear.ai 10-Q Q3 2025
======================================================

ALL GROUND TRUTH VALUES ARE REAL DATA FROM THE FILING!

Test breakdown:
- 25 Hard Tests (Needle Agent) - exact ground truth
- 13 LLM-as-Judge Tests (Summary Agent)
- 7 Human Grader Tests
Total: 45 tests
"""

import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import json
import time
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict, field

# ============================================================
# GROUND TRUTH - BigBear.ai 10-Q Q3 2025 - REAL DATA!
# ============================================================

GROUND_TRUTH = {
    # ===== COMPANY IDENTIFICATION =====
    "company_name": "BigBear.ai Holdings, Inc.",
    "ticker_symbol": "BBAI",
    "exchange": "New York Stock Exchange",
    "state_of_incorporation": "Delaware",
    "employer_id": "85-4164597",
    "commission_file_number": "001-40031",
    "fiscal_period": "Q3 2025",
    "fiscal_period_end_date": "September 30, 2025",
    "filing_type": "10-Q",
    "headquarters_address": "7950 Jones Branch Drive, McLean, VA",
    "headquarters_zip": "22102",
    "phone_number": "(410) 312-0885",
    
    # ===== SHARE DATA =====
    "shares_outstanding": 436_551_228,
    "par_value_per_share": 0.0001,
    "warrant_exercise_price": 11.50,
    
    # ===== REVENUE =====
    "total_revenue_q3_2025": 33_100_000,
    "total_revenue_q3_2024": 41_500_000,
    "revenue_change_pct": -20.0,
    "revenue_guidance_low": 125_000_000,
    "revenue_guidance_high": 140_000_000,
    
    # ===== GROSS PROFIT & MARGIN =====
    "gross_profit_q3_2025": 7_414_000,
    "gross_margin_q3_2025": 22.4,
    "gross_margin_q3_2024": 25.9,
    
    # ===== NET INCOME =====
    "net_income_q3_2025": 2_500_000,
    "net_loss_q3_2024": -15_100_000,
    "is_profitable_q3_2025": True,
    
    # ===== OPERATING METRICS =====
    "adjusted_ebitda_q3_2025": -9_400_000,
    "adjusted_ebitda_q3_2024": 900_000,
    "sga_expense_q3_2025": 25_300_000,
    "sga_expense_q3_2024": 17_500_000,
    
    # ===== EPS =====
    "eps_adjusted_q3_2025": -0.07,
    "eps_adjusted_q3_2024": -0.05,
    
    # ===== BALANCE SHEET =====
    "cash_and_equivalents": 456_600_000,
    "total_assets": 919_800_000,
    "total_liabilities": 309_700_000,
    "stockholders_equity": 610_000_000,
    "total_debt": 104_900_000,
    "debt_to_equity_ratio": 17.2,
    
    # ===== BUSINESS INFO =====
    "pending_acquisition_name": "Ask Sage",
    "has_pending_acquisition": True,
    "acquisition_close_expected": "Q4 2025 or Q1 2026",
    
    # ===== FILING CLASSIFICATIONS =====
    "is_smaller_reporting_company": True,
    "is_emerging_growth_company": True,
    "is_accelerated_filer": True,
    "is_shell_company": False,
    
    # ===== KEY DRIVERS =====
    "derivative_liability_change": 26_100_000,
    "sga_increase_yoy": 7_800_000,
    "marketing_increase": 1_400_000,
    "strategic_initiatives_cost": 2_000_000,
    "labor_cost_increase": 4_300_000,
    
    # ===== RISKS =====
    "key_risk_doge": True,
    "key_risk_government_contracts": True,
}


# ============================================================
# HARD TESTS (25) - Needle Agent
# ============================================================

HARD_TESTS = [
    # IDENTIFICATION (5)
    {"id": "H001", "question": "What is the company's official name as stated in the filing?",
     "ground_truth_key": "company_name", "ground_truth_type": "text", "agent": "needle", "category": "identification"},
    {"id": "H002", "question": "What is the company's stock ticker symbol?",
     "ground_truth_key": "ticker_symbol", "ground_truth_type": "text", "agent": "needle", "category": "identification"},
    {"id": "H003", "question": "On which stock exchange is the company listed?",
     "ground_truth_key": "exchange", "ground_truth_type": "text", "agent": "needle", "category": "identification"},
    {"id": "H004", "question": "What is the company's state of incorporation?",
     "ground_truth_key": "state_of_incorporation", "ground_truth_type": "text", "agent": "needle", "category": "identification"},
    {"id": "H005", "question": "What is the SEC commission file number?",
     "ground_truth_key": "commission_file_number", "ground_truth_type": "text", "agent": "needle", "category": "identification"},
    
    # SHARE DATA (4)
    {"id": "H006", "question": "How many shares of common stock were outstanding as of November 7, 2025?",
     "ground_truth_key": "shares_outstanding", "ground_truth_type": "number", "tolerance": 0.01, "agent": "needle", "category": "shares"},
    {"id": "H007", "question": "What is the par value per share of common stock?",
     "ground_truth_key": "par_value_per_share", "ground_truth_type": "decimal", "tolerance": 0.01, "agent": "needle", "category": "shares"},
    {"id": "H008", "question": "What is the exercise price for the redeemable warrants?",
     "ground_truth_key": "warrant_exercise_price", "ground_truth_type": "currency", "tolerance": 0.01, "agent": "needle", "category": "shares"},
    {"id": "H009", "question": "What is the company's I.R.S. Employer Identification Number?",
     "ground_truth_key": "employer_id", "ground_truth_type": "text", "agent": "needle", "category": "identification"},
    
    # REVENUE (4)
    {"id": "H010", "question": "What was the total revenue for Q3 2025?",
     "ground_truth_key": "total_revenue_q3_2025", "ground_truth_type": "currency", "tolerance": 0.03, "agent": "needle", "category": "revenue"},
    {"id": "H011", "question": "What was the total revenue for Q3 2024?",
     "ground_truth_key": "total_revenue_q3_2024", "ground_truth_type": "currency", "tolerance": 0.03, "agent": "needle", "category": "revenue"},
    {"id": "H012", "question": "By what percentage did revenue change year-over-year in Q3?",
     "ground_truth_key": "revenue_change_pct", "ground_truth_type": "percentage", "tolerance": 0.15, "agent": "needle", "category": "revenue"},
    {"id": "H013", "question": "What is the company's full-year 2025 revenue guidance (low end)?",
     "ground_truth_key": "revenue_guidance_low", "ground_truth_type": "currency", "tolerance": 0.05, "agent": "needle", "category": "revenue"},
    
    # PROFITABILITY (4)
    {"id": "H014", "question": "What was the gross margin percentage for Q3 2025?",
     "ground_truth_key": "gross_margin_q3_2025", "ground_truth_type": "percentage", "tolerance": 0.05, "agent": "needle", "category": "margins"},
    {"id": "H015", "question": "What was the net income for Q3 2025?",
     "ground_truth_key": "net_income_q3_2025", "ground_truth_type": "currency", "tolerance": 0.05, "agent": "needle", "category": "income"},
    {"id": "H016", "question": "Was BigBear.ai profitable in Q3 2025?",
     "ground_truth_key": "is_profitable_q3_2025", "ground_truth_type": "boolean",
     "true_indicators": ["yes", "profitable", "profit", "net income", "2.5 million"], "agent": "needle", "category": "income"},
    {"id": "H017", "question": "What was the Adjusted EBITDA for Q3 2025?",
     "ground_truth_key": "adjusted_ebitda_q3_2025", "ground_truth_type": "currency", "tolerance": 0.05, "agent": "needle", "category": "income"},
    
    # BALANCE SHEET (5)
    {"id": "H018", "question": "How much cash and cash equivalents did BigBear.ai have as of September 30, 2025?",
     "ground_truth_key": "cash_and_equivalents", "ground_truth_type": "currency", "tolerance": 0.02, "agent": "needle", "category": "balance_sheet"},
    {"id": "H019", "question": "What were the total assets as of September 30, 2025?",
     "ground_truth_key": "total_assets", "ground_truth_type": "currency", "tolerance": 0.03, "agent": "needle", "category": "balance_sheet"},
    {"id": "H020", "question": "What were the total liabilities?",
     "ground_truth_key": "total_liabilities", "ground_truth_type": "currency", "tolerance": 0.03, "agent": "needle", "category": "balance_sheet"},
    {"id": "H021", "question": "What was the total stockholders' equity?",
     "ground_truth_key": "stockholders_equity", "ground_truth_type": "currency", "tolerance": 0.03, "agent": "needle", "category": "balance_sheet"},
    {"id": "H022", "question": "What was the total debt?",
     "ground_truth_key": "total_debt", "ground_truth_type": "currency", "tolerance": 0.05, "agent": "needle", "category": "balance_sheet"},
    
    # BUSINESS (3)
    {"id": "H023", "question": "What company has BigBear.ai announced a definitive agreement to acquire?",
     "ground_truth_key": "pending_acquisition_name", "ground_truth_type": "text", "agent": "needle", "category": "business"},
    {"id": "H024", "question": "What were the SG&A expenses for Q3 2025?",
     "ground_truth_key": "sga_expense_q3_2025", "ground_truth_type": "currency", "tolerance": 0.03, "agent": "needle", "category": "expenses"},
    {"id": "H025", "question": "Is BigBear.ai classified as an emerging growth company?",
     "ground_truth_key": "is_emerging_growth_company", "ground_truth_type": "boolean",
     "true_indicators": ["yes", "emerging growth"], "agent": "needle", "category": "filing"},
]


# ============================================================
# LLM-AS-JUDGE TESTS (13) - Summary Agent
# ============================================================

LLM_JUDGE_TESTS = [
    {"id": "L001", "question": "Provide an executive summary of BigBear.ai's financial performance for Q3 2025.",
     "agent": "summary", "category": "financial_overview",
     "evaluation_criteria": ["Mentions revenue of $33.1 million", "Notes revenue decline of 20%", "Mentions net income of $2.5 million", "References gross margin", "Notes improvement from prior year loss"],
     "min_score": 3},
    {"id": "L002", "question": "What is the overall financial health of BigBear.ai based on this 10-Q filing?",
     "agent": "summary", "category": "financial_overview",
     "evaluation_criteria": ["Mentions strong cash position ($456.6 million)", "Notes revenue is declining", "Discusses profitability", "Considers debt levels", "Provides balanced assessment"],
     "min_score": 3},
    {"id": "L003", "question": "How did BigBear.ai's Q3 2025 performance compare to Q3 2024?",
     "agent": "summary", "category": "financial_overview",
     "evaluation_criteria": ["Revenue comparison", "Net income improvement", "Gross margin change", "EBITDA comparison"],
     "min_score": 3},
    {"id": "L004", "question": "Explain the main drivers of the change in net income from Q3 2024 to Q3 2025.",
     "agent": "summary", "category": "financial_overview",
     "evaluation_criteria": ["Mentions derivative liability changes", "Notes SG&A increase", "References fair value changes", "Explains improvement despite revenue decline"],
     "min_score": 3},
    {"id": "L005", "question": "What are the main risk factors facing BigBear.ai according to this filing?",
     "agent": "summary", "category": "risk_analysis",
     "evaluation_criteria": ["Government contract dependency", "DOGE / government spending cuts", "Sequestration risk", "Acquisition integration risk", "Revenue concentration"],
     "min_score": 3},
    {"id": "L006", "question": "How might changes in government spending or DOGE impact BigBear.ai?",
     "agent": "summary", "category": "risk_analysis",
     "evaluation_criteria": ["Acknowledges government dependency", "Discusses DOGE risks", "Mentions contract terminations", "Notes budget risks"],
     "min_score": 3},
    {"id": "L007", "question": "What are the risks associated with BigBear.ai's planned acquisition of Ask Sage?",
     "agent": "summary", "category": "risk_analysis",
     "evaluation_criteria": ["Integration challenges", "Regulatory approvals needed", "Failure to realize synergies", "Timeline uncertainty"],
     "min_score": 3},
    {"id": "L008", "question": "What is BigBear.ai's business strategy and competitive position?",
     "agent": "summary", "category": "strategic_analysis",
     "evaluation_criteria": ["AI-powered solutions", "Defense and national security focus", "Government sector", "Predictive analytics"],
     "min_score": 3},
    {"id": "L009", "question": "Explain the significance of the Ask Sage acquisition for BigBear.ai.",
     "agent": "summary", "category": "strategic_analysis",
     "evaluation_criteria": ["Generative AI platform", "Defense capabilities expansion", "Agentic AI", "Expected closing timeline"],
     "min_score": 3},
    {"id": "L010", "question": "Why did revenue decline in Q3 2025 and what is the outlook?",
     "agent": "summary", "category": "strategic_analysis",
     "evaluation_criteria": ["Lower Army program volume", "Revenue guidance $125-$140M", "Acquisition growth potential", "Cash position for investments"],
     "min_score": 3},
    {"id": "L011", "question": "Summarize the key highlights and concerns from this 10-Q filing.",
     "agent": "summary", "category": "comprehensive",
     "evaluation_criteria": ["Record cash highlight", "Profitability highlight", "Ask Sage acquisition", "Revenue decline concern", "EBITDA concern"],
     "min_score": 3},
    {"id": "L012", "question": "What are the key takeaways an investor should know from this filing?",
     "agent": "summary", "category": "comprehensive",
     "evaluation_criteria": ["Strong balance sheet", "Revenue declining but profitable", "Strategic acquisition", "Government risk", "Full year guidance"],
     "min_score": 3},
    {"id": "L013", "question": "Create a brief investment thesis for BigBear.ai based on this 10-Q.",
     "agent": "summary", "category": "comprehensive",
     "evaluation_criteria": ["Clear position", "Supported by data", "Growth potential", "Risk acknowledgment", "Professional tone"],
     "min_score": 3},
]


# ============================================================
# HUMAN GRADER TESTS (7)
# ============================================================

HUMAN_GRADER_TESTS = [
    {"id": "HG001", "question": "Based on the 10-Q filing, would you recommend investing in BigBear.ai? Provide a detailed justification.",
     "agent": "summary", "category": "investment_judgment",
     "grading_rubric": "5=Comprehensive analysis with specific numbers, risks, and clear recommendation. 4=Good justification. 3=Basic recommendation. 2=Weak. 1=No recommendation.",
     "aspects_to_evaluate": ["Uses specific financial data", "Considers Ask Sage", "Addresses risks", "Balanced analysis"]},
    {"id": "HG002", "question": "BigBear.ai achieved net income of $2.5M despite revenue declining 20%. Is this sustainable? Analyze the quality of earnings.",
     "agent": "summary", "category": "earnings_quality",
     "grading_rubric": "5=Identifies non-cash gains, compares to Adjusted EBITDA, questions sustainability. 4=Good analysis. 3=Basic. 2=Superficial. 1=No analysis.",
     "aspects_to_evaluate": ["Identifies derivative impact", "GAAP vs non-GAAP", "Sustainability", "SG&A increases"]},
    {"id": "HG003", "question": "Evaluate BigBear.ai's cash position of $456.6 million. Is this a strength or potential concern?",
     "agent": "summary", "category": "strategic_judgment",
     "grading_rubric": "5=Analyzes cash vs burn, M&A optionality, dilution source. 4=Good analysis. 3=Basic. 2=Superficial. 1=No analysis.",
     "aspects_to_evaluate": ["Cash vs losses", "M&A capacity", "Source of cash", "Strategic optionality"]},
    {"id": "HG004", "question": "How should BigBear.ai prepare for potential government spending cuts (DOGE impact)?",
     "agent": "summary", "category": "strategic_recommendation",
     "grading_rubric": "5=Specific actionable recommendations, multiple scenarios. 4=Practical suggestions. 3=Basic. 2=Vague. 1=No recommendations.",
     "aspects_to_evaluate": ["Understanding of risks", "Diversification strategies", "Ask Sage benefits", "Practical advice"]},
    {"id": "HG005", "question": "The gross margin declined from 25.9% to 22.4% YoY. What does this indicate about competitive position?",
     "agent": "summary", "category": "competitive_analysis",
     "grading_rubric": "5=Analyzes causes, compares to peers, discusses pricing power. 4=Good analysis. 3=Basic. 2=Superficial. 1=No analysis.",
     "aspects_to_evaluate": ["Margin trend", "Competitive comparison", "Pricing power", "Program mix"]},
    {"id": "HG006", "question": "Write a one-paragraph analyst note summarizing this 10-Q for institutional investors.",
     "agent": "summary", "category": "professional_writing",
     "grading_rubric": "5=Professional, concise, key metrics, actionable. 4=Well-written. 3=Acceptable. 2=Unprofessional. 1=Not suitable.",
     "aspects_to_evaluate": ["Professional tone", "Key metrics", "Conciseness", "Balanced view"]},
    {"id": "HG007", "question": "If you were on BigBear.ai's board, what three questions would you ask management?",
     "agent": "summary", "category": "critical_thinking",
     "grading_rubric": "5=Insightful probing questions showing deep understanding. 4=Good relevant questions. 3=Basic. 2=Superficial. 1=No meaningful questions.",
     "aspects_to_evaluate": ["Question quality", "Coverage of issues", "Strategic thinking", "Board perspective"]},
]


# ============================================================
# NUMBER EXTRACTOR
# ============================================================

class NumberExtractor:
    MULTIPLIERS = {'billion': 1e9, 'b': 1e9, 'million': 1e6, 'm': 1e6, 'mm': 1e6, 'thousand': 1e3, 'k': 1e3}
    
    @classmethod
    def extract_all(cls, text: str) -> List[Dict]:
        results = []
        # Currency with multiplier
        for match in re.finditer(r'\$\s*\(?([\d,]+(?:\.\d+)?)\)?\s*(billion|million|thousand|[bmk]|mm)?', text, re.IGNORECASE):
            try:
                num = float(match.group(1).replace(',', ''))
                is_neg = '(' in match.group(0) and ')' in match.group(0)
                if match.group(2):
                    m = match.group(2).lower()
                    for k, v in cls.MULTIPLIERS.items():
                        if m.startswith(k[0]) or m == 'mm':
                            num *= v
                            break
                if is_neg: num = -num
                results.append({'value': num, 'raw': match.group(0), 'type': 'currency'})
            except: pass
        # Percentage
        for match in re.finditer(r'([-]?[\d.]+)\s*%', text):
            try: results.append({'value': float(match.group(1)), 'raw': match.group(0), 'type': 'percentage'})
            except: pass
        # Down X%
        for match in re.finditer(r'(?:down|declined|decreased)\s*(\d+(?:\.\d+)?)\s*%', text, re.IGNORECASE):
            try: results.append({'value': -float(match.group(1)), 'raw': match.group(0), 'type': 'percentage'})
            except: pass
        # Large numbers
        for match in re.finditer(r'\b(\d{1,3}(?:,\d{3})+|\d{6,})\b', text):
            try:
                v = float(match.group(1).replace(',', ''))
                if not any(abs(r['value'] - v) < 1 for r in results):
                    results.append({'value': v, 'raw': match.group(0), 'type': 'number'})
            except: pass
        # Small decimals
        for match in re.finditer(r'\$?\s*(0\.\d+)', text):
            try:
                v = float(match.group(1))
                if not any(abs(r['value'] - v) < 0.0001 for r in results):
                    results.append({'value': v, 'raw': match.group(0), 'type': 'decimal'})
            except: pass
        return results


# ============================================================
# CONTEXT RECALL KEYWORDS - For each test, what should be in retrieved chunks
# ============================================================

CONTEXT_RECALL_KEYWORDS = {
    # Identification
    "H001": ["bigbear.ai", "holdings", "inc"],
    "H002": ["bbai", "ticker", "symbol", "nyse"],
    "H003": ["new york stock exchange", "nyse", "listed"],
    "H004": ["delaware", "incorporated", "state"],
    "H005": ["001-40031", "commission", "file"],
    
    # Shares
    "H006": ["436,551,228", "shares", "outstanding", "common stock"],
    "H007": ["0.0001", "par value"],
    "H008": ["11.50", "warrant", "exercise"],
    "H009": ["85-4164597", "employer", "i.r.s"],
    
    # Revenue
    "H010": ["33.1", "revenue", "million", "q3"],
    "H011": ["41.5", "revenue", "2024"],
    "H012": ["20%", "decrease", "decline", "revenue"],
    "H013": ["125", "140", "guidance", "outlook"],
    
    # Profitability
    "H014": ["22.4", "gross margin", "percent"],
    "H015": ["2.5", "net income", "million"],
    "H016": ["profit", "income", "2.5"],
    "H017": ["9.4", "ebitda", "adjusted"],
    
    # Balance Sheet
    "H018": ["456.6", "cash", "equivalents"],
    "H019": ["919", "total assets"],
    "H020": ["309", "liabilities"],
    "H021": ["610", "stockholders", "equity"],
    "H022": ["104", "debt"],
    
    # Business
    "H023": ["ask sage", "acquisition", "acquire"],
    "H024": ["25.3", "sg&a", "selling"],
    "H025": ["emerging growth", "company"],
}

# Expected agent and index for each test
EXPECTED_ROUTING = {
    # Hard tests - should use needle agent with hierarchical index
    "H001": {"agent": "needle", "index": "hierarchical"},
    "H002": {"agent": "needle", "index": "hierarchical"},
    "H003": {"agent": "needle", "index": "hierarchical"},
    "H004": {"agent": "needle", "index": "hierarchical"},
    "H005": {"agent": "needle", "index": "hierarchical"},
    "H006": {"agent": "needle", "index": "hierarchical"},
    "H007": {"agent": "needle", "index": "hierarchical"},
    "H008": {"agent": "needle", "index": "hierarchical"},
    "H009": {"agent": "needle", "index": "hierarchical"},
    "H010": {"agent": "needle", "index": "hierarchical"},
    "H011": {"agent": "needle", "index": "hierarchical"},
    "H012": {"agent": "needle", "index": "hierarchical"},
    "H013": {"agent": "needle", "index": "hierarchical"},
    "H014": {"agent": "needle", "index": "hierarchical"},
    "H015": {"agent": "needle", "index": "hierarchical"},
    "H016": {"agent": "needle", "index": "hierarchical"},
    "H017": {"agent": "needle", "index": "hierarchical"},
    "H018": {"agent": "needle", "index": "hierarchical"},
    "H019": {"agent": "needle", "index": "hierarchical"},
    "H020": {"agent": "needle", "index": "hierarchical"},
    "H021": {"agent": "needle", "index": "hierarchical"},
    "H022": {"agent": "needle", "index": "hierarchical"},
    "H023": {"agent": "needle", "index": "hierarchical"},
    "H024": {"agent": "needle", "index": "hierarchical"},
    "H025": {"agent": "needle", "index": "hierarchical"},
    
    # LLM Judge tests - should use summary agent with summary index
    "L001": {"agent": "summary", "index": "summary"},
    "L002": {"agent": "summary", "index": "summary"},
    "L003": {"agent": "summary", "index": "summary"},
    "L004": {"agent": "summary", "index": "summary"},
    "L005": {"agent": "summary", "index": "summary"},
    "L006": {"agent": "summary", "index": "summary"},
    "L007": {"agent": "summary", "index": "summary"},
    "L008": {"agent": "summary", "index": "summary"},
    "L009": {"agent": "summary", "index": "summary"},
    "L010": {"agent": "summary", "index": "summary"},
    "L011": {"agent": "summary", "index": "summary"},
    "L012": {"agent": "summary", "index": "summary"},
    "L013": {"agent": "summary", "index": "summary"},
    
    # Human grader tests
    "HG001": {"agent": "summary", "index": "summary"},
    "HG002": {"agent": "summary", "index": "summary"},
    "HG003": {"agent": "summary", "index": "summary"},
    "HG004": {"agent": "summary", "index": "summary"},
    "HG005": {"agent": "summary", "index": "summary"},
    "HG006": {"agent": "summary", "index": "summary"},
    "HG007": {"agent": "summary", "index": "summary"},
}


# ============================================================
# CONTEXT EVALUATOR
# ============================================================

class ContextEvaluator:
    """Evaluates context relevancy and recall."""
    
    def __init__(self):
        self.recall_keywords = CONTEXT_RECALL_KEYWORDS
        self.expected_routing = EXPECTED_ROUTING
    
    def evaluate_context_recall(self, test_id: str, contexts: List[str]) -> Dict:
        """
        Evaluate if the retrieved contexts contain the expected keywords.
        
        Context Recall = (# keywords found in contexts) / (# expected keywords)
        """
        keywords = self.recall_keywords.get(test_id, [])
        
        if not keywords:
            return {
                'recall_score': None,
                'keywords_expected': [],
                'keywords_found': [],
                'keywords_missing': [],
                'note': 'No keywords defined for this test'
            }
        
        if not contexts:
            return {
                'recall_score': 0.0,
                'keywords_expected': keywords,
                'keywords_found': [],
                'keywords_missing': keywords,
                'note': 'No contexts retrieved'
            }
        
        # Combine all contexts into one string for searching
        all_context = ' '.join(contexts).lower()
        
        found = []
        missing = []
        
        for kw in keywords:
            if kw.lower() in all_context:
                found.append(kw)
            else:
                missing.append(kw)
        
        recall_score = len(found) / len(keywords) if keywords else 0.0
        
        return {
            'recall_score': recall_score,
            'recall_pct': f"{recall_score * 100:.1f}%",
            'keywords_expected': keywords,
            'keywords_found': found,
            'keywords_missing': missing,
        }
    
    def evaluate_context_relevancy(self, test_id: str, actual_agent: str, actual_index: str = None) -> Dict:
        """
        Evaluate if the correct agent and index were used.
        
        Context Relevancy = Did the system route to the correct agent/index?
        """
        expected = self.expected_routing.get(test_id, {})
        expected_agent = expected.get('agent', 'unknown')
        expected_index = expected.get('index', 'unknown')
        
        agent_correct = actual_agent == expected_agent if actual_agent else False
        index_correct = actual_index == expected_index if actual_index else None
        
        return {
            'expected_agent': expected_agent,
            'actual_agent': actual_agent,
            'agent_correct': agent_correct,
            'expected_index': expected_index,
            'actual_index': actual_index,
            'index_correct': index_correct,
            'relevancy_score': 1.0 if agent_correct else 0.0,
        }


# ============================================================
# EVALUATION RESULT
# ============================================================

@dataclass
class EvaluationResult:
    test_id: str
    test_type: str
    question: str
    category: str
    agent: str
    answer: str
    score: float
    max_score: float
    passed: bool
    ground_truth: Any
    extracted_value: Any
    evaluation_details: Dict
    response_time: float
    # New fields for context evaluation
    context_recall: Dict = field(default_factory=dict)
    context_relevancy: Dict = field(default_factory=dict)


# ============================================================
# HARD TEST EVALUATOR
# ============================================================

class HardTestEvaluator:
    def __init__(self, ground_truth: Dict):
        self.ground_truth = ground_truth
        self.extractor = NumberExtractor()
    
    def evaluate(self, answer: str, test: Dict) -> Tuple[float, bool, Dict]:
        gt_key = test['ground_truth_key']
        gt_type = test['ground_truth_type']
        gt_value = self.ground_truth.get(gt_key)
        tolerance = test.get('tolerance', 0.05)
        
        details = {'ground_truth': gt_value, 'extracted': None, 'match_type': None}
        
        if gt_value is None:
            return 0.0, False, details
        
        answer_lower = answer.lower()
        
        # Text
        if gt_type == 'text':
            gt_lower = str(gt_value).lower().strip()
            details['answer_preview'] = answer_lower[:100]  # For debugging
            
            # Exact match
            if gt_lower in answer_lower:
                details['match_type'] = 'exact'
                return 5.0, True, details
            
            # For short strings (like ticker symbols), try word boundary match
            if len(gt_lower) <= 10:
                # Check with word boundaries (handles "BBAI" in "NYSE: BBAI")
                pattern = r'\b' + re.escape(gt_lower) + r'\b'
                if re.search(pattern, answer_lower):
                    details['match_type'] = 'exact'
                    return 5.0, True, details
                
                # Check without special chars (handles formatting variations)
                clean_gt = re.sub(r'[^a-z0-9]', '', gt_lower)
                clean_ans = re.sub(r'[^a-z0-9]', '', answer_lower)
                if clean_gt and clean_gt in clean_ans:
                    details['match_type'] = 'partial'
                    return 4.5, True, details
            
            # Multi-word matching
            words = gt_lower.replace('-', ' ').split()
            if len(words) > 1:
                matches = sum(1 for w in words if w in answer_lower)
                if matches >= len(words) * 0.6:
                    details['match_type'] = 'partial'
                    return 4.0, True, details
            
            # Longer string partial match
            if len(gt_lower) > 3:
                clean_gt = gt_lower.replace('-', '').replace(' ', '')
                clean_ans = answer_lower.replace('-', '').replace(' ', '')
                if clean_gt in clean_ans:
                    details['match_type'] = 'partial'
                    return 4.0, True, details
            
            return 0.0, False, details
        
        # Boolean
        if gt_type == 'boolean':
            true_ind = test.get('true_indicators', ['yes'])
            false_ind = test.get('false_indicators', ['no', 'not'])
            if gt_value:
                if any(i.lower() in answer_lower for i in true_ind):
                    return 5.0, True, details
            else:
                if any(i.lower() in answer_lower for i in false_ind):
                    return 5.0, True, details
            return 0.0, False, details
        
        # Numeric
        if gt_type in ['number', 'currency', 'percentage', 'decimal']:
            numbers = self.extractor.extract_all(answer)
            details['all_extracted'] = [n['value'] for n in numbers[:10]]
            check_values = [gt_value, abs(gt_value)] if gt_value < 0 else [gt_value]
            
            for num in numbers:
                for cv in check_values:
                    if cv == 0: continue
                    diff = abs(num['value'] - cv) / abs(cv)
                    if diff <= tolerance:
                        details['extracted'] = num['value']
                        details['difference'] = diff
                        details['match_type'] = 'exact_numeric'
                        return 5.0, True, details
                    elif diff <= tolerance * 2:
                        details['extracted'] = num['value']
                        details['difference'] = diff
                        details['match_type'] = 'close_numeric'
                        return 3.5, False, details
            return 0.0, False, details
        
        return 0.0, False, details


# ============================================================
# LLM JUDGE EVALUATOR
# ============================================================

class LLMJudgeEvaluator:
    def __init__(self, llm):
        self.llm = llm
    
    def evaluate(self, answer: str, test: Dict) -> Tuple[float, bool, Dict]:
        criteria = test.get('evaluation_criteria', [])
        min_score = test.get('min_score', 3)
        
        if not self.llm:
            return self._fallback(answer, test)
        
        criteria_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(criteria)])
        prompt = f"""Evaluate this answer about BigBear.ai's 10-Q Q3 2025.

QUESTION: {test['question']}

ANSWER:
{answer[:2000]}

CRITERIA:
{criteria_text}

KEY FACTS: Revenue $33.1M (-20%), Net income $2.5M, Cash $456.6M, Gross margin 22.4%, Adjusted EBITDA $(9.4)M, Acquiring Ask Sage.

Score 1-5. Respond ONLY with JSON: {{"score": <number>, "reasoning": "<text>"}}"""
        
        try:
            response = self.llm.invoke(prompt)
            text = response.content if hasattr(response, 'content') else str(response)
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                result = json.loads(match.group())
                score = float(result.get('score', 0))
                return score, score >= min_score, {'llm_score': score, 'reasoning': result.get('reasoning', '')}
        except Exception as e:
            return self._fallback(answer, test)
        
        return 2.0, False, {'error': 'eval failed'}
    
    def _fallback(self, answer: str, test: Dict) -> Tuple[float, bool, Dict]:
        answer_lower = answer.lower()
        terms = {'33.1': 1, 'revenue': 0.5, '2.5': 1, 'profit': 0.5, '456.6': 1, 'cash': 0.5,
                 '22.4': 0.5, '20%': 0.5, 'ask sage': 1, 'acquisition': 0.5, 'army': 0.5,
                 'government': 0.5, 'doge': 0.5, 'risk': 0.5}
        score = sum(v for t, v in terms.items() if t in answer_lower)
        score = min(5, max(1, score))
        return score, score >= test.get('min_score', 3), {'fallback': True}


# ============================================================
# HUMAN GRADER EVALUATOR
# ============================================================

class HumanGraderEvaluator:
    def prepare(self, answer: str, test: Dict) -> Dict:
        return {
            'test_id': test['id'], 'question': test['question'], 'category': test.get('category', ''),
            'answer': answer, 'grading_rubric': test.get('grading_rubric', ''),
            'aspects_to_evaluate': test.get('aspects_to_evaluate', []),
            'human_score': None, 'human_comments': None
        }


# ============================================================
# MAIN EVALUATOR
# ============================================================

class SECFilingEvaluator:
    def __init__(self, ground_truth: Dict = None, llm=None, verbose: bool = True):
        self.ground_truth = ground_truth or GROUND_TRUTH
        self.llm = llm
        self.verbose = verbose
        self.hard_eval = HardTestEvaluator(self.ground_truth)
        self.llm_eval = LLMJudgeEvaluator(llm)
        self.human_eval = HumanGraderEvaluator()
        self.context_eval = ContextEvaluator()  # NEW
        self.results = []
        self.human_queue = []
    
    def run_all_tests(self, system) -> Dict:
        print("\n" + "="*70)
        print("📊 SEC 10-Q EVALUATION - BigBear.ai (BBAI) Q3 2025")
        print("="*70)
        
        # Hard tests
        print(f"\n{'='*55}")
        print(f"📌 HARD TESTS ({len(HARD_TESTS)})")
        print(f"{'='*55}")
        hard_results = [self._run_test(system, t, 'hard') for t in HARD_TESTS]
        
        # LLM tests
        print(f"\n{'='*55}")
        print(f"🤖 LLM-AS-JUDGE TESTS ({len(LLM_JUDGE_TESTS)})")
        print(f"{'='*55}")
        llm_results = [self._run_test(system, t, 'llm_judge') for t in LLM_JUDGE_TESTS]
        
        # Human tests
        print(f"\n{'='*55}")
        print(f"👤 HUMAN GRADER TESTS ({len(HUMAN_GRADER_TESTS)})")
        print(f"{'='*55}")
        human_results = [self._run_test(system, t, 'human_grader') for t in HUMAN_GRADER_TESTS]
        
        summary = self._summary(hard_results, llm_results, human_results)
        self._save(summary)
        return summary
    
    def _run_test(self, system, test: Dict, test_type: str) -> EvaluationResult:
        q = test['question']
        if self.verbose:
            print(f"\n▶️  [{test['id']}] {q[:50]}...")
        
        start = time.time()
        try:
            answer, contexts, meta = system.route(q)
        except Exception as e:
            answer, contexts, meta = f"Error: {e}", [], None
        elapsed = time.time() - start
        
        # Answer evaluation
        if test_type == 'hard':
            score, passed, details = self.hard_eval.evaluate(answer, test)
        elif test_type == 'llm_judge':
            score, passed, details = self.llm_eval.evaluate(answer, test)
        else:
            details = self.human_eval.prepare(answer, test)
            self.human_queue.append(details)
            score, passed = 0.0, False
            details['pending'] = True
        
        # Context Recall evaluation
        context_recall = self.context_eval.evaluate_context_recall(
            test['id'], 
            contexts if contexts else []
        )
        
        # Context Relevancy evaluation
        actual_agent = meta.get('agent_used', test.get('agent', '')) if meta else test.get('agent', '')
        actual_index = meta.get('index_used', '') if meta else ''
        context_relevancy = self.context_eval.evaluate_context_relevancy(
            test['id'],
            actual_agent,
            actual_index
        )
        
        result = EvaluationResult(
            test_id=test['id'], test_type=test_type, question=q,
            category=test.get('category', ''), agent=test.get('agent', ''),
            answer=answer[:500], score=score, max_score=5.0, passed=passed,
            ground_truth=self.ground_truth.get(test.get('ground_truth_key')),
            extracted_value=details.get('extracted'),
            evaluation_details=details, response_time=elapsed,
            context_recall=context_recall,
            context_relevancy=context_relevancy
        )
        self.results.append(result)
        
        if self.verbose:
            s = "✅" if passed else "❌" if test_type != 'human_grader' else "👤"
            print(f"   {s} Score: {score:.1f}/5.0 | Time: {elapsed:.1f}s")
            
            # Show context recall for hard tests
            if test_type == 'hard':
                recall = context_recall.get('recall_score')
                if recall is not None:
                    recall_status = "✅" if recall >= 0.5 else "⚠️"
                    print(f"   {recall_status} Context Recall: {context_recall.get('recall_pct', 'N/A')} ({len(context_recall.get('keywords_found', []))}/{len(context_recall.get('keywords_expected', []))} keywords)")
                
                if not passed:
                    gt_type = test.get('ground_truth_type', '')
                    if gt_type == 'text':
                        ans_preview = answer[:150].replace('\n', ' ')
                        print(f"      GT: '{result.ground_truth}' | Answer: '{ans_preview}...'")
                    else:
                        print(f"      GT: {result.ground_truth} | Found: {details.get('all_extracted', [])[:3]}")
        
        return result
    
    def _summary(self, hard, llm, human) -> Dict:
        def stats(r):
            if not r: return {'total': 0, 'passed': 0, 'rate': 0, 'avg': 0}
            return {'total': len(r), 'passed': sum(1 for x in r if x.passed),
                    'rate': sum(1 for x in r if x.passed)/len(r), 'avg': sum(x.score for x in r)/len(r)}
        
        hs, ls = stats(hard), stats(llm)
        
        # Calculate context metrics
        def context_stats(results):
            recall_scores = []
            relevancy_scores = []
            for r in results:
                if r.context_recall and r.context_recall.get('recall_score') is not None:
                    recall_scores.append(r.context_recall['recall_score'])
                if r.context_relevancy and r.context_relevancy.get('relevancy_score') is not None:
                    relevancy_scores.append(r.context_relevancy['relevancy_score'])
            
            return {
                'avg_recall': sum(recall_scores) / len(recall_scores) if recall_scores else 0,
                'avg_relevancy': sum(relevancy_scores) / len(relevancy_scores) if relevancy_scores else 0,
                'recall_count': len(recall_scores),
                'relevancy_count': len(relevancy_scores),
            }
        
        hard_context = context_stats(hard)
        
        print(f"\n{'='*70}")
        print("📈 EVALUATION SUMMARY")
        print(f"{'='*70}")
        
        print(f"\n📌 HARD TESTS (Answer Correctness):")
        print(f"   Passed: {hs['passed']}/{hs['total']} ({hs['rate']*100:.0f}%) | Avg Score: {hs['avg']:.1f}/5")
        
        print(f"\n🔍 CONTEXT RECALL (Hard Tests):")
        print(f"   Average Recall: {hard_context['avg_recall']*100:.1f}%")
        print(f"   Tests with recall data: {hard_context['recall_count']}/{len(hard)}")
        
        print(f"\n🎯 CONTEXT RELEVANCY (Routing):")
        print(f"   Average Relevancy: {hard_context['avg_relevancy']*100:.1f}%")
        
        print(f"\n🤖 LLM-AS-JUDGE TESTS:")
        print(f"   Passed: {ls['passed']}/{ls['total']} ({ls['rate']*100:.0f}%) | Avg Score: {ls['avg']:.1f}/5")
        
        print(f"\n👤 HUMAN GRADER TESTS:")
        print(f"   Total: {len(human)} (pending human review)")
        
        auto = hard + llm
        if auto:
            overall_pass = sum(1 for x in auto if x.passed) / len(auto)
            overall_score = sum(x.score for x in auto) / len(auto)
            print(f"\n📊 OVERALL (Automated Tests):")
            print(f"   Pass Rate: {overall_pass*100:.0f}%")
            print(f"   Average Score: {overall_score:.1f}/5")
        
        return {
            'hard_tests': hs, 
            'llm_judge_tests': ls, 
            'human_grader_tests': {'total': len(human)},
            'context_recall': hard_context,
        }
    
    def _save(self, summary):
        with open("evaluation_results.json", "w") as f:
            json.dump({'time': datetime.now().isoformat(), 'company': 'BigBear.ai', 'filing': '10-Q Q3 2025',
                       'summary': summary, 'results': [asdict(r) for r in self.results],
                       'ground_truth': self.ground_truth}, f, indent=2, default=str)
        
        if self.human_queue:
            with open("human_grading_template.json", "w") as f:
                json.dump({'tests': self.human_queue}, f, indent=2)
            print(f"\n📝 Human grading: human_grading_template.json")
        print(f"💾 Results: evaluation_results.json")


def run_evaluation(system=None, verbose=True):
    if system is None:
        from core.system_builder import build_system
        system = build_system()
    try:
        from core.llm_provider import get_llm
        llm = get_llm()
    except:
        llm = None
    return SECFilingEvaluator(llm=llm, verbose=verbose).run_all_tests(system)


if __name__ == "__main__":
    run_evaluation()
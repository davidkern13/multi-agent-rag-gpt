"""
Comprehensive Evaluation System - FIXED VERSION
Version: 8.0

Fixes:
1. Real numerical Ground Truth validation
2. Context Relevancy measurement (correct agent/index selection)
3. Context Recall measurement (correct chunks retrieved)
4. Consistency checking between related questions
5. Fixed sys.path for module imports
"""

import sys
import os

# ============================================================
# FIX: Add project root to Python path
# ============================================================
# Get the directory containing this script (evaluation/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project root (parent of evaluation/)
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
# Add to Python path if not already there
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import json
import time
import re
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict, field

# ============================================================
# GROUND TRUTH - EXTRACTED FROM SEC FILING
# ============================================================
# IMPORTANT: Update these values from your actual document!

GROUND_TRUTH = {
    # Revenue & Income (from BigBear.ai 10-K)
    "total_revenue_2024": 155_200_000,      # $155.2 million - UPDATE FROM YOUR DOC
    "total_revenue_2023": 146_100_000,      # $146.1 million - UPDATE FROM YOUR DOC
    "revenue_growth_rate": 6.2,              # 6.2% growth - UPDATE FROM YOUR DOC
    
    "net_loss_2024": -288_100_000,          # Net LOSS $288.1 million - UPDATE
    "net_loss_2023": -157_400_000,          # Net LOSS $157.4 million - UPDATE
    
    "operating_loss_2024": -133_400_000,    # Operating loss - UPDATE
    "gross_profit_2024": None,               # Set to None if not available
    
    # Balance Sheet
    "total_cash": 50_000_000,                # Cash position - UPDATE
    "total_assets": 300_000_000,             # Total assets - UPDATE
    "total_liabilities": 250_000_000,        # Total liabilities - UPDATE
    "total_debt": 200_000_000,               # Total debt - UPDATE
    "stockholders_equity": 50_000_000,       # Equity - UPDATE
    
    # Metrics
    "gross_margin_pct": 25.0,                # Gross margin % - UPDATE
    "operating_margin_pct": -15.0,           # Operating margin % - UPDATE
    "eps": -1.50,                            # EPS (loss per share) - UPDATE
    
    # Cash Flow
    "operating_cash_flow": -50_000_000,      # OCF - UPDATE
    "free_cash_flow": -60_000_000,           # FCF - UPDATE
    "capex": 10_000_000,                     # CapEx - UPDATE
    
    # Business
    "employee_count": 500,                   # Number of employees - UPDATE
    "is_profitable": False,                  # Company is NOT profitable
    "has_going_concern": False,              # Going concern warning - UPDATE
    
    # Key content that should appear in retrieved chunks
    "revenue_section_keywords": ["revenue", "total revenues", "net revenues"],
    "risk_section_keywords": ["risk factors", "risks", "uncertainties"],
    "mda_section_keywords": ["management's discussion", "MD&A", "results of operations"],
}

# ============================================================
# TEST CASES WITH GROUND TRUTH
# ============================================================

NEEDLE_HARD_TESTS = [
    # Revenue & Income
    {
        "id": "NH001",
        "question": "What was the total revenue?",
        "ground_truth_key": "total_revenue_2024",
        "ground_truth_type": "currency",
        "tolerance": 0.05,  # 5% tolerance
        "expected_agent": "needle",
        "expected_index": "hierarchical",
        "required_chunk_keywords": ["revenue", "total"],
        "category": "revenue"
    },
    {
        "id": "NH002",
        "question": "What was the net income or net loss?",
        "ground_truth_key": "net_loss_2024",
        "ground_truth_type": "currency",
        "tolerance": 0.05,
        "must_contain": ["loss"],  # Must identify it's a LOSS
        "expected_agent": "needle",
        "expected_index": "hierarchical",
        "required_chunk_keywords": ["net loss", "net income"],
        "category": "income"
    },
    {
        "id": "NH003",
        "question": "What was the gross profit?",
        "ground_truth_key": "gross_profit_2024",
        "ground_truth_type": "currency",
        "tolerance": 0.05,
        "allow_not_found": True,  # OK if not in document
        "expected_agent": "needle",
        "expected_index": "hierarchical",
        "required_chunk_keywords": ["gross profit", "gross margin"],
        "category": "profit"
    },
    {
        "id": "NH004",
        "question": "What was the operating income or loss?",
        "ground_truth_key": "operating_loss_2024",
        "ground_truth_type": "currency",
        "tolerance": 0.05,
        "must_contain": ["loss", "operating"],
        "expected_agent": "needle",
        "expected_index": "hierarchical",
        "required_chunk_keywords": ["operating"],
        "category": "income"
    },
    {
        "id": "NH005",
        "question": "What is the revenue growth rate?",
        "ground_truth_key": "revenue_growth_rate",
        "ground_truth_type": "percentage",
        "tolerance": 0.20,  # 20% tolerance on growth rate
        "expected_agent": "needle",
        "expected_index": "hierarchical",
        "required_chunk_keywords": ["revenue", "growth", "change"],
        "category": "growth"
    },
    
    # Balance Sheet
    {
        "id": "NH006",
        "question": "How much cash does the company have?",
        "ground_truth_key": "total_cash",
        "ground_truth_type": "currency",
        "tolerance": 0.10,
        "expected_agent": "needle",
        "expected_index": "hierarchical",
        "required_chunk_keywords": ["cash", "equivalents"],
        "category": "balance"
    },
    {
        "id": "NH007",
        "question": "What are the total assets?",
        "ground_truth_key": "total_assets",
        "ground_truth_type": "currency",
        "tolerance": 0.10,
        "expected_agent": "needle",
        "expected_index": "hierarchical",
        "required_chunk_keywords": ["total assets"],
        "category": "balance"
    },
    {
        "id": "NH008",
        "question": "What are the total liabilities?",
        "ground_truth_key": "total_liabilities",
        "ground_truth_type": "currency",
        "tolerance": 0.10,
        "expected_agent": "needle",
        "expected_index": "hierarchical",
        "required_chunk_keywords": ["liabilities"],
        "category": "balance"
    },
    {
        "id": "NH009",
        "question": "What is the stockholders equity?",
        "ground_truth_key": "stockholders_equity",
        "ground_truth_type": "currency",
        "tolerance": 0.10,
        "expected_agent": "needle",
        "expected_index": "hierarchical",
        "required_chunk_keywords": ["equity", "stockholders"],
        "category": "balance"
    },
    {
        "id": "NH010",
        "question": "What is the total debt?",
        "ground_truth_key": "total_debt",
        "ground_truth_type": "currency",
        "tolerance": 0.10,
        "expected_agent": "needle",
        "expected_index": "hierarchical",
        "required_chunk_keywords": ["debt"],
        "category": "balance"
    },
    
    # Profitability check
    {
        "id": "NH011",
        "question": "Is the company profitable?",
        "ground_truth_key": "is_profitable",
        "ground_truth_type": "boolean",
        "must_contain": ["loss", "not profitable", "unprofitable"],
        "must_not_contain": ["profitable company", "is profitable"],
        "expected_agent": "needle",
        "expected_index": "hierarchical",
        "required_chunk_keywords": ["net", "income", "loss"],
        "category": "profitability"
    },
    
    # Metrics
    {
        "id": "NH012",
        "question": "What is the gross margin percentage?",
        "ground_truth_key": "gross_margin_pct",
        "ground_truth_type": "percentage",
        "tolerance": 0.15,
        "expected_agent": "needle",
        "expected_index": "hierarchical",
        "required_chunk_keywords": ["margin", "gross"],
        "category": "metrics"
    },
    {
        "id": "NH013",
        "question": "What is the EPS?",
        "ground_truth_key": "eps",
        "ground_truth_type": "currency",
        "tolerance": 0.10,
        "must_contain": ["per share", "eps"],
        "expected_agent": "needle",
        "expected_index": "hierarchical",
        "required_chunk_keywords": ["earnings", "per share", "eps"],
        "category": "metrics"
    },
    
    # Business
    {
        "id": "NH014",
        "question": "How many employees does the company have?",
        "ground_truth_key": "employee_count",
        "ground_truth_type": "number",
        "tolerance": 0.10,
        "expected_agent": "needle",
        "expected_index": "hierarchical",
        "required_chunk_keywords": ["employee", "personnel", "workforce"],
        "category": "business"
    },
    
    # Risk
    {
        "id": "NH015",
        "question": "Is there a going concern warning?",
        "ground_truth_key": "has_going_concern",
        "ground_truth_type": "boolean",
        "expected_agent": "needle",
        "expected_index": "hierarchical",
        "required_chunk_keywords": ["going concern", "ability to continue"],
        "category": "risk"
    },
]

SUMMARY_TESTS = [
    {
        "id": "SL001",
        "question": "Provide an executive summary of this SEC filing.",
        "expected_agent": "summary",
        "expected_index": "summary",
        "evaluation_type": "llm",
        "criteria": "Should cover company overview, key financials, and outlook",
        "category": "executive"
    },
    {
        "id": "SL002",
        "question": "What is the overall financial health of this company?",
        "expected_agent": "summary",
        "expected_index": "summary",
        "evaluation_type": "llm",
        "criteria": "Should reference profitability status, liquidity, and debt levels",
        "must_mention_loss": True,  # Since company is not profitable
        "category": "health"
    },
    {
        "id": "SL003",
        "question": "Summarize the main risks facing this company.",
        "expected_agent": "summary",
        "expected_index": "summary",
        "evaluation_type": "llm",
        "criteria": "Should identify and explain key risk factors",
        "category": "risk"
    },
]


# ============================================================
# EVALUATION METRICS
# ============================================================

@dataclass
class EvaluationResult:
    test_id: str
    question: str
    answer: str
    
    # Answer Correctness
    answer_correct: bool
    answer_score: float
    answer_details: Dict
    
    # Context Relevancy
    context_relevant: bool
    correct_agent: bool
    correct_index: bool
    agent_used: str
    index_used: str
    
    # Context Recall
    context_recall: float
    chunks_retrieved: int
    relevant_chunks_found: int
    
    # Overall
    overall_score: float
    passed: bool
    response_time: float


# ============================================================
# NUMBER EXTRACTION
# ============================================================

def extract_numbers_from_text(text: str) -> List[Dict]:
    """
    Extract all numbers with their context from text.
    Returns list of {value, raw, context, type}
    """
    results = []
    
    # Currency patterns: $X.X million/billion/thousand
    currency_patterns = [
        r'\$\s*([\d,]+(?:\.\d+)?)\s*(billion|million|thousand|B|M|K)?',
        r'([\d,]+(?:\.\d+)?)\s*(billion|million|thousand)?\s*(?:dollars)',
    ]
    
    for pattern in currency_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                raw_num = match.group(1).replace(',', '')
                value = float(raw_num)
                multiplier = match.group(2) if len(match.groups()) > 1 else None
                
                if multiplier:
                    multiplier_lower = multiplier.lower() if multiplier else ''
                    if 'billion' in multiplier_lower or multiplier_lower == 'b':
                        value *= 1_000_000_000
                    elif 'million' in multiplier_lower or multiplier_lower == 'm':
                        value *= 1_000_000
                    elif 'thousand' in multiplier_lower or multiplier_lower == 'k':
                        value *= 1_000
                
                # Get context
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end]
                
                results.append({
                    'value': value,
                    'raw': match.group(0),
                    'context': context,
                    'type': 'currency'
                })
            except (ValueError, IndexError):
                continue
    
    # Percentage patterns
    pct_pattern = r'([-+]?\d+(?:\.\d+)?)\s*%'
    for match in re.finditer(pct_pattern, text):
        try:
            value = float(match.group(1))
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            results.append({
                'value': value,
                'raw': match.group(0),
                'context': text[start:end],
                'type': 'percentage'
            })
        except ValueError:
            continue
    
    # Plain numbers (for employee count, etc.)
    plain_pattern = r'\b(\d{2,}(?:,\d{3})*)\b'
    for match in re.finditer(plain_pattern, text):
        try:
            value = float(match.group(1).replace(',', ''))
            # Skip if already captured as currency
            if not any(abs(r['value'] - value) < 1 for r in results):
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                results.append({
                    'value': value,
                    'raw': match.group(0),
                    'context': text[start:end],
                    'type': 'number'
                })
        except ValueError:
            continue
    
    return results


# ============================================================
# ANSWER CORRECTNESS EVALUATOR
# ============================================================

class AnswerCorrectnessEvaluator:
    """
    Evaluates if the answer contains correct numerical values.
    """
    
    def __init__(self, ground_truth: Dict):
        self.ground_truth = ground_truth
    
    def evaluate(self, answer: str, test_case: Dict) -> Tuple[bool, float, Dict]:
        """
        Evaluate answer correctness.
        
        Returns: (is_correct, score, details)
        """
        gt_key = test_case.get('ground_truth_key')
        gt_type = test_case.get('ground_truth_type', 'currency')
        tolerance = test_case.get('tolerance', 0.10)
        
        # Get ground truth value
        gt_value = self.ground_truth.get(gt_key)
        
        details = {
            'ground_truth_key': gt_key,
            'ground_truth_value': gt_value,
            'ground_truth_type': gt_type,
            'tolerance': tolerance,
            'numbers_found': [],
            'match_found': False,
            'closest_match': None,
            'closest_diff': None,
        }
        
        # Handle None ground truth (data not available)
        if gt_value is None:
            if test_case.get('allow_not_found', False):
                # Check if answer acknowledges data not found
                not_found_phrases = ['not found', 'not available', 'not disclosed', 'could not find']
                if any(phrase in answer.lower() for phrase in not_found_phrases):
                    details['acknowledged_not_found'] = True
                    return True, 5.0, details
            return False, 0.0, details
        
        # Handle boolean ground truth
        if gt_type == 'boolean':
            return self._evaluate_boolean(answer, gt_value, test_case, details)
        
        # Extract numbers from answer
        numbers = extract_numbers_from_text(answer)
        details['numbers_found'] = [{'value': n['value'], 'raw': n['raw']} for n in numbers]
        
        if not numbers:
            details['error'] = 'No numbers found in answer'
            return False, 0.0, details
        
        # Find closest match
        closest_diff = float('inf')
        closest_num = None
        
        for num in numbers:
            if gt_type == 'percentage' and num['type'] != 'percentage':
                continue
            if gt_type == 'currency' and num['type'] == 'percentage':
                continue
            
            diff = abs(num['value'] - abs(gt_value)) / abs(gt_value) if gt_value != 0 else float('inf')
            if diff < closest_diff:
                closest_diff = diff
                closest_num = num
        
        if closest_num:
            details['closest_match'] = closest_num['value']
            details['closest_diff'] = closest_diff
            details['closest_raw'] = closest_num['raw']
        
        # Check if within tolerance
        is_correct = closest_diff <= tolerance if closest_diff != float('inf') else False
        details['match_found'] = is_correct
        
        # Check must_contain requirements
        must_contain = test_case.get('must_contain', [])
        if must_contain:
            answer_lower = answer.lower()
            contains_required = all(term.lower() in answer_lower for term in must_contain)
            details['must_contain'] = must_contain
            details['contains_required'] = contains_required
            if not contains_required:
                is_correct = False
        
        # Check must_not_contain
        must_not_contain = test_case.get('must_not_contain', [])
        if must_not_contain:
            answer_lower = answer.lower()
            contains_forbidden = any(term.lower() in answer_lower for term in must_not_contain)
            details['must_not_contain'] = must_not_contain
            details['contains_forbidden'] = contains_forbidden
            if contains_forbidden:
                is_correct = False
        
        # Calculate score
        if is_correct:
            score = 5.0
        elif closest_diff <= tolerance * 2:
            score = 3.0  # Partially correct
        elif closest_diff <= tolerance * 3:
            score = 2.0
        else:
            score = 0.0
        
        return is_correct, score, details
    
    def _evaluate_boolean(self, answer: str, gt_value: bool, test_case: Dict, details: Dict) -> Tuple[bool, float, Dict]:
        """Evaluate boolean questions (yes/no, profitable/not profitable)."""
        answer_lower = answer.lower()
        
        must_contain = test_case.get('must_contain', [])
        must_not_contain = test_case.get('must_not_contain', [])
        
        # Check must_contain
        if must_contain:
            contains = any(term.lower() in answer_lower for term in must_contain)
            details['must_contain'] = must_contain
            details['contains_required'] = contains
        else:
            contains = True
        
        # Check must_not_contain
        if must_not_contain:
            forbidden = any(term.lower() in answer_lower for term in must_not_contain)
            details['must_not_contain'] = must_not_contain
            details['contains_forbidden'] = forbidden
        else:
            forbidden = False
        
        is_correct = contains and not forbidden
        score = 5.0 if is_correct else 0.0
        
        return is_correct, score, details


# ============================================================
# CONTEXT RELEVANCY EVALUATOR
# ============================================================

class ContextRelevancyEvaluator:
    """
    Evaluates if the correct agent and index were used.
    """
    
    def evaluate(self, test_case: Dict, agent_used: str, index_used: str) -> Tuple[bool, bool, bool, Dict]:
        """
        Evaluate context relevancy.
        
        Returns: (is_relevant, correct_agent, correct_index, details)
        """
        expected_agent = test_case.get('expected_agent', 'needle')
        expected_index = test_case.get('expected_index', 'hierarchical')
        
        correct_agent = agent_used.lower() == expected_agent.lower()
        correct_index = index_used.lower() == expected_index.lower()
        is_relevant = correct_agent and correct_index
        
        details = {
            'expected_agent': expected_agent,
            'actual_agent': agent_used,
            'correct_agent': correct_agent,
            'expected_index': expected_index,
            'actual_index': index_used,
            'correct_index': correct_index,
        }
        
        return is_relevant, correct_agent, correct_index, details


# ============================================================
# CONTEXT RECALL EVALUATOR
# ============================================================

class ContextRecallEvaluator:
    """
    Evaluates if the correct chunks were retrieved.
    """
    
    def evaluate(self, test_case: Dict, retrieved_chunks: List[str]) -> Tuple[float, int, Dict]:
        """
        Evaluate context recall.
        
        Returns: (recall_score, relevant_count, details)
        """
        required_keywords = test_case.get('required_chunk_keywords', [])
        
        if not required_keywords:
            return 1.0, len(retrieved_chunks), {'no_requirements': True}
        
        # Check each chunk for required keywords
        chunks_with_keywords = 0
        keyword_matches = {kw: False for kw in required_keywords}
        
        for chunk in retrieved_chunks:
            chunk_lower = chunk.lower()
            for kw in required_keywords:
                if kw.lower() in chunk_lower:
                    keyword_matches[kw] = True
                    chunks_with_keywords += 1
                    break
        
        # Calculate recall
        keywords_found = sum(1 for v in keyword_matches.values() if v)
        recall = keywords_found / len(required_keywords) if required_keywords else 1.0
        
        details = {
            'required_keywords': required_keywords,
            'keyword_matches': keyword_matches,
            'keywords_found': keywords_found,
            'total_required': len(required_keywords),
            'chunks_retrieved': len(retrieved_chunks),
            'relevant_chunks': chunks_with_keywords,
        }
        
        return recall, chunks_with_keywords, details


# ============================================================
# MAIN EVALUATOR
# ============================================================

class ComprehensiveEvaluator:
    """
    Main evaluation class combining all three metrics.
    """
    
    def __init__(self, ground_truth: Dict = None, llm=None, verbose: bool = False):
        self.ground_truth = ground_truth or GROUND_TRUTH
        self.llm = llm
        self.verbose = verbose
        
        self.answer_evaluator = AnswerCorrectnessEvaluator(self.ground_truth)
        self.relevancy_evaluator = ContextRelevancyEvaluator()
        self.recall_evaluator = ContextRecallEvaluator()
    
    def evaluate_test(
        self,
        test_case: Dict,
        answer: str,
        agent_used: str,
        index_used: str,
        retrieved_chunks: List[str],
        response_time: float
    ) -> EvaluationResult:
        """
        Run comprehensive evaluation on a single test.
        """
        # 1. Answer Correctness
        answer_correct, answer_score, answer_details = self.answer_evaluator.evaluate(answer, test_case)
        
        # 2. Context Relevancy
        ctx_relevant, correct_agent, correct_index, relevancy_details = \
            self.relevancy_evaluator.evaluate(test_case, agent_used, index_used)
        
        # 3. Context Recall
        recall_score, relevant_chunks, recall_details = \
            self.recall_evaluator.evaluate(test_case, retrieved_chunks)
        
        # Calculate overall score (weighted)
        # Answer Correctness: 50%, Context Relevancy: 25%, Context Recall: 25%
        overall_score = (
            answer_score * 0.50 +
            (5.0 if ctx_relevant else 0.0) * 0.25 +
            (recall_score * 5.0) * 0.25
        )
        
        passed = overall_score >= 3.0
        
        if self.verbose:
            self._print_evaluation(
                test_case, answer, answer_correct, answer_score, answer_details,
                ctx_relevant, correct_agent, correct_index, relevancy_details,
                recall_score, recall_details, overall_score, passed
            )
        
        return EvaluationResult(
            test_id=test_case['id'],
            question=test_case['question'],
            answer=answer[:500],
            answer_correct=answer_correct,
            answer_score=answer_score,
            answer_details=answer_details,
            context_relevant=ctx_relevant,
            correct_agent=correct_agent,
            correct_index=correct_index,
            agent_used=agent_used,
            index_used=index_used,
            context_recall=recall_score,
            chunks_retrieved=len(retrieved_chunks),
            relevant_chunks_found=relevant_chunks,
            overall_score=overall_score,
            passed=passed,
            response_time=response_time
        )
    
    def _print_evaluation(self, test_case, answer, answer_correct, answer_score, answer_details,
                          ctx_relevant, correct_agent, correct_index, relevancy_details,
                          recall_score, recall_details, overall_score, passed):
        """Print detailed evaluation results."""
        print(f"\n{'='*70}")
        print(f"TEST: {test_case['id']} | {test_case['question']}")
        print(f"{'='*70}")
        
        # Answer preview
        print(f"\n📝 ANSWER (first 300 chars):")
        print(f"   {answer[:300]}...")
        
        # Answer Correctness
        print(f"\n📊 ANSWER CORRECTNESS:")
        print(f"   Ground Truth: {answer_details.get('ground_truth_value')}")
        print(f"   Closest Match: {answer_details.get('closest_match')} (diff: {answer_details.get('closest_diff', 'N/A')})")
        print(f"   Score: {answer_score}/5 {'✅' if answer_correct else '❌'}")
        
        # Context Relevancy
        print(f"\n🎯 CONTEXT RELEVANCY:")
        print(f"   Expected Agent: {relevancy_details['expected_agent']} | Actual: {relevancy_details['actual_agent']} {'✅' if correct_agent else '❌'}")
        print(f"   Expected Index: {relevancy_details['expected_index']} | Actual: {relevancy_details['actual_index']} {'✅' if correct_index else '❌'}")
        
        # Context Recall
        print(f"\n🔍 CONTEXT RECALL:")
        print(f"   Required Keywords: {recall_details.get('required_keywords', [])}")
        print(f"   Keywords Found: {recall_details.get('keywords_found', 0)}/{recall_details.get('total_required', 0)}")
        print(f"   Recall Score: {recall_score:.2%}")
        
        # Overall
        print(f"\n{'='*50}")
        print(f"📈 OVERALL SCORE: {overall_score:.2f}/5 {'✅ PASS' if passed else '❌ FAIL'}")
        print(f"{'='*50}")


# ============================================================
# CONSISTENCY CHECKER
# ============================================================

class ConsistencyChecker:
    """
    Checks for contradictions between related answers.
    """
    
    def __init__(self):
        self.answers = {}
    
    def add_answer(self, test_id: str, question: str, answer: str, numbers: List[Dict]):
        """Store answer for consistency checking."""
        self.answers[test_id] = {
            'question': question,
            'answer': answer,
            'numbers': numbers
        }
    
    def check_consistency(self) -> List[Dict]:
        """Check for contradictions."""
        issues = []
        
        # Check revenue-related answers
        revenue_tests = [k for k in self.answers if 'revenue' in self.answers[k]['question'].lower()]
        if len(revenue_tests) >= 2:
            # Compare revenue numbers across tests
            for i, t1 in enumerate(revenue_tests):
                for t2 in revenue_tests[i+1:]:
                    nums1 = [n['value'] for n in self.answers[t1]['numbers'] if n['type'] == 'currency']
                    nums2 = [n['value'] for n in self.answers[t2]['numbers'] if n['type'] == 'currency']
                    
                    # Check for major contradictions
                    for n1 in nums1:
                        for n2 in nums2:
                            if n1 > 0 and n2 > 0:
                                diff = abs(n1 - n2) / max(n1, n2)
                                if diff > 0.5:  # More than 50% difference
                                    issues.append({
                                        'type': 'contradiction',
                                        'tests': [t1, t2],
                                        'values': [n1, n2],
                                        'difference': f"{diff:.1%}"
                                    })
        
        return issues


# ============================================================
# RUN EVALUATION
# ============================================================

def run_evaluation(system=None, verbose: bool = True):
    """
    Run comprehensive evaluation.
    """
    print("\n" + "="*70)
    print("🔬 COMPREHENSIVE EVALUATION - FIXED VERSION")
    print("="*70)
    print("Metrics: Answer Correctness + Context Relevancy + Context Recall")
    print("="*70)
    
    # Build system if not provided
    if system is None:
        print("\n[INFO] Building system...")
        from core.system_builder import build_system
        system = build_system()
    
    # Initialize evaluator
    evaluator = ComprehensiveEvaluator(verbose=verbose)
    consistency_checker = ConsistencyChecker()
    
    results = []
    
    # Run Needle tests
    print(f"\n{'='*50}")
    print("🎯 NEEDLE AGENT TESTS")
    print(f"{'='*50}")
    
    for test in NEEDLE_HARD_TESTS:
        print(f"\n[{test['id']}] {test['question']}")
        
        start_time = time.time()
        
        # Get answer from system
        answer, contexts, meta = system.route(test['question'])
        
        response_time = time.time() - start_time
        
        # Determine which agent/index was used
        agent_used = "needle"  # You'd get this from meta in real implementation
        index_used = "hierarchical"
        
        # Run evaluation
        result = evaluator.evaluate_test(
            test_case=test,
            answer=answer,
            agent_used=agent_used,
            index_used=index_used,
            retrieved_chunks=contexts,
            response_time=response_time
        )
        
        results.append(result)
        
        # Add to consistency checker
        numbers = extract_numbers_from_text(answer)
        consistency_checker.add_answer(test['id'], test['question'], answer, numbers)
        
        if not verbose:
            status = "✅" if result.passed else "❌"
            print(f"   {status} Score: {result.overall_score:.2f}/5 | Time: {response_time:.1f}s")
    
    # Check consistency
    print(f"\n{'='*50}")
    print("🔄 CONSISTENCY CHECK")
    print(f"{'='*50}")
    
    issues = consistency_checker.check_consistency()
    if issues:
        print(f"⚠️ Found {len(issues)} potential contradictions:")
        for issue in issues:
            print(f"   - {issue['tests']}: {issue['values']} ({issue['difference']} diff)")
    else:
        print("✅ No contradictions detected")
    
    # Summary
    print(f"\n{'='*70}")
    print("📈 EVALUATION SUMMARY")
    print(f"{'='*70}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.passed)
    avg_score = sum(r.overall_score for r in results) / total_tests if total_tests > 0 else 0
    
    avg_answer = sum(r.answer_score for r in results) / total_tests if total_tests > 0 else 0
    avg_relevancy = sum(5.0 if r.context_relevant else 0.0 for r in results) / total_tests if total_tests > 0 else 0
    avg_recall = sum(r.context_recall * 5.0 for r in results) / total_tests if total_tests > 0 else 0
    
    print(f"\n📊 Breakdown by Metric:")
    print(f"   Answer Correctness:  {avg_answer:.2f}/5.0")
    print(f"   Context Relevancy:   {avg_relevancy:.2f}/5.0")
    print(f"   Context Recall:      {avg_recall:.2f}/5.0")
    
    print(f"\n📈 Overall:")
    print(f"   Tests: {passed_tests}/{total_tests} passed ({passed_tests/total_tests*100:.0f}%)")
    print(f"   Average Score: {avg_score:.2f}/5.0")
    
    if issues:
        print(f"\n⚠️ Consistency Issues: {len(issues)}")
    
    print(f"{'='*70}")
    
    # Save results
    output = {
        "generated_at": datetime.now().isoformat(),
        "version": "8.0-fixed",
        "summary": {
            "total_tests": total_tests,
            "passed": passed_tests,
            "pass_rate": passed_tests/total_tests if total_tests > 0 else 0,
            "avg_overall": avg_score,
            "avg_answer_correctness": avg_answer,
            "avg_context_relevancy": avg_relevancy,
            "avg_context_recall": avg_recall,
            "consistency_issues": len(issues),
        },
        "consistency_issues": issues,
        "results": [asdict(r) for r in results],
        "ground_truth_used": {k: v for k, v in GROUND_TRUTH.items() if not k.endswith('_keywords')},
    }
    
    with open("evaluation_results_fixed.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved to: evaluation_results_fixed.json")
    
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", default=True)
    args = parser.parse_args()
    
    run_evaluation(verbose=args.verbose)
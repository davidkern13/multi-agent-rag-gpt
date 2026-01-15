"""
Comprehensive Evaluation System
Version: 7.0
- Verbose mode to see answers
- Manual override option
- Better validation
"""

import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import re
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict

from core.system_builder import build_system
from core.llm_provider import get_llm


# ============================================================
# TEST CASES
# ============================================================

NEEDLE_HARD_TESTS = [
    # Revenue & Income (5)
    {"id": "NH001", "question": "What was the total revenue?", "ground_truth_keywords": ["revenue", "$"], "expected_pattern": r"\$[\d,]+", "expected_answer": "~$114.4 million", "category": "revenue"},
    {"id": "NH002", "question": "What was the net income or net loss?", "ground_truth_keywords": ["net", "loss"], "expected_pattern": r"loss", "expected_answer": "Net LOSS (not profitable)", "category": "income"},
    {"id": "NH003", "question": "What was the gross profit?", "ground_truth_keywords": ["gross", "profit"], "expected_pattern": r"gross", "expected_answer": "Gross profit amount", "category": "profit"},
    {"id": "NH004", "question": "What was the operating income or loss?", "ground_truth_keywords": ["operating"], "expected_pattern": r"operating", "expected_answer": "Operating loss", "category": "income"},
    {"id": "NH005", "question": "What is the revenue growth rate?", "ground_truth_keywords": ["%"], "expected_pattern": r"[\d.]+\s*%", "expected_answer": "~14% growth", "category": "growth"},
    
    # Balance Sheet (5)
    {"id": "NH006", "question": "How much cash does the company have?", "ground_truth_keywords": ["cash", "$"], "expected_pattern": r"cash", "expected_answer": "Cash amount", "category": "balance"},
    {"id": "NH007", "question": "What are the total assets?", "ground_truth_keywords": ["assets", "$"], "expected_pattern": r"assets", "expected_answer": "Total assets", "category": "balance"},
    {"id": "NH008", "question": "What are the total liabilities?", "ground_truth_keywords": ["liabilities"], "expected_pattern": r"liabilities", "expected_answer": "Total liabilities", "category": "balance"},
    {"id": "NH009", "question": "What is the stockholders equity?", "ground_truth_keywords": ["equity"], "expected_pattern": r"equity", "expected_answer": "Equity amount", "category": "balance"},
    {"id": "NH010", "question": "What is the total debt?", "ground_truth_keywords": ["debt"], "expected_pattern": r"debt", "expected_answer": "Debt amount", "category": "balance"},
    
    # Metrics (5)
    {"id": "NH011", "question": "What is the gross margin percentage?", "ground_truth_keywords": ["margin", "%"], "expected_pattern": r"[\d.]+\s*%", "expected_answer": "Gross margin %", "category": "metrics"},
    {"id": "NH012", "question": "What is the operating margin?", "ground_truth_keywords": ["margin"], "expected_pattern": r"margin", "expected_answer": "Operating margin", "category": "metrics"},
    {"id": "NH013", "question": "What is the EPS?", "ground_truth_keywords": ["share"], "expected_pattern": r"(?:eps|per\s+share|\$)", "expected_answer": "EPS or loss per share", "category": "metrics"},
    {"id": "NH014", "question": "What is the current ratio?", "ground_truth_keywords": ["current"], "expected_pattern": r"(?:ratio|current)", "expected_answer": "Current ratio", "category": "metrics"},
    {"id": "NH015", "question": "What is the debt to equity ratio?", "ground_truth_keywords": ["debt", "equity"], "expected_pattern": r"(?:ratio|debt)", "expected_answer": "D/E ratio", "category": "metrics"},
    
    # Cash Flow (3)
    {"id": "NH016", "question": "What is the operating cash flow?", "ground_truth_keywords": ["cash", "flow"], "expected_pattern": r"cash", "expected_answer": "Operating cash flow", "category": "cashflow"},
    {"id": "NH017", "question": "What is the free cash flow?", "ground_truth_keywords": ["cash"], "expected_pattern": r"cash", "expected_answer": "Free cash flow", "category": "cashflow"},
    {"id": "NH018", "question": "What were the capital expenditures?", "ground_truth_keywords": ["capital"], "expected_pattern": r"(?:capex|capital|expenditure)", "expected_answer": "CapEx amount", "category": "cashflow"},
    
    # Business (4)
    {"id": "NH019", "question": "Who are the major customers?", "ground_truth_keywords": ["customer"], "expected_pattern": r"(?:customer|government|federal)", "expected_answer": "Major customers (US Government)", "category": "business"},
    {"id": "NH020", "question": "What is the backlog value?", "ground_truth_keywords": ["backlog"], "expected_pattern": r"backlog", "expected_answer": "Backlog amount", "category": "business"},
    {"id": "NH021", "question": "How many employees does the company have?", "ground_truth_keywords": ["employee"], "expected_pattern": r"(?:employee|staff|worker|personnel|\d{2,})", "expected_answer": "Number of employees", "category": "business"},
    {"id": "NH022", "question": "What segments does the company operate in?", "ground_truth_keywords": ["segment"], "expected_pattern": r"segment", "expected_answer": "Business segments", "category": "business"},
    
    # Risk (3)
    {"id": "NH023", "question": "What are the main risk factors?", "ground_truth_keywords": ["risk"], "expected_pattern": r"risk", "expected_answer": "Key risk factors", "category": "risk"},
    {"id": "NH024", "question": "Is there a going concern warning?", "ground_truth_keywords": ["concern"], "expected_pattern": r"(?:going\s+concern|no|not|warning)", "expected_answer": "Going concern status", "category": "risk"},
    {"id": "NH025", "question": "What legal proceedings are mentioned?", "ground_truth_keywords": ["legal"], "expected_pattern": r"(?:legal|litigation|lawsuit|proceeding|no)", "expected_answer": "Legal proceedings", "category": "risk"},
]

NEEDLE_LLM_TESTS = [
    {"id": "NL001", "question": "What was the total revenue and how did it change from last year?", "evaluation_criteria": "Answer should include revenue amount and YoY change", "category": "comparison"},
    {"id": "NL002", "question": "Is the company profitable? Explain with numbers.", "evaluation_criteria": "Answer should clearly state profit/loss with figures", "category": "profitability"},
    {"id": "NL003", "question": "What is the company's liquidity position?", "evaluation_criteria": "Answer should discuss cash and working capital", "category": "liquidity"},
    {"id": "NL004", "question": "What are the key risk factors and their potential impact?", "evaluation_criteria": "Answer should list specific risks with impact", "category": "risk"},
    {"id": "NL005", "question": "How did operating expenses change and why?", "evaluation_criteria": "Answer should show expense changes with drivers", "category": "expenses"},
    {"id": "NL006", "question": "What is the gross margin trend?", "evaluation_criteria": "Answer should show margin changes", "category": "trends"},
    {"id": "NL007", "question": "What major contracts or customers are mentioned?", "evaluation_criteria": "Answer should identify customers or contracts", "category": "business"},
    {"id": "NL008", "question": "What is the company's debt situation?", "evaluation_criteria": "Answer should cover debt amounts and terms", "category": "debt"},
    {"id": "NL009", "question": "What are the company's main revenue streams?", "evaluation_criteria": "Answer should break down revenue sources", "category": "revenue"},
    {"id": "NL010", "question": "What capital investments is the company making?", "evaluation_criteria": "Answer should cover CapEx and investments", "category": "investments"},
    {"id": "NL011", "question": "How does customer concentration affect the business?", "evaluation_criteria": "Answer should identify concentration risks", "category": "risk"},
    {"id": "NL012", "question": "What is the effective tax rate?", "evaluation_criteria": "Answer should explain tax rate", "category": "tax"},
    {"id": "NL013", "question": "What stock-based compensation was recorded?", "evaluation_criteria": "Answer should include SBC amount", "category": "compensation"},
    {"id": "NL014", "question": "What acquisitions or divestitures are discussed?", "evaluation_criteria": "Answer should identify M&A or state none", "category": "ma"},
    {"id": "NL015", "question": "What is the company's competitive position?", "evaluation_criteria": "Answer should discuss competitive landscape", "category": "competition"},
]

NEEDLE_HUMAN_TESTS = [
    {"id": "NHG001", "question": "What are the three most critical financial metrics investors should focus on?", "rubric": "5=3 relevant metrics with values; 3=metrics but weak reasoning; 1=fails", "category": "analysis"},
    {"id": "NHG002", "question": "What can we infer about the company's future from this filing?", "rubric": "5=thoughtful inference; 3=basic inference; 1=speculation", "category": "inference"},
    {"id": "NHG003", "question": "What are the biggest financial concerns evident from this filing?", "rubric": "5=valid concerns with data; 3=concerns but limited evidence; 1=fails", "category": "risk"},
    {"id": "NHG004", "question": "How has the company's financial position changed over the reporting period?", "rubric": "5=comprehensive comparison; 3=basic comparison; 1=none", "category": "trends"},
    {"id": "NHG005", "question": "What strategic implications can we draw from the financial data?", "rubric": "5=insightful analysis; 3=basic observations; 1=no insight", "category": "strategy"},
    {"id": "NHG006", "question": "What key assumptions is management making about the future?", "rubric": "5=specific assumptions; 3=some assumptions; 1=fails", "category": "assumptions"},
    {"id": "NHG007", "question": "How would you rate the overall quality of this company's financial disclosures?", "rubric": "5=thoughtful assessment; 3=basic assessment; 1=none", "category": "quality"},
]

SUMMARY_LLM_TESTS = [
    {"id": "SL001", "question": "Provide an executive summary of this SEC filing.", "evaluation_criteria": "Summary should cover company, period, key financials, outlook", "category": "executive"},
    {"id": "SL002", "question": "What is the overall financial health of this company?", "evaluation_criteria": "Should reference profitability, liquidity, debt", "category": "health"},
    {"id": "SL003", "question": "Summarize the company's business model.", "evaluation_criteria": "Should explain what company does and how it makes money", "category": "business"},
    {"id": "SL004", "question": "What is management's outlook for the company?", "evaluation_criteria": "Should capture forward-looking statements", "category": "outlook"},
    {"id": "SL005", "question": "Summarize the main risks facing this company.", "evaluation_criteria": "Should provide overview of key risks", "category": "risk"},
    {"id": "SL006", "question": "Describe this company in two sentences for an investor.", "evaluation_criteria": "Concise capture of business and financials", "category": "pitch"},
    {"id": "SL007", "question": "What are the key takeaways from this filing?", "evaluation_criteria": "Should identify 3-5 important points", "category": "takeaways"},
    {"id": "SL008", "question": "Summarize the company's growth strategy.", "evaluation_criteria": "Should capture strategic initiatives", "category": "strategy"},
    {"id": "SL009", "question": "What is the company's market position?", "evaluation_criteria": "Should describe competitive position", "category": "market"},
    {"id": "SL010", "question": "How sustainable is the company's business?", "evaluation_criteria": "Should assess sustainability", "category": "sustainability"},
    {"id": "SL011", "question": "What are the company's main revenue drivers?", "evaluation_criteria": "Should identify key revenue sources", "category": "revenue"},
    {"id": "SL012", "question": "What story does this filing tell about the company?", "evaluation_criteria": "Should provide narrative interpretation", "category": "narrative"},
    {"id": "SL013", "question": "What notable changes occurred from the previous period?", "evaluation_criteria": "Should highlight significant changes", "category": "changes"},
    {"id": "SL014", "question": "What should investors pay attention to in this filing?", "evaluation_criteria": "Should identify investor-relevant highlights", "category": "investor"},
    {"id": "SL015", "question": "Is this company in a strong or weak position? Why?", "evaluation_criteria": "Should provide balanced assessment", "category": "assessment"},
]

SUMMARY_HUMAN_TESTS = [
    {"id": "SHG001", "question": "Provide an executive summary suitable for a board presentation.", "rubric": "5=professional, comprehensive; 3=adequate; 1=unprofessional", "category": "executive"},
    {"id": "SHG002", "question": "Explain this filing to someone with no financial background.", "rubric": "5=clear, jargon-free; 3=understandable; 1=too technical", "category": "accessibility"},
    {"id": "SHG003", "question": "What is your assessment of this company's future prospects?", "rubric": "5=balanced with evidence; 3=reasonable; 1=biased", "category": "outlook"},
    {"id": "SHG004", "question": "What are the key strengths and weaknesses evident in this filing?", "rubric": "5=balanced identification; 3=some; 1=fails", "category": "swot"},
    {"id": "SHG005", "question": "How does this company compare to what you'd expect from a healthy company?", "rubric": "5=insightful comparison; 3=basic; 1=none", "category": "benchmark"},
    {"id": "SHG006", "question": "Write a one-paragraph summary suitable for financial news.", "rubric": "5=professional, newsworthy; 3=adequate; 1=not suitable", "category": "news"},
    {"id": "SHG007", "question": "What three follow-up questions would you ask management?", "rubric": "5=insightful questions; 3=reasonable; 1=basic", "category": "critical"},
]


# ============================================================
# EVALUATORS
# ============================================================

@dataclass
class TestResult:
    test_id: str
    test_type: str
    agent: str
    question: str
    answer: str
    score: float
    max_score: float
    passed: bool
    details: Dict
    response_time: float
    manual_override: bool = False


class HardTestEvaluator:
    def __init__(self, verbose=False):
        self.verbose = verbose
    
    def evaluate(self, answer: str, test_case: Dict, allow_override: bool = False) -> Tuple[float, bool, Dict]:
        answer_lower = answer.lower()
        
        # Check keywords
        keywords = test_case.get("ground_truth_keywords", [])
        found = [kw for kw in keywords if kw.lower() in answer_lower]
        keyword_score = len(found) / len(keywords) if keywords else 0
        
        # Check pattern
        pattern = test_case.get("expected_pattern", "")
        pattern_match = bool(re.search(pattern, answer, re.IGNORECASE)) if pattern else True
        
        # Calculate score
        score = (keyword_score * 0.6 + (1.0 if pattern_match else 0.0) * 0.4) * 5.0
        passed = score >= 3.0
        
        details = {
            "keywords_expected": keywords,
            "keywords_found": found,
            "pattern": pattern,
            "pattern_matched": pattern_match,
        }
        
        # Verbose mode - show answer and ask for override
        if self.verbose:
            print(f"\n  {'─' * 60}")
            print(f"  📝 ANSWER (first 500 chars):")
            print(f"  {answer[:500]}{'...' if len(answer) > 500 else ''}")
            print(f"  {'─' * 60}")
            print(f"  🎯 Expected: {test_case.get('expected_answer', 'N/A')}")
            print(f"  🔍 Keywords expected: {keywords}")
            print(f"  ✓  Keywords found: {found}")
            print(f"  📋 Pattern: {pattern}")
            print(f"  {'✓' if pattern_match else '✗'}  Pattern matched: {pattern_match}")
            print(f"  📊 Auto Score: {score:.1f}/5 → {'PASS' if passed else 'FAIL'}")
            
            if allow_override:
                override = input(f"  \n  >>> Override? [y=pass/n=fail/Enter=keep]: ").strip().lower()
                if override == 'y':
                    print("  ✅ Manual override: PASS")
                    return 5.0, True, {**details, "manual_override": True}
                elif override == 'n':
                    print("  ❌ Manual override: FAIL")
                    return 0.0, False, {**details, "manual_override": True}
        
        return score, passed, details


class LLMTestEvaluator:
    def __init__(self, llm, verbose=False):
        self.llm = llm
        self.verbose = verbose
    
    def evaluate(self, question: str, answer: str, criteria: str, allow_override: bool = False) -> Tuple[float, bool, Dict]:
        
        if self.verbose:
            print(f"\n  {'─' * 60}")
            print(f"  📝 ANSWER (first 500 chars):")
            print(f"  {answer[:500]}{'...' if len(answer) > 500 else ''}")
            print(f"  {'─' * 60}")
            print(f"  📋 Criteria: {criteria}")
        
        prompt = f"""Evaluate this financial analysis answer.

QUESTION: {question}
ANSWER: {answer[:1500]}
CRITERIA: {criteria}

Score 0-5:
5=Excellent (meets criteria with specific data)
4=Good (mostly meets criteria)
3=Adequate (partially meets)
2=Poor (significant gaps)
1=Very Poor
0=Fail

JSON only: {{"score": <0-5>, "reasoning": "<brief explanation>"}}"""

        try:
            response = self.llm.invoke(prompt)
            text = response.content.strip()
            if "```" in text:
                text = text.split("```")[1] if "```json" in text else text.replace("```", "")
            text = text.replace("```json", "").replace("```", "").strip()
            result = json.loads(text)
            score = float(result.get("score", 0))
            reasoning = result.get("reasoning", "")
            
            if self.verbose:
                print(f"  🤖 LLM Score: {score:.1f}/5")
                print(f"  💬 Reasoning: {reasoning}")
                
                if allow_override:
                    override = input(f"  \n  >>> Override score? [0-5/Enter=keep]: ").strip()
                    if override and override.replace('.','').isdigit():
                        new_score = float(override)
                        if 0 <= new_score <= 5:
                            print(f"  ✅ Manual override: {new_score}/5")
                            return new_score, new_score >= 3.0, {"reasoning": reasoning, "manual_override": True}
            
            return score, score >= 3.0, {"reasoning": reasoning}
        except Exception as e:
            if self.verbose:
                print(f"  ❌ Error: {e}")
            return 2.5, False, {"error": str(e)}


class HumanGraderInterface:
    def __init__(self, output_file: str = "human_grading_tasks.json"):
        self.output_file = output_file
        self.tasks = []
    
    def add_task(self, test_id: str, question: str, answer: str, rubric: str, agent: str):
        self.tasks.append({
            "test_id": test_id, "agent": agent, "question": question,
            "answer": answer, "rubric": rubric, "human_score": None,
        })
    
    def save_tasks(self):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump({"tasks": self.tasks, "count": len(self.tasks)}, f, indent=2, ensure_ascii=False)
        print(f"\n📝 Saved {len(self.tasks)} tasks for human grading: {self.output_file}")


# ============================================================
# MAIN RUNNER
# ============================================================

def run_evaluation(verbose: bool = False, interactive: bool = False):
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE EVALUATION SYSTEM")
    print("=" * 70)
    print(f"Mode: {'VERBOSE + INTERACTIVE' if verbose and interactive else 'VERBOSE' if verbose else 'STANDARD'}")
    print(f"Needle Agent: 25 hard + 15 LLM + 7 human = 47 tests")
    print(f"Summary Agent: 15 LLM + 7 human = 22 tests")
    print(f"Total: 69 tests")
    print("=" * 70)
    
    print("\n🔧 Building system...")
    manager = build_system()
    
    print("🔧 Initializing LLM evaluator...")
    llm = get_llm()
    
    hard_eval = HardTestEvaluator(verbose=verbose)
    llm_eval = LLMTestEvaluator(llm, verbose=verbose)
    human_grader = HumanGraderInterface()
    
    results = []
    
    # ==================== NEEDLE HARD TESTS ====================
    print("\n" + "=" * 50)
    print("🎯 NEEDLE AGENT - HARD TESTS (25)")
    print("=" * 50)
    
    for i, test in enumerate(NEEDLE_HARD_TESTS, 1):
        print(f"\n[{i}/25] {test['id']}: {test['question']}")
        start = time.time()
        answer, _, _ = manager.route(test["question"])
        elapsed = time.time() - start
        
        score, passed, details = hard_eval.evaluate(answer, test, allow_override=interactive)
        manual = details.get("manual_override", False)
        
        results.append(TestResult(
            test["id"], "hard", "needle", test["question"], 
            answer[:500], score, 5.0, passed, details, elapsed, manual
        ))
        
        status = "✅ PASS" if passed else "❌ FAIL"
        override_mark = " (manual)" if manual else ""
        print(f"  {status} | Score: {score:.1f}/5{override_mark} | Time: {elapsed:.1f}s")
    
    # ==================== NEEDLE LLM TESTS ====================
    print("\n" + "=" * 50)
    print("🤖 NEEDLE AGENT - LLM TESTS (15)")
    print("=" * 50)
    
    for i, test in enumerate(NEEDLE_LLM_TESTS, 1):
        print(f"\n[{i}/15] {test['id']}: {test['question']}")
        start = time.time()
        answer, _, _ = manager.route(test["question"])
        elapsed = time.time() - start
        
        score, passed, details = llm_eval.evaluate(
            test["question"], answer, test["evaluation_criteria"], 
            allow_override=interactive
        )
        manual = details.get("manual_override", False)
        
        results.append(TestResult(
            test["id"], "llm", "needle", test["question"],
            answer[:500], score, 5.0, passed, details, elapsed, manual
        ))
        
        status = "✅ PASS" if passed else "❌ FAIL"
        override_mark = " (manual)" if manual else ""
        print(f"  {status} | Score: {score:.1f}/5{override_mark} | Time: {elapsed:.1f}s")
    
    # ==================== NEEDLE HUMAN TESTS ====================
    print("\n" + "=" * 50)
    print("👤 NEEDLE AGENT - HUMAN TESTS (7)")
    print("=" * 50)
    
    for i, test in enumerate(NEEDLE_HUMAN_TESTS, 1):
        print(f"\n[{i}/7] {test['id']}: {test['question']}")
        start = time.time()
        answer, _, _ = manager.route(test["question"])
        elapsed = time.time() - start
        
        # Always show answer for human tests (need to grade them)
        print(f"\n  {'─' * 60}")
        print(f"  📝 ANSWER:")
        print(f"  {answer[:800]}{'...' if len(answer) > 800 else ''}")
        print(f"  {'─' * 60}")
        print(f"  📋 Rubric: {test['rubric']}")
        
        # Allow immediate grading in interactive mode
        score = 0
        graded = False
        if interactive:
            grade_input = input(f"  \n  >>> Grade now (0-5) or Enter to skip: ").strip()
            if grade_input and grade_input.replace('.','').isdigit():
                score = float(grade_input)
                if 0 <= score <= 5:
                    graded = True
                    print(f"  ✅ Graded: {score}/5")
        
        human_grader.add_task(test["id"], test["question"], answer, test["rubric"], "needle")
        if graded:
            human_grader.tasks[-1]["human_score"] = score
        
        results.append(TestResult(
            test["id"], "human", "needle", test["question"],
            answer[:500], score, 5.0, graded, {"status": "graded" if graded else "pending"}, elapsed
        ))
        
        if graded:
            print(f"  ✅ GRADED: {score}/5 | Time: {elapsed:.1f}s")
        else:
            print(f"  ⏳ PENDING HUMAN REVIEW | Time: {elapsed:.1f}s")
    
    # ==================== SUMMARY LLM TESTS ====================
    print("\n" + "=" * 50)
    print("🤖 SUMMARY AGENT - LLM TESTS (15)")
    print("=" * 50)
    
    for i, test in enumerate(SUMMARY_LLM_TESTS, 1):
        print(f"\n[{i}/15] {test['id']}: {test['question']}")
        start = time.time()
        answer, _, _ = manager.route(test["question"])
        elapsed = time.time() - start
        
        score, passed, details = llm_eval.evaluate(
            test["question"], answer, test["evaluation_criteria"],
            allow_override=interactive
        )
        manual = details.get("manual_override", False)
        
        results.append(TestResult(
            test["id"], "llm", "summary", test["question"],
            answer[:500], score, 5.0, passed, details, elapsed, manual
        ))
        
        status = "✅ PASS" if passed else "❌ FAIL"
        override_mark = " (manual)" if manual else ""
        print(f"  {status} | Score: {score:.1f}/5{override_mark} | Time: {elapsed:.1f}s")
    
    # ==================== SUMMARY HUMAN TESTS ====================
    print("\n" + "=" * 50)
    print("👤 SUMMARY AGENT - HUMAN TESTS (7)")
    print("=" * 50)
    
    for i, test in enumerate(SUMMARY_HUMAN_TESTS, 1):
        print(f"\n[{i}/7] {test['id']}: {test['question']}")
        start = time.time()
        answer, _, _ = manager.route(test["question"])
        elapsed = time.time() - start
        
        # Always show answer for human tests (need to grade them)
        print(f"\n  {'─' * 60}")
        print(f"  📝 ANSWER:")
        print(f"  {answer[:800]}{'...' if len(answer) > 800 else ''}")
        print(f"  {'─' * 60}")
        print(f"  📋 Rubric: {test['rubric']}")
        
        # Allow immediate grading in interactive mode
        score = 0
        graded = False
        if interactive:
            grade_input = input(f"  \n  >>> Grade now (0-5) or Enter to skip: ").strip()
            if grade_input and grade_input.replace('.','').isdigit():
                score = float(grade_input)
                if 0 <= score <= 5:
                    graded = True
                    print(f"  ✅ Graded: {score}/5")
        
        human_grader.add_task(test["id"], test["question"], answer, test["rubric"], "summary")
        if graded:
            human_grader.tasks[-1]["human_score"] = score
        
        results.append(TestResult(
            test["id"], "human", "summary", test["question"],
            answer[:500], score, 5.0, graded, {"status": "graded" if graded else "pending"}, elapsed
        ))
        
        if graded:
            print(f"  ✅ GRADED: {score}/5 | Time: {elapsed:.1f}s")
        else:
            print(f"  ⏳ PENDING HUMAN REVIEW | Time: {elapsed:.1f}s")
    
    # Save human grading tasks
    human_grader.save_tasks()
    
    # ==================== RESULTS SUMMARY ====================
    needle_hard = [r for r in results if r.agent == "needle" and r.test_type == "hard"]
    needle_llm = [r for r in results if r.agent == "needle" and r.test_type == "llm"]
    summary_llm = [r for r in results if r.agent == "summary" and r.test_type == "llm"]
    
    print("\n" + "=" * 70)
    print("📈 FINAL RESULTS SUMMARY")
    print("=" * 70)
    
    print(f"\n🎯 NEEDLE AGENT:")
    nh_avg = sum(r.score for r in needle_hard) / len(needle_hard) if needle_hard else 0
    nh_pass = sum(1 for r in needle_hard if r.passed)
    nh_manual = sum(1 for r in needle_hard if r.manual_override)
    print(f"  Hard Tests (25):  {nh_avg:.2f}/5.0 | Passed: {nh_pass}/25 ({nh_pass/25*100:.0f}%)" + (f" | {nh_manual} manual" if nh_manual else ""))
    
    nl_avg = sum(r.score for r in needle_llm) / len(needle_llm) if needle_llm else 0
    nl_pass = sum(1 for r in needle_llm if r.passed)
    nl_manual = sum(1 for r in needle_llm if r.manual_override)
    print(f"  LLM Tests (15):   {nl_avg:.2f}/5.0 | Passed: {nl_pass}/15 ({nl_pass/15*100:.0f}%)" + (f" | {nl_manual} manual" if nl_manual else ""))
    
    needle_human = [r for r in results if r.agent == "needle" and r.test_type == "human"]
    nh_graded = [r for r in needle_human if r.details.get("status") == "graded"]
    if nh_graded:
        nhh_avg = sum(r.score for r in nh_graded) / len(nh_graded)
        nhh_pass = sum(1 for r in nh_graded if r.score >= 3)
        print(f"  Human Tests (7):  {nhh_avg:.2f}/5.0 | Graded: {len(nh_graded)}/7 | Passed: {nhh_pass}/{len(nh_graded)}")
    else:
        print(f"  Human Tests (7):  ⏳ Pending - run 'python human_grader.py'")
    
    print(f"\n📋 SUMMARY AGENT:")
    sl_avg = sum(r.score for r in summary_llm) / len(summary_llm) if summary_llm else 0
    sl_pass = sum(1 for r in summary_llm if r.passed)
    sl_manual = sum(1 for r in summary_llm if r.manual_override)
    print(f"  LLM Tests (15):   {sl_avg:.2f}/5.0 | Passed: {sl_pass}/15 ({sl_pass/15*100:.0f}%)" + (f" | {sl_manual} manual" if sl_manual else ""))
    
    summary_human = [r for r in results if r.agent == "summary" and r.test_type == "human"]
    sh_graded = [r for r in summary_human if r.details.get("status") == "graded"]
    if sh_graded:
        shh_avg = sum(r.score for r in sh_graded) / len(sh_graded)
        shh_pass = sum(1 for r in sh_graded if r.score >= 3)
        print(f"  Human Tests (7):  {shh_avg:.2f}/5.0 | Graded: {len(sh_graded)}/7 | Passed: {shh_pass}/{len(sh_graded)}")
    else:
        print(f"  Human Tests (7):  ⏳ Pending - run 'python human_grader.py'")
    
    # Overall - include graded human tests
    all_auto = needle_hard + needle_llm + summary_llm
    all_graded_human = [r for r in results if r.test_type == "human" and r.details.get("status") == "graded"]
    all_tests = all_auto + all_graded_human
    
    overall_avg = sum(r.score for r in all_tests) / len(all_tests) if all_tests else 0
    overall_pass = sum(1 for r in all_tests if r.passed or (r.test_type == "human" and r.score >= 3))
    
    print(f"\n{'=' * 50}")
    print(f"📊 OVERALL:")
    print(f"  Tests Evaluated: {len(all_tests)} ({len(all_auto)} auto + {len(all_graded_human)} human)")
    print(f"  Average Score: {overall_avg:.2f}/5.0")
    print(f"  Pass Rate: {overall_pass}/{len(all_tests)} ({overall_pass/len(all_tests)*100:.0f}%)" if all_tests else "  No tests completed")
    print("=" * 70)
    
    # Save results
    output = {
        "generated_at": datetime.now().isoformat(),
        "mode": "verbose+interactive" if verbose and interactive else "verbose" if verbose else "standard",
        "summary": {
            "needle_hard": {"avg": nh_avg, "passed": nh_pass, "total": 25, "manual_overrides": nh_manual},
            "needle_llm": {"avg": nl_avg, "passed": nl_pass, "total": 15, "manual_overrides": nl_manual},
            "needle_human": {"total": 7, "graded": len(nh_graded), "avg": sum(r.score for r in nh_graded) / len(nh_graded) if nh_graded else 0},
            "summary_llm": {"avg": sl_avg, "passed": sl_pass, "total": 15, "manual_overrides": sl_manual},
            "summary_human": {"total": 7, "graded": len(sh_graded), "avg": sum(r.score for r in sh_graded) / len(sh_graded) if sh_graded else 0},
            "overall": {"avg": overall_avg, "passed": overall_pass, "total": len(all_tests)},
        },
        "results": [asdict(r) for r in results],
    }
    
    with open("evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Results saved to: evaluation_results.json")
    print(f"📝 Human tasks saved to: human_grading_tasks.json")
    print(f"\nNext: Run 'python human_grader.py' to complete human evaluation")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run evaluation")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show answers for each test")
    parser.add_argument("-i", "--interactive", action="store_true", help="Allow manual score overrides")
    args = parser.parse_args()
    
    run_evaluation(verbose=args.verbose, interactive=args.interactive)
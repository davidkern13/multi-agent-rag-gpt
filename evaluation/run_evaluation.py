"""
Complete Evaluation System - Matches Assignment Requirements Exactly

Evaluates on 3 metrics:
A. Answer Correctness - Does answer match ground truth?
B. Context Relevancy - Did agent use correct index and relevant segments?
C. Context Recall - Did system retrieve the correct chunks?
"""

from core.system_builder import build_system
from core.llm_provider import get_llm
from typing import List, Dict
from dataclasses import dataclass
import json
import time


# Test cases
TEST_CASES = [
    {
        "question": "What was the highest daily percentage increase?",
        "ground_truth": "The highest daily percentage increase was +5.05% on November 10, 2025",
        "expected_chunks": ["November 10", "5.05%", "percentage"],
        "category": "needle",
    },
    {
        "question": "What happened on November 5?",
        "ground_truth": "On November 5, 2025: Open $184.20, Close $186.50, Volume 45.2M",
        "expected_chunks": ["November 5", "184.20", "186.50"],
        "category": "needle",
    },
    # {
    #     "question": "What was the average closing price?",
    #     "ground_truth": "The average closing price was approximately $188.50",
    #     "expected_chunks": ["closing", "average", "price"],
    #     "category": "statistical",
    # },
    # {
    #     "question": "Compare first week vs last week",
    #     "ground_truth": "First week: avg $185, Last week: avg $192, Increase: +3.8%",
    #     "expected_chunks": ["first week", "last week", "comparison"],
    #     "category": "comparison",
    # },
    # {
    #     "question": "How many UP days were there?",
    #     "ground_truth": "There were 16 UP days in November 2025",
    #     "expected_chunks": ["UP", "positive", "days"],
    #     "category": "statistical",
    # },
    # {
    #     "question": "Give me an overview of November trading",
    #     "ground_truth": "November showed bullish trend, volatility 2.1%, overall gain 4.5%",
    #     "expected_chunks": ["overview", "November", "trend"],
    #     "category": "summary",
    # },
    # {
    #     "question": "What was the price range on November 15?",
    #     "ground_truth": "November 15: Low $186.30, High $191.20, Range $4.90",
    #     "expected_chunks": ["November 15", "range", "high", "low"],
    #     "category": "needle",
    # },
    # {
    #     "question": "What's the moving average trend?",
    #     "ground_truth": "5-day MA trending upward from $185 to $190",
    #     "expected_chunks": ["moving average", "trend", "upward"],
    #     "category": "statistical",
    # },
]


@dataclass
class MetricScore:
    metric: str
    score: float
    reasoning: str
    details: Dict

    def to_dict(self):
        return {
            "metric": self.metric,
            "score": self.score,
            "reasoning": self.reasoning,
            "details": self.details,
        }


class LLMJudge:
    """LLM-as-a-judge evaluator - implements exactly the 3 metrics from assignment"""

    def __init__(self, llm, debug=False):
        self.llm = llm
        self.debug = debug

    def evaluate_answer_correctness(
        self, query: str, answer: str, ground_truth: str
    ) -> MetricScore:
        """
        Metric A: Answer Correctness
        Does answer match ground truth?
        """
        prompt = f"""Evaluate if the ANSWER matches the GROUND TRUTH.

QUERY: {query}
ANSWER: {answer}
GROUND TRUTH: {ground_truth}

SCORING (0-5):
5 - Perfect match, all facts correct
4 - Minor details missing but main facts correct
3 - Main facts present, some inaccuracies
2 - Partially correct
1 - Mostly incorrect
0 - Completely wrong

Respond ONLY in JSON:
{{
    "score": <0-5>,
    "reasoning": "<why this score>",
    "matched_facts": ["<fact1>", "<fact2>"],
    "missed_facts": ["<missing fact>"]
}}"""

        response = self.llm.complete(prompt).text.strip()
        result = self._parse_json(response)

        return MetricScore(
            metric="answer_correctness",
            score=result.get("score", 0),
            reasoning=result.get("reasoning", ""),
            details={
                "matched_facts": result.get("matched_facts", []),
                "missed_facts": result.get("missed_facts", []),
            },
        )

    def evaluate_context_relevancy(
        self, query: str, contexts: List[str]
    ) -> MetricScore:
        """
        Metric B: Context Relevancy
        Did agent use the correct index and relevant segments?
        """
        contexts_text = "\n\n".join(
            [f"[{i+1}] {ctx[:200]}..." for i, ctx in enumerate(contexts[:5])]
        )

        prompt = f"""Evaluate if the CONTEXTS are relevant to the QUERY.

QUERY: {query}
RETRIEVED CONTEXTS:
{contexts_text}

SCORING (0-5):
5 - All contexts highly relevant
4 - Most contexts relevant (80%+)
3 - Some relevant contexts (60-80%)
2 - Few relevant contexts (40-60%)
1 - Barely relevant (<40%)
0 - No relevant contexts

Respond ONLY in JSON:
{{
    "score": <0-5>,
    "reasoning": "<why this score>",
    "relevant_contexts": [<indices of relevant contexts>],
    "irrelevant_contexts": [<indices of irrelevant>]
}}"""

        response = self.llm.complete(prompt).text.strip()
        result = self._parse_json(response)

        return MetricScore(
            metric="context_relevancy",
            score=result.get("score", 0),
            reasoning=result.get("reasoning", ""),
            details={
                "relevant_contexts": result.get("relevant_contexts", []),
                "irrelevant_contexts": result.get("irrelevant_contexts", []),
                "total_contexts": len(contexts),
            },
        )

    def evaluate_context_recall(
        self, ground_truth: str, contexts: List[str], expected_chunks: List[str]
    ) -> MetricScore:
        """
        Metric C: Context Recall
        Did the system retrieve the correct chunk(s)?
        """
        contexts_text = "\n\n".join(
            [f"[{i+1}] {ctx[:200]}..." for i, ctx in enumerate(contexts[:5])]
        )

        prompt = f"""Evaluate if the CONTEXTS contain the facts from GROUND TRUTH.

GROUND TRUTH: {ground_truth}
EXPECTED KEYWORDS: {', '.join(expected_chunks)}
RETRIEVED CONTEXTS:
{contexts_text}

SCORING (0-5):
5 - All ground truth facts present in contexts
4 - 80%+ facts present
3 - 60-80% facts present
2 - 40-60% facts present
1 - <40% facts present
0 - No facts present

Respond ONLY in JSON:
{{
    "score": <0-5>,
    "reasoning": "<why this score>",
    "found_facts": ["<fact1 from truth found in contexts>"],
    "missing_facts": ["<fact from truth NOT in contexts>"],
    "found_keywords": [<which expected keywords were found>]
}}"""

        response = self.llm.complete(prompt).text.strip()
        result = self._parse_json(response)

        return MetricScore(
            metric="context_recall",
            score=result.get("score", 0),
            reasoning=result.get("reasoning", ""),
            details={
                "found_facts": result.get("found_facts", []),
                "missing_facts": result.get("missing_facts", []),
                "found_keywords": result.get("found_keywords", []),
                "expected_keywords": expected_chunks,
            },
        )

    def evaluate(
        self,
        query: str,
        answer: str,
        contexts: List[str],
        ground_truth: str,
        expected_chunks: List[str],
    ) -> Dict:
        """Run all 3 evaluations"""

        print(f"\n[EVAL] {query}")

        correctness = self.evaluate_answer_correctness(query, answer, ground_truth)
        print(f"  A. Answer Correctness: {correctness.score}/5")

        relevancy = self.evaluate_context_relevancy(query, contexts)
        print(f"  B. Context Relevancy:  {relevancy.score}/5")

        recall = self.evaluate_context_recall(ground_truth, contexts, expected_chunks)
        print(f"  C. Context Recall:     {recall.score}/5")

        overall = correctness.score + relevancy.score + recall.score
        print(f"  → Overall: {overall}/15\n")

        return {
            "query": query,
            "answer_correctness": correctness.to_dict(),
            "context_relevancy": relevancy.to_dict(),
            "context_recall": recall.to_dict(),
            "overall_score": overall,
        }

    def _parse_json(self, response: str) -> Dict:
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        try:
            return json.loads(response)
        except:
            return {
                "score": 0,
                "reasoning": "Parse error",
                "matched_facts": [],
                "missed_facts": [],
            }


def run_evaluation():
    """Run complete evaluation matching assignment requirements"""

    print("\n" + "=" * 80)
    print("🚀 INSURANCE CLAIM TIMELINE EVALUATION")
    print("=" * 80)
    print(f"Test cases: {len(TEST_CASES)}")
    print("Metrics: A. Answer Correctness, B. Context Relevancy, C. Context Recall")
    print("=" * 80 + "\n")

    print("🔧 Building system...")
    start = time.time()
    manager = build_system("data/data.pdf")
    print(f"✅ System ready ({time.time()-start:.1f}s)\n")

    print("🔧 Initializing LLM Judge...")
    llm = get_llm()
    judge = LLMJudge(llm)
    print("✅ Judge ready!\n")

    results = []
    query_times = []

    print("🔍 Running test queries...\n")

    for i, case in enumerate(TEST_CASES, 1):
        q = case["question"]
        gt = case["ground_truth"]
        expected = case["expected_chunks"]
        cat = case.get("category", "general")

        print(f"[{i}/{len(TEST_CASES)}] {cat.upper()}: {q}")

        start = time.time()
        answer, ctx, _ = manager.route(q)
        elapsed = time.time() - start

        print(f"  Time: {elapsed:.1f}s, Contexts: {len(ctx)}")
        print(f"  Answer: {answer[:60]}...\n")

        query_times.append(elapsed)

        result = judge.evaluate(q, answer, ctx, gt, expected)
        results.append(result)

    # Calculate stats
    n = len(results)
    avg_correctness = sum(r["answer_correctness"]["score"] for r in results) / n
    avg_relevancy = sum(r["context_relevancy"]["score"] for r in results) / n
    avg_recall = sum(r["context_recall"]["score"] for r in results) / n
    avg_overall = sum(r["overall_score"] for r in results) / n
    avg_time = sum(query_times) / len(query_times)

    print("\n" + "=" * 80)
    print("✅ FINAL EVALUATION RESULTS")
    print("=" * 80)
    print(f"\n📊 Metrics (as per assignment):")
    print(f"  A. Answer Correctness:  {avg_correctness:.2f}/5.0")
    print(f"  B. Context Relevancy:   {avg_relevancy:.2f}/5.0")
    print(f"  C. Context Recall:      {avg_recall:.2f}/5.0")
    print(
        f"  → Overall Score:        {avg_overall:.2f}/15.0 ({(avg_overall/15)*100:.1f}%)"
    )
    print(f"\n📈 Performance:")
    print(f"  Total queries:          {len(TEST_CASES)}")
    print(f"  Average time:           {avg_time:.1f}s")
    print("=" * 80 + "\n")

    # Save results
    output = {
        "results": results,
        "stats": {
            "total_tests": n,
            "avg_answer_correctness": avg_correctness,
            "avg_context_relevancy": avg_relevancy,
            "avg_context_recall": avg_recall,
            "avg_overall": avg_overall,
            "percentage": (avg_overall / 15.0) * 100,
            "avg_query_time": avg_time,
        },
    }

    with open("evaluation_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print("✅ Results saved to evaluation_results.json\n")

    return output


if __name__ == "__main__":
    run_evaluation()

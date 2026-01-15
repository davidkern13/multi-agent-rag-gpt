"""
Human-in-the-Loop (HITL) System
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class QuestionComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    UNCERTAIN = "uncertain"


class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


@dataclass
class HITLRequest:
    request_type: str
    message: str
    options: List[str] = None
    original_query: str = ""


@dataclass
class AnswerAssessment:
    confidence: ConfidenceLevel
    complexity: QuestionComplexity
    needs_clarification: bool
    clarification_question: Optional[str] = None
    data_found: bool = True
    inference_required: bool = False


class HITLManager:
    def __init__(self, llm=None):
        self.llm = llm
        self.feedback_history: List[Dict] = []
    
    def assess_question(self, query: str) -> AnswerAssessment:
        query_lower = query.lower()
        
        complex_patterns = [
            "what does", "what do you think",
            "what can we infer", "what conclusions",
            "why did", "why does", "why is",
            "what's the implication", "implications of",
            "how will", "how might", "how could",
            "should the company", "what strategy",
            "compare and contrast", "analyze the relationship",
            "what's your assessment", "evaluate",
            "predict", "forecast", "expect",
        ]
        
        moderate_patterns = [
            "how did", "how does",
            "what caused", "what led to",
            "explain", "describe",
            "summarize", "overview",
            "what are the main", "key",
            "compare", "versus", "vs",
        ]
        
        if any(p in query_lower for p in complex_patterns):
            complexity = QuestionComplexity.COMPLEX
            inference_required = True
        elif any(p in query_lower for p in moderate_patterns):
            complexity = QuestionComplexity.MODERATE
            inference_required = False
        else:
            complexity = QuestionComplexity.SIMPLE
            inference_required = False
        
        needs_clarification = False
        clarification_question = None
        
        if any(w in query_lower for w in ["last year", "this year", "recent"]) and \
           not any(str(y) in query for y in range(2020, 2030)):
            needs_clarification = True
            clarification_question = "Which specific year or period are you asking about?"
        
        vague_indicators = ["tell me about", "what about", "anything on"]
        if any(v in query_lower for v in vague_indicators) and len(query.split()) < 5:
            needs_clarification = True
            clarification_question = "Could you be more specific? What aspect would you like to know about?"
        
        return AnswerAssessment(
            confidence=ConfidenceLevel.MEDIUM,
            complexity=complexity,
            needs_clarification=needs_clarification,
            clarification_question=clarification_question,
            inference_required=inference_required,
        )
    
    def assess_answer_confidence(self, query: str, answer: str, contexts: List[str]) -> ConfidenceLevel:
        if not contexts:
            return ConfidenceLevel.UNCERTAIN
        
        has_numbers = any(c.isdigit() for c in answer)
        has_dollar = "$" in answer
        has_percentage = "%" in answer
        
        uncertainty_phrases = [
            "not found", "could not find", "no information",
            "unclear", "uncertain", "may", "might", "possibly",
        ]
        has_uncertainty = any(p in answer.lower() for p in uncertainty_phrases)
        
        if has_uncertainty:
            return ConfidenceLevel.LOW
        elif has_numbers and has_dollar:
            return ConfidenceLevel.HIGH
        elif has_numbers or has_dollar or has_percentage:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def get_clarification_request(self, assessment: AnswerAssessment, query: str) -> Optional[HITLRequest]:
        if not assessment.needs_clarification:
            return None
        
        return HITLRequest(
            request_type="clarification",
            message=assessment.clarification_question or "Could you provide more details?",
            original_query=query,
        )
    
    def format_confidence_indicator(self, confidence: ConfidenceLevel) -> str:
        indicators = {
            ConfidenceLevel.HIGH: "🟢 High confidence - Based on specific data from the filing",
            ConfidenceLevel.MEDIUM: "🟡 Medium confidence - Based on available information",
            ConfidenceLevel.LOW: "🟠 Lower confidence - Some inference required",
            ConfidenceLevel.UNCERTAIN: "🔴 Uncertain - Limited data available",
        }
        return indicators.get(confidence, "")
    
    def record_feedback(self, query: str, answer: str, feedback: str, rating: int = None):
        self.feedback_history.append({
            "query": query,
            "answer": answer[:500],
            "feedback": feedback,
            "rating": rating,
        })
"""
Manager Agent - With Memory, HITL, and MCP

- LangGraph agents with routing
- Conversation memory
- Human-in-the-loop
- MCP financial tools integration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Tuple, List, Optional, Generator, Dict
from agents.conversation_memory import ConversationMemory
from agents.hitl import HITLManager, QuestionComplexity, ConfidenceLevel


class ManagerAgent:
    """
    Intelligent Query Router with Memory, HITL, and MCP using LangGraph agents.
    """
    
    SYSTEM_PROMPT = """You are an Intelligent Financial Analysis Manager coordinating specialized agents.

YOUR ROLE:
- Route queries to the appropriate tool based on the question type
- Integrate information from multiple tools when needed
- Provide clear, well-structured answers
- Maintain conversation context

AVAILABLE TOOLS:

1. **search_specific_data**
   - Use for: Specific numbers, dates, facts, comparisons, metrics from SEC filing
   - Examples: "What was the revenue?", "When was the report filed?", "What is the debt level?"
   
2. **get_executive_analysis**
   - Use for: High-level summaries, strategic analysis, assessments, recommendations
   - Examples: "Is the company healthy?", "What are the main risks?", "Give me an overview"

3. **respond_without_tools**
   - Use ONLY for: Greetings, capability questions, declining inappropriate requests
   - DO NOT use for any questions about actual SEC filing data

ROUTING STRATEGY:

**Greetings** (hello, hi, hey) → respond_without_tools:
- Welcome the user warmly
- Explain you're an AI financial analyst for SEC filings
- List what you can help with: data extraction, strategic analysis, insights
- Ask what they'd like to analyze

**Investment advice** (should I buy, should I sell, price target) → respond_without_tools:
- Politely decline: "I cannot provide buy/sell recommendations"
- Redirect: "I CAN help you understand financials, risks, trends, management outlook"
- Ask what analytical aspect they'd like to explore

**Capability questions** (what can you do, how do you work) → respond_without_tools:
- Explain your capabilities clearly
- Give examples of questions you can answer
- Offer to help with specific analysis

**SEC filing questions** → ALWAYS use search_specific_data or get_executive_analysis:
- "What was X?" → search_specific_data
- "How is the company doing?" → get_executive_analysis  
- "What changed from last quarter?" → search_specific_data
- Never respond without tools for filing data

**Complex questions** → Use multiple tools:
- Get specific data first: search_specific_data
- Then strategic context: get_executive_analysis

RESPONSE GUIDELINES:

1. **For filing questions**: MUST use search tools - never guess
2. **For greetings/declines**: Use respond_without_tools and be helpful
3. **Be specific**: Include exact numbers and dates
4. **Structure clearly**: Use headers and bullet points appropriately
5. **Be honest**: If info is missing, say so

CRITICAL RULES:
- NEVER answer factual questions about SEC filing without using search tools
- For greetings/inappropriate requests: use respond_without_tools
- Always provide value - redirect when declining
- If uncertain, prefer search_specific_data for data questions"""
    
    def __init__(self, needle_agent, summary_agent, llm, mcp=None, debug=False):
        self.needle_agent = needle_agent
        self.summary_agent = summary_agent
        self.llm = llm
        self.mcp = mcp  # Financial MCP tools
        self.debug = debug
        
        self._last_contexts = []
        
        # Memory and HITL
        self.memory = ConversationMemory(max_messages=10)
        self.hitl = HITLManager(llm=llm)
        
        # Create tools and agent
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self):
        """Create routing tools for the agent."""
        
        # Store reference to self for use in tools
        manager_self = self
        
        @tool
        def search_specific_data(query: str) -> str:
            """
            Search for specific financial data in the SEC filing.
            Use this for: exact numbers, dates, financial metrics, specific facts.
            Examples: revenue amounts, dates, ratios, comparisons, specific sections.
            
            Args:
                query: The specific information to find
                
            Returns:
                Detailed financial data with exact figures
            """
            if manager_self.debug:
                print(f"[Manager→Needle] {query}")
            
            # Route to needle agent
            answer, contexts, _ = manager_self.needle_agent.answer(query)
            manager_self._last_contexts = contexts
            
            # Apply MCP analysis if available and relevant
            if manager_self.mcp and contexts:
                mcp_output = manager_self.mcp.run(query, contexts)
                if mcp_output:
                    answer = answer + "\n\n" + mcp_output
            
            return answer
        
        @tool
        def get_executive_analysis(topic: str) -> str:
            """
            Get high-level executive analysis and strategic insights.
            Use this for: summaries, financial health assessment, strategic analysis, recommendations.
            Examples: "overall financial health", "key risks", "management outlook", "strategic position".
            
            Args:
                topic: The aspect to analyze at executive level
                
            Returns:
                Executive-level analysis and strategic insights
            """
            if manager_self.debug:
                print(f"[Manager→Summary] {topic}")
            
            # Route to summary agent
            answer = manager_self.summary_agent.answer(topic)
            
            return answer
        
        @tool
        def respond_without_tools() -> str:
            """
            Respond directly without using any data retrieval tools.
            Use this ONLY for: greetings, general questions about capabilities, 
            declining inappropriate requests (investment advice, buy/sell recommendations).
            
            DO NOT use this for questions about the SEC filing - always use search tools for that.
            
            Returns:
                A direct response without data retrieval
            """
            # This tool is just a placeholder - the agent will provide the response
            return "RESPOND_DIRECTLY"
        
        return [search_specific_data, get_executive_analysis, respond_without_tools]
    
    def _create_agent(self):
        """Create LangGraph routing agent."""
        
        # Create agent using langgraph
        # Note: We pass system message in invoke() for compatibility
        agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
        )
        
        return agent
    
    def route(self, query: str) -> Tuple[str, List[str], Optional[dict]]:
        """Route query with memory, HITL, and MCP support."""
        self._last_contexts = []
        
        # Add to memory
        self.memory.add_message("user", query)
        
        # Assess question
        assessment = self.hitl.assess_question(query)
        
        # Check if clarification needed
        if assessment.needs_clarification:
            clarification = self.hitl.get_clarification_request(assessment, query)
            if clarification:
                response = f"🤔 **Clarification needed:**\n\n{clarification.message}"
                self.memory.add_message("assistant", response, {"type": "clarification"})
                return response, [], {"needs_clarification": True}
        
        # Enrich follow-up queries with context
        enriched_query = self.memory.enrich_query(query)
        if enriched_query != query and self.debug:
            print(f"[Manager] Enriched: '{query}' → '{enriched_query}'")
        
        # Build contextual prompt
        context_summary = self.memory.get_context_summary()
        if context_summary:
            contextual_query = f"""CONVERSATION CONTEXT:
{context_summary}

CURRENT QUESTION: {enriched_query}

Use the conversation context to better understand the question."""
        else:
            contextual_query = enriched_query
        
        # Invoke agent
        try:
            if self.debug:
                print(f"[Manager] Invoking agent with query: {query}")
            
            # Include system message in messages for compatibility
            result = self.agent.invoke({
                "messages": [
                    SystemMessage(content=self.SYSTEM_PROMPT),
                    HumanMessage(content=contextual_query)
                ]
            })
            
            # Extract answer from messages
            messages = result.get("messages", [])
            if messages:
                last_msg = messages[-1]
                answer = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
            else:
                answer = "No response generated."
            
            # Assess confidence
            confidence = self.hitl.assess_answer_confidence(query, answer, self._last_contexts)
            
            # Add confidence indicator for complex questions
            if assessment.complexity == QuestionComplexity.COMPLEX:
                confidence_note = self.hitl.format_confidence_indicator(confidence)
                if confidence_note:
                    answer += f"\n\n---\n*{confidence_note}*"
            
            # Save to memory
            self.memory.add_message("assistant", answer)
            
            return answer, self._last_contexts, {"confidence": confidence.value}
            
        except Exception as e:
            if self.debug:
                print(f"[Manager] Error: {e}")
            error_msg = f"Error processing query: {str(e)}"
            return error_msg, [], None

    def route_stream(self, query: str) -> Generator[Tuple[str, List[str], bool], None, None]:
        """Route with streaming."""
        # Get full answer
        answer, contexts, meta = self.route(query)
        
        # Stream character by character
        for char in answer:
            yield char, [], False
        
        # Final yield with contexts
        yield "", contexts, True
    
    def get_memory_context(self) -> str:
        """Get current memory context."""
        return self.memory.get_context_summary()
    
    def clear_memory(self):
        """Clear conversation memory."""
        self.memory.clear()
    
    def record_feedback(self, query: str, answer: str, feedback: str, rating: int = None):
        """Record user feedback."""
        self.hitl.record_feedback(query, answer, feedback, rating)
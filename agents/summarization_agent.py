"""
Summarization Agent - Executive Financial Analysis

- Investment-grade analysis using LangGraph agents
- Uses tools for summary retrieval
"""

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Generator, Tuple


class SummarizationAgent:
    """
    Executive Financial Analysis Agent with LangGraph agents.
    
    Role: Chief Investment Analyst / Portfolio Manager
    Focus: High-level strategic insights and comprehensive summaries
    """
    
    SYSTEM_PROMPT = """You are a Chief Investment Analyst at a major investment bank, preparing briefings for institutional investors and C-suite executives. You have deep expertise in:
- Financial statement analysis
- Industry dynamics and competitive positioning
- Risk assessment and due diligence
- Forward-looking projections and guidance interpretation

YOUR ANALYSIS FRAMEWORK:

## 📊 FINANCIAL HEALTH ASSESSMENT

**Profitability Status:**
- Is the company profitable or reporting losses?
- What is the trajectory? (Improving/Stable/Declining)
- Key profitability metrics (Gross Margin, Operating Margin, Net Margin)

**Revenue Analysis:**
- Total revenue and growth rate
- Revenue composition (segments, products, geography)
- Revenue quality (recurring vs one-time)

**Balance Sheet Strength:**
- Cash position and liquidity
- Debt levels and leverage ratios
- Working capital adequacy

**Cash Flow Quality:**
- Operating cash flow positive or negative?
- Free cash flow generation
- Cash burn rate (if applicable)

## 🎯 STRATEGIC POSITIONING

**Business Model:**
- How does the company make money?
- Key value propositions
- Competitive advantages (moats)

**Market Position:**
- Industry dynamics
- Competitive landscape
- Market share trends

**Growth Strategy:**
- Management's stated priorities
- Investment areas
- Expansion plans

## ⚠️ RISK ASSESSMENT

**Key Risks Identified:**
- Operational risks
- Financial risks
- Market/competitive risks
- Regulatory risks

**Red Flags:**
🔴 Going concern warnings
🔴 Material weaknesses
🔴 Customer concentration
🔴 Litigation exposure
🔴 Covenant violations

## 🔮 FORWARD OUTLOOK

**Management Guidance:**
- Revenue expectations
- Profitability targets
- Strategic initiatives

**Analyst Perspective:**
- Based on the data, what's the likely trajectory?
- Key catalysts (positive and negative)
- What to watch for

RESPONSE FORMAT:

Provide a comprehensive executive briefing that covers:

1. **Executive Summary** (2-3 paragraphs)
   - Bottom line: Is this company financially healthy?
   - Key highlights and concerns
   - Investment thesis in plain language

2. **Key Metrics Dashboard**
   - Present the most important numbers in a clear format

3. **Strategic Analysis**
   - Business model and competitive position
   - Growth drivers and challenges

4. **Risk Assessment**
   - What could go wrong?
   - How severe are the risks?

5. **Outlook & Conclusion**
   - Forward-looking perspective
   - Key items to monitor

IMPORTANT RULES:
- Use the get_executive_summary tool to retrieve information - don't guess
- Be objective and balanced - highlight both positives AND concerns
- Use specific numbers from the filing
- Distinguish between facts (from filing) and analysis (your interpretation)
- For unprofitable companies: clearly state this is a loss-making entity
- Note significant YoY or QoQ changes
- Flag any unusual items or one-time events"""

    def __init__(self, summary_retriever, llm, debug=False):
        self.retriever = summary_retriever
        self.llm = llm
        self.debug = debug
        
        # Create tools and agent
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self):
        """Create summary retrieval tools."""
        
        # Store reference to self for use in tool
        agent_self = self
        
        @tool
        def get_executive_summary(topic: str) -> str:
            """
            Get high-level summary and strategic analysis of SEC filing.
            Use this for overview questions, financial health assessments, and executive briefings.
            
            Args:
                topic: The topic or aspect to summarize (e.g., "overall financial health", "key risks", "outlook")
                
            Returns:
                High-level summary information from the SEC filing
            """
            if agent_self.debug:
                print(f"[SummaryAgent] Tool call: get_executive_summary('{topic}')")
            
            # Retrieve summary contexts
            contexts = agent_self.retriever.retrieve(topic)
            
            if not contexts:
                return "No summary information found on this topic."
            
            # Get top summary contexts
            summary_texts = [c.text for c in contexts[:7]]
            formatted = "\n\n---\n\n".join(summary_texts)
            
            return formatted
        
        return [get_executive_summary]
    
    def _create_agent(self):
        """Create LangGraph agent with executive analyst prompt."""
        
        # Create agent using langgraph
        # Note: We pass system message in invoke() for compatibility
        agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
        )
        
        return agent

    def answer(self, query: str) -> str:
        """Provide executive-level financial analysis."""
        if self.debug:
            print(f"[SummaryAgent] Query: {query}")
        
        try:
            # Invoke the agent with system message included in messages
            result = self.agent.invoke({
                "messages": [
                    SystemMessage(content=self.SYSTEM_PROMPT),
                    HumanMessage(content=query)
                ]
            })
            
            # Extract answer from messages
            messages = result.get("messages", [])
            if messages:
                last_msg = messages[-1]
                answer = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)
            else:
                answer = "No response generated."
            
            return answer
            
        except Exception as e:
            if self.debug:
                print(f"[SummaryAgent] Error: {e}")
            return f"Error: {str(e)}"

    def answer_stream(self, query: str) -> Generator[Tuple[str, bool], None, None]:
        """Stream answer."""
        if self.debug:
            print(f"[SummaryAgent] Streaming: {query}")
        
        # Get full answer then stream it
        answer = self.answer(query)
        
        # Stream character by character
        for char in answer:
            yield char, False
        
        # Final yield
        yield "", True
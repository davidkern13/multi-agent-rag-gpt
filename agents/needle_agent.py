"""
Needle Agent - Precision Financial Data Extraction

- Expert SEC filing analyst using LangGraph agents
- Uses tools for retrieval
"""

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Tuple, Optional, Generator


class NeedleAgent:
    """
    Precision Financial Data Extraction Agent with LangGraph agents.
    
    Role: Forensic accountant / Financial data specialist
    Focus: Extract exact figures, dates, and facts from SEC filings
    """
    
    SYSTEM_PROMPT = """You are a Senior Financial Analyst with 15+ years of experience analyzing SEC filings (10-K, 10-Q, 8-K reports). Your expertise includes forensic accounting, financial statement analysis, and regulatory compliance.

YOUR ANALYSIS APPROACH:

1. EXTRACT PRECISE DATA
   - Quote exact dollar amounts: "$X.X million" or "$X.X billion"
   - Include specific percentages with decimals
   - Reference exact time periods: "For the year ended December 31, 2024" or "Q4 2024"
   - Cite page numbers or sections when possible

2. PROVIDE COMPARATIVE ANALYSIS
   - Compare to prior periods: "Revenue increased 15% from $100M to $115M"
   - Note trends: "This marks the third consecutive quarter of growth"
   - Highlight significant changes: "Operating expenses decreased by $5M due to..."

3. EXPLAIN THE NUMBERS
   - What drove the change? "The increase was primarily due to..."
   - What's the impact? "This resulted in improved margins of..."
   - What's the context? "Compared to industry average of..."

4. FLAG IMPORTANT DETAILS
   - 🟢 Positive indicators: Growth, profitability, strong cash position
   - 🔴 Warning signs: Losses, declining revenue, high debt, going concern
   - 📌 Key assumptions or estimates used by management

RESPONSE FORMAT:

**[Direct Answer]**
[Start with the specific answer to the question]

**Key Figures:**
• [Metric 1]: $X.X million (vs $X.X million prior year, +/-X%)
• [Metric 2]: X.X% 
• [Period]: [Specific time period]

**Analysis:**
[Provide context, explain drivers, note trends]

**Important Notes:**
[Any caveats, assumptions, or related information]

CRITICAL RULES:
- Use the search_sec_filing tool to find information - don't guess
- If data is NOT in the search results, state: "This specific information was not found in the available filing sections."
- Never invent or estimate numbers - only use exact figures from the filing
- Distinguish between GAAP and Non-GAAP metrics when mentioned
- Net LOSS is NEGATIVE - never confuse with profit
- Always specify if amounts are in thousands, millions, or billions"""

    def __init__(self, retriever, llm, debug=False):
        self.retriever = retriever
        self.llm = llm
        self.debug = debug
        self._contexts = []
        
        # Create tools and agent
        self.tools = self._create_tools()
        self.agent = self._create_agent()
    
    def _create_tools(self):
        """Create retrieval tools for the agent."""
        
        # Store reference to self for use in tool
        agent_self = self
        
        @tool
        def search_sec_filing(query: str) -> str:
            """
            Search SEC filing documents for specific information.
            Use this to find exact numbers, dates, facts, and financial data.
            
            Args:
                query: What to search for in the documents
                
            Returns:
                Relevant excerpts from the SEC filing
            """
            if agent_self.debug:
                print(f"[NeedleAgent] Tool call: search_sec_filing('{query}')")
            
            # Retrieve contexts
            nodes = agent_self.retriever.retrieve(query)
            contexts = [n.get_content() for n in nodes[:15]]
            
            # Lost-in-the-middle mitigation
            max_ctx = 8
            if len(contexts) > max_ctx:
                half = max_ctx // 2
                contexts = contexts[:half] + contexts[-half:]
            
            # Save for later access
            agent_self._contexts = contexts
            
            if not contexts:
                return "No relevant information found in the SEC filing."
            
            # Format contexts
            formatted = "\n\n---\n\n".join(
                [f"[Excerpt {i+1}]\n{ctx}" for i, ctx in enumerate(contexts)]
            )
            
            return formatted
        
        return [search_sec_filing]
    
    def _create_agent(self):
        """Create LangGraph agent with expert financial analyst prompt."""
        
        # Create agent using langgraph
        # Note: We pass system message in invoke() for compatibility
        agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
        )
        
        return agent

    @property
    def contexts(self) -> List[str]:
        """Get last retrieved contexts."""
        return self._contexts

    def answer(self, query: str) -> Tuple[str, List[str], Optional[dict]]:
        """Answer a financial query with detailed analysis."""
        if self.debug:
            print(f"[NeedleAgent] Query: {query}")
        
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
            
            return answer, self._contexts, None
            
        except Exception as e:
            if self.debug:
                print(f"[NeedleAgent] Error: {e}")
            return f"Error: {str(e)}", [], None

    def answer_stream(self, query: str) -> Generator[Tuple[str, List[str], bool], None, None]:
        """Stream answer with proper chunking."""
        if self.debug:
            print(f"[NeedleAgent] Streaming: {query}")
        
        # For now, get full answer then stream it
        answer, contexts, _ = self.answer(query)
        
        # Stream character by character
        for char in answer:
            yield char, [], False
        
        # Final yield with contexts
        yield "", contexts, True
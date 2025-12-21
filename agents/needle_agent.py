class NeedleAgent:
    def __init__(self, retriever, llm, debug=False):
        self.retriever = retriever
        self.llm = llm
        self.debug = debug

    def _is_statistical_query(self, query: str) -> bool:
        """
        Check if query requires statistical analysis across all data points
        """
        statistical_keywords = [
            "highest",
            "lowest",
            "maximum",
            "minimum",
            "max",
            "min",
            "best",
            "worst",
            "most",
            "least",
            "average",
            "total",
            "sum",
            "count",
            "all days",
            "across all",
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in statistical_keywords)

    def _get_query_instruction(self, query: str) -> str:
        """
        Generate specific instructions based on query type
        """
        query_lower = query.lower()

        if "highest" in query_lower or "maximum" in query_lower or "max" in query_lower:
            return """
🔍 CRITICAL INSTRUCTION - MAXIMUM VALUE SEARCH:
This question asks for the HIGHEST/MAXIMUM value.

YOU MUST:
1. Scan through EVERY date and percentage in ALL contexts provided
2. Compare ALL values to find the absolute maximum
3. Do NOT stop at the first high value you see
4. Return ONLY the date with the TRUE HIGHEST percentage
5. Include the exact date, percentage, close price, and range

WRONG: Returning the first day with a high percentage
RIGHT: Comparing all days and returning the absolute maximum
"""

        elif (
            "lowest" in query_lower or "minimum" in query_lower or "min" in query_lower
        ):
            return """
🔍 CRITICAL INSTRUCTION - MINIMUM VALUE SEARCH:
This question asks for the LOWEST/MINIMUM value.

YOU MUST:
1. Scan through EVERY date and percentage in ALL contexts provided
2. Compare ALL values to find the absolute minimum
3. Do NOT stop at the first low value you see
4. Return ONLY the date with the TRUE LOWEST percentage
5. Include the exact date, percentage, close price, and range

WRONG: Returning the first day with a low percentage
RIGHT: Comparing all days and returning the absolute minimum
"""

        elif "average" in query_lower or "mean" in query_lower:
            return """
🔍 CRITICAL INSTRUCTION - AVERAGE CALCULATION:
This question asks for an AVERAGE value.

YOU MUST:
1. Identify ALL relevant values in the contexts
2. Calculate or estimate the average across all data points
3. Show your calculation if possible
4. Include the number of data points used
"""

        else:
            return """
🔍 INSTRUCTION - COMPREHENSIVE SEARCH:
Scan through ALL contexts to find the most relevant information.
If multiple values exist, compare them and provide the most accurate answer.
"""

    def answer(self, query: str):
        is_statistical = self._is_statistical_query(query)

        retrieval_count = 20 if is_statistical else 15
        nodes = self.retriever.retrieve(query)

        if is_statistical and len(nodes) < retrieval_count:
            contexts = [n.get_content() for n in nodes]
        else:
            contexts = [n.get_content() for n in nodes[:retrieval_count]]

        if self.debug:
            print(f"\n🔍 Query Type: {'STATISTICAL' if is_statistical else 'STANDARD'}")
            print(f"📊 Retrieved {len(contexts)} contexts")

        # Lost-in-the-middle mitigation - but keep more for statistical queries
        MAX_CTX = 20 if is_statistical else 15
        if len(contexts) > MAX_CTX:
            half = MAX_CTX // 2
            contexts = contexts[:half] + contexts[-half:]
            if self.debug:
                print(
                    f"📉 Applied lost-in-middle mitigation: kept {len(contexts)} contexts"
                )

        context_text = "\n\n".join(contexts)

        specific_instruction = self._get_query_instruction(query)

        prompt = f"""You are a financial data analysis assistant specializing in trading data.

{specific_instruction}

CONTEXT (Multiple Trading Days):
{context_text}

QUESTION: {query}

GENERAL INSTRUCTIONS:
- Provide a complete answer with relevant details (date, numbers, context)
- If the question asks for a summary, provide a clear 2-3 sentence summary
- If answering about percentages, include the actual values too
- Be specific and cite exact information from the context
- For statistical queries (highest/lowest/average), you MUST compare ALL data points
- Double-check your answer before responding
- If information is not found, reply: "Not found in the document."

ANSWER FORMAT:
- Start with the direct answer to the question
- Include supporting details: date, exact percentage/value, price, range
- Add context about the market conditions if relevant
- Keep it concise but complete

YOUR ANSWER:"""

        if self.debug:
            print("\n" + "=" * 80)
            print("📝 PROMPT SENT TO LLM:")
            print("=" * 80)
            print(prompt)
            print("=" * 80 + "\n")

        response = self.llm.complete(prompt)

        return response.text.strip(), contexts, response

    def answer_stream(self, query: str):
        """
        Stream answer for real-time display
        Returns: generator of (text_chunk, contexts, is_final)
        """
        is_statistical = self._is_statistical_query(query)

        retrieval_count = 20 if is_statistical else 15
        nodes = self.retriever.retrieve(query)

        if is_statistical and len(nodes) < retrieval_count:
            contexts = [n.get_content() for n in nodes]
        else:
            contexts = [n.get_content() for n in nodes[:retrieval_count]]

        # Lost-in-the-middle mitigation
        MAX_CTX = 20 if is_statistical else 15
        if len(contexts) > MAX_CTX:
            half = MAX_CTX // 2
            contexts = contexts[:half] + contexts[-half:]

        context_text = "\n\n".join(contexts)

        specific_instruction = self._get_query_instruction(query)

        prompt = f"""You are a financial data analysis assistant specializing in trading data.

{specific_instruction}

CONTEXT (Multiple Trading Days):
{context_text}

QUESTION: {query}

GENERAL INSTRUCTIONS:
- Provide a complete answer with relevant details (date, numbers, context)
- Be specific and cite exact information from the context
- For statistical queries (highest/lowest/average), you MUST compare ALL data points

YOUR ANSWER:"""

        response_stream = self.llm.stream_complete(prompt)

        full_text = ""
        for chunk in response_stream:
            delta = chunk.delta
            full_text += delta
            yield delta, contexts, False

        yield full_text, contexts, True

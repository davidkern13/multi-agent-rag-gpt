class SummarizationAgent:
    def __init__(self, summary_retriever, llm):
        self.llm = llm
        self.retriever = summary_retriever

    def answer(self, query: str):
        contexts = self.retriever.retrieve(query)
        context_text = "\n\n".join(c.text for c in contexts)

        prompt = (
            f"{query}\n\n"
            "Provide a clear and concise summary in 2-3 sentences.\n\n"
            f"{context_text}"
        )

        response = self.llm.complete(prompt)
        return response.text

    def answer_stream(self, query: str):
        contexts = self.retriever.retrieve(query)
        context_text = "\n\n".join(c.text for c in contexts)

        prompt = (
            f"{query}\n\n"
            "Provide a clear and concise summary in 2-3 sentences.\n\n"
            f"{context_text}"
        )

        response_stream = self.llm.stream_complete(prompt)

        full_text = ""
        for chunk in response_stream:
            delta = chunk.delta
            if delta:
                full_text += delta
                yield delta, False

        yield full_text, True

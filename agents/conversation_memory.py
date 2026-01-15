"""
Conversation Memory - Pure LangChain Implementation

Simple wrapper around LangChain's ConversationBufferWindowMemory
without additional custom logic.
"""

from typing import List, Dict, Optional, Any

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class ConversationMemory:
    """
    Simple conversation memory using in-memory chat history.
    
    This is a thin wrapper that provides backward compatibility with the
    original ConversationMemory interface.
    
    Attributes:
        chat_history: The underlying chat message history
    """
    
    # Configuration constants
    DEFAULT_WINDOW_SIZE: int = 10
    
    def __init__(
        self,
        window_size: Optional[int] = None,
        max_messages: Optional[int] = None,  # Alias for backward compatibility
        return_messages: bool = True,
        memory_key: str = "chat_history"
    ):
        """
        Initialize conversation memory.
        
        Args:
            window_size: Number of messages to keep (default: 10)
            max_messages: Alias for window_size (backward compatibility)
            return_messages: Return messages as objects vs strings
            memory_key: Key to use for memory in agent state
        """
        # Support both parameter names
        size = max_messages or window_size
        self._window_size = size if size is not None else self.DEFAULT_WINDOW_SIZE
        self._memory_key = memory_key
        self._return_messages = return_messages
        
        # Use ChatMessageHistory directly
        self.chat_history = ChatMessageHistory()
    
    # Backward compatible methods
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """
        Add message to memory (backward compatible).
        
        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional message metadata (ignored)
        """
        if role == "user":
            self.add_user_message(content)
        else:
            self.add_ai_message(content)
    
    def add_user_message(self, content: str) -> None:
        """
        Add user message to memory.
        
        Args:
            content: Message content
        """
        self.chat_history.add_user_message(content)
        self._trim_to_window()
    
    def add_ai_message(self, content: str) -> None:
        """
        Add AI message to memory.
        
        Args:
            content: Message content
        """
        self.chat_history.add_ai_message(content)
        self._trim_to_window()
    
    def _trim_to_window(self) -> None:
        """Trim messages to window size."""
        messages = self.chat_history.messages
        if len(messages) > self._window_size * 2:  # *2 because user+assistant pairs
            # Keep only the last window_size pairs
            self.chat_history.messages = messages[-(self._window_size * 2):]
    
    def get_messages(self) -> List[BaseMessage]:
        """
        Get all messages in conversation.
        
        Returns:
            List of LangChain message objects
        """
        return self.chat_history.messages
    
    def get_context_summary(self) -> str:
        """
        Get simple context summary.
        
        Returns:
            Formatted string with recent messages
        """
        messages = self.get_messages()
        
        if not messages:
            return ""
        
        parts = ["Recent conversation:"]
        for msg in messages:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            content = msg.content
            if len(content) > 200:
                content = content[:200] + "..."
            parts.append(f"  {role}: {content}")
        
        return "\n".join(parts)
    
    def enrich_query(self, query: str) -> str:
        """
        Enrich a follow-up query with context from previous messages.
        
        Handles pronouns and references like "it", "that", "the company", etc.
        by looking at the conversation history.
        
        Args:
            query: The current query
            
        Returns:
            Enriched query with context if needed, otherwise original query
        """
        query_lower = query.lower().strip()
        messages = self.get_messages()
        
        if not messages:
            return query
        
        # Check if query seems like a follow-up
        follow_up_indicators = [
            "it", "that", "this", "they", "them", "their",
            "the company", "the same", "more about", "what about",
            "and what", "how about", "tell me more", "explain more",
            "why", "how come", "what else"
        ]
        
        is_follow_up = any(
            indicator in query_lower 
            for indicator in follow_up_indicators
        ) and len(query.split()) < 10
        
        if not is_follow_up:
            return query
        
        # Find the last user message topic
        last_topic = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                # Extract potential topic from previous query
                content = msg.content.lower()
                # Skip if it's the same as current query
                if content.strip() == query_lower:
                    continue
                last_topic = msg.content
                break
        
        if last_topic and last_topic != query:
            # Enrich the query with context
            return f"{query} (in context of: {last_topic})"
        
        return query
    
    def clear(self) -> None:
        """Clear all conversation memory."""
        self.chat_history.clear()
    
    # LangChain compatibility methods
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """
        Save conversation context (LangChain compatibility).
        
        Args:
            inputs: Input dictionary (expects 'input' key)
            outputs: Output dictionary (expects 'output' key)
        """
        if "input" in inputs:
            self.add_user_message(inputs["input"])
        if "output" in outputs:
            self.add_ai_message(outputs["output"])
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load memory variables (LangChain compatibility).
        
        Args:
            inputs: Input dictionary
            
        Returns:
            Dictionary with memory variables
        """
        if self._return_messages:
            return {self._memory_key: self.get_messages()}
        else:
            return {self._memory_key: self.get_context_summary()}
    
    # Properties for backward compatibility
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Get messages (backward compatibility)."""
        return self.get_messages()
    
    @property
    def memory(self):
        """Get self for backward compatibility."""
        return self
    
    @property
    def langchain_memory(self):
        """Backward compatibility alias."""
        return self
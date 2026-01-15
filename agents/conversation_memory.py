"""
Conversation Memory - Pure LangChain Implementation

Simple wrapper around LangChain's ConversationBufferWindowMemory
without additional custom logic.
"""

from typing import List, Dict, Optional, Any

from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class ConversationMemory:
    """
    Simple conversation memory using LangChain's ConversationBufferWindowMemory.
    
    This is a thin wrapper that provides backward compatibility with the
    original ConversationMemory interface while using LangChain's memory
    management under the hood.
    
    Attributes:
        langchain_memory: The underlying LangChain memory instance
    """
    
    # Configuration constants
    DEFAULT_WINDOW_SIZE: int = 10
    
    def __init__(
        self,
        window_size: Optional[int] = None,
        return_messages: bool = True,
        memory_key: str = "chat_history"
    ):
        """
        Initialize conversation memory with LangChain.
        
        Args:
            window_size: Number of messages to keep (default: 10)
            return_messages: Return messages as objects vs strings
            memory_key: Key to use for memory in agent state
        """
        self._window_size = window_size if window_size is not None else self.DEFAULT_WINDOW_SIZE
        
        # Initialize LangChain memory - that's it!
        self.langchain_memory = ConversationBufferWindowMemory(
            k=self._window_size,
            return_messages=return_messages,
            memory_key=memory_key
        )
    
    # Backward compatible methods
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """
        Add message to memory (backward compatible).
        
        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional message metadata (ignored - LangChain doesn't support this)
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
        self.langchain_memory.chat_memory.add_user_message(content)
    
    def add_ai_message(self, content: str) -> None:
        """
        Add AI message to memory.
        
        Args:
            content: Message content
        """
        self.langchain_memory.chat_memory.add_ai_message(content)
    
    def get_messages(self) -> List[BaseMessage]:
        """
        Get all messages in conversation.
        
        Returns:
            List of LangChain message objects
        """
        return self.langchain_memory.chat_memory.messages
    
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
    
    def clear(self) -> None:
        """Clear all conversation memory."""
        self.langchain_memory.clear()
    
    # LangChain compatibility methods
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """
        Save conversation context (LangChain compatibility).
        
        Args:
            inputs: Input dictionary
            outputs: Output dictionary
        """
        self.langchain_memory.save_context(inputs, outputs)
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load memory variables (LangChain compatibility).
        
        Args:
            inputs: Input dictionary
            
        Returns:
            Dictionary with memory variables
        """
        return self.langchain_memory.load_memory_variables(inputs)
    
    # Properties for backward compatibility
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Get messages (backward compatibility)."""
        return self.get_messages()
    
    @property
    def memory(self):
        """Get LangChain memory (for agent integration)."""
        return self.langchain_memory
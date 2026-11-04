from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ConversationMemory:
    """Manages chat session turns and history."""

    def __init__(self, max_turns: int = 30):
        self.max_turns = max_turns
        self.messages: List[Message] = []

    def add_user_message(self, content: str) -> None:
        self.messages.append(Message(role="user", content=content))
        self._trim()

    def add_assistant_message(
        self,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.messages.append(Message(role="assistant", content=content, tool_calls=tool_calls))
        self._trim()

    def add_tool_message(self, tool_call_id: str, tool_name: str, content: str) -> None:
        self.messages.append(Message(
            role="tool",
            content=content,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
        ))
        self._trim()

    def clear(self) -> None:
        self.messages.clear()

    def get_messages(self) -> List[Message]:
        return list(self.messages)

    def _trim(self) -> None:
        if len(self.messages) > self.max_turns * 2:
            self.messages = self.messages[-(self.max_turns * 2):]

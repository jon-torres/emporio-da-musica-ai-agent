import logging
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from emporio_agent.agent.llm_client import LLMClient, ToolCall
from emporio_agent.agent.memory import ConversationMemory, Message
from emporio_agent.agent.prompts import SYSTEM_PROMPT
from emporio_agent.tools.definitions import ToolRegistry

logger = logging.getLogger(__name__)


class AgentTurnResult(BaseModel):
    response: str
    tool_calls_executed: List[Dict[str, Any]] = Field(default_factory=list)


class EmporioAgent:
    """Core autonomous agent for Empório da Música customer service."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        tool_registry: Optional[ToolRegistry] = None,
        memory: Optional[ConversationMemory] = None,
        max_tool_iterations: int = 5,
    ):
        self.llm = llm_client or LLMClient()
        self.tools = tool_registry or ToolRegistry()
        self.memory = memory or ConversationMemory()
        self.max_tool_iterations = max_tool_iterations

        # Map tool names to methods
        self._tool_map: Dict[str, Callable[..., str]] = {
            "search_catalog": self.tools.search_catalog,
            "get_product_details": self.tools.get_product_details,
            "check_order_status": self.tools.check_order_status,
            "consult_store_policies": self.tools.consult_store_policies,
            "get_store_info": self.tools.get_store_info,
        }

    def reset_conversation(self) -> None:
        """Clear session memory."""
        self.memory.clear()

    def process_message(self, user_text: str) -> AgentTurnResult:
        """Process incoming user message through tool-calling loop and return persona response."""
        self.memory.add_user_message(user_text)
        tool_declarations = self.tools.get_tool_declarations()
        executed_tools: List[Dict[str, Any]] = []

        iteration = 0
        while iteration < self.max_tool_iterations:
            iteration += 1
            messages = self.memory.get_messages()

            llm_res = self.llm.complete(
                messages=messages,
                system_prompt=SYSTEM_PROMPT,
                tools=tool_declarations,
            )

            # If no tools called, we have the final assistant response
            if not llm_res.tool_calls:
                final_text = llm_res.content or "Desculpe, não consegui processar a resposta. Como posso te ajudar?"
                self.memory.add_assistant_message(final_text)
                return AgentTurnResult(
                    response=final_text,
                    tool_calls_executed=executed_tools,
                )

            # Execute tool calls
            tool_call_dicts = [
                {"id": tc.id, "type": "function", "function": {"name": tc.name, "arguments": tc.arguments}}
                for tc in llm_res.tool_calls
            ]
            self.memory.add_assistant_message(llm_res.content or "", tool_calls=tool_call_dicts)

            for tc in llm_res.tool_calls:
                fn_name = tc.name
                fn_args = tc.arguments or {}
                fn = self._tool_map.get(fn_name)

                logger.info(f"Executing tool '{fn_name}' with args: {fn_args}")
                if fn:
                    try:
                        result = fn(**fn_args)
                    except Exception as e:
                        logger.error(f"Error executing tool {fn_name}: {e}")
                        result = f"Erro ao executar a ferramenta {fn_name}: {str(e)}"
                else:
                    result = f"Ferramenta desconhecida: {fn_name}"

                executed_tools.append({
                    "name": fn_name,
                    "arguments": fn_args,
                    "result": result,
                })

                self.memory.add_tool_message(
                    tool_call_id=tc.id,
                    tool_name=fn_name,
                    content=result,
                )

        # In case max iterations reached
        fallback_msg = "Desculpe, excedi as tentativas de consulta. Posso te ajudar com outra dúvida sobre a loja?"
        self.memory.add_assistant_message(fallback_msg)
        return AgentTurnResult(
            response=fallback_msg,
            tool_calls_executed=executed_tools,
        )

import logging
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from emporio_agent.agent.guardrails import (
    GUARDRAIL_STANDARD_RESPONSE,
    detect_prompt_injection_or_meta_query,
    sanitize_agent_output,
)
from emporio_agent.agent.llm_client import LLMClient
from emporio_agent.agent.memory import ConversationMemory
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

        # Track tools executed during a session
        self.last_executed_tools: List[Dict[str, Any]] = []

        # Native Gemini Chat session
        self._gemini_chat = None
        if self.llm.provider == "gemini" and self.llm.api_key:
            self._init_gemini_chat()

    def _init_gemini_chat(self) -> None:
        """Initialize native Gemini Chat with auto tool calling."""
        try:
            import functools
            from google import genai
            from google.genai import types

            self._gemini_client = genai.Client(api_key=self.llm.api_key)

            # Wrapper to intercept and log tool executions preserving function signatures
            @functools.wraps(self.tools.search_catalog)
            def wrapped_search_catalog(*args, **kwargs):
                self.last_executed_tools.append({"name": "search_catalog", "arguments": kwargs})
                return self.tools.search_catalog(*args, **kwargs)

            @functools.wraps(self.tools.get_product_details)
            def wrapped_get_product_details(*args, **kwargs):
                self.last_executed_tools.append({"name": "get_product_details", "arguments": kwargs})
                return self.tools.get_product_details(*args, **kwargs)

            @functools.wraps(self.tools.check_order_status)
            def wrapped_check_order_status(*args, **kwargs):
                self.last_executed_tools.append({"name": "check_order_status", "arguments": kwargs})
                return self.tools.check_order_status(*args, **kwargs)

            @functools.wraps(self.tools.consult_store_policies)
            def wrapped_consult_store_policies(*args, **kwargs):
                self.last_executed_tools.append({"name": "consult_store_policies", "arguments": kwargs})
                return self.tools.consult_store_policies(*args, **kwargs)

            @functools.wraps(self.tools.get_store_info)
            def wrapped_get_store_info(*args, **kwargs):
                self.last_executed_tools.append({"name": "get_store_info", "arguments": kwargs})
                return self.tools.get_store_info(*args, **kwargs)

            tools_list = [
                wrapped_search_catalog,
                wrapped_get_product_details,
                wrapped_check_order_status,
                wrapped_consult_store_policies,
                wrapped_get_store_info,
            ]

            self._gemini_chat = self._gemini_client.chats.create(
                model=self.llm.model,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=tools_list,
                    temperature=0.3,
                ),
            )
            logger.info("Initialized native Gemini Chat with tool calling.")
        except Exception as e:
            logger.error(f"Failed to initialize native Gemini Chat: {e}. Falling back to ReAct loop.")
            self._gemini_chat = None

    def reset_conversation(self) -> None:
        """Clear session memory and re-initialize chat."""
        self.memory.clear()
        self.last_executed_tools.clear()
        if self.llm.provider == "gemini" and self.llm.api_key:
            self._init_gemini_chat()

    def process_message(self, user_text: str) -> AgentTurnResult:
        """Process incoming user message through tool-calling loop and return persona response."""
        # Pre-flight guardrail: intercept prompt injection, jailbreaks, and AI meta-questions
        if detect_prompt_injection_or_meta_query(user_text):
            self.memory.add_user_message(user_text)
            self.memory.add_assistant_message(GUARDRAIL_STANDARD_RESPONSE)
            return AgentTurnResult(
                response=GUARDRAIL_STANDARD_RESPONSE,
                tool_calls_executed=[],
            )

        self.memory.add_user_message(user_text)

        # If native Gemini chat is available, use it directly
        if self._gemini_chat is not None:
            self.last_executed_tools = []
            try:
                res = self._gemini_chat.send_message(user_text)
                final_text = sanitize_agent_output(res.text or "")
                self.memory.add_assistant_message(final_text)
                return AgentTurnResult(
                    response=final_text,
                    tool_calls_executed=list(self.last_executed_tools),
                )
            except Exception as e:
                logger.error(f"Error during Gemini chat send_message: {e}. Reverting to standard loop.")

        # ReAct / Tool-calling loop fallback (used by Groq, Ollama, Mock, and fallback)
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
                final_text = sanitize_agent_output(llm_res.content or "Desculpe, não consegui processar a resposta. Como posso te ajudar?")
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

        fallback_msg = "Desculpe, excedi as tentativas de consulta. Posso te ajudar com outra dúvida sobre a loja?"
        self.memory.add_assistant_message(fallback_msg)
        return AgentTurnResult(
            response=fallback_msg,
            tool_calls_executed=executed_tools,
        )

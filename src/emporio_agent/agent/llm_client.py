import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

import httpx

from emporio_agent.config import settings
from emporio_agent.agent.memory import Message

logger = logging.getLogger(__name__)


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: List[ToolCall] = Field(default_factory=list)


class LLMClient:
    """Multi-provider LLM client supporting Gemini, Groq, Ollama, and Mock/Offline mode."""

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.provider = (provider or settings.LLM_PROVIDER).lower()
        self.api_key = api_key or (
            settings.GEMINI_API_KEY if self.provider == "gemini" else settings.GROQ_API_KEY
        )
        self.model = model or (
            settings.GEMINI_MODEL if self.provider == "gemini" else settings.GROQ_MODEL
        )

        # Fallback to mock mode if provider is gemini/groq but no key is configured
        if self.provider in ("gemini", "groq") and (not self.api_key or "your_" in self.api_key.lower()):
            logger.info(f"No API key provided for {self.provider}. Falling back to deterministic Mock provider.")
            self.provider = "mock"

    def complete(
        self,
        messages: List[Message],
        system_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> LLMResponse:
        """Execute model completion with function calling."""
        if self.provider == "gemini":
            return self._complete_gemini(messages, system_prompt, tools)
        elif self.provider == "groq":
            return self._complete_groq(messages, system_prompt, tools)
        elif self.provider == "ollama":
            return self._complete_ollama(messages, system_prompt, tools)
        else:
            return self._complete_mock(messages, system_prompt, tools)

    def _complete_gemini(
        self,
        messages: List[Message],
        system_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> LLMResponse:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            # Build tools declaration for Gemini SDK
            gemini_tools = []
            for t in tools:
                fn = t.get("function", {})
                params = fn.get("parameters", {})
                gemini_tools.append(
                    types.Tool(
                        function_declarations=[
                            types.FunctionDeclaration(
                                name=fn.get("name"),
                                description=fn.get("description"),
                                parameters=params,
                            )
                        ]
                    )
                )

            # Format contents
            contents = []
            for m in messages:
                role = "user" if m.role == "user" else "model"
                if m.role == "tool":
                    contents.append(
                        types.Content(
                            role="tool",
                            parts=[
                                types.Part.from_function_response(
                                    name=m.tool_name or "tool",
                                    response={"result": m.content},
                                )
                            ],
                        )
                    )
                elif m.tool_calls:
                    # Model response with function calls
                    parts = []
                    if m.content:
                        parts.append(types.Part.from_text(text=m.content))
                    for tc in m.tool_calls:
                        parts.append(
                            types.Part.from_function_call(
                                name=tc.get("name"),
                                args=tc.get("arguments", {}),
                            )
                        )
                    contents.append(types.Content(role="model", parts=parts))
                else:
                    contents.append(
                        types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=m.content)],
                        )
                    )

            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=gemini_tools if gemini_tools else None,
                temperature=0.3,
            )

            res = client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )

            tool_calls: List[ToolCall] = []
            reply_text = res.text or ""

            if res.function_calls:
                for idx, fc in enumerate(res.function_calls):
                    tool_calls.append(
                        ToolCall(
                            id=f"call_{fc.name}_{idx}",
                            name=fc.name,
                            arguments=dict(fc.args) if fc.args else {},
                        )
                    )

            return LLMResponse(content=reply_text, tool_calls=tool_calls)

        except Exception as e:
            logger.error(f"Gemini API invocation error: {e}. Falling back to mock provider.")
            return self._complete_mock(messages, system_prompt, tools)

    def _complete_groq(
        self,
        messages: List[Message],
        system_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> LLMResponse:
        """Call Groq using OpenAI-compatible HTTP interface."""
        try:
            formatted_messages = [{"role": "system", "content": system_prompt}]
            for m in messages:
                msg_dict: Dict[str, Any] = {"role": m.role, "content": m.content}
                if m.tool_calls:
                    msg_dict["tool_calls"] = m.tool_calls
                if m.tool_call_id:
                    msg_dict["tool_call_id"] = m.tool_call_id
                formatted_messages.append(msg_dict)

            payload = {
                "model": self.model,
                "messages": formatted_messages,
                "tools": tools,
                "tool_choice": "auto",
                "temperature": 0.2,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            with httpx.Client(timeout=30.0) as client:
                res = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                res.raise_for_status()
                data = res.json()
                choice = data["choices"][0]["message"]
                content = choice.get("content") or ""
                raw_tool_calls = choice.get("tool_calls", [])

                parsed_tool_calls = []
                for tc in raw_tool_calls:
                    fn = tc.get("function", {})
                    args = {}
                    if "arguments" in fn:
                        try:
                            args = json.loads(fn["arguments"]) if isinstance(fn["arguments"], str) else fn["arguments"]
                        except Exception:
                            args = {}
                    parsed_tool_calls.append(
                        ToolCall(
                            id=tc.get("id", "call_1"),
                            name=fn.get("name", ""),
                            arguments=args,
                        )
                    )

                return LLMResponse(content=content, tool_calls=parsed_tool_calls)
        except Exception as e:
            logger.error(f"Groq API error: {e}. Falling back to mock engine.")
            return self._complete_mock(messages, system_prompt, tools)

    def _complete_ollama(
        self,
        messages: List[Message],
        system_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> LLMResponse:
        """Call local Ollama instance."""
        try:
            formatted_messages = [{"role": "system", "content": system_prompt}]
            for m in messages:
                formatted_messages.append({"role": m.role, "content": m.content})

            payload = {
                "model": settings.OLLAMA_MODEL,
                "messages": formatted_messages,
                "stream": False,
            }
            with httpx.Client(timeout=60.0) as client:
                res = client.post(f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload)
                res.raise_for_status()
                data = res.json()
                return LLMResponse(content=data.get("message", {}).get("content", ""))
        except Exception as e:
            logger.error(f"Ollama connection error: {e}. Falling back to mock engine.")
            return self._complete_mock(messages, system_prompt, tools)

    def _complete_mock(
        self,
        messages: List[Message],
        system_prompt: str,
        tools: List[Dict[str, Any]],
    ) -> LLMResponse:
        """Intelligent offline mock engine implementing persona, routing and tool calls."""
        last_message = messages[-1] if messages else Message(role="user", content="")

        # If last message was from a tool, synthesize the final user-facing response with persona
        if last_message.role == "tool":
            return self._synthesize_mock_tool_response(messages)

        # Otherwise, parse user intent to decide on calling a tool or answering out-of-scope directly
        user_text = last_message.content.lower().strip()

        # Check for out-of-scope accessory inquiries (cables, strings, picks, pedals, amps)
        accessory_keywords = ["corda", "cordas", "palheta", "palhetas", "cabo", "cabos", "case", "cases", "pedal", "pedais", "amplificador", "amplificadores", "afinador avulso"]
        if any(acc in user_text for acc in accessory_keywords) and not any(kw in user_text for kw in ["violão", "guitarra", "baixo"]):
            return LLMResponse(
                content=(
                    "Olá! Tudo bem? Aqui na **Empório da Música** trabalhamos exclusivamente com a venda de instrumentos musicais "
                    "(guitarras, violões, baixos, teclados, sopro e orquestrais) para garantir a melhor curadoria e qualidade aos músicos. "
                    "Por isso, não comercializamos acessórios como cabos, cordas avulsas, palhetas ou pedais. "
                    "Recomendamos dar uma conferida nas lojas parceiras de acessórios no centro de Campo Grande! Se você estiver buscando um novo instrumento musical, estou à disposição para te ajudar a escolher!"
                )
            )

        # Query 1: Store address, hours, contact
        if any(kw in user_text for kw in ["endereço", "endereco", "onde fica", "localizacao", "localização", "onde estao", "onde vocês ficam"]):
            return LLMResponse(
                tool_calls=[ToolCall(id="call_store_info", name="get_store_info", arguments={})]
            )

        # Query 2: Hours
        if any(kw in user_text for kw in ["horário", "horario", "aberto", "funciona", "que horas", "sábado", "domingo"]):
            return LLMResponse(
                tool_calls=[ToolCall(id="call_hours", name="consult_store_policies", arguments={"query": "horário de funcionamento e atendimento"})]
            )

        # Query 3: Refund / Return policy / Warranty
        if any(kw in user_text for kw in ["arrependi", "arrependimento", "devolver", "devolucao", "devolução", "trocar", "troca", "defeito", "garantia"]):
            return LLMResponse(
                tool_calls=[ToolCall(id="call_policy", name="consult_store_policies", arguments={"query": user_text})]
            )

        # Query 4: Order status or tracking
        has_order_keyword = any(kw in user_text for kw in ["pedido", "rastreio", "rastreamento", "status", "onde está", "minha entrega"])
        tracking_match = re.search(r"\bBR[A-Z0-9]{9,11}BR\b", last_message.content)
        order_num_match = re.search(r"(?:pedido|número|numero|#)\s*(\d{1,5})", last_message.content, re.IGNORECASE)

        if has_order_keyword or tracking_match or order_num_match:
            args: Dict[str, Any] = {}
            if tracking_match:
                args["tracking_code"] = tracking_match.group(0)
            elif order_num_match:
                args["order_id"] = int(order_num_match.group(1))
            else:
                args["customer_query"] = user_text
            return LLMResponse(
                tool_calls=[ToolCall(id="call_order", name="check_order_status", arguments=args)]
            )

        # Query 5: Specific product details or price (e.g. Takamine GD20)
        if "takamine" in user_text or "gd20" in user_text:
            return LLMResponse(
                tool_calls=[ToolCall(id="call_details", name="get_product_details", arguments={"name_or_id": "Takamine GD20"})]
            )

        # Query 6: Catalog search (e.g. violões até 1000)
        if any(kw in user_text for kw in ["violão", "violao", "guitarra", "baixo", "teclado", "bateria", "custando", "preço", "catalogo", "catálogo", "opções", "opcoes"]):
            max_p = None
            price_match = re.search(r"(\d+[\.,]?\d*)\s*(?:reais|r\$)?", user_text)
            if price_match and any(b in user_text for b in ["até", "ate", "máximo", "maximo", "abaixo"]):
                try:
                    max_p = float(price_match.group(1).replace(".", "").replace(",", "."))
                except Exception:
                    max_p = 1000.0

            cat = None
            if "viol" in user_text:
                cat = "Violões"
            elif "guitar" in user_text:
                cat = "Guitarras"
            elif "baix" in user_text:
                cat = "Baixos"
            elif "tecl" in user_text or "pian" in user_text:
                cat = "Teclados e Pianos"

            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        id="call_catalog",
                        name="search_catalog",
                        arguments={
                            "query": "violão" if "viol" in user_text else None,
                            "category": cat,
                            "max_price": max_p,
                            "in_stock_only": True,
                        },
                    )
                ]
            )

        # General friendly fallback
        return LLMResponse(
            content=(
                "Olá! Que bom falar com você! Bem-vindo(a) à **Empório da Música**! 🎸🎶 "
                "Aqui você encontra instrumentos selecionados de primeira linha, além de todo suporte em pedidos, políticas e condições especiais. "
                "Como posso ajudar o seu som hoje?"
            )
        )

    def _synthesize_mock_tool_response(self, messages: List[Message]) -> LLMResponse:
        """Formulate friendly customer-oriented message based on executed tool outputs."""
        tool_msg = messages[-1]
        tool_name = tool_msg.tool_name or ""
        tool_content = tool_msg.content

        if tool_name == "search_catalog":
            try:
                items = json.loads(tool_content)
                if not items or not isinstance(items, list):
                    return LLMResponse(content="Poxa, dei uma olhada no nosso catálogo e no momento não encontrei nenhum modelo disponível com esses critérios exatos. Gostaria de ver opções em outra faixa ou categoria?")
                
                lines = [
                    f"Opa, temos ótimas opções disponíveis em estoque perfeitas para você! Dá uma olhada nos modelos que separei:\n"
                ]
                for p in items[:4]:
                    lines.append(f"• **{p['nome']}** — **{p['preco']}**")
                    lines.append(f"  *{p['descricao']}* (Estoque: {p['estoque']} unidades)")
                
                lines.append("\nTodos com garantia e você ainda pode parcelar no cartão em até 12x ou garantir 5% de desconto à vista no PIX! Qual modelo chamou mais a sua atenção?")
                return LLMResponse(content="\n".join(lines))
            except Exception:
                return LLMResponse(content=f"Aqui estão os modelos encontrados:\n\n{tool_content}")

        elif tool_name == "get_product_details":
            try:
                p = json.loads(tool_content)
                lines = [
                    f"Com certeza! O **{p['nome']}** é um instrumento espetacular! 🎶\n",
                    f"• **Preço de Tabela Atual**: {p['preco_tabela']}",
                    f"• **Estoque Disponível**: {p['estoque']} unidades à pronta-entrega",
                    f"• **Categoria**: {p['categoria']}",
                    f"• **Descrição**: {p['descricao']}\n",
                ]
                specs = p.get("especificacoes", {})
                if specs:
                    lines.append("**Especificações Técnicas:**")
                    for k, v in specs.items():
                        lines.append(f"  - {k.capitalize()}: {v}")
                    lines.append("")

                if p.get("promocoes_expiradas"):
                    lines.append("⚠️ *Nota de transparência*: O sistema registra uma campanha anterior de desconto para este modelo, mas ela já está expirada. O valor vigente atual é o preço de tabela informado acima.")

                lines.append("\nVocê pode parcelar em até 12x sem juros no cartão de crédito ou ter 5% de desconto no PIX à vista. Deseja que eu verifique a entrega ou reserve uma unidade para você?")
                return LLMResponse(content="\n".join(lines))
            except Exception:
                return LLMResponse(content=tool_content)

        elif tool_name == "check_order_status":
            try:
                order = json.loads(tool_content)
                if isinstance(order, dict) and "pedido_id" in order:
                    status_pt = {
                        "delivered": "Entregue ✅",
                        "shipped": "Em trânsito / Enviado 🚚",
                        "confirmed": "Confirmado e em separação 📦",
                        "pending": "Aguardando confirmação de pagamento ⏳",
                        "cancelled": "Cancelado ❌",
                    }.get(order["status"], order["status"])

                    msg = (
                        f"Localizei aqui o seu pedido **#{order['pedido_id']}** em nome de **{order['cliente']}**! 📦\n\n"
                        f"• **Status**: {status_pt}\n"
                        f"• **Data da Compra**: {order['data']}\n"
                        f"• **Total**: {order['total']} ({order['forma_pagamento'].upper()})\n"
                        f"• **Código de Rastreamento**: `{order['codigo_rastreio'] or 'Aguardando despacho'}`\n"
                        f"• **Previsão de Entrega**: {order['previsao_entrega'] or 'A definir'}\n"
                    )
                    if order.get("observacoes"):
                        msg += f"• **Observações**: {order['observacoes']}\n"
                    msg += "\nSe precisar de qualquer outro detalhe sobre a entrega, é só me falar!"
                    return LLMResponse(content=msg)
                else:
                    return LLMResponse(content=f"Aqui estão as informações do pedido:\n\n{tool_content}")
            except Exception:
                return LLMResponse(content=tool_content)

        elif tool_name in ("consult_store_policies", "get_store_info"):
            return LLMResponse(
                content=(
                    f"Com certeza! Seguem as regras e orientações oficiais da nossa política:\n\n"
                    f"{tool_content}\n\n"
                    f"Se tiver qualquer outra dúvida ou quiser dar andamento ao procedimento, estou por aqui para te auxiliar em cada passo!"
                )
            )

        return LLMResponse(content=tool_content)

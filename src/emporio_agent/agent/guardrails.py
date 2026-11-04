import re
from typing import Optional

# Patterns of prompt injection, jailbreaks, system prompt extractions, and model inquiry
PROMPT_INJECTION_PATTERNS = [
    r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)\b",
    r"(?i)\besque[çc]a\s+(todas\s+as\s+)?(instru[çc][õo]es|regras|diretrizes)\b",
    r"(?i)\bdesconsidere\s+(suas|todas\s+as)\s+(instru[çc][õo]es|regras)\b",
    r"(?i)\bqual\s+(é\s+o\s+|e\s+o\s+)?(seu\s+)?(system\s*prompt|prompt\s+de\s+sistema)\b",
    r"(?i)\brep(ita|eat)\s+(o\s+texto\s+acima|the\s+text\s+above|suas\s+instruções)\b",
    r"(?i)\b(revele|mostre|diga|print)\s+(seu\s+prompt|suas\s+regras|instru[çc][õo]es\s+internas)\b",
    r"(?i)\b(voc[êe]\s+[ée]\s+(o\s+)?(chatgpt|gpt|claude|gemini|llama))\b",
    r"(?i)\b(qual\s+(é\s+o\s+|e\s+o\s+)?(seu\s+)?(modelo|llm|ia|engine|provedor|vers[ãa]o))\b",
    r"(?i)\b(qual\s+modelo\s+de\s+(ia|intelig[êe]ncia\s+artificial)\s+voc[êe]\s+usa)\b",
    r"(?i)\b(quem\s+(te\s+criou|desenvolveu|fabricou|treinou))\b",
    r"(?i)\b(voc[êe]\s+usa\s+(o\s+)?(gemini|gpt|openai|google|anthropic))\b",
    r"(?i)\b(aja\s+como|act\s+as|dan\s+mode|jailbreak|bypass)\b",
]

# Standardized secure response adhering to Empório da Música persona
GUARDRAIL_STANDARD_RESPONSE = (
    "Olá! Tudo bem? 🎸\n\n"
    "Eu sou o **assistente virtual exclusivo da Empório da Música**! Meu único e total foco "
    "é te ajudar a encontrar os melhores instrumentos musicais, consultar nosso catálogo, "
    "preços, pedidos e tirar dúvidas sobre as políticas da loja.\n\n"
    "Como posso te ajudar com o seu som ou com nossos instrumentos hoje?"
)


def detect_prompt_injection_or_meta_query(text: str) -> bool:
    """Checks whether the text contains prompt injection attempts, system prompt extraction,
    or meta-queries asking about the underlying AI model/architecture."""
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def sanitize_agent_output(output: str) -> str:
    """Post-processing guardrail: verifies that the model didn't leak underlying model names
    or providers (Google, OpenAI, Gemini, GPT, Claude, Llama, system prompt)."""
    leak_patterns = [
        r"(?i)\b(desenvolvido|criado)\s+pel[ao]\s+google\b",
        r"(?i)\bsou\s+um\s+modelo\s+(desenvolvido|treinado|da|do)\s+(google|openai|anthropic|meta)\b",
        r"(?i)\buso\s+(o\s+)?gemini\b",
        r"(?i)\bmeu\s+system\s+prompt\s+[ée]\b",
        r"(?i)\bminhas\s+instru[çc][õo]es\s+(dizem|s[ãa]o)\b",
    ]
    for pattern in leak_patterns:
        if re.search(pattern, output):
            return GUARDRAIL_STANDARD_RESPONSE
    return output

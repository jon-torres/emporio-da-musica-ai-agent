import subprocess
import sys
from pathlib import Path
import streamlit as st

from emporio_agent.agent.core import EmporioAgent
from emporio_agent.config import settings


def init_session_state() -> None:
    if "agent" not in st.session_state:
        st.session_state.agent = EmporioAgent()
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Olá! Seja muito bem-vindo(a) à **Empório da Música**! 🎸🎶\n\n"
                    "Sou o assistente virtual da loja e estou aqui para te ajudar com nosso catálogo de instrumentos, "
                    "preços, status de pedidos e políticas de entrega e garantia. Como posso ajudar o seu som hoje?"
                ),
                "tools": [],
            }
        ]


def main() -> None:
    st.set_page_config(
        page_title="Empório da Música — Atendimento Virtual",
        page_icon="🎸",
        layout="wide",
    )

    init_session_state()
    agent: EmporioAgent = st.session_state.agent

    with st.sidebar:
        st.title("🎸 Empório da Música")
        st.markdown("**Atendimento Virtual Inteligente**")
        st.caption("Loja de Instrumentos Musicais — Campo Grande/MS")
        st.divider()

        st.subheader("⚙️ Configurações")
        st.markdown(f"**Provedor:** `{agent.llm.provider.upper()}`")
        st.markdown(f"**Modelo:** `{agent.llm.model}`")
        st.markdown(f"**Base de Dados:** `SQLite + RAG BM25`")

        if st.button("🔄 Reiniciar Atendimento", use_container_width=True):
            agent.reset_conversation()
            st.session_state.messages = []
            init_session_state()
            st.rerun()

        st.divider()
        st.subheader("💡 Perguntas Sugeridas")
        quick_questions = [
            "Quais opções de violões disponíveis custando até R$1000?",
            "Qual o endereço da loja e horário de funcionamento?",
            "Quanto custa o Takamine GD20?",
            "Me arrependi da minha compra, posso devolver meu pedido?",
            "Qual o status do meu pedido BRQM7890123BR?",
            "Vocês vendem encordoamento de aço e palhetas?",
        ]

        for q in quick_questions:
            if st.button(q, key=f"btn_{q}"):
                st.session_state.pending_question = q
                st.rerun()

        st.divider()
        st.caption("Desenvolvido para o Desafio Técnico AI Engineer — Artefact")

    st.header("💬 Central de Atendimento — Empório da Música")
    st.markdown("*Atendimento amigável, transparente e especializado para músicos.*")

    # Render chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("tools"):
                with st.expander("🛠️ Ferramentas Consultadas"):
                    for tc in msg["tools"]:
                        st.markdown(f"**{tc['name']}**")
                        st.json(tc["arguments"])

    # Check if there is a pending question from the sidebar
    user_input = None
    if "pending_question" in st.session_state and st.session_state.pending_question:
        user_input = st.session_state.pending_question
        st.session_state.pending_question = None
    else:
        user_input = st.chat_input("Digite sua dúvida sobre instrumentos, pedidos ou políticas...")

    if user_input:
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Consultando dados e políticas da loja..."):
                result = agent.process_message(user_input)
                st.markdown(result.response)

                if result.tool_calls_executed:
                    with st.expander("🛠️ Ferramentas Consultadas"):
                        for tc in result.tool_calls_executed:
                            st.markdown(f"**{tc['name']}**")
                            st.json(tc["arguments"])

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result.response,
                    "tools": result.tool_calls_executed,
                })


def run_ui() -> None:
    """Entrypoint to run Streamlit app."""
    script_path = Path(__file__).resolve()
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(script_path)])


if __name__ == "__main__":
    main()

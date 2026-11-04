import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from emporio_agent.agent.core import EmporioAgent
from emporio_agent.config import settings

console = Console()


def print_banner(agent: EmporioAgent) -> None:
    banner = f"""[bold yellow]🎸 EMPÓRIO DA MÚSICA — ATENDIMENTO VIRTUAL[/bold yellow]
[dim]Loja especializada em instrumentos musicais | Campo Grande - MS[/dim]

[cyan]Provedor:[/cyan] {agent.llm.provider.upper()} | [cyan]Modelo:[/cyan] {agent.llm.model}
[dim]Comandos: [bold]/reset[/bold] (limpar histórico) | [bold]/debug[/bold] (alternar visualização de ferramentas) | [bold]/sair[/bold] (encerrar)[/dim]
"""
    console.print(Panel(banner, border_style="yellow", expand=False))


def main() -> None:
    agent = EmporioAgent()
    print_banner(agent)

    show_debug = True

    console.print("[green]Olá! Sou o assistente virtual da Empório da Música. Como posso te ajudar hoje?[/green]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]Você[/bold cyan]")
            if not user_input.strip():
                continue

            cleaned = user_input.strip()

            if cleaned.lower() in ("/sair", "sair", "exit", "quit"):
                console.print("[yellow]Até mais! Quando precisar de um bom som, conte com a Empório da Música! 🎸👋[/yellow]")
                sys.exit(0)

            if cleaned.lower() == "/reset":
                agent.reset_conversation()
                console.print("[dim italic]Histórico de conversa reiniciado.[/dim italic]\n")
                continue

            if cleaned.lower() == "/debug":
                show_debug = not show_debug
                console.print(f"[dim italic]Exibição de ferramentas executadas: {'ATIVADA' if show_debug else 'DESATIVADA'}[/dim italic]\n")
                continue

            with console.status("[bold green]Consultando informações e preparando resposta...[/bold green]", spinner="dots"):
                result = agent.process_message(cleaned)

            if show_debug and result.tool_calls_executed:
                for tc in result.tool_calls_executed:
                    console.print(
                        f"[dim yellow]🛠️ Ferramenta chamada:[/dim yellow] [bold]{tc['name']}[/bold] | [dim]Args: {tc['arguments']}[/dim]"
                    )

            console.print("\n[bold yellow]Empório da Música:[/bold yellow]")
            console.print(Markdown(result.response))
            console.print()

        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Atendimento finalizado. Até breve![/yellow]")
            break


if __name__ == "__main__":
    main()

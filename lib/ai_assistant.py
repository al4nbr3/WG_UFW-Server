"""Claude AI assistant for WireGuard + UFW setup guidance and troubleshooting."""

import os
import anthropic
from rich.console import Console
from rich.markdown import Markdown

console = Console()

SYSTEM_PROMPT = """You are a Linux systems expert specializing in WireGuard VPN and UFW firewall
configuration on Ubuntu 24.04. Help the user set up, troubleshoot, and manage their WireGuard
VPN server and UFW firewall rules. Be concise and practical. When suggesting commands that require
sudo, always recommend the user run the provided bash scripts in the scripts/ directory rather than
running sudo commands directly."""


def get_client() -> anthropic.Anthropic | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


def ask(question: str, context: str = "") -> str:
    """Send a question to Claude and return the response text."""
    client = get_client()
    if not client:
        return "AI assistant unavailable — set ANTHROPIC_API_KEY in .env to enable."

    user_message = question
    if context:
        user_message = f"Context:\n{context}\n\nQuestion: {question}"

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text


def interactive_chat() -> None:
    """Start an interactive AI chat session in the terminal."""
    client = get_client()
    if not client:
        console.print("[red]ANTHROPIC_API_KEY not set. Add it to .env to use AI assistant.[/red]")
        return

    console.print("[bold green]WG_UFW AI Assistant[/bold green] — type 'exit' to quit\n")
    history = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.lower() in ("exit", "quit", "q"):
            break
        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        reply = response.content[0].text
        history.append({"role": "assistant", "content": reply})

        console.print("\n[bold cyan]Assistant:[/bold cyan]")
        console.print(Markdown(reply))
        console.print()

"""
Interactive CLI for Laptop Agent (Stage 1).
Provides a rich terminal chat interface with the JARVIS Brain backend.
"""

import sys
import requests
from laptop_agent.config import config

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.text import Text
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None


def print_banner(session_id: str):
    """Display startup banner."""
    if HAS_RICH:
        banner_text = Text()
        banner_text.append("⚡ J.A.R.V.I.S. — Laptop Client ⚡\n", style="bold cyan")
        banner_text.append(f"Backend: {config.BACKEND_URL}  |  Device: {config.DEVICE_ID}  |  Session: {session_id}\n", style="dim")
        banner_text.append("Commands: /history, /clear, /session <id>, /help, /exit", style="italic yellow")
        console.print(Panel(banner_text, border_style="cyan"))
    else:
        print("==================================================")
        print("⚡ J.A.R.V.I.S. — Laptop Client")
        print(f"Backend: {config.BACKEND_URL} | Session: {session_id}")
        print("Commands: /history, /clear, /session <id>, /help, /exit")
        print("==================================================")


def check_backend_connection() -> bool:
    """Verify backend is alive."""
    try:
        resp = requests.get(f"{config.BACKEND_URL}/health", timeout=3.0)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def send_chat_message(message: str, session_id: str):
    """Send natural language command to /chat endpoint."""
    url = f"{config.BACKEND_URL}/chat"
    payload = {
        "message": message,
        "session_id": session_id,
        "device_id": config.DEVICE_ID
    }

    try:
        response = requests.post(url, json=payload, timeout=60.0)
        if response.status_code == 200:
            data = response.json()
            assistant_reply = data["response"]
            provider = data.get("provider", "unknown")
            history_count = data.get("history_count", 0)

            if HAS_RICH:
                meta = f"[dim]provider: {provider} | context: {history_count} turn(s)[/dim]"
                console.print(Panel(
                    Markdown(assistant_reply),
                    title=f"[bold green]Jarvis[/bold green] ({meta})",
                    border_style="green"
                ))
            else:
                print(f"\n[Jarvis ({provider})]: {assistant_reply}\n")
        else:
            err_msg = f"HTTP {response.status_code}: {response.text}"
            if HAS_RICH:
                console.print(f"[bold red]Backend Error:[/bold red] {err_msg}")
            else:
                print(f"Backend Error: {err_msg}")

    except requests.ConnectionError:
        err = f"Could not connect to JARVIS brain at {config.BACKEND_URL}."
        hint = "Ensure backend is running: python -m uvicorn backend.app.main:app --reload --port 8000"
        if HAS_RICH:
            console.print(f"[bold red]Connection Error:[/bold red] {err}\n[yellow]Hint:[/yellow] {hint}")
        else:
            print(f"Connection Error: {err}\nHint: {hint}")
    except requests.Timeout:
        if HAS_RICH:
            console.print("[bold red]Timeout:[/bold red] Backend took too long to respond.")
        else:
            print("Timeout: Backend took too long to respond.")
    except Exception as e:
        if HAS_RICH:
            console.print(f"[bold red]Unexpected Error:[/bold red] {e}")
        else:
            print(f"Unexpected Error: {e}")


def display_history(session_id: str):
    """Fetch and print session message history."""
    url = f"{config.BACKEND_URL}/history/{session_id}"
    try:
        resp = requests.get(url, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            messages = data.get("messages", [])
            if not messages:
                if HAS_RICH:
                    console.print("[yellow]No message history found for this session.[/yellow]")
                else:
                    print("No message history found for this session.")
                return

            if HAS_RICH:
                table = Table(title=f"Conversation History ({session_id})", border_style="cyan")
                table.add_column("ID", style="dim", width=6)
                table.add_column("Role", style="bold", width=12)
                table.add_column("Device", style="magenta", width=10)
                table.add_column("Content", style="white")
                table.add_column("Timestamp", style="dim", width=20)

                for msg in messages:
                    role_color = "cyan" if msg["role"] == "user" else "green"
                    table.add_row(
                        str(msg["id"]),
                        f"[{role_color}]{msg['role'].upper()}[/{role_color}]",
                        msg.get("device_id") or "-",
                        msg["content"],
                        str(msg["created_at"])[:19]
                    )
                console.print(table)
            else:
                print(f"--- History for session {session_id} ---")
                for msg in messages:
                    print(f"[{msg['role'].upper()}] ({msg.get('created_at')}): {msg['content']}")
                print("---------------------------------------")
        else:
            print(f"Failed to retrieve history: {resp.text}")
    except Exception as e:
        print(f"Error retrieving history: {e}")


def clear_history(session_id: str):
    """Clear session message history."""
    url = f"{config.BACKEND_URL}/history/{session_id}"
    try:
        resp = requests.delete(url, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            count = data.get("deleted_messages_count", 0)
            if HAS_RICH:
                console.print(f"[green]✓ Cleared {count} message(s) from session '{session_id}'. Memory reset.[/green]")
            else:
                print(f"Cleared {count} message(s) from session '{session_id}'.")
        else:
            print(f"Failed to clear history: {resp.text}")
    except Exception as e:
        print(f"Error clearing history: {e}")


def run_cli():
    """Main CLI loop."""
    current_session = config.DEFAULT_SESSION_ID
    print_banner(current_session)

    # Check backend on startup
    if not check_backend_connection():
        if HAS_RICH:
            console.print(
                "[yellow]Warning: JARVIS brain is currently offline or unreachable at "
                f"{config.BACKEND_URL}. Please start the backend server.[/yellow]\n"
            )
        else:
            print(f"Warning: JARVIS brain is currently offline at {config.BACKEND_URL}.\n")
    else:
        if HAS_RICH:
            console.print("[green]● Connected to JARVIS Brain successfully.[/green]\n")
        else:
            print("Connected to JARVIS Brain successfully.\n")

    while True:
        try:
            prompt_label = f"[{current_session}] You > "
            if HAS_RICH:
                user_input = console.input(f"[bold cyan]{prompt_label}[/bold cyan]").strip()
            else:
                user_input = input(prompt_label).strip()

            if not user_input:
                continue

            # Command routing
            cmd_lower = user_input.lower()
            if cmd_lower in ("/exit", "/quit", "exit", "quit"):
                if HAS_RICH:
                    console.print("[dim cyan]Shutting down client. Goodbye, sir.[/dim cyan]")
                else:
                    print("Goodbye.")
                break

            elif cmd_lower == "/help":
                help_text = (
                    "Available Commands:\n"
                    "  /history         - View stored conversation transcript\n"
                    "  /clear           - Reset conversation memory for current session\n"
                    "  /session <name>  - Switch to a new session ID\n"
                    "  /help            - Show this guide\n"
                    "  /exit            - Exit the CLI"
                )
                if HAS_RICH:
                    console.print(Panel(help_text, title="Help", border_style="yellow"))
                else:
                    print(help_text)

            elif cmd_lower == "/history":
                display_history(current_session)

            elif cmd_lower == "/clear":
                clear_history(current_session)

            elif cmd_lower.startswith("/session"):
                parts = user_input.split(maxsplit=1)
                if len(parts) > 1 and parts[1].strip():
                    current_session = parts[1].strip()
                    if HAS_RICH:
                        console.print(f"[cyan]Switched active session to: [bold]{current_session}[/bold][/cyan]")
                    else:
                        print(f"Switched session to: {current_session}")
                else:
                    print("Usage: /session <session_id>")

            else:
                send_chat_message(user_input, current_session)

        except (KeyboardInterrupt, EOFError):
            if HAS_RICH:
                console.print("\n[dim cyan]Interrupted. Goodbye, sir.[/dim cyan]")
            else:
                print("\nInterrupted. Goodbye.")
            sys.exit(0)


if __name__ == "__main__":
    run_cli()

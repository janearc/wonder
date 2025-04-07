def wonder_repl(self):
    """Start a Wonder REPL session."""
    import readline
    import yaml
    from datetime import datetime
    from rich.console import Console

    console = Console()
    session_log = []
    date_stamp = datetime.now().strftime("%Y-%m-%dT%H-%M")
    session_file = f"wonder-session-{date_stamp}.yaml"

    console.print("\n[bold green]🌀 wonder-local shell[/bold green]")
    console.print(f"[dim]Model:[/dim] [cyan]{self.model_name}[/cyan]")
    console.print(f"[dim]Session:[/dim] [magenta]{date_stamp}[/magenta]\n")
    console.print("[italic]To open a session is to invite emergence. To care.[/italic]\n")

    while True:
        prompt = input("\n[bold]>[/bold] ").strip()
        if prompt.lower() in {"exit", "quit"}:
            break

        try:
            response = self.generate(prompt, max_length=2048)
        except Exception as e:
            console.print(f"[red]Generation error: {e}[/red]")
            continue

        console.print(f"\n[bold cyan]Tinker:[/bold cyan]\n{response}\n")

        approved = input("Approve response? (y/n): ").strip().lower()
        if approved == "y":
            entry = {
                "prompt": prompt,
                "response": response,
                "approved": True,
                "tags": []
            }
        else:
            rejection_type = input("Rejection type (e.g., tone, ethic, decoherence): ").strip()
            note = input("Note on rejection: ").strip()
            entry = {
                "prompt": prompt,
                "response": response,
                "approved": False,
                "rejection": {
                    "type": rejection_type,
                    "note": note
                }
            }

        session_log.append(entry)
        console.print("[green]Entry added to session log.[/green]\n")

    session_data = {
        "session": {
            "id": date_stamp,
            "model": self.model_name,
            "approved": sum(1 for e in session_log if e.get("approved")),
            "rejected": sum(1 for e in session_log if not e.get("approved")),
            "entries": session_log
        }
    }

    try:
        with open(session_file, "w", encoding="utf-8") as f:
            yaml.dump(session_data, f, allow_unicode=True, width=78)
        console.print("\n[bold green]🧾 Session complete[/bold green]")
        console.print(f"[dim]Saved:[/dim] {session_file}\n")
    except Exception as e:
        console.print(f"[red]Error saving session: {e}[/red]")

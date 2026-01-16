import typer
import json
import os
import re
import ast
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from .verifier import VeritasVerifier

app = typer.Typer(help="Veritas: AI Agent Audit Verification Tool")
console = Console()

@app.command()
def verify(
    proof_file: str = typer.Argument(..., help="Path to the session_proof.json file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show full content of verified logs")
):
    """
    Verify the cryptographic integrity of an agent session.
    """
    if not os.path.exists(proof_file):
        console.print(f"[red]Error:[/red] File {proof_file} not found")
        raise typer.Exit(code=1)
        
    try:
        with open(proof_file, "r") as f:
            proof_data = json.load(f)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to parse JSON: {e}")
        raise typer.Exit(code=1)
        
    console.print(Panel(f"Verifying Session Proof: [bold cyan]{proof_file}[/bold cyan]", title="Veritas Auditor"))
    
    is_valid, message, details = VeritasVerifier.verify_session(proof_data)
    
    if is_valid:
        console.print(f"\n[bold green]SUCCESS:[/bold green] {message}")
    else:
        console.print(f"\n[bold red]FAILURE:[/bold red] {message}")
        
    # Show Details Table
    table = Table(title="Verification Details")
    table.add_column("Status", style="bold")
    table.add_column("Check")
    
    for i, detail in enumerate(details):
        status = "[green]PASS[/green]" if "Verified" in detail or "verified" in detail else "[yellow]INFO[/yellow]"
        if "Warning" in detail: status = "[yellow]WARN[/yellow]"
        if "FAILURE" in detail or "TAMPER" in detail: status = "[red]FAIL[/red]"
        table.add_row(status, detail)
        
        # Verbose: Show log content if this is a log verification line
        if verbose and "Log #" in detail:
            match = re.search(r"Log #(\d+)", detail)
            if match:
                try:
                    idx = int(match.group(1))
                    content = proof_data["logs"][idx]["output_result"]
                    
                    # Try to parse python dict string representation to JSON
                    try:
                        if isinstance(content, str) and content.strip().startswith("{"):
                             parsed = ast.literal_eval(content)
                             pretty = json.dumps(parsed, indent=2)
                             table.add_row("", f"[dim]{pretty}[/dim]")
                        else:
                             table.add_row("", f"[dim]{content}[/dim]")
                    except:
                        table.add_row("", f"[dim]{content}[/dim]")
                except Exception:
                    pass
        
    console.print(table)
    
    if not is_valid:
        raise typer.Exit(code=1)

@app.command()
def info():
    """Display Veritas version and status."""
    console.print("[bold cyan]Veritas[/bold cyan] v0.1.0")
    console.print("Audit Layer for AI Agents on Base")

if __name__ == "__main__":
    app()
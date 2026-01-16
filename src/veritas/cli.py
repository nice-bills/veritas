import typer
import json
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from .verifier import VeritasVerifier

app = typer.Typer(help="Veritas: AI Agent Audit Verification Tool")
console = Console()

@app.command()
def verify(proof_file: str = typer.Argument(..., help="Path to the session_proof.json file")):
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
    
    for detail in details:
        status = "[green]PASS[/green]" if "Verified" in detail or "verified" in detail else "[yellow]INFO[/yellow]"
        if "Warning" in detail: status = "[yellow]WARN[/yellow]"
        table.add_row(status, detail)
        
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

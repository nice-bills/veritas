import requests
import os
import time
import json
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

load_dotenv()
console = Console()

BASE_URL = "http://localhost:8000"

def log_step(title):
    console.print(f"\n[bold cyan]--- {title} ---[/bold cyan]")

def test_api():
    console.print(Panel("Veritas API Battle Test", style="bold red"))

    # 1. Health Check
    log_step("1. Health Check")
    try:
        res = requests.get(f"{BASE_URL}/")
        console.print(f"Status: {res.status_code}")
        console.print(f"Response: {res.json()}")
        if res.status_code != 200:
            console.print("[red]FAILED: API is down[/red]")
            return
    except Exception as e:
        console.print(f"[red]FAILED: Could not connect. Is the server running?[/red] {e}")
        return

    # 2. Create Agent
    log_step("2. Create Agent")
    payload = {
        "name": "BattleTester",
        "brain_provider": "minimax",
        "network": "base-sepolia",
        "capabilities": ["wallet", "data", "social", "erc20"], # Load specific caps
        # Inject keys from env to simulate BYOK
        "minimax_api_key": os.getenv("MINIMAX_API_KEY"),
        "cdp_api_key_id": os.getenv("CDP_API_KEY_ID"),
        "cdp_api_key_secret": os.getenv("CDP_API_KEY_SECRET"),
        # Use the funded wallet
        "private_key": os.getenv("AGENT_PRIVATE_KEY")
    }
    
    res = requests.post(f"{BASE_URL}/agents", json=payload)
    if res.status_code != 200:
        console.print(f"[red]FAILED to create agent:[/red] {res.text}")
        return
        
    agent_data = res.json()
    agent_id = agent_data["id"]
    console.print(f"[green]SUCCESS:[/green] Created Agent {agent_id}")
    console.print(f"Address: {agent_data['address']}")

    # 3. Simple Mission
    log_step("3. Run Simple Mission (Wallet)")
    mission_payload = {"objective": "Check my wallet balance."}
    res = requests.post(f"{BASE_URL}/agents/{agent_id}/run", json=mission_payload)
    
    if res.status_code == 200:
        data = res.json()
        console.print(f"[green]SUCCESS:[/green] Mission Complete")
        console.print(f"Root: {data['session_root']}")
        console.print(f"Logs: {len(data['logs'])} events")
        # Verify specific tool usage
        tools_used = [l['tool_name'] for l in data['logs']]
        console.print(f"Tools Used: {tools_used}")
    else:
        console.print(f"[red]FAILED:[/red] {res.text}")

    # 4. Complex Mission (Data + Social)
    log_step("4. Run Complex Mission (Pyth + Twitter)")
    mission_payload = {
        "objective": "Get the current ETH price from Pyth (ID: 0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace). Then Tweet the price."
    }
    # Increase timeout for complex chain
    try:
        res = requests.post(f"{BASE_URL}/agents/{agent_id}/run", json=mission_payload, timeout=60)
        
        if res.status_code == 200:
            data = res.json()
            console.print(f"[green]SUCCESS:[/green] Complex Mission Complete")
            tools_used = [l['tool_name'] for l in data['logs']]
            console.print(f"Tools Used: {tools_used}")
            # Check if post_tweet was actually called
            if "post_tweet" in tools_used:
                console.print("[green]VERIFIED:[/green] Agent bridged Data -> Social")
            else:
                console.print("[yellow]WARNING:[/yellow] Agent failed to tweet")
        else:
            console.print(f"[red]FAILED:[/red] {res.text}")
    except Exception as e:
        console.print(f"[red]TIMEOUT/ERROR:[/red] {e}")

    # 5. Error Handling
    log_step("5. Test Invalid Agent ID")
    res = requests.post(f"{BASE_URL}/agents/fake-id-123/run", json={"objective": "hi"})
    if res.status_code == 404:
        console.print("[green]SUCCESS:[/green] Correctly handled 404")
    else:
        console.print(f"[red]FAILED:[/red] Expected 404, got {res.status_code}")

    # 6. Cleanup
    log_step("6. Cleanup / Shutdown")
    res = requests.delete(f"{BASE_URL}/agents/{agent_id}")
    if res.status_code == 200:
        console.print("[green]SUCCESS:[/green] Agent terminated")
    else:
        console.print(f"[red]FAILED:[/red] {res.text}")

if __name__ == "__main__":
    test_api()

import asyncio
import os
from veritas.agent import VeritasAgent
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()
console = Console()

async def main():
    console.print("[bold cyan]Veritas Phase B Dry Run[/bold cyan]")
    
    # 1. Initialize Agent
    # We use your persistent key if available
    key = os.getenv("AGENT_PRIVATE_KEY")
    agent = VeritasAgent(
        name="PhaseBAgent",
        brain_provider="minimax",
        network="base-sepolia",
        private_key=key
    )
    
    try:
        # 2. Run Mission
        objective = "Check balance and execute a test audit step."
        root = await agent.run_mission(objective)
        
        # 3. Automatic Attestation
        # This is what Phase B adds: the agent audits itself
        console.print("\n[bold cyan]Phase B: Self-Auditing...[/bold cyan]")
        tx_hash = await agent.attestor.attest_root(
            merkle_root=root,
            schema_uid="0x4ee2145e253098e581a38bdbb7f7c81eae64b6d9d5868063c71b562779056441",
            agent_id=agent.name
        )
        
        console.print(f"Mission Fingerprint Attested: [bold green]{tx_hash}[/bold green]")
        console.print(f"View on BaseScan: https://sepolia.basescan.org/tx/{tx_hash}")
        
    except Exception as e:
        console.print(f"[red]Demo failed:[/red] {e}")
    finally:
        await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

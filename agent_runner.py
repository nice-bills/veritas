import os
import json
import asyncio
from dotenv import load_dotenv
from eth_account import Account
from cdp import CdpClient
from veritas import VeritasLogger, VeritasAttestor, VeritasVerifier
from rich.console import Console
from rich.panel import Panel
import requests

# Setup
load_dotenv()
console = Console()

# Configuration
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
CDP_API_KEY_ID = os.getenv("CDP_API_KEY_ID")
CDP_API_KEY_SECRET = os.getenv("CDP_API_KEY_SECRET")
AGENT_PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")

# Constants
VAULT_ADDRESS = "0x000000000000000000000000000000000000dead" # Burn address for demo
SCHEMA_UID = "0x4ee2145e253098e581a38bdbb7f7c81eae64b6d9d5868063c71b562779056441"

class AuditedAgent:
    def __init__(self, private_key: str):
        self.account = Account.from_key(private_key)
        self.logger = VeritasLogger()
        self.client = CdpClient()
        console.print(f"Agent Booted: [bold green]{self.account.address}[/bold green]")

    def ask_minimax(self, prompt: str) -> str:
        """Consult the MiniMax brain."""
        url = "https://api.minimax.io/v1/chat/completions"
        headers = {"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "MiniMax-M2.1",
            "messages": [
                {"role": "system", "content": "You are a DeFi security agent. Output ONLY 'SECURE' or 'WAIT'."},
                {"role": "user", "content": prompt}
            ]
        }
        res = requests.post(url, headers=headers, json=payload).json()
        content = res['choices'][0]['message']['content']
        
        # Remove thinking block if present
        if "</think>" in content:
            content = content.split("</think>")[-1].strip()
            
        return content.strip()

    async def run_mission(self):
        console.print(Panel("Mission Started: Fund Protection Loop", title="Veritas Agent OS"))
        
        # Setup Web3 for Real Calls with Fallback
        from web3 import Web3
        rpc_urls = [
            "https://base-sepolia-rpc.publicnode.com",
            "https://sepolia.base.org"
        ]
        
        w3 = None
        for url in rpc_urls:
            temp_w3 = Web3(Web3.HTTPProvider(url))
            if temp_w3.is_connected():
                w3 = temp_w3
                console.print(f"Connected to RPC: {url}")
                break
        
        if not w3:
            console.print("[red]Error:[/red] Could not connect to any Base Sepolia RPC")
            return

        # 0. Bootstrapping: Ensure Funds
        console.print("Checking fuel status...")
        try:
            wei_bal = w3.eth.get_balance(self.account.address)
        except Exception:
            wei_bal = 0

        if wei_bal < w3.to_wei(0.005, 'ether'):
            console.print("Low fuel. Requesting from Base Sepolia faucet...")
            try:
                # Faucet call is one-way, we don't necessarily need to wait for clearing here
                # if we have retries on the next steps.
                await self.client.evm.request_faucet(
                    address=self.account.address,
                    network="base-sepolia",
                    token="eth"
                )
                console.print("Fuel requested. Waiting for arrival...")
                await asyncio.sleep(15)
            except Exception as e:
                console.print(f"Faucet skipped: {e}")

        # Ensure vault address is checksummed
        checksum_vault = w3.to_checksum_address(VAULT_ADDRESS)

        # 1. Observation: Check Balance
        @self.logger.wrap(event_type="OBSERVATION")
        def check_balance():
            wei = w3.eth.get_balance(self.account.address)
            eth = w3.from_wei(wei, 'ether')
            # Threshold: 0.0 (Force action)
            return {"ETH": float(eth), "Threshold": 0.0}

        balance_data = check_balance()
        obs_id = self.logger.last_event_id
        console.print(f"Observation Captured: {balance_data}")

        # 2. Thinking: MiniMax
        prompt = f"Current balance is {balance_data['ETH']} ETH. The safety threshold is {balance_data['Threshold']}. Should I SECURE funds (send small amount to vault) or WAIT? Output only SECURE or WAIT."
        decision = self.ask_minimax(prompt)
        console.print(f"MiniMax Decision: [bold cyan]{decision}[/bold cyan]")

        # 3. Action: Execute Trade/Transfer
        if "SECURE" in decision.upper():
            @self.logger.wrap(event_type="ACTION")
            def secure_funds(amount):
                console.print(f"   Executing Real Transfer of {amount} ETH to Vault...")
                
                tx = {
                    'to': checksum_vault,
                    'value': w3.to_wei(amount, 'ether'),
                    'gas': 21000,
                    'gasPrice': w3.eth.gas_price,
                    'nonce': w3.eth.get_transaction_count(self.account.address),
                    'chainId': 84532
                }
                
                signed_tx = w3.eth.account.sign_transaction(tx, self.account.key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                tx_hex = w3.to_hex(tx_hash)
                
                return {"status": "success", "tx_hash": tx_hex, "amount": amount}

            # Secure 10% of the threshold or a fixed tiny amount
            secure_funds(0.0001, basis_id=obs_id)
        else:
            console.print("Agent decided to wait.")

        # 4. Finalize & Attest
        console.print("\nFinalizing Session & Generating Proof...")
        proof_path = "agent_session.json"
        self.logger.export_proofs(proof_path)

        # 5. On-Chain Notary
        attestor = VeritasAttestor(self.client, self.account)
        try:
            tx_hash = await attestor.attest_root(
                merkle_root=self.logger.get_current_root(),
                schema_uid=SCHEMA_UID,
                agent_id="Veritas-Defender-01"
            )
            console.print(f"[bold green]Mission Attested![/bold green] Tx: {tx_hash}")
        except Exception as e:
            console.print(f"[red]Attestation Failed:[/red] {e}")

async def main():
    if not AGENT_PRIVATE_KEY:
        # Create a temp one if none provided
        temp_acc = Account.create()
        console.print(f"[yellow]Warning:[/yellow] No AGENT_PRIVATE_KEY in .env. Using temp: {temp_acc.address}")
        key = temp_acc.key.hex()
    else:
        key = AGENT_PRIVATE_KEY

    agent = AuditedAgent(key)
    await agent.run_mission()
    await agent.client.close()

if __name__ == "__main__":
    asyncio.run(main())

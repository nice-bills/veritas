from typing import Any, Dict, List, Optional
import os
import asyncio
from .logger import VeritasLogger
from .attestor import VeritasAttestor
from .brain import BrainFactory
from eth_account import Account
from cdp import CdpClient
from web3 import Web3

class VeritasAgent:
    """
    High-level agent abstraction that integrates LLM, Wallet, and Auditing.
    """
    
    def __init__(
        self, 
        name: str,
        brain_provider: str = "minimax",
        network: str = "base-sepolia",
        private_key: Optional[str] = None
    ):
        self.name = name
        self.network = network
        self.logger = VeritasLogger()
        
        # Brain
        self.brain = BrainFactory.create(brain_provider)
        
        # Identity
        if private_key:
            self.account = Account.from_key(private_key)
        else:
            self.account = Account.create()
            
        # Infrastructure
        self.client = CdpClient()
        self.attestor = VeritasAttestor(self.client, self.account, network_id=network)
        
        # RPC Setup
        rpc_urls = [
            "https://sepolia.base.org",
            "https://base-sepolia-rpc.publicnode.com"
        ]
        self.w3 = None
        for url in rpc_urls:
            temp_w3 = Web3(Web3.HTTPProvider(url))
            try:
                if temp_w3.is_connected():
                    self.w3 = temp_w3
                    print(f"[VeritasAgent] Connected to RPC: {url}")
                    break
            except Exception:
                continue
        
        if not self.w3:
            print("[VeritasAgent] Warning: Could not connect to any Base Sepolia RPC")
            # We don't raise error here to allow offline testing if needed
        
        print(f"[VeritasAgent] Initialized '{name}' on {network} | Address: {self.account.address}")

    async def shutdown(self):
        """Clean up connections."""
        await self.client.close()

    def execute_action(self, tool_name: str, func: callable, *args, **kwargs):
        """
        Execute a tool action with automatic logging and evidence linking.
        """
        basis_id = self.logger.last_event_id
        
        @self.logger.wrap(event_type="ACTION", tool_name=tool_name)
        def _exec():
            return func(*args, **kwargs)
            
        return _exec(basis_id=basis_id)

    async def run_mission(self, objective: str):
        """
        Execute a mission: Observe -> Think -> Act.
        Automatically logs and audits every step.
        """
        print(f"[VeritasAgent] Starting mission: {objective}")

        # 1. Observe (Example: Check balance)
        @self.logger.wrap(event_type="OBSERVATION", tool_name="check_balance")
        def check_balance():
            wei = self.w3.eth.get_balance(self.account.address)
            return {"balance_eth": float(self.w3.from_wei(wei, 'ether'))}

        state = check_balance()
        obs_id = self.logger.last_event_id
        print(f"[VeritasAgent] Observation: {state}")

        # 2. Think
        system_prompt = f"You are an agent named {self.name}. Objective: {objective}. Output only 'ACT' or 'WAIT'."
        user_prompt = f"Current State: {state}"
        
        decision = self.brain.think(system_prompt, user_prompt)
        print(f"[VeritasAgent] Brain Decision: {decision}")

        # 3. Act
        if "ACT" in decision.upper():
            def execute_step():
                return {"status": "success", "detail": "Action executed based on reasoning"}
            
            self.execute_action("execute_mission_step", execute_step)
        else:
            print("[VeritasAgent] Decided to wait.")

        # 4. Audit
        root = self.logger.get_current_root()
        print(f"[VeritasAgent] Session Root: {root}")
        return root

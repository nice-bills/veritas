from typing import Any, Dict, List, Optional, Callable
import os
import json
import asyncio
from .logger import VeritasLogger
from .attestor import VeritasAttestor
from .brain import BrainFactory
from .tools import (
    VeritasCapability, 
    VeritasTool, 
    WalletCapability, 
    TradeCapability,
    TokenCapability,
    ERC721Capability,
    BasenameCapability,
    SocialCapability,
    PaymentCapability,
    CreatorCapability,
    PrivacyCapability,
    AaveCapability,
    CompoundCapability,
    PythCapability,
    OnrampCapability
)
from eth_account import Account
from cdp import CdpClient
from web3 import Web3

class VeritasAgent:
    """
    High-level agent abstraction that integrates LLM, Wallet, and Auditing.
    """
    
    CHAIN_IDS = {
        "base-sepolia": 84532,
        "base-mainnet": 8453
    }

    def __init__(
        self, 
        name: str,
        brain_provider: str = "minimax",
        network: str = "base-sepolia",
        private_key: Optional[str] = None,
        cdp_api_key_id: Optional[str] = None,
        cdp_api_key_secret: Optional[str] = None,
        minimax_api_key: Optional[str] = None
    ):
        self.name = name
        self.network = network
        self.logger = VeritasLogger()
        self.capabilities: Dict[str, VeritasCapability] = {}
        self.tools: Dict[str, VeritasTool] = {}
        
        # Identity
        if private_key:
            self.account = Account.from_key(private_key)
        else:
            self.account = Account.create()
            
        # Infrastructure Setup
        # We pass keys directly to CdpClient to avoid polluting global os.environ
        # and to ensure thread-safety for multiple users with different keys.
        self.client_credentials = {}
        if cdp_api_key_id and cdp_api_key_secret:
            self.client_credentials = {
                "api_key_name": cdp_api_key_id,
                "private_key": cdp_api_key_secret
            }
        
        self.brain = BrainFactory.create(brain_provider, api_key=minimax_api_key)
        
        # Initialize CDP Client with explicit keys if provided
        if self.client_credentials:
            self.client = CdpClient.configure(**self.client_credentials)
        else:
            # Fallback to env vars (for local dev)
            self.client = CdpClient()

        self.attestor = VeritasAttestor(self.client, self.account, network_id=network)
        
        # RPC Setup
        rpc_urls = [
            "https://base-sepolia.drpc.org",
            "https://84532.rpc.thirdweb.com",
            "https://base-sepolia-rpc.publicnode.com"
        ]
        self.w3 = None
        for url in rpc_urls:
            temp_w3 = Web3(Web3.HTTPProvider(url))
            try:
                if temp_w3.is_connected():
                    self.w3 = temp_w3
                    break
            except Exception:
                continue
        
        if not self.w3:
            raise ConnectionError(f"Could not connect to any RPC for network: {network}")
        
        print(f"[VeritasAgent] Initialized '{name}' on {network} | Address: {self.account.address}")

    def _validate_credentials(self):
        """Ensure all required API keys are present."""
        required = ["CDP_API_KEY_ID", "CDP_API_KEY_SECRET", "MINIMAX_API_KEY"]
        missing = [k for k in required if not os.getenv(k)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    def load_capability(self, capability: VeritasCapability):
        """Register a capability and its tools with the agent."""
        self.capabilities[capability.name] = capability
        for tool in capability.get_tools():
            self.tools[tool.name] = tool
        print(f"[VeritasAgent] Loaded capability: {capability.name}")

    async def call_tool(self, tool_name: str, **kwargs):
        """Execute a tool by name with automatic auditing."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        tool = self.tools[tool_name]
        return await self.execute_action(tool_name, tool.func, **kwargs)

    async def shutdown(self):
        """Clean up connections."""
        if hasattr(self.client, 'close'):
            await self.client.close()

    async def execute_action(self, tool_name: str, func: Callable, *args, **kwargs):
        """Execute a tool action with automatic logging."""
        basis_id = self.logger.last_event_id
        wrapped = self.logger.wrap(func, tool_name=tool_name, event_type="ACTION")
        
        import inspect
        if inspect.iscoroutinefunction(wrapped):
            return await wrapped(*args, basis_id=basis_id, **kwargs)
        else:
            return wrapped(*args, basis_id=basis_id, **kwargs)

    async def run_mission(self, objective: str, max_steps: int = 5):
        """Execute a mission autonomously: Observe -> Think -> Act (Loop)."""
        print(f"[VeritasAgent] Starting autonomous mission: {objective}")
        
        current_step = 0
        while current_step < max_steps:
            current_step += 1
            print(f"\n[VeritasAgent] --- Step {current_step} ---")

            tool_descriptions = [
                {"name": t.name, "description": t.description, "parameters": t.parameters}
                for t in self.tools.values()
            ]
            recent_logs = [log.model_dump(mode='json') for log in self.logger.get_logs()[-3:]]
            
            system_prompt = f"""You are an autonomous crypto agent named {self.name}.
Objective: {objective}

AVAILABLE TOOLS:
{json.dumps(tool_descriptions, indent=2)}

INSTRUCTIONS:
1. Analyze the current state and history.
2. Decide the next tool to call.
3. Output ONLY a valid JSON object in this format. Do not include any other text.
{{
  "thought": "your reasoning",
  "tool": "tool_name",
  "params": {{ "param_name": "value" }},
  "finished": true/false
}}
If you need to check a balance, use 'get_balance'.
If you need a Pyth Price Feed ID:
- ETH/USD: 0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace"""

            user_prompt = f"History: {json.dumps(recent_logs)}"
            
            # 2. Think (Async)
            response_text = await self.brain.think(system_prompt, user_prompt)
            print(f"[VeritasAgent] Brain Thought: {response_text}")
            
            # Log the thought
            try:
                self.logger.log_action("Brain", {"objective": objective}, response_text, event_type="THOUGHT", basis_id=self.logger.last_event_id)
            except Exception as e:
                print(f"[VeritasAgent] Logging Failed: {e}")
            
            try:
                clean_json = response_text.strip()
                if "```" in clean_json:
                    clean_json = clean_json.split("```json")[-1].split("```")[0]
                
                start_idx, end_idx = clean_json.find('{'), clean_json.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    clean_json = clean_json[start_idx:end_idx+1]
                
                decision = json.loads(clean_json)
            except Exception as e:
                print(f"[VeritasAgent] Failed to parse decision: {e}")
                self.logger.log_action("System", {"error": str(e), "raw": response_text}, "JSON Parsing Failed", event_type="ERROR")
                break

            if decision.get("finished"):
                print("[VeritasAgent] Objective reached.")
                break
                
            tool_name = decision.get("tool")
            if tool_name and tool_name in self.tools:
                params = decision.get("params", {})
                print(f"[VeritasAgent] Executing tool: {tool_name}")
                await self.call_tool(tool_name, **params)
            else:
                print(f"[VeritasAgent] Invalid tool: {tool_name}")

        root = self.logger.get_current_root()
        print(f"\n[VeritasAgent] Mission Terminated. Session Root: {root}")
        return root

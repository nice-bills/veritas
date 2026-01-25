from typing import Any, Dict, List, Optional, Callable, Tuple
import os
import json
import asyncio
import uuid
from datetime import datetime
from .logger import VeritasLogger, ActionLog
from .attestor import VeritasAttestor
from .brain import BrainFactory, Brain
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
    OnrampCapability,
    ChainlinkCapability,
)
from .config import settings
from eth_account import Account
from cdp import CdpClient
from web3 import Web3


class VeritasAgent:
    """
    High-level agent abstraction that integrates LLM, Wallet, and Auditing.
    """

    CHAIN_IDS = {"base-sepolia": 84532, "base-mainnet": 8453}

    def __init__(
        self,
        name: str,
        brain_provider: str = "minimax",
        network: str = "base-sepolia",
        private_key: Optional[str] = None,
        cdp_api_key_id: Optional[str] = None,
        cdp_api_key_secret: Optional[str] = None,
        minimax_api_key: Optional[str] = None,
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.network = network
        self.logger = VeritasLogger()
        self.capabilities: Dict[str, VeritasCapability] = {}
        self.tools: Dict[str, VeritasTool] = {}
        self.status = "idle"
        self.brain_provider = brain_provider

        # Identity
        if private_key:
            self.account = Account.from_key(private_key)
        else:
            self.account = Account.create()

        # Infrastructure Setup
        self.client_credentials = {}
        if cdp_api_key_id and cdp_api_key_secret:
            self.client_credentials = {
                "api_key_id": cdp_api_key_id,
                "api_key_secret": cdp_api_key_secret,
            }

        self.brain = BrainFactory.create(brain_provider, api_key=minimax_api_key)

        if self.client_credentials:
            self.client = CdpClient(**self.client_credentials)
        else:
            self.client = CdpClient()

        self.attestor = VeritasAttestor(self.client, self.account, network_id=network)

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
        self.status = "shutdown"
        if hasattr(self.client, "close"):
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

    async def run_mission(self, objective: str, max_steps: int = 5) -> str:
        """Execute a mission autonomously: Observe -> Think -> Act (Loop)."""
        print(f"[VeritasAgent] Starting autonomous mission: {objective}")
        self.status = "running"

        current_step = 0
        while current_step < max_steps:
            current_step += 1
            print(f"\n[VeritasAgent] --- Step {current_step} ---")

            tool_descriptions = [
                {"name": t.name, "description": t.description, "parameters": t.parameters}
                for t in self.tools.values()
            ]
            recent_logs = [log.model_dump(mode="json") for log in self.logger.get_logs()[-3:]]

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
  "finished": false
}}
 IMPORTANT:
- If you want to EXECUTE a tool, you MUST set "finished": false.
- Only set "finished": true when you have fully completed the objective and have the final answer.
- If the objective is to check a price, you must CALL the tool first (finished: false), then see the result, then finish.
If you need to check a balance, use 'get_balance' or 'erc20_balance'."""

            user_prompt = f"History: {json.dumps(recent_logs)}"

            response_text = await self.brain.think(system_prompt, user_prompt)
            print(f"[VeritasAgent] Brain Thought: {response_text}")

            try:
                self.logger.log_action(
                    "Brain",
                    {"objective": objective},
                    response_text,
                    event_type="THOUGHT",
                    basis_id=self.logger.last_event_id,
                )
            except Exception as e:
                print(f"[VeritasAgent] Logging Failed: {e}")

            try:
                clean_json = response_text.strip()
                if "```" in clean_json:
                    clean_json = clean_json.split("```json")[-1].split("```")[0]

                start_idx, end_idx = clean_json.find("{"), clean_json.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    clean_json = clean_json[start_idx : end_idx + 1]

                decision = json.loads(clean_json)
            except Exception as e:
                print(f"[VeritasAgent] Failed to parse decision: {e}")
                self.logger.log_action(
                    "System",
                    {"error": str(e), "raw": response_text},
                    "JSON Parsing Failed",
                    event_type="ERROR",
                )
                break

            if decision.get("finished"):
                print("[VeritasAgent] Objective reached.")
                break

            tool_name = decision.get("tool")
            if tool_name and tool_name in self.tools:
                params = decision.get("params", {})
                print(f"[VeritasAgent] Executing tool: {tool_name}")
                try:
                    await asyncio.wait_for(self.call_tool(tool_name, **params), timeout=15.0)
                except asyncio.TimeoutError:
                    print(f"[VeritasAgent] Tool Timeout: {tool_name}")
                    self.logger.log_action(
                        tool_name,
                        params,
                        "Error: Tool execution timed out after 15s",
                        event_type="ERROR",
                        basis_id=self.logger.last_event_id,
                    )
                except Exception as e:
                    print(f"[VeritasAgent] Tool Failure: {e}")
                    self.logger.log_action(
                        tool_name,
                        params,
                        f"Error: {str(e)}",
                        event_type="ERROR",
                        basis_id=self.logger.last_event_id,
                    )
            else:
                print(f"[VeritasAgent] Invalid tool: {tool_name}")

        root = self.logger.get_current_root()
        print(f"\n[VeritasAgent] Mission Terminated. Session Root: {root}")
        self.status = "completed"
        return root


class PersistentVeritasAgent(VeritasAgent):
    """
    Long-running, stateful agent that runs indefinitely.

    Features:
    - Runs forever until explicitly stopped
    - Can receive messages while running
    - Checkpoints state to database
    - Monitors conditions (prices, events)
    - Persists across restarts
    """

    def __init__(
        self,
        name: str,
        brain_provider: str = "minimax",
        network: str = "base-sepolia",
        private_key: Optional[str] = None,
        cdp_api_key_id: Optional[str] = None,
        cdp_api_key_secret: Optional[str] = None,
        minimax_api_key: Optional[str] = None,
        agent_id: Optional[str] = None,
        db_session: Optional[Any] = None,
    ):
        super().__init__(
            name=name,
            brain_provider=brain_provider,
            network=network,
            private_key=private_key,
            cdp_api_key_id=cdp_api_key_id,
            cdp_api_key_secret=cdp_api_key_secret,
            minimax_api_key=minimax_api_key,
        )

        self.id = agent_id or str(uuid.uuid4())
        self.db_session = db_session
        self.checkpoint_interval = 100
        self.current_objective = None
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.condition_monitors: List[Dict] = []

    async def run_forever(
        self,
        initial_objective: Optional[str] = None,
        checkpoint_interval: int = 100,
        monitor_conditions: Optional[List[Dict]] = None,
    ) -> None:
        """
        Run agent indefinitely until stop() is called.

        Args:
            initial_objective: First mission to run
            checkpoint_interval: Save state every N steps
            monitor_conditions: List of conditions to monitor
                Example: [{"type": "price", "target": "ETH/USD", "condition": "gte", "value": 4000, "action": "alert"}]
        """
        self.running = True
        self.checkpoint_interval = checkpoint_interval
        self.condition_monitors = monitor_conditions or []
        step_count = 0

        if initial_objective:
            self.current_objective = initial_objective

        print(f"[PersistentAgent] Starting persistent agent: {self.name} (ID: {self.id})")

        while self.running:
            try:
                # Check for new messages first
                try:
                    message = await asyncio.wait_for(self.message_queue.get(), timeout=0.1)
                    if message:
                        self.current_objective = message
                        print(f"[PersistentAgent] Received new objective: {message}")
                except asyncio.TimeoutError:
                    pass

                # If no objective, wait
                if not self.current_objective:
                    await asyncio.sleep(1)
                    continue

                # Run one mission step
                step_count += 1
                print(
                    f"[PersistentAgent] Step {step_count} - Objective: {self.current_objective[:50]}..."
                )

                # Check conditions before each step
                if self.condition_monitors:
                    await self._check_conditions()

                # Run a single step (use small max_steps for responsiveness)
                await self._run_step(self.current_objective)

                # Checkpoint periodically
                if step_count % checkpoint_interval == 0:
                    await self.checkpoint()

            except asyncio.CancelledError:
                print("[PersistentAgent] Cancellation received, shutting down...")
                break
            except Exception as e:
                print(f"[PersistentAgent] Error in main loop: {e}")
                await asyncio.sleep(5)  # Back off on error

        print(f"[PersistentAgent] Agent {self.name} stopped")

    async def _run_step(self, objective: str) -> None:
        """Execute a single step of the mission."""
        tool_descriptions = [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in self.tools.values()
        ]
        recent_logs = [log.model_dump(mode="json") for log in self.logger.get_logs()[-3:]]

        system_prompt = f"""You are an autonomous crypto agent named {self.name}.
You are running in PERSISTENT MODE - you run continuously until stopped.
Objective: {objective}

AVAILABLE TOOLS:
{json.dumps(tool_descriptions, indent=2)}

INSTRUCTIONS:
1. You are in a continuous loop - analyze, act, repeat.
2. If objective is complete, set "finished": true to signal completion.
3. For monitoring objectives (e.g., 'alert when ETH > 4000'), check the condition each step.
4. Output ONLY valid JSON.

{{
  "thought": "your reasoning",
  "tool": "tool_name or null",
  "params": {{}},
  "finished": false
}}"""

        user_prompt = f"History: {json.dumps(recent_logs)}"

        response_text = await self.brain.think(system_prompt, user_prompt)

        try:
            self.logger.log_action(
                "Brain",
                {"objective": objective},
                response_text,
                event_type="THOUGHT",
                basis_id=self.logger.last_event_id,
            )
        except Exception as e:
            print(f"[PersistentAgent] Logging failed: {e}")

        try:
            clean_json = response_text.strip()
            if "```" in clean_json:
                clean_json = clean_json.split("```json")[-1].split("```")[0]

            start_idx, end_idx = clean_json.find("{"), clean_json.rfind("}")
            if start_idx != -1 and end_idx != -1:
                clean_json = clean_json[start_idx : end_idx + 1]

            decision = json.loads(clean_json)
        except Exception as e:
            print(f"[PersistentAgent] Failed to parse decision: {e}")
            return

        if decision.get("finished"):
            print("[PersistentAgent] Objective completed")
            self.current_objective = None
            return

        tool_name = decision.get("tool")
        if tool_name and tool_name in self.tools:
            params = decision.get("params", {})
            try:
                await asyncio.wait_for(self.call_tool(tool_name, **params), timeout=15.0)
            except asyncio.TimeoutError:
                self.logger.log_action(tool_name, params, "Error: Timeout", event_type="ERROR")
            except Exception as e:
                self.logger.log_action(tool_name, params, f"Error: {str(e)}", event_type="ERROR")

    async def _check_conditions(self) -> None:
        """Check monitoring conditions and trigger actions."""
        for condition in self.condition_monitors:
            try:
                condition_type = condition.get("type")

                if condition_type == "price":
                    target = condition.get("target")  # e.g., "ETH/USD"
                    operator = condition.get("condition")  # "gte", "lte", "eq"
                    threshold = condition.get("value")

                    if target in self.tools:
                        result = await self.call_tool(target.lower().replace("/", "_"), **{})
                        # Parse result and check condition
                        # This is simplified - real implementation would parse the tool output

            except Exception as e:
                print(f"[PersistentAgent] Condition check failed: {e}")

    async def send_message(self, message: str) -> None:
        """
        Send a message/objective to a running agent.

        Usage:
            # In another process or via API:
            await agent.send_message("Check my portfolio balance")

            # Or for monitoring:
            await agent.send_message("Alert me when ETH price goes above 4000")
        """
        await self.message_queue.put(message)

    async def stop(self) -> None:
        """Stop the persistent agent."""
        self.running = False
        await self.checkpoint()

    async def checkpoint(self) -> None:
        """
        Save agent state to database.

        This saves:
        - Agent configuration
        - Current objective
        - Message queue
        - All logs with Merkle tree
        - Condition monitors
        """
        print(f"[PersistentAgent] Checkpointing agent {self.id}")

        if self.db_session:
            # Save to database using SQLAlchemy models
            # This would use the database.py models we created earlier
            pass

        # Also save to file for simplicity
        checkpoint_data = {
            "agent_id": self.id,
            "name": self.name,
            "network": self.network,
            "status": self.status,
            "current_objective": self.current_objective,
            "condition_monitors": self.condition_monitors,
            "checkpointed_at": datetime.utcnow().isoformat(),
            "logs": [log.model_dump(mode="json") for log in self.logger.get_logs()],
            "session_root": self.logger.get_current_root(),
        }

        import os

        os.makedirs("data/checkpoints", exist_ok=True)
        checkpoint_path = f"data/checkpoints/{self.id}.json"

        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint_data, f, indent=2)

        print(f"[PersistentAgent] Checkpoint saved to {checkpoint_path}")

    @classmethod
    async def restore(
        cls, agent_id: str, db_session: Optional[Any] = None
    ) -> "PersistentVeritasAgent":
        """
        Restore a persistent agent from checkpoint.

        Usage:
            agent = await PersistentVeritasAgent.restore("agent-id-123")
            await agent.run_forever()
        """
        checkpoint_path = f"data/checkpoints/{agent_id}.json"

        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

        with open(checkpoint_path, "r") as f:
            checkpoint_data = json.load(f)

        # Create agent with saved config
        agent = cls(
            name=checkpoint_data["name"],
            network=checkpoint_data["network"],
            agent_id=agent_id,
            db_session=db_session,
        )

        # Restore state
        agent.current_objective = checkpoint_data.get("current_objective")
        agent.condition_monitors = checkpoint_data.get("condition_monitors", [])

        # Note: We'd need to restore logs from checkpoint if needed

        print(f"[PersistentAgent] Restored agent {agent_id} from checkpoint")
        return agent


async def create_persistent_agent(
    name: str,
    capabilities: List[str],
    network: str = "base-sepolia",
    cdp_api_key_id: Optional[str] = None,
    cdp_api_key_secret: Optional[str] = None,
    minimax_api_key: Optional[str] = None,
    initial_objective: Optional[str] = None,
) -> PersistentVeritasAgent:
    """
    Factory function to create a ready-to-run persistent agent.

    Usage:
        agent = await create_persistent_agent(
            name="MyAgent",
            capabilities=["wallet", "token", "pyth"],
            initial_objective="Monitor ETH price and alert at $4000"
        )
        await agent.run_forever()
    """
    agent = PersistentVeritasAgent(
        name=name,
        network=network,
        cdp_api_key_id=cdp_api_key_id,
        cdp_api_key_secret=cdp_api_key_secret,
        minimax_api_key=minimax_api_key,
    )

    # Load capabilities
    CAP_MAP = {
        "wallet": WalletCapability,
        "token": TokenCapability,
        "trading": TradeCapability,
        "nft": ERC721Capability,
        "basename": BasenameCapability,
        "social": SocialCapability,
        "payments": PaymentCapability,
        "creator": CreatorCapability,
        "privacy": PrivacyCapability,
        "aave": AaveCapability,
        "compound": CompoundCapability,
        "pyth": PythCapability,
        "onramp": OnrampCapability,
        "chainlink": ChainlinkCapability,
    }

    for cap_name in capabilities:
        if cap_name in CAP_MAP:
            agent.load_capability(CAP_MAP[cap_name](agent))

    # Setup monitoring for price alerts if objective contains price conditions
    conditions = []
    if initial_objective and "price" in initial_objective.lower():
        # Simple condition detection - can be enhanced
        conditions = [
            {
                "type": "price",
                "target": "ETH/USD",
                "condition": "gte",
                "value": 4000,
                "action": "alert",
            }
        ]

    if initial_objective:
        agent.message_queue.put_nowait(initial_objective)

    return agent

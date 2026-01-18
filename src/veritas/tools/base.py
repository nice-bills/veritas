from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

class VeritasTool(BaseModel):
    """
    Definition of a single tool available to an agent.
    """
    name: str
    description: str
    func: Callable = Field(exclude=True) # The actual function to execute
    parameters: Dict[str, Any] # JSON Schema of parameters for the LLM

class VeritasCapability:
    """
    A collection of related tools (e.g. Wallet, Trading, Social).
    """
    def __init__(self, name: str):
        self.name = name
        self.tools: List[VeritasTool] = []

    def get_tools(self) -> List[VeritasTool]:
        return self.tools

class WalletCapability(VeritasCapability):
    """
    Basic wallet operations: balance, transfer.
    """
    def __init__(self, agent: Any):
        super().__init__("wallet")
        self.agent = agent
        
        # Add Balance Tool
        self.tools.append(VeritasTool(
            name="get_balance",
            description="Get the current ETH balance of the agent's wallet.",
            func=self.get_balance,
            parameters={"type": "object", "properties": {}}
        ))

    def get_balance(self) -> Dict[str, Any]:
        wei = self.agent.w3.eth.get_balance(self.agent.account.address)
        eth = self.agent.w3.from_wei(wei, 'ether')
        return {"balance_eth": float(eth), "address": self.agent.account.address}

class TradeCapability(VeritasCapability):
    """
    Advanced trading operations: swaps, price quotes.
    Uses the VeritasAdapter to wrap CDP SDK actions.
    """
    def __init__(self, agent: Any):
        super().__init__("trading")
        self.agent = agent
        from .adapter import VeritasAdapter # This will now be relative
        
        # 1. Price Quote Tool
        self.tools.append(VeritasAdapter.to_tool(
            agent=self.agent,
            func=self.agent.client.evm.get_swap_price,
            name="get_swap_price",
            description="Get a price quote for swapping two tokens.",
            parameters={
                "type": "object",
                "properties": {
                    "from_token": {"type": "string", "description": "Token to swap from"},
                    "to_token": {"type": "string", "description": "Token to swap to"},
                    "amount": {"type": "string", "description": "Amount to swap"}
                },
                "required": ["from_token", "to_token", "amount"]
            }
        ))

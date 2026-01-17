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

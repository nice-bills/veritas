from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal

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
    Basic wallet operations: balance, native transfer, details.
    """
    def __init__(self, agent: Any):
        super().__init__("wallet")
        self.agent = agent
        
        # Get Wallet Details
        self.tools.append(VeritasTool(
            name="get_wallet_details",
            description="Get details of the connected wallet (address, network, balance).",
            func=self.get_wallet_details,
            parameters={"type": "object", "properties": {}}
        ))

        # Get Native Balance
        self.tools.append(VeritasTool(
            name="get_balance",
            description="Get the native currency balance (ETH) of the wallet.",
            func=self.get_balance,
            parameters={"type": "object", "properties": {}}
        ))

        # Native Transfer
        self.tools.append(VeritasTool(
            name="native_transfer",
            description="Transfer native tokens (ETH) to another address.",
            func=self.native_transfer,
            parameters={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Destination address"},
                    "value": {"type": "string", "description": "Amount to transfer in whole units (e.g. '0.5')"}
                },
                "required": ["to", "value"]
            }
        ))

    def get_wallet_details(self) -> str:
        addr = self.agent.account.address
        net = self.agent.network
        bal_data = self.get_balance()
        bal = bal_data['balance_eth']
        return f"""Wallet Details:
- Address: {addr}
- Network: {net}
- Native Balance: {bal} ETH"""

    def get_balance(self) -> Dict[str, Any]:
        wei = self.agent.w3.eth.get_balance(self.agent.account.address)
        eth = self.agent.w3.from_wei(wei, 'ether')
        return {"balance_eth": float(eth), "address": self.agent.account.address}

    def native_transfer(self, to: str, value: str) -> str:
        w3 = self.agent.w3
        wei_value = w3.to_wei(Decimal(value), 'ether')
        
        # Determine chainId from network string
        network_id = getattr(self.agent, 'network', 'base-sepolia')
        chain_id = 84532 if 'sepolia' in network_id else 8453
        
        tx = {
            'to': w3.to_checksum_address(to),
            'value': wei_value,
            'gas': 21000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(self.agent.account.address),
            'chainId': chain_id
        }
        
        signed = w3.eth.account.sign_transaction(tx, self.agent.account.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        return f"Transferred {value} ETH to {to}. Hash: {w3.to_hex(tx_hash)}"

class TradeCapability(VeritasCapability):
    """
    Advanced trading operations: swaps, price quotes.
    Uses the VeritasAdapter to wrap CDP SDK actions.
    """
    def __init__(self, agent: Any):
        super().__init__("trading")
        self.agent = agent
        from veritas.adapter import VeritasAdapter 
        
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
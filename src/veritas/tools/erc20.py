from typing import Any, Dict
from .base import VeritasCapability, VeritasTool
from ..abis import ERC20_ABI

class ERC20Capability(VeritasCapability):
    """
    Interact with ERC20 tokens (Transfer, Balance).
    """
    def __init__(self, agent: Any):
        super().__init__("erc20")
        self.agent = agent
        
        self.tools.append(VeritasTool(
            name="erc20_balance",
            description="Get balance of a specific ERC20 token.",
            func=self.get_balance,
            parameters={
                "type": "object",
                "properties": {
                    "token_address": {"type": "string", "description": "Contract address of the token"}
                },
                "required": ["token_address"]
            }
        ))
        
        self.tools.append(VeritasTool(
            name="erc20_transfer",
            description="Transfer ERC20 tokens to another address.",
            func=self.transfer,
            parameters={
                "type": "object",
                "properties": {
                    "token_address": {"type": "string"},
                    "to_address": {"type": "string"},
                    "amount": {"type": "number", "description": "Amount in human-readable units (e.g. 1.5)"}
                },
                "required": ["token_address", "to_address", "amount"]
            }
        ))

    def get_balance(self, token_address: str) -> Dict[str, Any]:
        w3 = self.agent.w3
        contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
        
        balance = contract.functions.balanceOf(self.agent.account.address).call()
        decimals = contract.functions.decimals().call()
        symbol = contract.functions.symbol().call()
        
        readable = balance / (10 ** decimals)
        return {"symbol": symbol, "balance": readable, "raw": balance}

    def transfer(self, token_address: str, to_address: str, amount: float) -> Dict[str, Any]:
        w3 = self.agent.w3
        contract = w3.eth.contract(address=w3.to_checksum_address(token_address), abi=ERC20_ABI)
        decimals = contract.functions.decimals().call()
        
        # Convert to raw units
        raw_amount = int(amount * (10 ** decimals))
        
        tx = contract.functions.transfer(
            w3.to_checksum_address(to_address),
            raw_amount
        ).build_transaction({
            'chainId': 84532, # Base Sepolia (todo: dynamic)
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(self.agent.account.address),
            'from': self.agent.account.address
        })
        
        signed = w3.eth.account.sign_transaction(tx, self.agent.account.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        
        return {"status": "success", "tx_hash": w3.to_hex(tx_hash), "amount": amount}

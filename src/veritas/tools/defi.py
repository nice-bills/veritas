from typing import Any, Dict
from web3 import Web3
from .base import VeritasCapability, VeritasTool
from .constants import (
    AAVE_POOL_ABI, AAVE_POOL_ADDRESSES,
    COMET_ABI, COMET_ADDRESSES,
    TOKEN_ADDRESSES_BY_SYMBOLS
)
from decimal import Decimal

class AaveCapability(VeritasCapability):
    """
    Interact with Aave V3 (Supply, Withdraw, Borrow, Repay).
    """
    def __init__(self, agent: Any):
        super().__init__("aave")
        self.agent = agent
        
        self.tools.append(VeritasTool(
            name="aave_supply",
            description="Supply assets to Aave V3.",
            func=self.supply,
            parameters={
                "type": "object",
                "properties": {
                    "asset_symbol": {"type": "string", "description": "Asset symbol (e.g. USDC, WETH)"},
                    "amount": {"type": "string", "description": "Amount to supply"}
                },
                "required": ["asset_symbol", "amount"]
            }
        ))
        
        self.tools.append(VeritasTool(
            name="aave_withdraw",
            description="Withdraw assets from Aave V3.",
            func=self.withdraw,
            parameters={
                "type": "object",
                "properties": {
                    "asset_symbol": {"type": "string"},
                    "amount": {"type": "string"}
                },
                "required": ["asset_symbol", "amount"]
            }
        ))

    def _get_pool_contract(self):
        network_id = getattr(self.agent, 'network', 'base-mainnet')
        address = AAVE_POOL_ADDRESSES.get(network_id)
        if not address:
            raise ValueError(f"Aave not supported on {network_id}")
        return self.agent.w3.eth.contract(address=self.agent.w3.to_checksum_address(address), abi=AAVE_POOL_ABI)

    def _get_asset_address(self, symbol: str) -> str:
        network_id = getattr(self.agent, 'network', 'base-mainnet')
        tokens = TOKEN_ADDRESSES_BY_SYMBOLS.get(network_id, {})
        addr = tokens.get(symbol.upper())
        if not addr:
            raise ValueError(f"Token {symbol} not found on {network_id}")
        return addr

    def supply(self, asset_symbol: str, amount: str) -> Dict[str, Any]:
        contract = self._get_pool_contract()
        asset_addr = self._get_asset_address(asset_symbol)
        
        # TODO: Need decimals here. Assuming 18 for now, but USDC is 6.
        # Ideally we fetch decimals from the token contract first.
        # For MVP, we'll try to guess or use a standard helper if we had one.
        decimals = 6 if asset_symbol.upper() in ["USDC", "USDT"] else 18
        raw_amount = int(Decimal(amount) * (10 ** decimals))
        
        tx = contract.functions.supply(
            self.agent.w3.to_checksum_address(asset_addr),
            raw_amount,
            self.agent.account.address,
            0
        ).build_transaction({
            'chainId': 8453, # TODO: Dynamic
            'gas': 300000,
            'gasPrice': self.agent.w3.eth.gas_price,
            'nonce': self.agent.w3.eth.get_transaction_count(self.agent.account.address),
            'from': self.agent.account.address
        })
        
        signed = self.agent.w3.eth.account.sign_transaction(tx, self.agent.account.key)
        tx_hash = self.agent.w3.eth.send_raw_transaction(signed.raw_transaction)
        
        return {"status": "success", "action": "supply", "tx_hash": self.agent.w3.to_hex(tx_hash)}

    def withdraw(self, asset_symbol: str, amount: str) -> Dict[str, Any]:
        contract = self._get_pool_contract()
        asset_addr = self._get_asset_address(asset_symbol)
        decimals = 6 if asset_symbol.upper() in ["USDC", "USDT"] else 18
        raw_amount = int(Decimal(amount) * (10 ** decimals))
        
        tx = contract.functions.withdraw(
            self.agent.w3.to_checksum_address(asset_addr),
            raw_amount,
            self.agent.account.address
        ).build_transaction({
            'chainId': 8453,
            'gas': 300000,
            'gasPrice': self.agent.w3.eth.gas_price,
            'nonce': self.agent.w3.eth.get_transaction_count(self.agent.account.address),
            'from': self.agent.account.address
        })
        
        signed = self.agent.w3.eth.account.sign_transaction(tx, self.agent.account.key)
        tx_hash = self.agent.w3.eth.send_raw_transaction(signed.raw_transaction)
        
        return {"status": "success", "action": "withdraw", "tx_hash": self.agent.w3.to_hex(tx_hash)}

class CompoundCapability(VeritasCapability):
    """
    Interact with Compound V3 (Comet).
    """
    def __init__(self, agent: Any):
        super().__init__("compound")
        self.agent = agent
        
        self.tools.append(VeritasTool(
            name="compound_supply",
            description="Supply assets to Compound V3.",
            func=self.supply,
            parameters={
                "type": "object",
                "properties": {
                    "asset_symbol": {"type": "string"},
                    "amount": {"type": "string"}
                },
                "required": ["asset_symbol", "amount"]
            }
        ))

    def supply(self, asset_symbol: str, amount: str) -> Dict[str, Any]:
        network_id = getattr(self.agent, 'network', 'base-mainnet')
        comet_addr = COMET_ADDRESSES.get(network_id)
        if not comet_addr:
            return {"error": f"Compound not supported on {network_id}"}
            
        contract = self.agent.w3.eth.contract(address=self.agent.w3.to_checksum_address(comet_addr), abi=COMET_ABI)
        
        # Similar logic for asset address and decimals
        tokens = TOKEN_ADDRESSES_BY_SYMBOLS.get(network_id, {})
        asset_addr = tokens.get(asset_symbol.upper())
        decimals = 6 if asset_symbol.upper() == "USDC" else 18
        raw_amount = int(Decimal(amount) * (10 ** decimals))
        
        tx = contract.functions.supply(
            self.agent.w3.to_checksum_address(asset_addr),
            raw_amount
        ).build_transaction({
            'chainId': 8453,
            'gas': 200000,
            'gasPrice': self.agent.w3.eth.gas_price,
            'nonce': self.agent.w3.eth.get_transaction_count(self.agent.account.address),
            'from': self.agent.account.address
        })
        
        signed = self.agent.w3.eth.account.sign_transaction(tx, self.agent.account.key)
        tx_hash = self.agent.w3.eth.send_raw_transaction(signed.raw_transaction)
        
        return {"status": "success", "protocol": "Compound", "tx_hash": self.agent.w3.to_hex(tx_hash)}
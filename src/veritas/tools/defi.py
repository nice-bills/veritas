import asyncio
from typing import Any, Dict
from .base import VeritasCapability, VeritasTool
from .constants import (
    AAVE_POOL_ABI,
    AAVE_POOL_ADDRESSES,
    COMET_ABI,
    COMET_ADDRESSES,
    TOKEN_ADDRESSES_BY_SYMBOLS,
    ERC20_ABI,
)
from decimal import Decimal


class DeFiCapability(VeritasCapability):
    """
    Base class for DeFi protocols with shared safety features.
    """

    def __init__(self, name: str, agent: Any):
        super().__init__(name)
        self.agent = agent

    async def _get_decimals(self, token_address: str) -> int:
        """Fetch decimals from the ERC20 contract."""
        try:
            contract = self.agent.w3.eth.contract(
                address=self.agent.w3.to_checksum_address(token_address), abi=ERC20_ABI
            )
            return await asyncio.to_thread(contract.functions.decimals().call)
        except Exception:
            return 18  # Fallback

    async def _simulate_and_send(self, tx_params: dict) -> str:
        """Simulate a transaction and then sign/send if successful."""
        w3 = self.agent.w3

        # 1. Simulate
        try:
            await asyncio.to_thread(w3.eth.call, tx_params)
        except Exception as e:
            raise Exception(f"Transaction simulation failed: {e}")

        # 2. Build remaining params
        gas_price = await asyncio.to_thread(w3.eth.gas_price)
        nonce = await asyncio.to_thread(
            w3.eth.get_transaction_count, self.agent.account.address
        )

        tx_params.update(
            {
                "gas": 300000,  # Base buffer
                "gasPrice": gas_price,
                "nonce": nonce,
            }
        )

        # 3. Sign and Send
        signed = w3.eth.account.sign_transaction(tx_params, self.agent.account.key)
        tx_hash = await asyncio.to_thread(
            w3.eth.send_raw_transaction, signed.raw_transaction
        )
        return w3.to_hex(tx_hash)


class AaveCapability(DeFiCapability):
    """
    Interact with Aave V3 (Supply, Withdraw, Borrow, Repay).
    """

    def __init__(self, agent: Any):
        super().__init__("aave", agent)

        self.tools.append(
            VeritasTool(
                name="aave_supply",
                description="Supply assets to Aave V3 to earn yield.",
                func=self.supply,
                parameters={
                    "type": "object",
                    "properties": {
                        "asset_symbol": {"type": "string"},
                        "amount": {"type": "string"},
                    },
                    "required": ["asset_symbol", "amount"],
                },
            )
        )

        self.tools.append(
            VeritasTool(
                name="aave_borrow",
                description="Borrow assets from Aave V3. Requires existing collateral.",
                func=self.borrow,
                parameters={
                    "type": "object",
                    "properties": {
                        "asset_symbol": {"type": "string"},
                        "amount": {"type": "string"},
                    },
                    "required": ["asset_symbol", "amount"],
                },
            )
        )

    def _get_pool_contract(self):
        network_id = getattr(self.agent, "network", "base-mainnet")
        address = AAVE_POOL_ADDRESSES.get(network_id)
        if not address:
            raise ValueError(f"Aave not supported on {network_id}")
        return self.agent.w3.eth.contract(
            address=self.agent.w3.to_checksum_address(address), abi=AAVE_POOL_ABI
        )

    def _get_asset_address(self, symbol: str) -> str:
        network_id = getattr(self.agent, "network", "base-mainnet")
        tokens = TOKEN_ADDRESSES_BY_SYMBOLS.get(network_id, {})
        addr = tokens.get(symbol.upper())
        if not addr:
            raise ValueError(f"Token {symbol} not found on {network_id}")
        return addr

    async def supply(self, asset_symbol: str, amount: str) -> Dict[str, Any]:
        contract = self._get_pool_contract()
        asset_addr = self._get_asset_address(asset_symbol)
        decimals = await self._get_decimals(asset_addr)
        raw_amount = int(Decimal(amount) * (10**decimals))

        tx_params = contract.functions.supply(
            self.agent.w3.to_checksum_address(asset_addr), raw_amount, self.agent.account.address, 0
        ).build_transaction(
            {
                "from": self.agent.account.address,
                "chainId": 84532 if "sepolia" in getattr(self.agent, "network", "") else 8453,
            }
        )

        tx_hash = await self._simulate_and_send(tx_params)
        return {"status": "success", "action": "supply", "tx_hash": tx_hash}

    async def borrow(self, asset_symbol: str, amount: str) -> Dict[str, Any]:
        contract = self._get_pool_contract()
        asset_addr = self._get_asset_address(asset_symbol)
        decimals = await self._get_decimals(asset_addr)
        raw_amount = int(Decimal(amount) * (10**decimals))

        tx_params = contract.functions.borrow(
            self.agent.w3.to_checksum_address(asset_addr),
            raw_amount,
            2,  # Variable interest rate mode
            0,
            self.agent.account.address,
        ).build_transaction(
            {
                "from": self.agent.account.address,
                "chainId": 84532 if "sepolia" in getattr(self.agent, "network", "") else 8453,
            }
        )

        tx_hash = await self._simulate_and_send(tx_params)
        return {"status": "success", "action": "borrow", "tx_hash": tx_hash}


class CompoundCapability(DeFiCapability):
    """
    Interact with Compound V3 (Comet).
    """

    def __init__(self, agent: Any):
        super().__init__("compound", agent)

        self.tools.append(
            VeritasTool(
                name="compound_supply",
                description="Supply assets to Compound V3.",
                func=self.supply,
                parameters={
                    "type": "object",
                    "properties": {
                        "asset_symbol": {"type": "string"},
                        "amount": {"type": "string"},
                    },
                    "required": ["asset_symbol", "amount"],
                },
            )
        )

    async def supply(self, asset_symbol: str, amount: str) -> Dict[str, Any]:
        network_id = getattr(self.agent, "network", "base-mainnet")
        comet_addr = COMET_ADDRESSES.get(network_id)
        if not comet_addr:
            raise ValueError(f"Compound not supported on {network_id}")

        contract = self.agent.w3.eth.contract(
            address=self.agent.w3.to_checksum_address(comet_addr), abi=COMET_ABI
        )
        tokens = TOKEN_ADDRESSES_BY_SYMBOLS.get(network_id, {})
        asset_addr = tokens.get(asset_symbol.upper())
        decimals = await self._get_decimals(asset_addr)
        raw_amount = int(Decimal(amount) * (10**decimals))

        tx_params = contract.functions.supply(
            self.agent.w3.to_checksum_address(asset_addr), raw_amount
        ).build_transaction(
            {
                "from": self.agent.account.address,
                "chainId": 84532 if "sepolia" in network_id else 8453,
            }
        )

        tx_hash = await self._simulate_and_send(tx_params)
        return {"status": "success", "protocol": "Compound", "tx_hash": tx_hash}

from typing import Any, Dict, Optional
from decimal import Decimal
from .base import VeritasCapability, VeritasTool
from .constants import ERC20_ABI, WETH_ABI, TOKEN_ADDRESSES_BY_SYMBOLS


class TokenCapability(VeritasCapability):
    """
    Interact with ERC20 tokens (Transfer, Balance, Approve) and WETH (Wrap/Unwrap).
    """

    def __init__(self, agent: Any):
        super().__init__("token")
        self.agent = agent

        # --- ERC20 Tools ---
        self.tools.append(
            VeritasTool(
                name="erc20_transfer",
                description="Transfer ERC20 tokens to another address.",
                func=self.transfer,
                parameters={
                    "type": "object",
                    "properties": {
                        "token_address": {
                            "type": "string",
                            "description": "The contract address of the token",
                        },
                        "to_address": {"type": "string", "description": "The destination address"},
                        "amount": {
                            "type": "string",
                            "description": "Amount to transfer in whole units (e.g. '1.5')",
                        },
                    },
                    "required": ["token_address", "to_address", "amount"],
                },
            )
        )

        self.tools.append(
            VeritasTool(
                name="erc20_balance",
                description="Get balance of a specific ERC20 token.",
                func=self.get_balance,
                parameters={
                    "type": "object",
                    "properties": {
                        "token_address": {
                            "type": "string",
                            "description": "Contract address of the token",
                        },
                        "address": {
                            "type": "string",
                            "description": "Optional address to check balance for (defaults to agent's wallet)",
                        },
                    },
                    "required": ["token_address"],
                },
            )
        )

        self.tools.append(
            VeritasTool(
                name="erc20_approve",
                description="Approve a spender to transfer your tokens.",
                func=self.approve,
                parameters={
                    "type": "object",
                    "properties": {
                        "token_address": {
                            "type": "string",
                            "description": "Contract address of the token",
                        },
                        "spender_address": {"type": "string", "description": "Address to approve"},
                        "amount": {
                            "type": "string",
                            "description": "Amount to approve in whole units (e.g. '100')",
                        },
                    },
                    "required": ["token_address", "spender_address", "amount"],
                },
            )
        )

        self.tools.append(
            VeritasTool(
                name="erc20_allowance",
                description="Get the allowance amount for a spender.",
                func=self.get_allowance,
                parameters={
                    "type": "object",
                    "properties": {
                        "token_address": {"type": "string"},
                        "spender_address": {"type": "string"},
                    },
                    "required": ["token_address", "spender_address"],
                },
            )
        )

        self.tools.append(
            VeritasTool(
                name="get_token_address",
                description="Get the contract address for a token symbol (e.g. USDC, WETH) on the current network.",
                func=self.get_token_address,
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Token symbol (e.g. 'USDC')"}
                    },
                    "required": ["symbol"],
                },
            )
        )

        # --- WETH Tools ---
        self.tools.append(
            VeritasTool(
                name="wrap_eth",
                description="Wrap ETH into WETH.",
                func=self.wrap_eth,
                parameters={
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "string",
                            "description": "Amount of ETH to wrap (e.g. '0.1')",
                        }
                    },
                    "required": ["amount"],
                },
            )
        )

        self.tools.append(
            VeritasTool(
                name="unwrap_eth",
                description="Unwrap WETH into ETH.",
                func=self.unwrap_eth,
                parameters={
                    "type": "object",
                    "properties": {
                        "amount": {
                            "type": "string",
                            "description": "Amount of WETH to unwrap (e.g. '0.1')",
                        }
                    },
                    "required": ["amount"],
                },
            )
        )

    def _get_contract(self, address: str, abi: list):
        return self.agent.w3.eth.contract(
            address=self.agent.w3.to_checksum_address(address), abi=abi
        )

    def get_balance(self, token_address: str, address: Optional[str] = None) -> Dict[str, Any]:
        target_address = address if address else self.agent.account.address
        contract = self._get_contract(token_address, ERC20_ABI)

        balance = contract.functions.balanceOf(
            self.agent.w3.to_checksum_address(target_address)
        ).call()
        decimals = contract.functions.decimals().call()
        symbol = contract.functions.symbol().call()

        readable = Decimal(balance) / Decimal(10**decimals)
        return {"symbol": symbol, "balance": float(readable), "address": target_address}

    def transfer(self, token_address: str, to_address: str, amount: str) -> Dict[str, Any]:
        w3 = self.agent.w3
        contract = self._get_contract(token_address, ERC20_ABI)
        decimals = contract.functions.decimals().call()

        # Convert to raw units
        raw_amount = int(Decimal(amount) * (10**decimals))

        tx = contract.functions.transfer(
            w3.to_checksum_address(to_address), raw_amount
        ).build_transaction(
            {
                "chainId": 84532,  # TODO: Dynamic Chain ID from agent.network
                "gas": 100000,  # Basic estimation, ideally simulate
                "gasPrice": w3.eth.gas_price,
                "nonce": w3.eth.get_transaction_count(self.agent.account.address),
                "from": self.agent.account.address,
            }
        )

        signed = w3.eth.account.sign_transaction(tx, self.agent.account.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

        return {"status": "success", "tx_hash": w3.to_hex(tx_hash), "amount": amount}

    def approve(self, token_address: str, spender_address: str, amount: str) -> Dict[str, Any]:
        w3 = self.agent.w3
        contract = self._get_contract(token_address, ERC20_ABI)
        decimals = contract.functions.decimals().call()
        raw_amount = int(Decimal(amount) * (10**decimals))

        tx = contract.functions.approve(
            w3.to_checksum_address(spender_address), raw_amount
        ).build_transaction(
            {
                "chainId": 84532,
                "gas": 100000,
                "gasPrice": w3.eth.gas_price,
                "nonce": w3.eth.get_transaction_count(self.agent.account.address),
                "from": self.agent.account.address,
            }
        )

        signed = w3.eth.account.sign_transaction(tx, self.agent.account.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

        return {
            "status": "success",
            "tx_hash": w3.to_hex(tx_hash),
            "amount": amount,
            "spender": spender_address,
        }

    def get_allowance(self, token_address: str, spender_address: str) -> Dict[str, Any]:
        w3 = self.agent.w3
        contract = self._get_contract(token_address, ERC20_ABI)
        decimals = contract.functions.decimals().call()

        allowance = contract.functions.allowance(
            self.agent.account.address, w3.to_checksum_address(spender_address)
        ).call()

        readable = Decimal(allowance) / Decimal(10**decimals)
        return {"allowance": float(readable), "token": token_address, "spender": spender_address}

    def get_token_address(self, symbol: str) -> str:
        # Check network ID from agent (defaulting to base-sepolia for now if not set)
        network_id = getattr(self.agent, "network", "base-sepolia")
        tokens = TOKEN_ADDRESSES_BY_SYMBOLS.get(network_id, {})
        address = tokens.get(symbol.upper())
        if not address:
            available = list(tokens.keys())
            return f"Error: Token {symbol} not found on {network_id}. Available: {available}"
        return address

    def _get_weth_address(self) -> Optional[str]:
        network_id = getattr(self.agent, "network", "base-sepolia")
        tokens = TOKEN_ADDRESSES_BY_SYMBOLS.get(network_id, {})
        return tokens.get("WETH")

    def wrap_eth(self, amount: str) -> Dict[str, Any]:
        w3 = self.agent.w3
        weth_address = self._get_weth_address()
        if not weth_address:
            return {"error": "WETH not supported on this network"}

        wei_amount = w3.to_wei(Decimal(amount), "ether")

        contract = self._get_contract(weth_address, WETH_ABI)
        tx = contract.functions.deposit().build_transaction(
            {
                "chainId": 84532,
                "value": wei_amount,
                "gas": 100000,
                "gasPrice": w3.eth.gas_price,
                "nonce": w3.eth.get_transaction_count(self.agent.account.address),
                "from": self.agent.account.address,
            }
        )

        signed = w3.eth.account.sign_transaction(tx, self.agent.account.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

        return {"status": "success", "tx_hash": w3.to_hex(tx_hash), "wrapped_amount": amount}

    def unwrap_eth(self, amount: str) -> Dict[str, Any]:
        w3 = self.agent.w3
        weth_address = self._get_weth_address()
        if not weth_address:
            return {"error": "WETH not supported on this network"}

        wei_amount = w3.to_wei(Decimal(amount), "ether")

        contract = self._get_contract(weth_address, WETH_ABI)
        tx = contract.functions.withdraw(wei_amount).build_transaction(
            {
                "chainId": 84532,
                "gas": 100000,
                "gasPrice": w3.eth.gas_price,
                "nonce": w3.eth.get_transaction_count(self.agent.account.address),
                "from": self.agent.account.address,
            }
        )

        signed = w3.eth.account.sign_transaction(tx, self.agent.account.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

        return {"status": "success", "tx_hash": w3.to_hex(tx_hash), "unwrapped_amount": amount}

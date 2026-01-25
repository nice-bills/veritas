from typing import Any, Dict, Optional
from .base import VeritasCapability, VeritasTool
from .constants import (
    ERC721_ABI,
    L2_RESOLVER_ABI,
    REGISTRAR_ABI,
    BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_MAINNET,
    BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_TESTNET,
    L2_RESOLVER_ADDRESS_MAINNET,
    L2_RESOLVER_ADDRESS_TESTNET,
    REGISTRATION_DURATION,
)


class ERC721Capability(VeritasCapability):
    """
    Interact with NFTs (ERC721).
    """

    def __init__(self, agent: Any):
        super().__init__("nft")
        self.agent = agent

        self.tools.append(
            VeritasTool(
                name="nft_balance",
                description="Get balance of NFTs for a specific contract.",
                func=self.get_balance,
                parameters={
                    "type": "object",
                    "properties": {
                        "contract_address": {
                            "type": "string",
                            "description": "Address of the NFT contract",
                        },
                        "address": {
                            "type": "string",
                            "description": "Optional address to check (defaults to agent)",
                        },
                    },
                    "required": ["contract_address"],
                },
            )
        )

        self.tools.append(
            VeritasTool(
                name="nft_transfer",
                description="Transfer an NFT to another address.",
                func=self.transfer,
                parameters={
                    "type": "object",
                    "properties": {
                        "contract_address": {"type": "string"},
                        "to_address": {"type": "string"},
                        "token_id": {"type": "integer"},
                    },
                    "required": ["contract_address", "to_address", "token_id"],
                },
            )
        )

    def get_balance(self, contract_address: str, address: Optional[str] = None) -> Dict[str, Any]:
        target = address if address else self.agent.account.address
        contract = self.agent.w3.eth.contract(
            address=self.agent.w3.to_checksum_address(contract_address), abi=ERC721_ABI
        )
        balance = contract.functions.balanceOf(self.agent.w3.to_checksum_address(target)).call()
        return {"contract": contract_address, "balance": balance, "owner": target}

    def transfer(self, contract_address: str, to_address: str, token_id: int) -> Dict[str, Any]:
        w3 = self.agent.w3
        contract = w3.eth.contract(address=w3.to_checksum_address(contract_address), abi=ERC721_ABI)

        network_id = getattr(self.agent, "network", "base-sepolia")
        chain_id = 84532 if "sepolia" in network_id else 8453

        tx = contract.functions.safeTransferFrom(
            self.agent.account.address, w3.to_checksum_address(to_address), token_id
        ).build_transaction(
            {
                "chainId": chain_id,
                "gas": 150000,
                "gasPrice": w3.eth.gas_price,
                "nonce": w3.eth.get_transaction_count(self.agent.account.address),
                "from": self.agent.account.address,
            }
        )

        signed = w3.eth.account.sign_transaction(tx, self.agent.account.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

        return {"status": "success", "tx_hash": w3.to_hex(tx_hash), "token_id": token_id}


class BasenameCapability(VeritasCapability):
    """
    Register and manage Base Names (.base.eth).
    """

    def __init__(self, agent: Any):
        super().__init__("basename")
        self.agent = agent

        self.tools.append(
            VeritasTool(
                name="register_basename",
                description="Register a .base.eth (or .basetest.eth) name for the agent.",
                func=self.register,
                parameters={
                    "type": "object",
                    "properties": {
                        "basename": {
                            "type": "string",
                            "description": "The desired name (e.g. 'alice')",
                        },
                        "amount": {
                            "type": "string",
                            "description": "Amount of ETH to pay (default '0.00001')",
                        },
                    },
                    "required": ["basename", "amount"],
                },
            )
        )

    def register(self, basename: str, amount: str = "0.00001") -> Dict[str, Any]:
        w3 = self.agent.w3
        network_id = getattr(self.agent, "network", "base-sepolia")
        is_mainnet = "sepolia" not in network_id

        suffix = ".base.eth" if is_mainnet else ".basetest.eth"
        full_name = basename if basename.endswith(suffix) else f"{basename}{suffix}"

        registrar_addr = (
            BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_MAINNET
            if is_mainnet
            else BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_TESTNET
        )
        resolver_addr = L2_RESOLVER_ADDRESS_MAINNET if is_mainnet else L2_RESOLVER_ADDRESS_TESTNET

        resolver_contract = w3.eth.contract(abi=L2_RESOLVER_ABI)
        registrar_contract = w3.eth.contract(
            address=w3.to_checksum_address(registrar_addr), abi=REGISTRAR_ABI
        )

        name_hash = w3.ens.namehash(full_name)
        address_data = resolver_contract.encode_abi(
            "setAddr", args=[name_hash, self.agent.account.address]
        )
        name_data = resolver_contract.encode_abi("setName", args=[name_hash, full_name])

        register_request = {
            "name": full_name.replace(suffix, ""),
            "owner": self.agent.account.address,
            "duration": int(REGISTRATION_DURATION),
            "resolver": w3.to_checksum_address(resolver_addr),
            "data": [address_data, name_data],
            "reverseRecord": True,
        }

        tx = registrar_contract.functions.register(register_request).build_transaction(
            {
                "chainId": 84532 if not is_mainnet else 8453,
                "value": w3.to_wei(amount, "ether"),
                "gas": 300000,
                "gasPrice": w3.eth.gas_price,
                "nonce": w3.eth.get_transaction_count(self.agent.account.address),
                "from": self.agent.account.address,
            }
        )

        signed = w3.eth.account.sign_transaction(tx, self.agent.account.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

        return {"status": "success", "basename": full_name, "tx_hash": w3.to_hex(tx_hash)}

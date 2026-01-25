from eth_abi import encode
from typing import Optional, Any
from web3 import Web3
import time
import json
import os

# Constants
EAS_CONTRACT_ADDRESS = "0x4200000000000000000000000000000000000021"
DEFAULT_SCHEMA_UID = "0x4ee2145e253098e581a38bdbb7f7c81eae64b6d9d5868063c71b562779056441"


class VeritasAttestor:
    """
    Handles on-chain attestations using EAS on Base (Base Sepolia/Mainnet).
    """

    NETWORK_CONFIG = {
        "base-sepolia": {"chainId": 84532, "rpc": "https://base-sepolia.drpc.org"},
        "base-mainnet": {"chainId": 8453, "rpc": "https://mainnet.base.org"},
    }

    def __init__(self, client: Any, account: Any, network_id: str = "base-sepolia"):
        self.client = client
        self.account = account
        self.network_id = network_id
        self.schema_uid = os.getenv("EAS_SCHEMA_UID", DEFAULT_SCHEMA_UID)

        abi_path = os.path.join(os.path.dirname(__file__), "eas_abi.json")
        with open(abi_path, "r") as f:
            self.eas_abi = json.load(f)

    async def attest_root(
        self, merkle_root: str, schema_uid: Optional[str] = None, agent_id: str = "veritas-agent"
    ) -> str:
        """
        Attests a Merkle Root to the EAS contract.
        """
        uid = schema_uid or self.schema_uid
        clean_root = merkle_root[2:] if merkle_root.startswith("0x") else merkle_root
        root_bytes = bytes.fromhex(clean_root)
        timestamp = int(time.time())

        # Encode data: bytes32 merkleRoot, string agentId, uint256 timestamp
        encoded_payload = encode(
            ["bytes32", "string", "uint256"], [root_bytes, agent_id, timestamp]
        )

        config = self.NETWORK_CONFIG.get(self.network_id, self.NETWORK_CONFIG["base-sepolia"])
        w3 = Web3(Web3.HTTPProvider(config["rpc"]))

        if not w3.is_connected():
            raise ConnectionError(f"Could not connect to RPC: {config['rpc']}")

        eas_contract = w3.eth.contract(address=EAS_CONTRACT_ADDRESS, abi=self.eas_abi)

        # Construct AttestationRequest
        request = (
            uid,
            (
                "0x0000000000000000000000000000000000000000",  # recipient
                0,  # expirationTime
                True,  # revocable
                b"\x00" * 32,  # refUID
                encoded_payload,
                0,  # value
            ),
        )

        try:
            nonce = w3.eth.get_transaction_count(self.account.address, "pending")
            tx_params = {
                "chainId": config["chainId"],
                "gas": 300000,
                "gasPrice": int(w3.eth.gas_price * 1.1),
                "nonce": nonce,
                "from": self.account.address,
            }

            tx_data = eas_contract.functions.attest(request).build_transaction(tx_params)

            # 1. Simulate
            w3.eth.call(tx_data)

            # 2. Sign & Send
            signed_tx = w3.eth.account.sign_transaction(tx_data, self.account.key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            print(f"[Veritas] Attestation submitted: {w3.to_hex(tx_hash)}")
            return w3.to_hex(tx_hash)

        except Exception as e:
            print(f"[Veritas] Attestation failed: {e}")
            raise e

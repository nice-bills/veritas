from eth_abi import encode
from typing import Optional, Dict, Any
from web3 import Web3
import time
import json
import os

# EAS Contract Addresses on Base Sepolia
EAS_CONTRACT_ADDRESS = "0x4200000000000000000000000000000000000021"
SCHEMA_REGISTRY_ADDRESS = "0x4200000000000000000000000000000000000020"

class VeritasAttestor:
    """
    Handles on-chain attestations of Veritas Merkle Roots using EAS on Base.
    Uses CDP SDK for wallet management and transaction execution.
    """
    
    def __init__(self, client: Any, account: Any, network_id: str = "base-sepolia"):
        self.client = client
        self.account = account
        self.network_id = network_id
        
        # Load ABI
        abi_path = os.path.join(os.path.dirname(__file__), "eas_abi.json")
        with open(abi_path, "r") as f:
            self.eas_abi = json.load(f)

    async def attest_root(self, merkle_root: str, schema_uid: str, agent_id: str = "veritas-agent") -> str:
        """
        Attests a Merkle Root to the EAS contract.
        Returns the transaction hash.
        """
        # Convert hex root to bytes
        clean_root = merkle_root[2:] if merkle_root.startswith("0x") else merkle_root
        root_bytes = bytes.fromhex(clean_root)
        
        timestamp = int(time.time())

        # Encode data according to schema: bytes32 merkleRoot, string agentId, uint256 timestamp
        encoded_payload = encode(
            ['bytes32', 'string', 'uint256'], 
            [root_bytes, agent_id, timestamp]
        )

        print(f"[Veritas] Sending attestation to EAS | Root: {merkle_root[:10]}...")
        
        try:
            # We are using a local account (eth_account), so we must sign locally and broadcast via Web3.
            
            # Public Base Sepolia RPC
            w3 = Web3(Web3.HTTPProvider("https://base-sepolia-rpc.publicnode.com"))
            
            if not w3.is_connected():
                raise ConnectionError("Could not connect to Base Sepolia RPC")

            # Initialize EAS Contract
            eas_contract = w3.eth.contract(address=EAS_CONTRACT_ADDRESS, abi=self.eas_abi)

            # Construct AttestationRequest Struct
            # struct AttestationRequest { bytes32 schema; AttestationRequestData data; }
            # struct AttestationRequestData { address recipient; uint64 expirationTime; bool revocable; bytes32 refUID; bytes data; uint256 value; }
            
            request = (
                schema_uid,
                (
                    "0x0000000000000000000000000000000000000000", # recipient (none)
                    0, # expirationTime (0 = no expiration)
                    True, # revocable
                    b'\x00' * 32, # refUID (none)
                    encoded_payload, # data
                    0 # value
                )
            )

            # Build Transaction
            nonce = w3.eth.get_transaction_count(self.account.address, 'pending')
            
            tx_params = {
                'chainId': 84532,
                'gas': 300000, # Safe buffer for EAS
                'gasPrice': int(w3.eth.gas_price * 1.2), # Add 20% tip for speed
                'nonce': nonce,
                'from': self.account.address
            }
            
            # Estimate gas or hardcode safe buffer
            tx_data = eas_contract.functions.attest(request).build_transaction(tx_params)
            
            # Simulate transaction to catch errors early
            try:
                w3.eth.call(tx_data)
            except Exception as e:
                raise RuntimeError(f"Attestation simulation failed (revert): {e}")
            
            # Sign
            signed_tx = w3.eth.account.sign_transaction(tx_data, self.account.key)
            
            # Broadcast
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = w3.to_hex(tx_hash)
            
            print(f"[Veritas] On-chain transaction submitted! Tx: {tx_hash_hex}")
            return tx_hash_hex

        except Exception as e:
            print(f"[Veritas] Transaction failed: {e}")
            raise e
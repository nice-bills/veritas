from eth_abi import encode
from cdp import EvmServerAccount
from typing import Optional, Dict, Any
import time

# EAS Contract Addresses on Base Sepolia
EAS_CONTRACT_ADDRESS = "0x4200000000000000000000000000000000000021"
SCHEMA_REGISTRY_ADDRESS = "0x4200000000000000000000000000000000000020"

class VeritasAttestor:
    """
    Handles on-chain attestations of Veritas Merkle Roots using EAS on Base.
    Uses CDP SDK for wallet management and transaction execution.
    """
    
    def __init__(self, account: EvmServerAccount, network_id: str = "base-sepolia"):
        self.account = account
        self.network_id = network_id

    def attest_root(self, merkle_root: str, schema_uid: str, agent_id: str = "veritas-agent") -> str:
        """
        Attests a Merkle Root to the EAS contract.
        Returns the transaction hash.
        """
        # Convert hex root to bytes
        clean_root = merkle_root[2:] if merkle_root.startswith("0x") else merkle_root
        root_bytes = bytes.fromhex(clean_root)
        
        timestamp = int(time.time())

        # Encode data according to schema: bytes32 merkleRoot, string agentId, uint256 timestamp
        # This matches the EAS 'attest' function expected data.
        encoded_payload = encode(
            ['bytes32', 'string', 'uint256'], 
            [root_bytes, agent_id, timestamp]
        )

        # We need to encode the full call to EAS.attest((schema, data_struct))
        # But CDP send_transaction just takes 'data' for the contract call.
        # We need to manually construct the data or use a helper.
        # For EAS.attest: selector is 0xf1856d3a (for common attest overload)
        # However, it's easier to use a dedicated 'TransactionRequest' or similar.
        
        print(f"[Veritas] Sending attestation to EAS | Root: {merkle_root[:10]}...")
        
        # In a real scenario, we'd use web3 to encode the full transaction 'data'.
        # For this prototype, we'll demonstrate the intent:
        tx_hash = self.account.send_transaction(
            transaction="0x...", # Full encoded EAS.attest data would go here
            network=self.network_id
        )
        
        print(f"[Veritas] On-chain attestation submitted! Tx: {tx_hash}")
        return tx_hash
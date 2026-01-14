from eth_abi import encode
from cdp import Wallet
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
    
    def __init__(self, wallet: Wallet):
        self.wallet = wallet

    def register_veritas_schema(self) -> str:
        """
        Registers the Veritas Audit Schema on the Schema Registry.
        Schema: "bytes32 merkleRoot, string agentId, uint256 timestamp"
        Returns the Schema UID.
        """
        schema_string = "bytes32 merkleRoot, string agentId, uint256 timestamp"
        resolver = "0x0000000000000000000000000000000000000000" # No resolver
        revocable = True

        print(f"[Veritas] Registering schema: '{schema_string}' on Base Sepolia...")
        
        # SchemaRegistry.register(string schema, address resolver, bool revocable)
        invocation = self.wallet.invoke_contract(
            contract_address=SCHEMA_REGISTRY_ADDRESS,
            method="register",
            args={
                "schema": schema_string,
                "resolver": resolver,
                "revocable": revocable
            }
        )
        invocation.wait()
        
        # Note: The Schema UID is actually a hash of the registration data.
        # In a real app, we'd parse the logs to get the UID.
        # For now, we'll return the transaction hash as a placeholder for the ID 
        # or explain how to find it.
        print(f"[Veritas] Schema registration transaction: {invocation.transaction_hash}")
        return invocation.transaction_hash

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
        encoded_data = encode(
            ['bytes32', 'string', 'uint256'], 
            [root_bytes, agent_id, timestamp]
        )

        # EAS.attest((bytes32 schema, (address recipient, uint64 expirationTime, bool revocable, bytes32 refUID, bytes data, uint256 value)))
        # Inner struct: AttestationRequestData
        attestation_data = (
            "0x0000000000000000000000000000000000000000", # recipient
            0, # expirationTime (never)
            True, # revocable
            b'\x00' * 32, # refUID
            encoded_data, # data
            0 # value
        )

        # Full Request struct: AttestationRequest
        request = (schema_uid, attestation_data)

        print(f"[Veritas] Sending attestation to EAS | Root: {merkle_root[:10]}...")
        
        invocation = self.wallet.invoke_contract(
            contract_address=EAS_CONTRACT_ADDRESS,
            method="attest",
            args={"request": request}
        )
        
        invocation.wait()
        
        print(f"[Veritas] On-chain attestation successful! Tx: {invocation.transaction_hash}")
        return invocation.transaction_hash
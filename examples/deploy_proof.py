import os
import json
import time
from cdp import Cdp, EvmServerAccount
from veritas import VeritasAttestor

def main():
    print("Veritas On-Chain Attestation Utility")
    print("------------------------------------")

    # 1. Load Credentials
    api_key_name = os.getenv("CDP_API_KEY_NAME")
    api_key_private_key = os.getenv("CDP_API_KEY_PRIVATE_KEY")

    if not api_key_name or not api_key_private_key:
        print("ERROR: Missing CDP Credentials.")
        print("Please set CDP_API_KEY_NAME and CDP_API_KEY_PRIVATE_KEY environment variables.")
        return

    # 2. Configure CDP
    try:
        # Check if keys are paths or raw strings
        if os.path.exists(api_key_private_key):
             # Logic for file-based keys if needed, but standard env var is usually the string
             pass
        
        Cdp.configure(api_key_name, api_key_private_key)
        print("CDP SDK Configured.")
    except Exception as e:
        print(f"Failed to configure CDP: {e}")
        return

    # 3. Initialize Wallet/Account
    print("Initializing Agent Wallet...")
    try:
        # Create a new server-controlled wallet on Base Sepolia
        # In production, you'd use 'get_account' or seed matching
        agent_account = EvmServerAccount.create_with_network_id("base-sepolia")
        print(f"Agent Address: {agent_account.address}")
    except Exception as e:
        print(f"Failed to create wallet: {e}")
        return

    # 4. Fund the Wallet (Dev Only)
    print("Checking Balance...")
    try:
        # Request testnet funds
        faucet_tx = agent_account.request_faucet()
        print(f"Faucet Requested. Tx: {faucet_tx}")
        # Wait for funds to arrive
        print("Waiting 5s for faucet transaction...")
        time.sleep(5) 
    except Exception as e:
        print(f"Faucet skipped or failed (might have funds already): {e}")

    # 5. Load Proof
    proof_file = "minimax_session.json"
    # Fallback to basic proof if minimax one doesn't exist
    if not os.path.exists(proof_file):
        proof_file = "test_proof.json"
    
    if not os.path.exists(proof_file):
        print(f"ERROR: No proof file found (checked {proof_file}).")
        print("Run 'python examples/minimax_audit.py' first.")
        return

    with open(proof_file, "r") as f:
        proof_data = json.load(f)
    
    merkle_root = proof_data.get("session_root")
    print(f"Loaded Merkle Root: {merkle_root}")

    # 6. Attest
    attestor = VeritasAttestor(agent_account, network_id="base-sepolia")
    
    try:
        # Use a placeholder Schema UID for now (or register one)
        # We will use the common "Bytes32" schema if it exists, or just our custom logic.
        # For this demo, we assume the logic in attestor.py handles the EAS call.
        tx_hash = attestor.attest_root(
            merkle_root=merkle_root, 
            schema_uid="0x0000000000000000000000000000000000000000000000000000000000000000", 
            agent_id="MiniMax-Agent-001"
        )
        print("\nSUCCESS: Proof Attested on Base Sepolia!")
        print(f"View Transaction: https://sepolia.basescan.org/tx/{tx_hash}")
    except Exception as e:
        print(f"Attestation Failed: {e}")

if __name__ == "__main__":
    main()

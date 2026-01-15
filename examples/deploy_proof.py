import os
import json
import time
import asyncio
from cdp import CdpClient, EvmServerAccount
from veritas import VeritasAttestor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def main():
    print("Veritas On-Chain Attestation Utility")
    print("------------------------------------")

    # 1. Load Credentials
    api_key_id = os.getenv("CDP_API_KEY_ID")
    api_key_secret = os.getenv("CDP_API_KEY_SECRET")
    wallet_secret = os.getenv("CDP_WALLET_SECRET")

    if not api_key_id or not api_key_secret:
        print("ERROR: Missing CDP Credentials.")
        print("Please set CDP_API_KEY_ID and CDP_API_KEY_SECRET in your .env file.")
        return

    # 2. Configure CDP
    try:
        # Instantiate the client with API keys and the wallet encryption secret
        client = CdpClient(
            api_key_id=api_key_id, 
            api_key_secret=api_key_secret,
            wallet_secret=wallet_secret
        )
        print("CDP Client Initialized.")
    except Exception as e:
        print(f"Failed to initialize CDP: {e}")
        return

    # 3. Initialize Wallet/Account
    print("Initializing Agent Wallet...")
    try:
        # Use the client to create an account (async)
        agent_account = await client.evm.create_account()
        print(f"Agent Address: {agent_account.address}")
    except Exception as e:
        print(f"Failed to create wallet: {e}")
        return

    # 4. Fund the Wallet (Dev Only)
    print("Checking Balance...")
    try:
        # Request testnet funds (async)
        faucet_tx = await agent_account.request_faucet()
        print(f"Faucet Requested. Tx: {faucet_tx}")
        # Wait for funds to arrive
        print("Waiting 10s for faucet transaction...")
        await asyncio.sleep(10) 
    except Exception as e:
        print(f"Faucet skipped or failed (might have funds already): {e}")

    # 5. Load Proof
    proof_file = "minimax_session.json"
    if not os.path.exists(proof_file):
        proof_file = "test_proof.json"
    
    if not os.path.exists(proof_file):
        print(f"ERROR: No proof file found.")
        return

    with open(proof_file, "r") as f:
        proof_data = json.load(f)
    
    merkle_root = proof_data.get("session_root")
    print(f"Loaded Merkle Root: {merkle_root}")

    # 6. Attest
    attestor = VeritasAttestor(agent_account, network_id="base-sepolia")
    
    try:
        # Note: attestor.py needs to be checked for async as well
        tx_hash = await attestor.attest_root(
            merkle_root=merkle_root, 
            schema_uid="0x0000000000000000000000000000000000000000000000000000000000000000", 
            agent_id="MiniMax-Agent-001"
        )
        print("\nSUCCESS: Proof Attested on Base Sepolia!")
        print(f"View Transaction: https://sepolia.basescan.org/tx/{tx_hash}")
    except Exception as e:
        print(f"Attestation Failed: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())

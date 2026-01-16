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
    # (Just verifying they exist, CdpClient will load them from env)
    if not os.getenv("CDP_API_KEY_ID") or not os.getenv("CDP_API_KEY_SECRET"):
        print("ERROR: Missing CDP Credentials in environment.")
        return

    # 2. Configure CDP
    client = None
    try:
        # Initialize Client
        client = CdpClient()
        print("CDP Client Initialized.")
    except Exception as e:
        print(f"Failed to initialize CDP: {e}")
        return

    # 3. Initialize Wallet/Account
    print("Initializing Agent Wallet...")
    try:
        # Step A: Use eth_account for a local wallet
        from eth_account import Account
        # Enable Mnemonic features if needed, but simple create is fine
        agent_account = Account.create()
        print(f"Agent Created Locally! Address: {agent_account.address}")
    except Exception as e:
        print(f"Failed to create local wallet: {e}")
        return

    # 4. Fund the Wallet (Dev Only)
    print("Checking Balance & Requesting Faucet...")
    try:
        # Request testnet funds (async)
        faucet_tx = await client.evm.request_faucet(
            address=agent_account.address,
            network="base-sepolia",
            token="eth"
        )
        print(f"Faucet Requested. Transaction: {faucet_tx}")
        # Wait for funds to arrive
        print("Waiting 20s for faucet transaction to clear on-chain...")
        await asyncio.sleep(20) 
        print("Wait complete. Proceeding to attestation...")
    except Exception as e:
        print(f"Faucet skipped or failed: {e}")

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
    # Pass both client and account to the attestor
    attestor = VeritasAttestor(client, agent_account, network_id="base-sepolia")
    
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

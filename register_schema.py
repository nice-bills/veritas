from web3 import Web3
from eth_account import Account
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Schema Registry Address on Base Sepolia
SCHEMA_REGISTRY_ADDRESS = "0x4200000000000000000000000000000000000020"

# Minimal ABI for register
SCHEMA_REGISTRY_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "schema", "type": "string"},
            {"internalType": "address", "name": "resolver", "type": "address"},
            {"internalType": "bool", "name": "revocable", "type": "bool"}
        ],
        "name": "register",
        "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

import asyncio

async def main():
    print("Registering Veritas Schema on Base Sepolia...")
    
    # ... (web3 setup) ...
    w3 = Web3(Web3.HTTPProvider("https://base-sepolia-rpc.publicnode.com"))
    
    account = Account.create()
    print(f"Temporary Account: {account.address}")
    
    # Faucet logic
    print("Requesting funds from Coinbase faucet...")
    from cdp import CdpClient
    try:
        # Load credentials
        api_key_id = os.getenv("CDP_API_KEY_ID")
        api_key_secret = os.getenv("CDP_API_KEY_SECRET")
        if "\n" in api_key_secret:
            api_key_secret = api_key_secret.replace("\n", "\n")
            
        client = CdpClient(api_key_id=api_key_id, api_key_secret=api_key_secret)
        # Fix: await the async call
        await client.evm.request_faucet(address=account.address, network="base-sepolia", token="eth")
        print("Faucet requested. Waiting 15s...")
        await asyncio.sleep(15)
    except Exception as e:
        print(f"Faucet failed: {e}")
        return

    # ... (rest of logic) ...
    contract = w3.eth.contract(address=SCHEMA_REGISTRY_ADDRESS, abi=SCHEMA_REGISTRY_ABI)
    
    schema_string = "bytes32 merkleRoot, string agentId, uint256 timestamp"
    
    tx = contract.functions.register(
        schema_string,
        "0x0000000000000000000000000000000000000000",
        True
    ).build_transaction({
        'chainId': 84532,
        'gas': 400000, # Bump gas
        'gasPrice': w3.eth.gas_price,
        'nonce': w3.eth.get_transaction_count(account.address),
        'from': account.address
    })
    
    signed_tx = w3.eth.account.sign_transaction(tx, account.key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    print(f"Schema Registration Tx: {w3.to_hex(tx_hash)}")
    print("Waiting for receipt...")
    
    # Wait for receipt
    while True:
        try:
            receipt = w3.eth.get_transaction_receipt(tx_hash)
            if receipt: break
        except:
            await asyncio.sleep(1)
            
    print("Schema Registered!")
    print(f"View on BaseScan: https://sepolia.basescan.org/tx/{w3.to_hex(tx_hash)}")
    
    # Attempt to parse logs for UID (Topic 0 is the event hash)
    # Event: Registered(bytes32 indexed uid, address indexed registerer, ...)
    # The UID is the first topic (index 1)
    if receipt.logs:
        uid = receipt.logs[0].topics[1].hex()
        print(f"NEW SCHEMA UID: {uid}")

if __name__ == "__main__":
    asyncio.run(main())

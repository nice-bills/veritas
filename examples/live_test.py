import os
import sys
from web3 import Web3
from decimal import Decimal

# Fix path to import src
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from veritas.tools.token import TokenCapability
from veritas.tools.infra import PythCapability, OnrampCapability
from veritas.tools.nft import BasenameCapability
from veritas.tools.payments import PaymentCapability
from veritas.tools.constants import TOKEN_ADDRESSES_BY_SYMBOLS

# Mock Agent Class to hold Web3 connection
class MockAgent:
    def __init__(self):
        rpc_urls = [
            "https://base-sepolia.drpc.org",
            "https://84532.rpc.thirdweb.com",
            "https://base-sepolia-rpc.publicnode.com",
            "https://sepolia.base.org"
        ]
        
        self.w3 = None
        for url in rpc_urls:
            print(f"Connecting to {url}...")
            temp_w3 = Web3(Web3.HTTPProvider(url))
            try:
                if temp_w3.is_connected():
                    self.w3 = temp_w3
                    print(f"Connected to RPC: {url}")
                    break
            except Exception as e:
                print(f"Failed {url}: {e}")
                continue
        
        if not self.w3:
            raise Exception("Could not connect to any Base Sepolia RPC")
        
        self.account = type('obj', (object,), {'address': '0x742d35Cc6634C0532925a3b844Bc454e4438f44e', 'key': b''})
        self.network = "base-sepolia"

def run_live_test():
    print("--- Starting Live Chain Test (Base Sepolia) ---")
    try:
        agent = MockAgent()
    except Exception as e:
        print(f"Initialization Failed: {e}")
        return

    print(f"Connected. Current Block: {agent.w3.eth.block_number}")

    # 1. Test Pyth Price (Read)
    print("\n[1] Testing Pyth Oracle (Real Read)...")
    pyth = PythCapability(agent)
    # ETH/USD Price Feed ID on Base Sepolia
    feed_id = "0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace"
    try:
        price_data = pyth.get_price(feed_id)
        print(f"ETH/USD Price: ${price_data['price']:.2f}")
    except Exception as e:
        print(f"Pyth Failed: {e}")

    # 2. Test Token Balance (Read)
    print("\n[2] Testing Token Balance (USDC)...")
    token = TokenCapability(agent)
    usdc_addr = TOKEN_ADDRESSES_BY_SYMBOLS["base-sepolia"]["USDC"]
    try:
        bal = token.get_balance(usdc_addr, "0x4200000000000000000000000000000000000006")
        print(f"USDC ({bal['symbol']}) Balance of WETH contract: {bal['balance']}")
    except Exception as e:
        print(f"Token Balance Failed: {e}")

    # 3. Test Base Identity (Read Code)
    print("\n[3] Verifying Infrastructure Contracts...")
    from veritas.tools.constants import BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_TESTNET
    try:
        code = agent.w3.eth.get_code(agent.w3.to_checksum_address(BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_TESTNET))
        if len(code) > 0:
            print(f"Basename Registrar detected on-chain.")
        else:
            print(f"Basename Registrar NOT found.")
    except Exception as e:
        print(f"Infra Check Failed: {e}")

    # 4. Test Onramp
    print("\n[4] Testing Onramp URL Generation...")
    onramp = OnrampCapability(agent)
    try:
        url = onramp.get_buy_url("USDC", "base")
        print(f"Generated Onramp URL: {url}")
    except Exception as e:
        print(f"Onramp Failed: {e}")

    # 5. Test Payments (HTTP Request)
    print("\n[5] Testing Payments (HTTP Request)...")
    payments = PaymentCapability(agent)
    try:
        res = payments.http_request("https://www.google.com")
        print(f"HTTP Request Status: {res['status']}")
    except Exception as e:
        print(f"Payments Failed: {e}")

    print("\n--- Live Test Complete ---")

if __name__ == "__main__":
    run_live_test()
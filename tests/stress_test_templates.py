import requests
import json
import time
import sys
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"

TEMPLATES = [
    {
        "name": "Arbitrage",
        "objective": "Check ETH price on Pyth and compare with Uniswap pools. If there is a >1% spread, simulate a trade to capture profit.",
        "expected_tools": ["get_price", "get_swap_price"]
    },
    {
        "name": "Identity",
        "objective": "Register a new .basetest.eth name for this agent and verify it on-chain.",
        "expected_tools": ["register_basename"]
    },
    {
        "name": "Yield",
        "objective": "Check my USDC balance and supply it to Aave V3 to earn yield.",
        "expected_tools": ["erc20_balance", "aave_supply"]
    }
]

def run_test():
    print("🔥 Starting Template Stress Test...")
    
    # Create Agent
    payload = {
        "name": "StressTester",
        "brain_provider": "minimax",
        "network": "base-sepolia",
        "capabilities": ["wallet", "token", "pyth", "trading", "basename", "aave"],
        # Keys must be in .env or passed here. Assuming .env on server.
        "minimax_api_key": os.getenv("MINIMAX_API_KEY"),
        "cdp_api_key_id": os.getenv("CDP_API_KEY_ID"),
        "cdp_api_key_secret": os.getenv("CDP_API_KEY_SECRET"),
    }
    
    try:
        res = requests.post(f"{BASE_URL}/agents", json=payload)
        res.raise_for_status()
        agent_id = res.json()["id"]
        print(f"✅ Agent Created: {agent_id}")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return

    for t in TEMPLATES:
        print(f"\n🧪 Testing Template: {t['name']}")
        print(f"   Objective: {t['objective']}")
        
        mission = {"objective": t["objective"]}
        try:
            start = time.time()
            res = requests.post(f"{BASE_URL}/agents/{agent_id}/run", json=mission, timeout=60)
            res.raise_for_status()
            data = res.json()
            duration = time.time() - start
            
            logs = data.get("logs", [])
            tools_called = [l["tool_name"] for l in logs if l["event_type"] == "ACTION"]
            
            print(f"   ⏱️ Duration: {duration:.2f}s")
            print(f"   🛠️ Tools Called: {tools_called}")
            
            # Verification
            success = any(tool in tools_called for tool in t["expected_tools"])
            if success:
                print(f"   ✅ PASSED: Expected tools executed.")
            else:
                print(f"   ❌ FAILED: Agent did not execute expected tools. It mostly thought.")
                # Print thoughts to debug
                for l in logs:
                    if l["event_type"] == "THOUGHT":
                        print(f"      💭 Thought: {str(l['output_result'])[:100]}...")

        except Exception as e:
            print(f"   ❌ ERROR: {e}")

    # Cleanup
    requests.delete(f"{BASE_URL}/agents/{agent_id}")
    print("\n🏁 Stress Test Complete.")

if __name__ == "__main__":
    run_test()

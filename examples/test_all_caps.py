import asyncio
import os
from veritas.agent import VeritasAgent
from veritas.tools.erc20 import ERC20Capability
from veritas.tools.data import DataCapability
from veritas.tools.social import SocialCapability
from veritas.tools.identity import IdentityCapability
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("Veritas Full Capability Gauntlet")
    print("--------------------------------")
    
    agent = VeritasAgent(name="GauntletAgent")
    
    # 1. Load All Caps
    agent.load_capability(ERC20Capability(agent))
    agent.load_capability(DataCapability(agent))
    agent.load_capability(SocialCapability(agent))
    agent.load_capability(IdentityCapability(agent))
    
    print("\n--- 1. Testing ERC20 (USDC) ---")
    try:
        # USDC on Base Sepolia
        usdc = "0x036CbD53842c5426634e7929541eC2318f3dCF7e" 
        bal = await agent.call_tool("erc20_balance", token_address=usdc)
        print(f"USDC Balance: {bal}")
    except Exception as e:
        print(f"ERC20 Failed: {e}")

    print("\n--- 2. Testing Pyth (ETH/USD) ---")
    try:
        # ETH/USD Price ID
        eth_feed = "ff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace"
        price = await agent.call_tool("get_price", price_id=eth_feed)
        print(f"ETH Price: ${price['price']}")
    except Exception as e:
        print(f"Pyth Failed: {e}")

    print("\n--- 3. Testing Social (Twitter) ---")
    try:
        tweet = await agent.call_tool("post_tweet", text="Hello from Veritas Agent!")
        print(f"Tweet Status: {tweet['status']}")
    except Exception as e:
        print(f"Social Failed: {e}")

    print("\n--- 4. Testing Identity (Basename) ---")
    try:
        name = await agent.call_tool("register_name", name="veritas-test")
        print(f"Identity Status: {name['status']}")
    except Exception as e:
        print(f"Identity Failed: {e}")

    await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

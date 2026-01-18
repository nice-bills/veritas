import asyncio
import os
from veritas.agent import VeritasAgent
from veritas.tools import (
    ERC20Capability, DataCapability, SocialCapability, IdentityCapability,
    PaymentCapability, CreatorCapability, PrivacyCapability, DeFiCapability
)
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("Veritas FULL Platform Gauntlet")
    print("------------------------------")
    
    agent = VeritasAgent(name="FullPlatformAgent")
    
    # Load everything
    agent.load_capability(ERC20Capability(agent))
    agent.load_capability(DataCapability(agent))
    agent.load_capability(SocialCapability(agent))
    agent.load_capability(IdentityCapability(agent))
    agent.load_capability(PaymentCapability(agent))
    agent.load_capability(CreatorCapability(agent))
    agent.load_capability(PrivacyCapability(agent))
    agent.load_capability(DeFiCapability(agent))
    
    print("\n--- Testing New Capabilities ---")
    
    # DeFi
    yield_tx = await agent.call_tool("supply_asset", asset="USDC", amount=100, protocol="aave")
    print(f"DeFi: {yield_tx['status']} ({yield_tx['protocol']})")

    # x402
    pay = await agent.call_tool("pay_api_request", url="https://api.premium.com", amount_usdc=0.5)
    print(f"Payment: {pay['status']}")
    
    # Wow
    coin = await agent.call_tool("launch_token", name="VeritasCoin", symbol="VRT")
    print(f"Token: {coin['status']} at {coin['token_address'][:10]}...")
    
    # Privacy
    secret = await agent.call_tool("store_secret", secret_name="agent_key", secret_value="shhh")
    print(f"Privacy: {secret['status']} (ID: {secret['store_id'][:10]}...)")

    print("\nFinal Audit Trail Length:", len(agent.logger.get_logs()))
    await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
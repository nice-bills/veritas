import asyncio
import os
from veritas.agent import VeritasAgent
from veritas.tools import WalletCapability, VeritasCapability
from veritas.adapter import VeritasAdapter
import cdp.actions.evm
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("Testing Veritas Capability System")
    
    # 1. Initialize Agent
    agent = VeritasAgent(name="ToolTestAgent")
    
    # 2. Load Wallet Capability
    wallet_cap = WalletCapability(agent)
    agent.load_capability(wallet_cap)
    
    # 3. Call Tool (Audited)
    print("\nCalling 'get_balance' via call_tool...")
    result = await agent.call_tool("get_balance")
    print(f"Result: {result}")
    
    # 4. Demonstrate Generic Adapter
    print("\nAdapting CDP 'request_faucet' action...")
    # Map the CDP SDK internal function to a VeritasTool
    faucet_tool = VeritasAdapter.to_tool(
        agent=agent,
        func=agent.client.evm.request_faucet,
        name="faucet",
        description="Request testnet funds for the agent's wallet."
    )
    
    # Register this tool manually or via a capability
    custom_cap = VeritasCapability("custom")
    custom_cap.tools.append(faucet_tool)
    agent.load_capability(custom_cap)
    
    print("Calling 'faucet' via call_tool...")
    try:
        # Requesting 0.001 ETH
        result = await agent.call_tool("faucet", address=agent.account.address, network="base-sepolia", token="eth")
        print(f"Faucet Result: {result}")
    except Exception as e:
        print(f"Call failed: {e}")
        
    # 5. Verify Logs
    logs = agent.logger.get_logs()
    print(f"\nAudit Trail Length: {len(logs)}")
    for i, log in enumerate(logs):
        print(f"[{i}] {log.tool_name}: {log.output_result}")
        
    await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(main())


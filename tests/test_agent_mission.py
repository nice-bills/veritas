import unittest
import asyncio
import os
from veritas.agent import VeritasAgent
from dotenv import load_dotenv

load_dotenv()

class TestAgentMission(unittest.IsolatedAsyncioTestCase):
    async def test_run_mission(self):
        # We need MiniMax and CDP keys in env
        if not os.getenv("MINIMAX_API_KEY") or not os.getenv("CDP_API_KEY_ID"):
            self.skipTest("Missing API keys in environment")
            
        agent = VeritasAgent(name="MissionAgent")
        
        try:
            # Run a simple mission
            objective = "If I have any ETH, execute a successful action."
            root = await agent.run_mission(objective)
            
            self.assertIsNotNone(root)
            self.assertTrue(len(agent.logger.get_logs()) >= 1)
        finally:
            await agent.shutdown()

if __name__ == "__main__":
    unittest.main()

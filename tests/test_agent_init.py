import unittest
import asyncio
import os
from veritas.agent import VeritasAgent
from dotenv import load_dotenv

load_dotenv()

class TestAgentInit(unittest.IsolatedAsyncioTestCase):
    async def test_initialization(self):
        # We need CDP keys in env for this to work
        if not os.getenv("CDP_API_KEY_ID"):
            self.skipTest("CDP keys not found in environment")
            
        agent = VeritasAgent(name="TestAgent")
        self.assertEqual(agent.name, "TestAgent")
        self.assertIsNotNone(agent.account.address)
        
        await agent.shutdown()

if __name__ == "__main__":
    unittest.main()

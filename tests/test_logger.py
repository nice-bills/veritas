import unittest
import os
import json
from veritas.logger import VeritasLogger

class TestLogger(unittest.TestCase):
    def setUp(self):
        self.logger = VeritasLogger()

    def test_log_action(self):
        entry = self.logger.log_action("tool_test", {"param": 1}, "result_test")
        self.assertEqual(entry.tool_name, "tool_test")
        self.assertEqual(entry.event_type, "ACTION") # Default
        self.assertEqual(self.logger.last_event_id, entry.id)

    def test_semantic_methods(self):
        # Observation
        obs_id = self.logger.observe("market_api", {}, {"price": 100})
        self.assertTrue(obs_id)
        
        # Action with basis
        act_id = self.logger.act("trade_tool", {}, "success", basis_id=obs_id)
        
        logs = self.logger.get_logs()
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[1].basis_id, obs_id)

    def test_export(self):
        filename = "test_export.json"
        self.logger.log_action("tool_a", {}, "ok")
        self.logger.export_proofs(filename)
        
        self.assertTrue(os.path.exists(filename))
        
        with open(filename, "r") as f:
            data = json.load(f)
            self.assertIn("session_root", data)
            self.assertEqual(len(data["logs"]), 1)
        
        # Cleanup
        os.remove(filename)

if __name__ == "__main__":
    unittest.main()

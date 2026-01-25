import unittest
import os
import json
from veritas.logger import VeritasLogger


class TestLogger(unittest.TestCase):
    def setUp(self):
        self.logger = VeritasLogger()

    def test_log_action(self):
        """Test basic action logging."""
        entry = self.logger.log_action("tool_test", {"param": 1}, "result_test")
        self.assertEqual(entry.tool_name, "tool_test")
        self.assertEqual(entry.event_type, "ACTION")  # Default
        self.assertEqual(self.logger.last_event_id, entry.id)
        self.assertIsNotNone(entry.id)
        self.assertIsNotNone(entry.timestamp)

    def test_log_observation(self):
        """Test observation logging."""
        entry = self.logger.log_action("market_api", {}, {"price": 100}, event_type="OBSERVATION")
        self.assertEqual(entry.event_type, "OBSERVATION")
        self.assertTrue(entry.id)

    def test_basis_chaining(self):
        """Test that actions can be chained to observations."""
        obs_id = self.logger.log_action(
            "market_api", {}, {"price": 100}, event_type="OBSERVATION"
        ).id

        act_entry = self.logger.log_action("trade_tool", {}, "success", basis_id=obs_id)

        logs = self.logger.get_logs()
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[1].basis_id, obs_id)

    def test_get_current_root(self):
        """Test Merkle root generation."""
        self.logger.log_action("tool_a", {}, "ok")
        self.logger.log_action("tool_b", {}, "ok2")

        root = self.logger.get_current_root()
        self.assertIsNotNone(root)
        # Root could be hex or bytes, just check it's not empty
        self.assertTrue(len(root) > 0)

    def test_get_logs(self):
        """Test log retrieval."""
        self.logger.log_action("tool_a", {}, "result_a")
        self.logger.log_action("tool_b", {}, "result_b")

        logs = self.logger.get_logs()
        self.assertEqual(len(logs), 2)
        self.assertEqual(logs[0].tool_name, "tool_a")
        self.assertEqual(logs[1].tool_name, "tool_b")

    def test_export(self):
        """Test session export."""
        filename = "test_export.json"
        self.logger.log_action("tool_a", {}, "ok")
        self.logger.log_action("tool_b", {"param": "test"}, "result")

        root = self.logger.get_current_root()
        logs = self.logger.get_logs()

        export_data = {
            "session_root": root,
            "logs": [log.model_dump(mode="json") for log in logs],
        }

        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2)

        self.assertTrue(os.path.exists(filename))

        with open(filename, "r") as f:
            data = json.load(f)
            self.assertIn("session_root", data)
            self.assertEqual(len(data["logs"]), 2)

        # Cleanup
        os.remove(filename)

    def test_wrapper_decorator_sync(self):
        """Test the @wrap decorator for sync functions."""

        @self.logger.wrap(tool_name="wrapped_tool")
        def simple_function(x, y):
            return x + y

        result = simple_function(1, 2)
        self.assertEqual(result, 3)

        logs = self.logger.get_logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].tool_name, "wrapped_tool")
        self.assertIn("3", logs[0].output_result)

    def test_wrapper_decorator_async(self):
        """Test the @wrap decorator for async functions."""
        import asyncio

        @self.logger.wrap(tool_name="async_tool", event_type="ACTION")
        async def async_function(value):
            await asyncio.sleep(0.01)
            return value * 2

        result = asyncio.run(async_function(5))
        self.assertEqual(result, 10)

        logs = self.logger.get_logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].tool_name, "async_tool")
        self.assertEqual(logs[0].event_type, "ACTION")

    def test_listeners(self):
        """Test event listeners."""
        received = []

        def listener(entry):
            received.append(entry.id)

        self.logger.listeners.append(listener)

        self.logger.log_action("tool_a", {}, "result_a")

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], self.logger.last_event_id)


if __name__ == "__main__":
    unittest.main()

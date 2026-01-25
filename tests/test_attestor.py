import unittest
from unittest.mock import MagicMock, patch
from veritas.attestor import VeritasAttestor


class TestAttestor(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.mock_account = MagicMock()
        self.mock_account.address = "0xAgentAddress"
        self.mock_account.key = b"private_key_bytes"

        self.attestor = VeritasAttestor(self.mock_client, self.mock_account)

    @patch("veritas.attestor.Web3")
    async def test_attest_root_success(self, MockWeb3):
        # Setup Mock Web3
        mock_w3 = MagicMock()
        MockWeb3.return_value = mock_w3
        MockWeb3.HTTPProvider.return_value = MagicMock()

        # Mock Connection
        mock_w3.is_connected.return_value = True

        # Mock Gas/Nonce
        mock_w3.eth.gas_price = 1000000000
        mock_w3.eth.get_transaction_count.return_value = 5

        # Mock Signing
        mock_signed_tx = MagicMock()
        mock_signed_tx.raw_transaction = b"raw_tx_bytes"
        mock_w3.eth.account.sign_transaction.return_value = mock_signed_tx

        # Mock Broadcast
        mock_w3.eth.send_raw_transaction.return_value = b"tx_hash_bytes"
        mock_w3.to_hex.return_value = "0xTransactionHash"

        # Execute
        result = await self.attestor.attest_root("0x" + "00" * 32, "schema_uid")

        # Verify - just check it returns something and doesn't raise
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()

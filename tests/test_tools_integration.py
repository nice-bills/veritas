import unittest
import sys
import os

# Add src to path so we can import veritas
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from unittest.mock import MagicMock, patch
from veritas.tools.token import TokenCapability
from veritas.tools.nft import ERC721Capability, BasenameCapability
from veritas.tools.defi import AaveCapability, CompoundCapability
from veritas.tools.infra import PythCapability, OnrampCapability
from veritas.tools.base import WalletCapability
from decimal import Decimal


class TestVeritasTools(unittest.TestCase):
    def setUp(self):
        # Mock Agent
        self.mock_agent = MagicMock()
        self.mock_agent.account.address = "0x1234567890123456789012345678901234567890"
        self.mock_agent.network = "base-sepolia"

        # Mock Web3
        self.mock_w3 = MagicMock()
        self.mock_agent.w3 = self.mock_w3
        self.mock_w3.to_checksum_address.side_effect = lambda x: x  # Identity for test
        self.mock_w3.eth.gas_price = 1000000000
        self.mock_w3.eth.get_transaction_count.return_value = 5
        self.mock_w3.to_hex.return_value = "0xhash"

        # Mock Contract
        self.mock_contract = MagicMock()
        self.mock_w3.eth.contract.return_value = self.mock_contract

        # Mock Contract Functions
        self.mock_contract.functions.transfer.return_value.build_transaction.return_value = {
            "data": "0x123"
        }
        self.mock_contract.functions.approve.return_value.build_transaction.return_value = {
            "data": "0x456"
        }
        self.mock_contract.functions.deposit.return_value.build_transaction.return_value = {
            "data": "0x789"
        }
        self.mock_contract.functions.withdraw.return_value.build_transaction.return_value = {
            "data": "0xabc"
        }
        self.mock_contract.functions.balanceOf.return_value.call.return_value = (
            1000000000000000000  # 1 ETH/Token
        )
        self.mock_contract.functions.decimals.return_value.call.return_value = 18
        self.mock_contract.functions.symbol.return_value.call.return_value = "TST"

        # Mock Account Sign
        self.mock_w3.eth.account.sign_transaction.return_value.raw_transaction = b"signed_tx"

    def test_wallet_capability(self):
        print("\nTesting Wallet Capability...")
        cap = WalletCapability(self.mock_agent)

        # Test Get Balance
        self.mock_w3.eth.get_balance.return_value = 5000000000000000000  # 5 ETH
        self.mock_w3.from_wei.return_value = Decimal("5.0")
        bal = cap.get_balance()
        self.assertEqual(bal["balance_eth"], 5.0)
        print("OK: Wallet Balance")

    def test_token_capability(self):
        print("\nTesting Token Capability (ERC20/WETH)...")
        cap = TokenCapability(self.mock_agent)

        # Test ERC20 Transfer
        res = cap.transfer("0xtoken", "0xrecipient", "1.0")
        self.assertEqual(res["status"], "success")
        self.mock_contract.functions.transfer.assert_called()
        print("OK: ERC20 Transfer")

        # Test WETH Wrap
        res = cap.wrap_eth("0.5")
        self.assertEqual(res["status"], "success")
        self.mock_contract.functions.deposit.return_value.build_transaction.assert_called()
        print("OK: WETH Wrap")

    def test_nft_capability(self):
        print("\nTesting NFT Capability...")
        cap = ERC721Capability(self.mock_agent)

        # Test Transfer
        cap.transfer("0xnft", "0xrecipient", 1)
        self.mock_contract.functions.safeTransferFrom.assert_called()
        print("OK: NFT Transfer")

    def test_basename_capability(self):
        print("\nTesting Basename Capability...")
        cap = BasenameCapability(self.mock_agent)

        # Test Register
        res = cap.register("myname")
        self.assertEqual(res["basename"], "myname.basetest.eth")  # Sepolia defaults
        self.mock_contract.functions.register.assert_called()
        print("OK: Basename Register")

    def test_defi_capability(self):
        print("\nTesting DeFi Capability (Aave)...")
        cap = AaveCapability(self.mock_agent)

        # Mock Supply
        self.mock_contract.functions.supply.return_value.build_transaction.return_value = {
            "data": "0xsupply"
        }

        res = cap.supply("USDC", "100")
        self.assertEqual(res["status"], "success")
        self.mock_contract.functions.supply.assert_called()
        print("OK: Aave Supply")

    def test_infra_capability(self):
        print("\nTesting Infra Capability (Pyth)...")
        cap = PythCapability(self.mock_agent)

        # Mock Pyth Price - just verify it doesn't crash
        self.mock_contract.functions.getPrice.return_value.call.return_value = (
            200000000000,
            100,
            -8,
            1234567890,
        )

        res = cap.get_price("0x" + "feed" * 16)
        self.assertIn("price", res)
        print("OK: Pyth Price")


if __name__ == "__main__":
    unittest.main()

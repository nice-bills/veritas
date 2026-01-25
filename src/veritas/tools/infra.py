from typing import Any, Dict
from .base import VeritasCapability, VeritasTool
from .constants import PYTH_ABI, CHAINLINK_ABI, CHAINLINK_FEED_ADDRESSES


class PythCapability(VeritasCapability):
    """
    Interact with Pyth Oracles.
    """

    def __init__(self, agent: Any):
        super().__init__("pyth")
        self.agent = agent

        self.tools.append(
            VeritasTool(
                name="get_price",
                description="Get the price of an asset from Pyth Oracle.",
                func=self.get_price,
                parameters={
                    "type": "object",
                    "properties": {
                        "price_feed_id": {
                            "type": "string",
                            "description": "The Pyth Price Feed ID (hex)",
                        }
                    },
                    "required": ["price_feed_id"],
                },
            )
        )

    def get_price(self, price_feed_id: str) -> Dict[str, Any]:
        # Pyth Contract on Base Sepolia
        raw_address = "0xA2aa501b19aff244D90cc15a4Cf739D2725B5729"
        contract_address = self.agent.w3.to_checksum_address(raw_address)
        contract = self.agent.w3.eth.contract(address=contract_address, abi=PYTH_ABI)

        # Use getPriceUnsafe to bypass staleness checks common on testnets
        # Convert hex string to bytes32 for contract
        if isinstance(price_feed_id, str):
            clean_id = price_feed_id.strip()
            if clean_id.startswith("0x"):
                clean_id = clean_id[2:]
            feed_id_bytes = bytes.fromhex(clean_id[:64])  # Force 32 bytes
        else:
            feed_id_bytes = price_feed_id

        price_data = contract.functions.getPriceUnsafe(feed_id_bytes).call()
        # Struct: price, conf, expo, publishTime
        price = price_data[0]
        expo = price_data[2]

        real_price = price * (10**expo)
        return {"price": real_price, "feed_id": price_feed_id}


class OnrampCapability(VeritasCapability):
    """
    Generate Coinbase Onramp URLs.
    """

    def __init__(self, agent: Any):
        super().__init__("onramp")
        self.agent = agent

        self.tools.append(
            VeritasTool(
                name="get_buy_url",
                description="Get a URL to buy crypto via Coinbase Onramp.",
                func=self.get_buy_url,
                parameters={
                    "type": "object",
                    "properties": {
                        "asset": {
                            "type": "string",
                            "description": "Asset to buy (e.g. USDC)",
                        },
                        "network": {
                            "type": "string",
                            "description": "Network (e.g. base)",
                        },
                    },
                    "required": ["asset"],
                },
            )
        )

    def get_buy_url(self, asset: str, network: str = "base") -> str:
        # Simulated URL generation
        address = self.agent.account.address
        return f"https://pay.coinbase.com/buy/select-asset?appId=veritas&destinationWallets=[{{'address': '{address}', 'blockchains': ['{network}']}}]"


class ChainlinkCapability(VeritasCapability):
    """
    Interact with Chainlink Price Feeds.
    Free to use, works on both Base Mainnet and Sepolia.
    """

    def __init__(self, agent: Any):
        super().__init__("chainlink")
        self.agent = agent

        self.tools.append(
            VeritasTool(
                name="get_price",
                description="Get the price of an asset from Chainlink Oracle. Available pairs: ETH/USD, BTC/USD, USDC/USD.",
                func=self.get_price,
                parameters={
                    "type": "object",
                    "properties": {
                        "pair": {
                            "type": "string",
                            "description": "Price pair (e.g., ETH/USD, BTC/USD)",
                        }
                    },
                    "required": ["pair"],
                },
            )
        )

    def get_price(self, pair: str) -> Dict[str, Any]:
        network_id = getattr(self.agent, "network", "base-sepolia")
        feeds = CHAINLINK_FEED_ADDRESSES.get(
            network_id, CHAINLINK_FEED_ADDRESSES.get("base-sepolia")
        )

        if pair not in feeds:
            available = list(feeds.keys())
            raise ValueError(f"Pair {pair} not available. Available pairs: {available}")

        raw_address = feeds[pair]
        contract_address = self.agent.w3.to_checksum_address(raw_address)
        contract = self.agent.w3.eth.contract(
            address=contract_address, abi=CHAINLINK_ABI
        )

        round_data = contract.functions.latestRoundData().call()
        price = round_data[1]  # answer
        decimals = contract.functions.decimals().call()
        updated_at = round_data[3]

        real_price = price / (10**decimals)
        return {
            "pair": pair,
            "price": round(real_price, 2),
            "decimals": decimals,
            "updated_at": updated_at,
            "feed_address": raw_address,
        }

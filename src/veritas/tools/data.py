from typing import Any, Dict
from .base import VeritasCapability, VeritasTool
from ..abis import PYTH_ABI

class DataCapability(VeritasCapability):
    """
    Market Data tools (Pyth Oracle).
    """
    def __init__(self, agent: Any):
        super().__init__("data")
        self.agent = agent
        self.pyth_address = "0xA2aa501b19aff244D90cc15a4Cf739D2725B5729" # Base Sepolia
        
        self.tools.append(VeritasTool(
            name="get_price",
            description="Get real-time price from Pyth Network oracle.",
            func=self.get_price,
            parameters={
                "type": "object",
                "properties": {
                    "price_id": {"type": "string", "description": "Pyth Price ID (hex)"}
                },
                "required": ["price_id"]
            }
        ))

    def get_price(self, price_id: str) -> Dict[str, Any]:
        w3 = self.agent.w3
        contract = w3.eth.contract(address=self.pyth_address, abi=PYTH_ABI)
        
        # Clean ID
        if not price_id.startswith("0x"): price_id = "0x" + price_id
        
        # Try getPriceUnsafe which is better for testnets
        data = contract.functions.getPriceUnsafe(bytes.fromhex(price_id[2:])).call()
        
        # Parse struct
        # Output: (price, conf, expo, timestamp)
        price_raw = data[0]
        expo = data[2]
        
        real_price = price_raw * (10 ** expo)
        
        return {
            "price": real_price,
            "raw": price_raw,
            "expo": expo,
            "timestamp": data[3]
        }

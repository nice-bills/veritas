from typing import Any, Dict, Optional
import requests
from .base import VeritasCapability, VeritasTool

class PaymentCapability(VeritasCapability):
    """
    x402 Internet-native micropayments and HTTP requests.
    """
    def __init__(self, agent: Any):
        super().__init__("payments")
        self.agent = agent
        
        self.tools.append(VeritasTool(
            name="http_request",
            description="Make an HTTP request (GET/POST).",
            func=self.http_request,
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to request"},
                    "method": {"type": "string", "description": "GET or POST"},
                    "body": {"type": "object", "description": "JSON body for POST"}
                },
                "required": ["url"]
            }
        ))

        self.tools.append(VeritasTool(
            name="pay_api_request",
            description="Execute an x402 payment for a restricted API endpoint.",
            func=self.pay_api_request,
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL requiring payment"},
                    "amount_usdc": {"type": "number", "description": "Amount to pay"}
                },
                "required": ["url", "amount_usdc"]
            }
        ))

    def http_request(self, url: str, method: str = "GET", body: Optional[Dict] = None) -> Dict[str, Any]:
        try:
            if method.upper() == "POST":
                resp = requests.post(url, json=body)
            else:
                resp = requests.get(url)
            return {"status": resp.status_code, "data": resp.text[:500]} # Truncate for safety
        except Exception as e:
            return {"error": str(e)}

    def pay_api_request(self, url: str, amount_usdc: float) -> Dict[str, Any]:
        # Logic to handle 402 Payment Required would go here
        # For now, we simulate the payment flow
        return {
            "status": "simulated_payment",
            "url": url,
            "amount": amount_usdc,
            "currency": "USDC"
        }
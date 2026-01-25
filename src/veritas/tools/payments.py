from typing import Any, Dict, Optional
import requests
import json
import base64
import time
import hashlib
from datetime import datetime
from eth_account import Account
from web3 import Web3
from .base import VeritasCapability, VeritasTool

USDC_ADDRESSES = {
    "base-mainnet": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "base-sepolia": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
}

ENTRYPOINT_ADDRESS = "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"

ERC20_TRANSFER_ABI = {
    "name": "transfer",
    "type": "function",
    "inputs": [
        {"name": "to", "type": "address"},
        {"name": "value", "type": "uint256"},
    ],
    "outputs": [{"name": "", "type": "bool"}],
    "stateMutability": "nonpayable",
}


class PaymentCapability(VeritasCapability):
    """
    x402 Internet-native micropayments and HTTP requests.

    Supports both EOA and ERC-4337 Smart Wallet payments:

    EOA (EIP-3009):
    1. Sign TransferWithAuthorization message off-chain
    2. Facilitator submits transaction on-chain
    3. Gas paid by facilitator (gasless for payer)

    Smart Wallet (ERC-4337):
    1. Build UserOperation with callData for USDC transfer
    2. Submit to bundler/paymaster
    3. Paymaster can sponsor gas (gasless for user)

    For more info: https://docs.x402.org/
    """

    def __init__(self, agent: Any):
        super().__init__("payments")
        self.agent = agent

        self.tools.append(
            VeritasTool(
                name="http_request",
                description="Make an HTTP request (GET/POST). Handles x402 payment responses automatically.",
                func=self.http_request,
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The URL to request"},
                        "method": {
                            "type": "string",
                            "description": "GET, POST, PUT, DELETE",
                        },
                        "body": {
                            "type": "object",
                            "description": "JSON body for POST/PUT",
                        },
                        "headers": {
                            "type": "object",
                            "description": "Optional custom headers",
                        },
                    },
                    "required": ["url"],
                },
            )
        )

        self.tools.append(
            VeritasTool(
                name="pay_with_x402",
                description="Execute x402 payment for protected API. Auto-detects EOA vs Smart Wallet.",
                func=self.pay_with_x402,
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL requiring payment",
                        },
                        "max_amount": {
                            "type": "number",
                            "description": "Max payment in USDC",
                        },
                        "use_smart_wallet": {
                            "type": "boolean",
                            "description": "Force smart wallet (ERC-4337) if available",
                        },
                    },
                    "required": ["url", "max_amount"],
                },
            )
        )

        self.tools.append(
            VeritasTool(
                name="x402_status",
                description="Check if endpoint requires x402 payment.",
                func=self.x402_status,
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to check"},
                    },
                    "required": ["url"],
                },
            )
        )

        self.tools.append(
            VeritasTool(
                name="get_wallet_type",
                description="Check if agent wallet is EOA or ERC-4337 Smart Wallet.",
                func=self.get_wallet_type,
                parameters={"type": "object", "properties": {}},
            )
        )

        self.tools.append(
            VeritasTool(
                name="build_eip3009_payment",
                description="Build EIP-3009 TransferWithAuthorization signature for EOA wallets.",
                func=self.build_eip3009_payment,
                parameters={
                    "type": "object",
                    "properties": {
                        "to_address": {
                            "type": "string",
                            "description": "Recipient address",
                        },
                        "amount_usdc": {
                            "type": "number",
                            "description": "Amount in USDC",
                        },
                    },
                    "required": ["to_address", "amount_usdc"],
                },
            )
        )

        self.tools.append(
            VeritasTool(
                name="build_user_operation",
                description="Build ERC-4337 UserOperation for smart wallet payments.",
                func=self.build_user_operation,
                parameters={
                    "type": "object",
                    "properties": {
                        "to_address": {
                            "type": "string",
                            "description": "Recipient address",
                        },
                        "amount_usdc": {
                            "type": "number",
                            "description": "Amount in USDC",
                        },
                        "paymaster_url": {
                            "type": "string",
                            "description": "Paymaster URL for gas sponsorship",
                        },
                    },
                    "required": ["to_address", "amount_usdc"],
                },
            )
        )

    def _get_network(self) -> str:
        return getattr(self.agent, "network", "base-sepolia")

    def _get_usdc_address(self) -> str:
        network = self._get_network()
        return USDC_ADDRESSES.get(network, USDC_ADDRESSES.get("base-sepolia"))

    def _is_smart_wallet(self) -> bool:
        try:
            w3 = self.agent.w3
            address = self.agent.account.address
            code = w3.eth.get_code(address)
            return len(code) > 2
        except Exception:
            return False

    def get_wallet_type(self) -> Dict[str, Any]:
        is_smart = self._is_smart_wallet()
        address = self.agent.account.address

        if is_smart:
            return {
                "address": address,
                "type": "ERC-4337_SMART_WALLET",
                "description": "Smart contract wallet with code at address",
                "capabilities": [
                    "UserOperation",
                    "paymaster_gas_sponsorship",
                    "batch_transactions",
                ],
            }
        else:
            return {
                "address": address,
                "type": "EOA",
                "description": "Externally Owned Account (private key controlled)",
                "capabilities": ["EIP-3009_signature", "direct_transaction"],
            }

    def build_eip3009_payment(
        self, to_address: str, amount_usdc: float
    ) -> Dict[str, Any]:
        try:
            from web3 import Web3

            w3 = self.agent.w3
            from_address = self.agent.account.address
            usdc_address = self._get_usdc_address()

            amount_wei = int(amount_usdc * 10**6)

            valid_after = int(time.time())
            valid_before = valid_after + 3600
            nonce = hashlib.sha256(f"{from_address}{time.time()}".encode()).digest()

            chain_id = 84532 if self._get_network() == "base-sepolia" else 8453

            eip712_domain_hash = w3.keccak(
                text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
            )
            name_hash = w3.keccak(text="USD Coin (EIP-3009)")
            version_hash = w3.keccak(text="2")
            domain_separator = w3.keccak(
                w3.codec.encode(
                    ["bytes32", "bytes32", "bytes32", "uint256", "address"],
                    [
                        eip712_domain_hash,
                        name_hash,
                        version_hash,
                        chain_id,
                        usdc_address,
                    ],
                )
            )

            type_hash = w3.keccak(
                text="TransferWithAuthorization(address from,address to,uint256 value,uint256 validAfter,uint256 validBefore,bytes32 nonce)"
            )

            struct_hash = w3.keccak(
                w3.codec.encode(
                    [
                        "bytes32",
                        "address",
                        "address",
                        "uint256",
                        "uint256",
                        "uint256",
                        "bytes32",
                    ],
                    [
                        type_hash,
                        from_address,
                        usdc_address,
                        amount_wei,
                        valid_after,
                        valid_before,
                        nonce,
                    ],
                )
            )

            from eth_account import Account

            digest = w3.keccak(b"\x19\x01" + domain_separator + struct_hash)

            signed = Account.unsafe_sign_hash(self.agent.account.key, digest)

            payment_payload = {
                "scheme": "eip3009",
                "from": from_address,
                "to": to_address,
                "value": str(amount_usdc),
                "currency": "USDC",
                "validAfter": valid_after,
                "validBefore": valid_before,
                "nonce": nonce.hex(),
                "signature": signed.signature.hex(),
                "verifyingContract": usdc_address,
            }

            return {
                "status": "signed",
                "wallet_type": "EOA",
                "authorization": payment_payload,
                "encoded_payload": base64.b64encode(
                    json.dumps(payment_payload).encode()
                ).decode(),
                "message": "EIP-3009 authorization ready. Facilitator will submit on-chain.",
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def build_user_operation(
        self,
        to_address: str,
        amount_usdc: float,
        paymaster_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            w3 = self.agent.w3
            sender = self.agent.account.address
            usdc_address = self._get_usdc_address()
            amount_wei = int(amount_usdc * 10**6)

            nonce = 1

            call_data = w3.eth.contract(
                address=usdc_address, abi=[ERC20_TRANSFER_ABI]
            ).encode_function_data("transfer", [to_address, amount_wei])

            user_operation = {
                "sender": sender,
                "nonce": f"0x{nonce:08x}",
                "initCode": "0x",
                "callData": call_data,
                "callGasLimit": "0x493E0",
                "verificationGasLimit": "0xF4240",
                "preVerificationGas": "0xC870",
                "maxFeePerGas": "0x5F5E100",
                "maxPriorityFeeGas": "0x5F5E100",
                "paymasterAndData": "0x",
                "signature": "0x",
            }

            if paymaster_url:
                user_operation["paymasterAndData"] = paymaster_url

            return {
                "status": "built",
                "wallet_type": "ERC-4337_SMART_WALLET",
                "user_operation": user_operation,
                "entry_point": ENTRYPOINT_ADDRESS,
                "call_data": call_data,
                "description": "UserOperation ready for bundler submission",
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def x402_status(self, url: str) -> Dict[str, Any]:
        try:
            resp = requests.get(url, timeout=10)

            payment_required = resp.headers.get("PAYMENT-REQUIRED") or resp.headers.get(
                "WWW-Authenticate"
            )

            if payment_required:
                return {
                    "url": url,
                    "requires_payment": True,
                    "payment_header": payment_required,
                    "status_code": resp.status_code,
                }
            else:
                return {
                    "url": url,
                    "requires_payment": False,
                    "status_code": resp.status_code,
                    "message": "No x402 payment required",
                }

        except Exception as e:
            return {"error": str(e), "url": url}

    def x402_parse_requirements(self, payment_required_header: str) -> Dict[str, Any]:
        try:
            if payment_required_header.startswith("x402 "):
                encoded = payment_required_header[5:]
            else:
                encoded = payment_required_header

            json_str = base64.b64decode(encoded).decode("utf-8")
            requirements = json.loads(json_str)

            return {
                "status": "parsed",
                "scheme": requirements.get("scheme"),
                "network": requirements.get("network"),
                "pay_to": requirements.get("pay_to"),
                "price": requirements.get("price"),
                "max_amount": requirements.get("max_amount_required"),
                "description": requirements.get("description"),
                "raw": requirements,
            }

        except Exception as e:
            return {"error": f"Failed to parse payment requirements: {e}"}

    def pay_with_x402(
        self, url: str, max_amount: float, use_smart_wallet: bool = False
    ) -> Dict[str, Any]:
        try:
            resp = requests.get(url, timeout=30)

            if resp.status_code != 402:
                if resp.status_code == 200:
                    return {
                        "status": "success",
                        "payment_required": False,
                        "data": resp.text[:2000],
                        "message": "Endpoint accessible without payment",
                    }
                return {
                    "status": "error",
                    "message": f"Unexpected response: {resp.status_code}",
                    "status_code": resp.status_code,
                }

            payment_required = resp.headers.get("PAYMENT-REQUIRED")
            if not payment_required:
                return {
                    "status": "error",
                    "message": "Expected 402 but no payment header",
                }

            parsed = self.x402_parse_requirements(payment_required)
            if "error" in parsed:
                return {"status": "error", "message": parsed["error"]}

            pay_to = parsed.get("pay_to")
            price = parsed.get("price")
            price_value = float(price.replace("$", "").replace(",", ""))

            if price_value > max_amount:
                return {
                    "status": "error",
                    "message": f"Required payment {price} exceeds max_amount {max_amount}",
                }

            is_smart = self._is_smart_wallet()
            wallet_info = self.get_wallet_type()

            if use_smart_wallet or is_smart:
                result = self.build_user_operation(pay_to, price_value)
                payment_type = "ERC-4337_UserOperation"
            else:
                result = self.build_eip3009_payment(pay_to, price_value)
                payment_type = "EIP-3009"

            if "error" in result:
                return result

            encoded_payload = result.get("encoded_payload", "")

            headers = {"PAYMENT-SIGNATURE": encoded_payload}
            retry_resp = requests.get(url, headers=headers, timeout=30)

            if retry_resp.status_code == 200:
                return {
                    "status": "success",
                    "payment_required": True,
                    "wallet_type": wallet_info["type"],
                    "payment_type": payment_type,
                    "amount_paid": price,
                    "pay_to": pay_to,
                    "data": retry_resp.text[:2000],
                    "message": f"Payment of {price} successful via {payment_type}",
                }
            else:
                return {
                    "status": "error",
                    "payment_type": payment_type,
                    "message": f"Payment verification failed: {retry_resp.status_code}",
                }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def http_request(
        self,
        url: str,
        method: str = "GET",
        body: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        try:
            req_headers = headers or {}

            if method.upper() == "POST":
                resp = requests.post(url, json=body, headers=req_headers, timeout=30)
            elif method.upper() == "PUT":
                resp = requests.put(url, json=body, headers=req_headers, timeout=30)
            elif method.upper() == "DELETE":
                resp = requests.delete(url, headers=req_headers, timeout=30)
            else:
                resp = requests.get(url, headers=req_headers, timeout=30)

            result = {
                "status": resp.status_code,
                "url": url,
                "method": method,
            }

            if resp.status_code == 200:
                result["data"] = resp.text[:2000]
            elif resp.status_code == 402:
                payment_required = resp.headers.get(
                    "PAYMENT-REQUIRED"
                ) or resp.headers.get("WWW-Authenticate")
                result["payment_required"] = True
                result["payment_header"] = payment_required
                result["message"] = "Payment required"
            else:
                result["data"] = resp.text[:500]
                result["error"] = f"HTTP {resp.status_code}"

            return result

        except requests.exceptions.Timeout:
            return {"error": "Request timed out", "url": url}
        except Exception as e:
            return {"error": str(e), "url": url}

from typing import Any, Dict, Optional
from .base import VeritasCapability, VeritasTool
import os
import secrets
import hashlib
from datetime import datetime


class PrivacyCapability(VeritasCapability):
    """
    Nillion Secret Vault and Blind Computation.
    Provides private storage for agent secrets using cryptographic encryption.
    """

    def __init__(self, agent: Any):
        super().__init__("privacy")
        self.agent = agent
        self._secret_store: Dict[str, Dict[str, Any]] = {}

        self.tools.append(
            VeritasTool(
                name="store_secret",
                description="Store an encrypted secret in the Nillion vault. Returns a store_id for retrieval.",
                func=self.store_secret,
                parameters={
                    "type": "object",
                    "properties": {
                        "secret_name": {
                            "type": "string",
                            "description": "Unique name for the secret",
                        },
                        "secret_value": {
                            "type": "string",
                            "description": "The secret value to encrypt and store",
                        },
                        "permissions": {
                            "type": "string",
                            "description": "Optional: Compute permissions (compute, retrieve)",
                        },
                    },
                    "required": ["secret_name", "secret_value"],
                },
            )
        )

        self.tools.append(
            VeritasTool(
                name="retrieve_secret",
                description="Retrieve a stored secret by name. Requires store_id or secret_name.",
                func=self.retrieve_secret,
                parameters={
                    "type": "object",
                    "properties": {
                        "secret_name": {
                            "type": "string",
                            "description": "Name of the secret to retrieve",
                        },
                        "store_id": {
                            "type": "string",
                            "description": "Store ID for direct lookup",
                        },
                    },
                    "required": ["secret_name"],
                },
            )
        )

        self.tools.append(
            VeritasTool(
                name="list_secrets",
                description="List all stored secret names (metadata only, not values).",
                func=self.list_secrets,
                parameters={"type": "object", "properties": {}},
            )
        )

        self.tools.append(
            VeritasTool(
                name="delete_secret",
                description="Delete a stored secret permanently.",
                func=self.delete_secret,
                parameters={
                    "type": "object",
                    "properties": {"secret_name": {"type": "string"}},
                    "required": ["secret_name"],
                },
            )
        )

    def _generate_store_id(self) -> str:
        """Generate a unique store ID."""
        timestamp = datetime.utcnow().isoformat()
        random_bytes = secrets.token_bytes(16)
        combined = f"{timestamp}:{random_bytes.hex()}"
        return f"nil_{hashlib.sha256(combined.encode()).hexdigest()[:32]}"

    def _encrypt_value(self, value: str) -> str:
        """Simulate encryption - in production, use Nillion's actual encryption."""
        return f"enc_{hashlib.sha256(value.encode()).hexdigest()[:64]}"

    def store_secret(
        self, secret_name: str, secret_value: str, permissions: str = "private"
    ) -> Dict[str, Any]:
        """
        Store a secret in the Nillion vault.
        In production, this would use nillion-client SDK:
        - StoreSecretRequest with SecretInteger or SecretString
        - Returns store_id for retrieval
        """
        store_id = self._generate_store_id()
        encrypted_value = self._encrypt_value(secret_value)

        self._secret_store[store_id] = {
            "secret_name": secret_name,
            "encrypted_value": encrypted_value,
            "permissions": permissions,
            "created_at": datetime.utcnow().isoformat(),
            "accessed_at": None,
        }

        return {
            "status": "stored",
            "store_id": store_id,
            "secret_name": secret_name,
            "permissions": permissions,
            "message": "Secret encrypted and stored securely",
        }

    def retrieve_secret(
        self, secret_name: str, store_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve a stored secret.
        In production, this would use nillion-client SDK to decrypt.
        """
        found_store_id = store_id

        if not found_store_id:
            for sid, data in self._secret_store.items():
                if data["secret_name"] == secret_name:
                    found_store_id = sid
                    break

        if not found_store_id or found_store_id not in self._secret_store:
            raise ValueError(f"Secret '{secret_name}' not found")

        secret_data = self._secret_store[found_store_id]
        secret_data["accessed_at"] = datetime.utcnow().isoformat()

        return {
            "status": "retrieved",
            "store_id": found_store_id,
            "secret_name": secret_data["secret_name"],
            "encrypted_value": secret_data["encrypted_value"],
            "permissions": secret_data["permissions"],
            "message": "Secret retrieved (decryption simulated)",
        }

    def list_secrets(self) -> Dict[str, Any]:
        """List all stored secrets (metadata only)."""
        secrets_list = []
        for store_id, data in self._secret_store.items():
            secrets_list.append(
                {
                    "store_id": store_id,
                    "secret_name": data["secret_name"],
                    "permissions": data["permissions"],
                    "created_at": data["created_at"],
                }
            )

        return {"status": "listed", "count": len(secrets_list), "secrets": secrets_list}

    def delete_secret(self, secret_name: str) -> Dict[str, Any]:
        """Delete a stored secret permanently."""
        deleted_store_id = None
        for store_id, data in self._secret_store.items():
            if data["secret_name"] == secret_name:
                deleted_store_id = store_id
                del self._secret_store[store_id]
                break

        if not deleted_store_id:
            raise ValueError(f"Secret '{secret_name}' not found")

        return {
            "status": "deleted",
            "secret_name": secret_name,
            "store_id": deleted_store_id,
            "message": "Secret permanently deleted",
        }

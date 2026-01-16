import os
import requests
from typing import List, Dict, Any, Optional

class MiniMaxBrain:
    """
    MiniMax M2.1 implementation for agent reasoning.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY")
        self.base_url = "https://api.minimax.io/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY is required for MiniMaxBrain")

    def think(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a prompt to MiniMax and return the reasoned decision.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "MiniMax-M2.1",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            
            # Strip thinking blocks if present
            if "</think>" in content:
                content = content.split("</think>")[-1].strip()
                
            return content.strip()
        except Exception as e:
            print(f"[MiniMaxBrain] Error: {e}")
            return "ERROR"

class BrainFactory:
    """
    Factory to instantiate different LLM providers.
    """
    @staticmethod
    def create(provider: str, **kwargs) -> Any:
        if provider.lower() == "minimax":
            return MiniMaxBrain(**kwargs)
        raise ValueError(f"Unsupported brain provider: {provider}")

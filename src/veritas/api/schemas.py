from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AgentCreate(BaseModel):
    name: str
    brain_provider: str = "minimax"
    network: str = "base-sepolia"
    private_key: Optional[str] = None
    capabilities: List[str] = ["wallet"] # List of caps to load: ['wallet', 'trading', 'social']
    # User-provided keys
    cdp_api_key_id: Optional[str] = None
    cdp_api_key_secret: Optional[str] = None
    minimax_api_key: Optional[str] = None

class MissionRequest(BaseModel):
    objective: str

class AgentResponse(BaseModel):
    id: str
    name: str
    address: str
    network: str

class MissionResponse(BaseModel):
    status: str
    session_root: str
    attestation_tx: Optional[str] = None
    logs: List[Dict[str, Any]]

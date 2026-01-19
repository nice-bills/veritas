from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .schemas import AgentCreate, MissionRequest, AgentResponse, MissionResponse
from ..agent import VeritasAgent
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import uuid
import json
import asyncio
import os
from typing import Dict, List

# Load environment variables
load_dotenv()

# Rate Limiter Setup
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Veritas Agent OS API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS Configuration
# In production, set CORS_ORIGINS="https://your-frontend.vercel.app"
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for active agents
active_agents: Dict[str, VeritasAgent] = {}

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, agent_id: str, websocket: WebSocket):
        await websocket.accept()
        if agent_id not in self.active_connections:
            self.active_connections[agent_id] = []
        self.active_connections[agent_id].append(websocket)

    def disconnect(self, agent_id: str, websocket: WebSocket):
        if agent_id in self.active_connections:
            self.active_connections[agent_id].remove(websocket)

    async def broadcast(self, agent_id: str, message: dict):
        if agent_id in self.active_connections:
            for connection in self.active_connections[agent_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()

@app.get("/")
async def root():
    return {"status": "online", "version": "0.1.0"}

@app.post("/agents", response_model=AgentResponse)
@limiter.limit("5/minute")
async def create_agent(request: Request, config: AgentCreate):
    # 0. Safety Guardrail
    if config.network != "base-sepolia" and not os.getenv("ENABLE_MAINNET"):
        raise HTTPException(status_code=400, detail="Mainnet deployment is currently disabled for beta. Use 'base-sepolia'.")

    agent_id = str(uuid.uuid4())
    try:
        agent = VeritasAgent(
            name=config.name,
            brain_provider=config.brain_provider,
            network=config.network,
            private_key=config.private_key,
            cdp_api_key_id=config.cdp_api_key_id,
            cdp_api_key_secret=config.cdp_api_key_secret,
            minimax_api_key=config.minimax_api_key
        )
        
        # 1. Auto-Funding (Faucet)
        if config.network == "base-sepolia":
            try:
                # Check balance
                wei_bal = agent.w3.eth.get_balance(agent.account.address)
                if wei_bal == 0:
                    print(f"[API] Wallet {agent.account.address} empty. Requesting Faucet...")
                    await agent.client.evm.request_faucet(
                        address=agent.account.address,
                        network="base-sepolia",
                        token="eth"
                    )
                    await asyncio.sleep(2) 
            except Exception as fe:
                print(f"[API] Faucet skipped: {fe}")

        # 2. Setup Real-Time Log Listener
        def on_new_log(log_entry):
            asyncio.create_task(manager.broadcast(agent_id, log_entry.model_dump(mode='json')))
        
        agent.logger.listeners.append(on_new_log)

        # 3. Load capabilities
        from ..tools import (
            WalletCapability, TradeCapability, TokenCapability,
            ERC721Capability, BasenameCapability,
            SocialCapability, PaymentCapability,
            CreatorCapability, PrivacyCapability, AaveCapability,
            CompoundCapability, PythCapability, OnrampCapability
        )
        
        CAP_MAP = {
            "wallet": WalletCapability, "trading": TradeCapability, "token": TokenCapability,
            "nft": ERC721Capability, "basename": BasenameCapability,
            "social": SocialCapability, "payments": PaymentCapability,
            "creator": CreatorCapability, "privacy": PrivacyCapability, "aave": AaveCapability,
            "compound": CompoundCapability, "pyth": PythCapability, "onramp": OnrampCapability
        }
        CAP_MAP["erc20"] = TokenCapability
        CAP_MAP["defi"] = AaveCapability
        CAP_MAP["data"] = PythCapability
        CAP_MAP["identity"] = BasenameCapability
        
        for cap_name in config.capabilities:
            if cap_name in CAP_MAP:
                agent.load_capability(CAP_MAP[cap_name](agent))
                
        active_agents[agent_id] = agent
        return {
            "id": agent_id,
            "name": agent.name,
            "address": agent.account.address,
            "network": agent.network
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/agents/{agent_id}/ws")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    await manager.connect(agent_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(agent_id, websocket)

@app.post("/agents/{agent_id}/run", response_model=MissionResponse)
@limiter.limit("10/minute")
async def run_mission(request: Request, agent_id: str, mission_req: MissionRequest):
    if agent_id not in active_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = active_agents[agent_id]
    try:
        # 1. Run Mission
        root = await agent.run_mission(mission_req.objective)
        
        # 2. On-Chain Attestation
        tx_hash = await agent.attestor.attest_root(
            merkle_root=root,
            agent_id=agent.name
        )
        
        # 3. Format Response
        return {
            "status": "success",
            "session_root": root,
            "attestation_tx": tx_hash,
            "logs": [log.model_dump(mode='json') for log in agent.logger.get_logs()]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/agents/{agent_id}")
async def stop_agent(agent_id: str):
    if agent_id in active_agents:
        await active_agents[agent_id].shutdown()
        del active_agents[agent_id]
        return {"status": "terminated"}
    raise HTTPException(status_code=404, detail="Agent not found")
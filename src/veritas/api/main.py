from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy import select
from .schemas import AgentCreate, MissionRequest, AgentResponse, MissionResponse
from ..agent import VeritasAgent, PersistentVeritasAgent
from ..database import AgentModel, SessionModel, LogModel, get_db_context, init_db, close_db
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import uuid
import asyncio
import os
from typing import Dict, List, Any
from web3 import Web3

load_dotenv()

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Veritas Agent OS API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[call-arg]
app.add_middleware(SlowAPIMiddleware)

# SECURITY: Only allow specific origins
# For development: localhost:3001 (frontend)
# For production: add your domain
allowed_origins = [
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
# Allow additional origins from env (for production)
if os.getenv("CORS_ORIGINS"):
    allowed_origins.extend(os.getenv("CORS_ORIGINS").split(","))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
)


@app.on_event("startup")
async def startup():
    await init_db()


@app.on_event("shutdown")
async def shutdown():
    await close_db()


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
            dead_connections = []
            for connection in self.active_connections[agent_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    # Log error and mark connection for removal
                    print(f"[WebSocket] Failed to send to agent {agent_id}: {e}")
                    dead_connections.append(connection)

            # Clean up dead connections
            for conn in dead_connections:
                self.disconnect(agent_id, conn)


manager = ConnectionManager()
active_agents: Dict[str, VeritasAgent] = {}
persistent_agents: Dict[str, Any] = {}


@app.get("/")
async def root():
    return {"status": "online", "version": "0.1.0"}


@app.post("/init-db")
async def init_database():
    await init_db()
    return {"status": "database initialized"}


@app.get("/debug/agents")
async def debug_agents():
    return {
        "active_agents": list(active_agents.keys()),
        "persistent_agents": list(persistent_agents.keys()),
    }


@app.get("/agents")
async def list_agents():
    async with get_db_context() as db:
        agents = await db.execute(select(AgentModel).order_by(AgentModel.created_at.desc()))
        result = []
        for a in agents.scalars().all():
            created = a.created_at.isoformat() if a.created_at else None
            result.append(
                {
                    "id": a.id,
                    "name": a.name,
                    "address": a.address,
                    "network": a.network,
                    "status": a.status or "active",
                    "created_at": created,
                }
            )
        return result


@app.post("/debug/clear-agents")
async def clear_agents():
    active_agents.clear()
    persistent_agents.clear()
    return {"status": "cleared"}


def load_agent_capabilities(agent, capabilities):
    from ..tools import (
        WalletCapability,
        TradeCapability,
        TokenCapability,
        ERC721Capability,
        BasenameCapability,
        SocialCapability,
        PaymentCapability,
        CreatorCapability,
        PrivacyCapability,
        AaveCapability,
        CompoundCapability,
        PythCapability,
        OnrampCapability,
        ChainlinkCapability,
    )

    CAP_MAP = {
        "wallet": WalletCapability,
        "trading": TradeCapability,
        "token": TokenCapability,
        "erc20": TokenCapability,  # Alias for token
        "nft": ERC721Capability,
        "basename": BasenameCapability,
        "identity": BasenameCapability,  # Alias for basename
        "social": SocialCapability,
        "payments": PaymentCapability,
        "creator": CreatorCapability,
        "privacy": PrivacyCapability,
        "aave": AaveCapability,
        "defi": AaveCapability,  # Alias for aave
        "compound": CompoundCapability,
        "pyth": PythCapability,
        "onramp": OnrampCapability,
        "chainlink": ChainlinkCapability,
        "data": ChainlinkCapability,  # Alias for chainlink
    }

    for cap_name in capabilities:
        if cap_name in CAP_MAP:
            agent.load_capability(CAP_MAP[cap_name](agent))


@app.post("/agents", response_model=AgentResponse)
@limiter.limit("5/minute")
async def create_agent(request: Request, config: AgentCreate):
    if config.network != "base-sepolia" and not os.getenv("ENABLE_MAINNET"):
        raise HTTPException(
            status_code=400,
            detail="Mainnet deployment is currently disabled for beta. Use 'base-sepolia'.",
        )

    agent_id = str(uuid.uuid4())
    try:
        agent = VeritasAgent(
            name=config.name,
            brain_provider=config.brain_provider,
            network=config.network,
            private_key=config.private_key,
            cdp_api_key_id=config.cdp_api_key_id,
            cdp_api_key_secret=config.cdp_api_key_secret,
            minimax_api_key=config.minimax_api_key,
        )

        if config.network == "base-sepolia":
            try:
                wei_bal = agent.w3.eth.get_balance(agent.account.address)
                min_balance = Web3.to_wei(0.001, "ether")
                if wei_bal < min_balance:
                    print(
                        f"[API] Wallet {agent.account.address} has {Web3.from_wei(wei_bal, 'ether')} ETH. Requesting faucet..."
                    )
                    for _ in range(3):
                        await agent.client.evm.request_faucet(
                            address=agent.account.address,
                            network="base-sepolia",
                            token="eth",
                        )
                        await asyncio.sleep(2)
                        new_bal = agent.w3.eth.get_balance(agent.account.address)
                        if new_bal >= min_balance:
                            print(f"[API] Faucet success: {Web3.from_wei(new_bal, 'ether')} ETH")
                            break
            except Exception as fe:
                print(f"[API] Faucet skipped: {fe}")

        def on_new_log(log_entry):
            asyncio.create_task(manager.broadcast(agent_id, log_entry.model_dump(mode="json")))

        agent.logger.listeners.append(on_new_log)

        load_agent_capabilities(agent, config.capabilities)

        async with get_db_context() as db:
            db_agent = AgentModel(
                id=agent_id,
                name=config.name,
                network=config.network,
                brain_provider=config.brain_provider,
                address=agent.account.address,
                private_key=config.private_key,
                capabilities=config.capabilities,
                config={
                    "cdp_api_key_id": config.cdp_api_key_id,
                    "cdp_api_key_secret": config.cdp_api_key_secret,
                    "minimax_api_key": config.minimax_api_key,
                },
            )
            db.add(db_agent)
            await db.commit()

        return {
            "id": agent_id,
            "name": agent.name,
            "address": agent.account.address,
            "network": agent.network,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        import traceback

        error_msg = traceback.format_exc()
        raise HTTPException(status_code=500, detail=error_msg)


@app.websocket("/agents/{agent_id}/ws")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    # Extract token from query parameters
    token = websocket.query_params.get("token")

    # Strip quotes if present (frontend may send quoted token)
    if token:
        token = token.strip("\"'")

    # Get expected token from environment variable
    expected_token = os.getenv("WEBSOCKET_TOKEN") or os.getenv("CDP_API_KEY_ID")
    if expected_token:
        expected_token = expected_token.strip("\"'")

    # Log authentication attempt
    client_host = websocket.client.host if websocket.client else "unknown"
    if not token:
        print(
            f"[WebSocket] Authentication failed for agent {agent_id}: missing token from {client_host}"
        )
        await websocket.close(code=403, reason="Missing authentication token")
        return

    if token != expected_token:
        print(
            f"[WebSocket] Authentication failed for agent {agent_id}: invalid token from {client_host}"
        )
        print(f"[WebSocket] Expected: {expected_token[:20]}... Received: {token[:20]}...")
        await websocket.close(code=403, reason="Invalid authentication token")
        return

    # Authentication successful
    print(f"[WebSocket] Authentication successful for agent {agent_id} from {client_host}")
    await manager.connect(agent_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(agent_id, websocket)
        print(f"[WebSocket] Client disconnected from agent {agent_id}")


@app.post("/agents/{agent_id}/run", response_model=MissionResponse)
@limiter.limit("10/minute")
async def run_mission(request: Request, agent_id: str, mission_req: MissionRequest):
    agent = None

    if agent_id in active_agents:
        agent = active_agents[agent_id]
    else:
        async with get_db_context() as db:
            db_agent = await db.get(AgentModel, agent_id)
            if not db_agent:
                raise HTTPException(status_code=404, detail="Agent not found")

            config = db_agent.config or {}

            agent = VeritasAgent(
                name=str(db_agent.name),
                brain_provider=str(db_agent.brain_provider)
                if db_agent.brain_provider is not None
                else "minimax",
                network=str(db_agent.network) if db_agent.network is not None else "base-sepolia",
                private_key=str(db_agent.private_key).strip()
                if db_agent.private_key is not None and str(db_agent.private_key) != ""
                else None,
                cdp_api_key_id=config.get("cdp_api_key_id") or "",
                cdp_api_key_secret=config.get("cdp_api_key_secret") or "",
                minimax_api_key=config.get("minimax_api_key") or "",
            )

            load_agent_capabilities(agent, db_agent.capabilities or [])

            def on_new_log(log_entry):
                asyncio.create_task(manager.broadcast(agent_id, log_entry.model_dump(mode="json")))

            agent.logger.listeners.append(on_new_log)

    session_id = str(uuid.uuid4())

    try:
        root = await agent.run_mission(mission_req.objective)

        # Try to attest on-chain, but don't fail if wallet has no ETH
        tx_hash = None
        try:
            tx_hash = await agent.attestor.attest_root(merkle_root=root, agent_id=agent.name)
        except Exception as att_err:
            if "insufficient funds" in str(att_err).lower():
                print(f"[API] Attestation skipped: Agent wallet has no ETH for gas")
            else:
                print(f"[API] Attestation failed: {att_err}")

        logs = agent.logger.get_logs()

        async with get_db_context() as db:
            session = SessionModel(
                id=session_id,
                agent_id=agent_id,
                objective=mission_req.objective,
                status="completed",
                session_root=root,
                attestation_tx=tx_hash,
            )
            db.add(session)

            for log in logs:
                db_log = LogModel(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    basis_id=log.basis_id,
                    event_type=log.event_type,
                    tool_name=log.tool_name,
                    input_params={},
                    output_result=str(log.output_result) if log.output_result else None,
                    timestamp=log.timestamp,
                    merkle_leaf=log.merkle_leaf if hasattr(log, "merkle_leaf") else "",
                )
                db.add(db_log)

            await db.commit()

        return {
            "status": "success",
            "session_root": root,
            "attestation_tx": tx_hash,
            "logs": [log.model_dump(mode="json") for log in logs],
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_id}/start")
async def start_persistent_agent(request: Request, agent_id: str, body: dict | None = None):
    if agent_id in persistent_agents:
        raise HTTPException(status_code=400, detail="Agent already running")

    try:
        async with get_db_context() as db:
            db_agent = await db.get(AgentModel, agent_id)
            if not db_agent:
                raise HTTPException(status_code=404, detail="Agent not found")

            config = db_agent.config or {}

            name_val = str(db_agent.name) if db_agent.name is not None else "Agent"
            brain_val = (
                str(db_agent.brain_provider) if db_agent.brain_provider is not None else "minimax"
            )
            network_val = str(db_agent.network) if db_agent.network is not None else "base-sepolia"
            private_raw = str(db_agent.private_key) if db_agent.private_key is not None else None
            private_val = private_raw.strip() if private_raw and private_raw.strip() != "" else None

            persistent_agent = PersistentVeritasAgent(
                name=name_val,
                brain_provider=brain_val,
                network=network_val,
                private_key=private_val,
                cdp_api_key_id=config.get("cdp_api_key_id") or "",
                cdp_api_key_secret=config.get("cdp_api_key_secret") or "",
                minimax_api_key=config.get("minimax_api_key") or "",
                agent_id=agent_id,
            )

            load_agent_capabilities(persistent_agent, db_agent.capabilities or [])

            def on_new_log(log_entry):
                asyncio.create_task(manager.broadcast(agent_id, log_entry.model_dump(mode="json")))

            persistent_agent.logger.listeners.append(on_new_log)

            persistent_agents[agent_id] = persistent_agent

            asyncio.create_task(persistent_agent.run_forever())

            return {
                "status": "started",
                "agent_id": agent_id,
                "name": persistent_agent.name,
            }
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_id}/stop")
async def stop_persistent_agent(agent_id: str):
    if agent_id not in persistent_agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent = persistent_agents[agent_id]
    await agent.stop()
    del persistent_agents[agent_id]

    async with get_db_context() as db:
        db_agent = await db.get(AgentModel, agent_id)
        if db_agent:
            object.__setattr__(db_agent, "status", "stopped")  # noqa: F841
            await db.commit()

    return {"status": "stopped", "agent_id": agent_id}


@app.post("/agents/{agent_id}/send")
async def send_message_to_agent(agent_id: str, body: dict):
    if agent_id not in persistent_agents:
        raise HTTPException(status_code=404, detail="Agent not found")

    message = body.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Message required")

    agent = persistent_agents[agent_id]
    await agent.send_message(message)

    return {"status": "message_sent", "agent_id": agent_id}


@app.delete("/agents/{agent_id}")
async def stop_agent(agent_id: str):
    if agent_id in active_agents:
        await active_agents[agent_id].shutdown()
        del active_agents[agent_id]

    if agent_id in persistent_agents:
        agent = persistent_agents[agent_id]
        await agent.stop()
        del persistent_agents[agent_id]

    async with get_db_context() as db:
        agent = await db.get(AgentModel, agent_id)
        if agent:
            object.__setattr__(agent, "status", "terminated")  # type: ignore[attr-defined]
            await db.commit()

    return {"status": "terminated"}


@app.get("/agents/{agent_id}/history")
async def get_agent_history(agent_id: str):
    from ..database import SessionModel, LogModel, AgentModel

    async with get_db_context() as db:
        # First check if agent exists
        agent = await db.get(AgentModel, agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        sessions = await db.execute(
            SessionModel.__table__.select().where(SessionModel.agent_id == agent_id)
        )
        sessions = sessions.fetchall()

        history = []
        for session in sessions:
            logs = await db.execute(
                LogModel.__table__.select().where(LogModel.session_id == session.id)
            )
            logs = logs.fetchall()

            history.append(
                {
                    "session_id": session.id,
                    "objective": session.objective,
                    "status": session.status,
                    "session_root": session.session_root,
                    "attestation_tx": session.attestation_tx,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "logs": [
                        {
                            "event_type": log.event_type,
                            "tool_name": log.tool_name,
                            "output_result": log.output_result,
                            "timestamp": log.timestamp,
                        }
                        for log in logs
                    ],
                }
            )

        return {"agent_id": agent_id, "sessions": history}

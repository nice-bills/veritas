from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import AgentCreate, MissionRequest, AgentResponse, MissionResponse
from ..agent import VeritasAgent
import uuid
from typing import Dict

app = FastAPI(title="Veritas Agent OS API")

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for active agents (for MVP)
active_agents: Dict[str, VeritasAgent] = {}

@app.get("/")
async def root():
    return {"status": "online", "version": "0.1.0"}

@app.post("/agents", response_model=AgentResponse)
async def create_agent(config: AgentCreate):
    agent_id = str(uuid.uuid4())
    try:
        agent = VeritasAgent(
            name=config.name,
            brain_provider=config.brain_provider,
            network=config.network,
            private_key=config.private_key
        )
        active_agents[agent_id] = agent
        return {
            "id": agent_id,
            "name": agent.name,
            "address": agent.account.address,
            "network": agent.network
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/agents/{agent_id}/run", response_model=MissionResponse)
async def run_mission(agent_id: str, request: MissionRequest):
    if agent_id not in active_agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = active_agents[agent_id]
    try:
        # 1. Run Mission
        root = await agent.run_mission(request.objective)
        
        # 2. On-Chain Attestation
        tx_hash = await agent.attestor.attest_root(
            merkle_root=root,
            schema_uid="0x4ee2145e253098e581a38bdbb7f7c81eae64b6d9d5868063c71b562779056441",
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
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/agents/{agent_id}")
async def stop_agent(agent_id: str):
    if agent_id in active_agents:
        await active_agents[agent_id].shutdown()
        del active_agents[agent_id]
        return {"status": "terminated"}
    raise HTTPException(status_code=404, detail="Agent not found")

from typing import Any, Callable, Dict, List, Optional
import time
import json
from pydantic import BaseModel, Field
from .merkle import MerkleTree

import uuid

class ActionLog(BaseModel):
    """Immutable record of a single agent action."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    basis_id: Optional[str] = None  # ID of the observation/action that justifies this
    timestamp: float = Field(default_factory=time.time)
    event_type: str = "ACTION"  # "OBSERVATION" or "ACTION"
    tool_name: str
    input_params: Dict[str, Any]
    output_result: Any
    
    def to_hashable_json(self) -> str:
        """Deterministic JSON serialization for hashing."""
        # Sort keys to ensure consistent hashing
        return json.dumps(self.model_dump(mode='json'), sort_keys=True)

class VeritasLogger:
    """
    The Black Box Recorder.
    Captures actions, logs them, and builds a real-time Merkle Tree.
    """
    
    def __init__(self):
        self._logs: List[ActionLog] = []
        self._merkle_tree = MerkleTree()
        self.last_event_id: Optional[str] = None

    def log_action(
        self, 
        tool_name: str, 
        params: Dict[str, Any], 
        result: Any, 
        event_type: str = "ACTION",
        basis_id: Optional[str] = None
    ) -> ActionLog:
        """Record an action to the immutable log."""
        entry = ActionLog(
            tool_name=tool_name,
            input_params=params,
            output_result=result,
            event_type=event_type,
            basis_id=basis_id
        )
        self._logs.append(entry)
        self.last_event_id = entry.id
        
        # Add to Merkle Tree
        self._merkle_tree.add_leaf(entry.to_hashable_json())
        
        print(f"[Veritas] 🔒 Recorded {event_type}: {tool_name} | Root: {self.get_current_root()[:8]}...")
        return entry

    def observe(self, source: str, query: Dict[str, Any], result: Any) -> str:
        """semantic alias for logging an observation. returns the event ID."""
        entry = self.log_action(source, query, result, event_type="OBSERVATION")
        return entry.id

    def act(self, tool: str, params: Dict[str, Any], result: Any, basis_id: str) -> str:
        """semantic alias for logging an action. returns the event ID."""
        entry = self.log_action(tool, params, result, event_type="ACTION", basis_id=basis_id)
        return entry.id

    def get_logs(self) -> List[ActionLog]:
        return self._logs

    def get_current_root(self) -> str:
        """Get the current Merkle Root of all actions."""
        return self._merkle_tree.get_root() or "0x0"

    def export_proofs(self, filepath: str):
        """Export the full session proof package to a JSON file."""
        data = {
            "session_root": self.get_current_root(),
            "event_count": len(self._logs),
            "timestamp": time.time(),
            "logs": [log.model_dump(mode='json') for log in self._logs]
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[Veritas] 💾 Proof package saved to: {filepath}")

    def wrap(self, func: Optional[Callable] = None, *, tool_name: str = None, event_type: str = "ACTION"):
        """
        Decorator to automatically audit a function call.
        Can be used as @wrap or @wrap(event_type="OBSERVATION").
        """
        def decorator(f: Callable):
            name = tool_name or f.__name__
            
            def wrapper(*args, **kwargs):
                # Capture Input
                basis_id = kwargs.pop("basis_id", None)
                try:
                    params = {"args": [str(a) for a in args], "kwargs": {k: str(v) for k,v in kwargs.items()}}
                except Exception:
                    params = {"args": "unserializable", "kwargs": "unserializable"}
                
                # Execute Real Action
                result = f(*args, **kwargs)
                
                # Log Result
                try:
                    res_serializable = str(result)
                except:
                    res_serializable = "unserializable_result"
                    
                self.log_action(name, params, res_serializable, event_type=event_type, basis_id=basis_id)
                return result
            return wrapper

        if func is None:
            return decorator
        return decorator(func)

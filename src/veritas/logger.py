from typing import Any, Callable, Dict, List, Optional
import time
import json
from pydantic import BaseModel, Field
from .merkle import MerkleTree

class ActionLog(BaseModel):
    """Immutable record of a single agent action."""
    timestamp: float = Field(default_factory=time.time)
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

    def log_action(self, tool_name: str, params: Dict[str, Any], result: Any) -> ActionLog:
        """Record an action to the immutable log."""
        entry = ActionLog(
            tool_name=tool_name,
            input_params=params,
            output_result=result
        )
        self._logs.append(entry)
        
        # Add to Merkle Tree
        self._merkle_tree.add_leaf(entry.to_hashable_json())
        
        print(f"[Veritas] 🔒 Recorded: {tool_name} | Root: {self.get_current_root()[:8]}...")
        return entry

    def get_logs(self) -> List[ActionLog]:
        return self._logs

    def get_current_root(self) -> str:
        """Get the current Merkle Root of all actions."""
        return self._merkle_tree.get_root() or "0x0"

    def wrap(self, func: Callable, tool_name: str = None):
        """Decorator to automatically audit a function call."""
        name = tool_name or func.__name__
        
        def wrapper(*args, **kwargs):
            # Capture Input
            # Note: We must be careful with un-serializable objects (like client instances)
            # For MVP, we assume simple types or stringify
            try:
                params = {"args": [str(a) for a in args], "kwargs": {k: str(v) for k,v in kwargs.items()}}
            except Exception:
                params = {"args": "unserializable", "kwargs": "unserializable"}
            
            # Execute Real Action
            result = func(*args, **kwargs)
            
            # Log Result
            try:
                res_serializable = str(result)
            except:
                res_serializable = "unserializable_result"
                
            self.log_action(name, params, res_serializable)
            return result
        return wrapper

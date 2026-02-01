from typing import Any, Callable, Dict, List, Optional
import time
import json
from pydantic import BaseModel, Field
from .merkle import MerkleTree
import uuid
import inspect


class ActionLog(BaseModel):
    """Immutable record of a single agent action."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    basis_id: Optional[str] = None  # ID of the observation/action that justifies this
    timestamp: float = Field(default_factory=time.time)
    event_type: str = "ACTION"  # "OBSERVATION" or "ACTION"
    tool_name: str
    input_params: Dict[str, Any]
    output_result: Any
    merkle_leaf: str = ""  # Merkle leaf hash for this log entry

    def to_hashable_json(self) -> str:
        """Deterministic JSON serialization for hashing."""
        return json.dumps(self.model_dump(mode="json"), sort_keys=True)


class VeritasLogger:
    """
    The Black Box Recorder.
    Captures actions, logs them, and builds a real-time Merkle Tree.
    """

    def __init__(self):
        self._logs: List[ActionLog] = []
        self._merkle_tree = MerkleTree()
        self.last_event_id: Optional[str] = None
        self.listeners: List[Callable[[ActionLog], None]] = []

    def log_action(
        self,
        tool_name: str,
        params: Dict[str, Any],
        result: Any,
        event_type: str = "ACTION",
        basis_id: Optional[str] = None,
    ) -> ActionLog:
        """Record an action to the immutable log."""
        entry = ActionLog(
            tool_name=tool_name,
            input_params=params,
            output_result=result,
            event_type=event_type,
            basis_id=basis_id,
        )
        self._merkle_tree.add_leaf(entry.to_hashable_json())
        leaf_hash = self._merkle_tree.get_leaf_hash(len(self._logs))
        entry.merkle_leaf = leaf_hash or ""

        self._logs.append(entry)
        self.last_event_id = entry.id

        for listener in self.listeners:
            try:
                listener(entry)
            except Exception:
                pass

        return entry

    def get_logs(self) -> List[ActionLog]:
        return self._logs

    def get_current_root(self) -> str:
        return self._merkle_tree.get_root() or "0x0"

    def wrap(
        self, func: Optional[Callable] = None, *, tool_name: str = None, event_type: str = "ACTION"
    ):
        """
        Decorator to automatically audit a function call.
        Correctly handles both sync and async functions.
        """

        def decorator(f: Callable):
            name = tool_name or f.__name__

            if inspect.iscoroutinefunction(f):

                async def async_wrapper(*args, **kwargs):
                    basis_id = kwargs.pop("basis_id", self.last_event_id)
                    # Convert args/kwargs to serializable format
                    params = {
                        "args": [str(a) for a in args],
                        "kwargs": {k: str(v) for k, v in kwargs.items()},
                    }

                    result = await f(*args, **kwargs)

                    res_serializable = str(result)
                    self.log_action(
                        name, params, res_serializable, event_type=event_type, basis_id=basis_id
                    )
                    return result

                return async_wrapper
            else:

                def sync_wrapper(*args, **kwargs):
                    basis_id = kwargs.pop("basis_id", self.last_event_id)
                    params = {
                        "args": [str(a) for a in args],
                        "kwargs": {k: str(v) for k, v in kwargs.items()},
                    }

                    result = f(*args, **kwargs)

                    res_serializable = str(result)
                    self.log_action(
                        name, params, res_serializable, event_type=event_type, basis_id=basis_id
                    )
                    return result

                return sync_wrapper

        if func is None:
            return decorator
        return decorator(func)

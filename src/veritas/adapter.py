from typing import Any, Callable, Dict, Optional
from .tools import VeritasTool
from .agent import VeritasAgent

class VeritasAdapter:
    """
    Utility to adapt external functions (like CDP actions) into VeritasTools.
    """
    @staticmethod
    def to_tool(
        agent: VeritasAgent,
        func: Callable,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> VeritasTool:
        """
        Wraps any function into a VeritasTool that is automatically audited by the agent.
        """
        import inspect
        
        if inspect.iscoroutinefunction(func):
            async def audited_func(*args, **kwargs):
                return await agent.execute_action(name, func, *args, **kwargs)
        else:
            def audited_func(*args, **kwargs):
                return agent.execute_action(name, func, *args, **kwargs)
            
        return VeritasTool(
            name=name,
            description=description,
            func=audited_func,
            parameters=parameters or {"type": "object", "properties": {}}
        )

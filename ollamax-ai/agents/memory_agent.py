"""
Memory Agent - Context management and information storage
"""

from typing import Dict, List, Optional, Any
from .base_agent import BaseAgent, AgentAction

class MemoryAgent(BaseAgent):
    def __init__(self, ollama_client, model_router, vector_db, task_logger):
        super().__init__(ollama_client, model_router, vector_db, task_logger, "memory")
    
    async def _execute_action(self, action: AgentAction) -> Any:
        action_type = action.action_type
        parameters = action.parameters
        
        if action_type == "store_information":
            return await self._store_information(parameters.get('data', {}))
        elif action_type == "retrieve_context":
            return await self._retrieve_context(parameters.get('query', ''))
        else:
            return {"error": f"Unknown memory action: {action_type}"}
    
    def get_available_tools(self) -> List[str]:
        return ["context_manager", "information_storage", "memory_retrieval", "knowledge_base"]
    
    def _get_system_prompt(self) -> str:
        return "You are a memory agent specialized in storing and retrieving contextual information."
    
    async def _store_information(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            await self.vector_db.store(data)
            return {"success": True, "stored": True}
        except Exception as e:
            return {"error": f"Storage failed: {e}"}
    
    async def _retrieve_context(self, query: str) -> Dict[str, Any]:
        try:
            context = await self.vector_db.search(query, limit=5)
            return {"success": True, "context": context}
        except Exception as e:
            return {"error": f"Retrieval failed: {e}"}
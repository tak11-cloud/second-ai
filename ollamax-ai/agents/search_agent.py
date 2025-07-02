"""
Search Agent - Information retrieval and knowledge lookup
"""

from typing import Dict, List, Optional, Any
from .base_agent import BaseAgent, AgentAction

class SearchAgent(BaseAgent):
    def __init__(self, ollama_client, model_router, vector_db, task_logger):
        super().__init__(ollama_client, model_router, vector_db, task_logger, "search")
    
    async def _execute_action(self, action: AgentAction) -> Any:
        action_type = action.action_type
        parameters = action.parameters
        
        if action_type == "search_knowledge":
            return await self._search_knowledge(parameters.get('query', ''))
        elif action_type == "lookup_documentation":
            return await self._lookup_documentation(parameters.get('topic', ''))
        else:
            return {"error": f"Unknown search action: {action_type}"}
    
    def get_available_tools(self) -> List[str]:
        return ["knowledge_searcher", "documentation_lookup", "code_search", "reference_finder"]
    
    def _get_system_prompt(self) -> str:
        return "You are a search agent specialized in finding relevant information and documentation."
    
    async def _search_knowledge(self, query: str) -> Dict[str, Any]:
        try:
            results = await self.vector_db.search(query, limit=10)
            return {"success": True, "query": query, "results": results}
        except Exception as e:
            return {"error": f"Search failed: {e}"}
    
    async def _lookup_documentation(self, topic: str) -> Dict[str, Any]:
        # Simulate documentation lookup
        return {"success": True, "topic": topic, "documentation": f"Documentation for {topic}"}
"""
Reflection Agent - Performance analysis and improvement suggestions
"""

from typing import Dict, List, Optional, Any
from .base_agent import BaseAgent, AgentAction

class ReflectionAgent(BaseAgent):
    def __init__(self, ollama_client, model_router, vector_db, task_logger):
        super().__init__(ollama_client, model_router, vector_db, task_logger, "reflection")
    
    async def _execute_action(self, action: AgentAction) -> Any:
        action_type = action.action_type
        parameters = action.parameters
        
        if action_type == "analyze_results":
            return await self._analyze_results(parameters.get('results', {}))
        elif action_type == "suggest_improvements":
            return await self._suggest_improvements(parameters.get('performance_data', {}))
        else:
            return {"error": f"Unknown reflection action: {action_type}"}
    
    def get_available_tools(self) -> List[str]:
        return ["performance_analyzer", "improvement_suggester", "quality_assessor", "optimization_finder"]
    
    def _get_system_prompt(self) -> str:
        return "You are a reflection agent specialized in analyzing performance and suggesting improvements."
    
    async def _analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        # Use reasoning model for analysis
        routing_decision = self.model_router.route_task(
            "analyze task results and performance",
            context={'agent_type': 'reflection', 'task_type': 'reflection'}
        )
        
        analysis_prompt = f"""
Analyze the following task execution results:

Results:
{results}

Provide analysis on:
1. Success/failure patterns
2. Performance metrics
3. Areas for improvement
4. Lessons learned

Analysis:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=analysis_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            analysis = response.response
            return {"success": True, "analysis": analysis}
        except Exception as e:
            return {"error": f"Analysis failed: {e}"}
    
    async def _suggest_improvements(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "success": True,
            "improvements": [
                "Optimize model routing",
                "Improve error handling",
                "Add more comprehensive testing"
            ]
        }
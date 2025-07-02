"""
Test Agent - Test creation, validation, and quality assurance
"""

from typing import Dict, List, Optional, Any
from .base_agent import BaseAgent, AgentAction

class TestAgent(BaseAgent):
    def __init__(self, ollama_client, model_router, vector_db, task_logger):
        super().__init__(ollama_client, model_router, vector_db, task_logger, "test")
    
    async def _execute_action(self, action: AgentAction) -> Any:
        action_type = action.action_type
        parameters = action.parameters
        
        if action_type == "generate_tests":
            return await self._generate_tests(parameters.get('code', ''))
        elif action_type == "run_tests":
            return await self._run_tests(parameters.get('test_code', ''))
        else:
            return {"error": f"Unknown test action: {action_type}"}
    
    def get_available_tools(self) -> List[str]:
        return ["test_generator", "test_runner", "coverage_analyzer", "quality_checker"]
    
    def _get_system_prompt(self) -> str:
        return "You are a test agent specialized in creating and running comprehensive tests."
    
    async def _generate_tests(self, code: str) -> Dict[str, Any]:
        # Use code model for test generation
        routing_decision = self.model_router.route_task(
            f"generate tests for code",
            context={'agent_type': 'test', 'task_type': 'testing'}
        )
        
        test_prompt = f"""
Generate comprehensive unit tests for the following code:

```python
{code}
```

Include:
- Normal case tests
- Edge case tests
- Error condition tests
- Mock/stub usage where appropriate

Tests:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=test_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            test_code = response.response
            return {"success": True, "test_code": test_code}
        except Exception as e:
            return {"error": f"Test generation failed: {e}"}
    
    async def _run_tests(self, test_code: str) -> Dict[str, Any]:
        # Simulate test execution
        return {
            "success": True,
            "tests_run": 5,
            "tests_passed": 4,
            "tests_failed": 1,
            "coverage": 85.0
        }
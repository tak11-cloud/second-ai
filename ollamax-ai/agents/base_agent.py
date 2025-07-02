"""
Base Agent class implementing ReAct pattern for OllamaX-AI
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

@dataclass
class AgentState:
    """Represents the current state of an agent"""
    agent_id: str
    agent_type: str
    current_task: Optional[str] = None
    context: Dict[str, Any] = None
    memory: List[Dict[str, Any]] = None
    status: str = "idle"  # idle, thinking, acting, reflecting, error
    last_action: Optional[str] = None
    error_count: int = 0
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.memory is None:
            self.memory = []

@dataclass
class AgentAction:
    """Represents an action taken by an agent"""
    action_id: str
    agent_id: str
    action_type: str
    parameters: Dict[str, Any]
    timestamp: datetime
    result: Optional[Any] = None
    success: bool = False
    error_message: Optional[str] = None
    execution_time: float = 0.0

@dataclass
class AgentObservation:
    """Represents an observation made by an agent"""
    observation_id: str
    agent_id: str
    observation_type: str
    data: Any
    timestamp: datetime
    confidence: float = 1.0
    source: Optional[str] = None

@dataclass
class AgentThought:
    """Represents a thought/reasoning step by an agent"""
    thought_id: str
    agent_id: str
    content: str
    reasoning_type: str  # analysis, planning, reflection, decision
    timestamp: datetime
    confidence: float = 1.0

class BaseAgent(ABC):
    """
    Base class for all OllamaX-AI agents implementing ReAct pattern:
    - Observe: Gather information from environment
    - Think: Reason about observations and plan actions
    - Act: Execute actions based on reasoning
    - Reflect: Analyze results and update understanding
    """
    
    def __init__(self, ollama_client, model_router, vector_db, task_logger, agent_type: str):
        self.agent_id = str(uuid.uuid4())
        self.agent_type = agent_type
        self.ollama_client = ollama_client
        self.model_router = model_router
        self.vector_db = vector_db
        self.task_logger = task_logger
        
        self.state = AgentState(
            agent_id=self.agent_id,
            agent_type=agent_type
        )
        
        self.action_history = []
        self.observation_history = []
        self.thought_history = []
        
        # Agent-specific configuration
        self.max_iterations = 10
        self.max_errors = 3
        self.reflection_threshold = 0.7  # confidence threshold for reflection
        
    async def process(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main processing method implementing ReAct loop
        """
        self.state.current_task = task
        self.state.context.update(context or {})
        self.state.status = "processing"
        
        try:
            # Initial observation
            initial_obs = await self.observe(task, context)
            
            iteration = 0
            while iteration < self.max_iterations:
                iteration += 1
                
                # Think about current situation
                thought = await self.think(task, initial_obs if iteration == 1 else None)
                
                # Decide on action
                action_plan = await self.plan_action(thought)
                
                if action_plan.get('action_type') == 'complete':
                    # Task is complete
                    break
                
                # Execute action
                action_result = await self.act(action_plan)
                
                # Observe results
                new_observation = await self.observe_result(action_result)
                
                # Check if we should reflect
                if (action_result.get('confidence', 1.0) < self.reflection_threshold or 
                    action_result.get('success', True) is False):
                    reflection = await self.reflect(action_result, new_observation)
                    if reflection.get('should_retry', False):
                        continue
                
                # Check for completion
                if self._is_task_complete(action_result, new_observation):
                    break
            
            # Final reflection and response generation
            final_result = await self.generate_response()
            self.state.status = "completed"
            
            return final_result
            
        except Exception as e:
            self.state.status = "error"
            self.state.error_count += 1
            logger.error(f"Agent {self.agent_id} error: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_id': self.agent_id,
                'agent_type': self.agent_type
            }
    
    async def observe(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentObservation:
        """
        Observe the current environment and gather relevant information
        """
        observation_data = {
            'task': task,
            'context': context or {},
            'agent_state': asdict(self.state),
            'available_tools': self.get_available_tools(),
            'memory_context': await self._get_relevant_memory(task)
        }
        
        observation = AgentObservation(
            observation_id=str(uuid.uuid4()),
            agent_id=self.agent_id,
            observation_type="initial_task_observation",
            data=observation_data,
            timestamp=datetime.now(),
            confidence=1.0,
            source="environment"
        )
        
        self.observation_history.append(observation)
        return observation
    
    async def think(self, task: str, observation: Optional[AgentObservation] = None) -> AgentThought:
        """
        Reason about the current situation and plan next steps
        """
        # Get the best model for reasoning
        routing_decision = self.model_router.route_task(
            f"reasoning and planning for: {task}",
            context={'agent_type': self.agent_type}
        )
        
        # Prepare reasoning prompt
        reasoning_prompt = await self._build_reasoning_prompt(task, observation)
        
        # Generate reasoning
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=reasoning_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            reasoning_content = response.response
        except Exception as e:
            # Fallback to simpler reasoning
            reasoning_content = f"Error in reasoning: {e}. Proceeding with basic approach."
        
        thought = AgentThought(
            thought_id=str(uuid.uuid4()),
            agent_id=self.agent_id,
            content=reasoning_content,
            reasoning_type="planning",
            timestamp=datetime.now(),
            confidence=routing_decision.confidence
        )
        
        self.thought_history.append(thought)
        return thought
    
    async def plan_action(self, thought: AgentThought) -> Dict[str, Any]:
        """
        Plan the next action based on reasoning
        """
        # Extract action plan from thought
        action_plan = await self._extract_action_plan(thought.content)
        return action_plan
    
    async def act(self, action_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the planned action
        """
        action = AgentAction(
            action_id=str(uuid.uuid4()),
            agent_id=self.agent_id,
            action_type=action_plan.get('action_type', 'unknown'),
            parameters=action_plan.get('parameters', {}),
            timestamp=datetime.now()
        )
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Execute the specific action
            result = await self._execute_action(action)
            action.result = result
            action.success = True
            
        except Exception as e:
            action.error_message = str(e)
            action.success = False
            result = {'success': False, 'error': str(e)}
        
        action.execution_time = asyncio.get_event_loop().time() - start_time
        self.action_history.append(action)
        
        return {
            'action': action,
            'result': result,
            'success': action.success
        }
    
    async def observe_result(self, action_result: Dict[str, Any]) -> AgentObservation:
        """
        Observe the results of an action
        """
        observation = AgentObservation(
            observation_id=str(uuid.uuid4()),
            agent_id=self.agent_id,
            observation_type="action_result",
            data=action_result,
            timestamp=datetime.now(),
            confidence=1.0,
            source="action_execution"
        )
        
        self.observation_history.append(observation)
        return observation
    
    async def reflect(self, action_result: Dict[str, Any], observation: AgentObservation) -> Dict[str, Any]:
        """
        Reflect on results and decide on improvements
        """
        reflection_prompt = await self._build_reflection_prompt(action_result, observation)
        
        # Use reasoning model for reflection
        routing_decision = self.model_router.route_task(
            "reflection and improvement analysis",
            context={'agent_type': self.agent_type}
        )
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=reflection_prompt,
            system=self._get_reflection_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            reflection_content = response.response
        except Exception as e:
            reflection_content = f"Reflection error: {e}"
        
        reflection_thought = AgentThought(
            thought_id=str(uuid.uuid4()),
            agent_id=self.agent_id,
            content=reflection_content,
            reasoning_type="reflection",
            timestamp=datetime.now(),
            confidence=routing_decision.confidence
        )
        
        self.thought_history.append(reflection_thought)
        
        # Parse reflection for actionable insights
        reflection_analysis = await self._parse_reflection(reflection_content)
        
        return reflection_analysis
    
    async def respond(self, final_result: Dict[str, Any]) -> str:
        """
        Generate final response to user
        """
        response_prompt = await self._build_response_prompt(final_result)
        
        routing_decision = self.model_router.route_task(
            "generate user response",
            context={'agent_type': self.agent_type}
        )
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=response_prompt,
            system=self._get_response_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            return response.response
        except Exception as e:
            return f"Error generating response: {e}"
    
    # Abstract methods to be implemented by specific agents
    @abstractmethod
    async def _execute_action(self, action: AgentAction) -> Any:
        """Execute agent-specific action"""
        pass
    
    @abstractmethod
    def get_available_tools(self) -> List[str]:
        """Return list of available tools for this agent"""
        pass
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Return agent-specific system prompt"""
        pass
    
    # Helper methods
    async def _get_relevant_memory(self, task: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for the task"""
        if self.vector_db:
            try:
                return await self.vector_db.search(task, limit=5)
            except Exception as e:
                logger.warning(f"Memory retrieval failed: {e}")
        return []
    
    async def _build_reasoning_prompt(self, task: str, observation: Optional[AgentObservation]) -> str:
        """Build prompt for reasoning phase"""
        prompt = f"""
Task: {task}

Agent Type: {self.agent_type}
Available Tools: {', '.join(self.get_available_tools())}

Current Context:
{json.dumps(self.state.context, indent=2)}

"""
        
        if observation:
            prompt += f"""
Current Observation:
{json.dumps(observation.data, indent=2)}

"""
        
        if self.thought_history:
            prompt += f"""
Previous Thoughts:
{self.thought_history[-3:]}  # Last 3 thoughts

"""
        
        prompt += """
Please analyze the situation and provide your reasoning for the next action.
Consider:
1. What information do you have?
2. What is the goal?
3. What actions are available?
4. What would be the best next step?

Reasoning:"""
        
        return prompt
    
    async def _build_reflection_prompt(self, action_result: Dict[str, Any], observation: AgentObservation) -> str:
        """Build prompt for reflection phase"""
        return f"""
Action Result Analysis:
{json.dumps(action_result, indent=2)}

Observation:
{json.dumps(observation.data, indent=2)}

Please reflect on:
1. Was the action successful?
2. What went well?
3. What could be improved?
4. Should we retry or change approach?
5. What did we learn?

Reflection:"""
    
    async def _extract_action_plan(self, reasoning_content: str) -> Dict[str, Any]:
        """Extract action plan from reasoning content"""
        # Simple extraction - in real implementation would use more sophisticated parsing
        lines = reasoning_content.lower().split('\n')
        
        action_type = "continue"
        parameters = {}
        
        for line in lines:
            if 'complete' in line or 'finished' in line:
                action_type = "complete"
            elif 'search' in line:
                action_type = "search"
            elif 'code' in line:
                action_type = "code"
            elif 'execute' in line or 'run' in line:
                action_type = "execute"
        
        return {
            'action_type': action_type,
            'parameters': parameters,
            'reasoning': reasoning_content
        }
    
    async def _parse_reflection(self, reflection_content: str) -> Dict[str, Any]:
        """Parse reflection content for actionable insights"""
        lines = reflection_content.lower().split('\n')
        
        should_retry = any('retry' in line or 'try again' in line for line in lines)
        should_change_approach = any('change' in line or 'different' in line for line in lines)
        
        return {
            'should_retry': should_retry,
            'should_change_approach': should_change_approach,
            'reflection_content': reflection_content,
            'confidence': 0.8  # Default confidence
        }
    
    def _is_task_complete(self, action_result: Dict[str, Any], observation: AgentObservation) -> bool:
        """Check if task is complete"""
        return action_result.get('action', {}).action_type == 'complete'
    
    async def generate_response(self) -> Dict[str, Any]:
        """Generate final response"""
        return {
            'success': True,
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'task': self.state.current_task,
            'actions_taken': len(self.action_history),
            'thoughts_generated': len(self.thought_history),
            'observations_made': len(self.observation_history),
            'final_state': asdict(self.state)
        }
    
    def _get_reflection_system_prompt(self) -> str:
        """System prompt for reflection"""
        return f"You are a {self.agent_type} agent reflecting on your actions and results. Be honest about successes and failures."
    
    def _get_response_system_prompt(self) -> str:
        """System prompt for response generation"""
        return f"You are a {self.agent_type} agent generating a final response to the user. Be clear and helpful."
    
    async def _build_response_prompt(self, final_result: Dict[str, Any]) -> str:
        """Build prompt for response generation"""
        return f"""
Task: {self.state.current_task}
Final Result: {json.dumps(final_result, indent=2)}

Generate a clear, helpful response to the user explaining what was accomplished.

Response:"""
    
    async def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step from a plan"""
        return await self.process(step.get('description', ''), step.get('context', {}))
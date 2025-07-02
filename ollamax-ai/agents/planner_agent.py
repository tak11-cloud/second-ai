"""
Planner Agent - Responsible for task decomposition and strategic planning
"""

import json
import re
from typing import Dict, List, Optional, Any
from .base_agent import BaseAgent, AgentAction

class PlannerAgent(BaseAgent):
    """
    Strategic planning agent that breaks down complex tasks into manageable steps
    and coordinates multi-agent workflows
    """
    
    def __init__(self, ollama_client, model_router, vector_db, task_logger):
        super().__init__(ollama_client, model_router, vector_db, task_logger, "planner")
        self.planning_templates = self._load_planning_templates()
        
    def _load_planning_templates(self) -> Dict[str, str]:
        """Load planning templates for different task types"""
        return {
            "red_team": """
Red Team Planning Template:
1. Reconnaissance and Information Gathering
2. Vulnerability Assessment
3. Exploit Development/Selection
4. Attack Vector Planning
5. Payload Preparation
6. Execution Strategy
7. Post-Exploitation Planning
8. Evidence Collection
9. Cleanup and Stealth
10. Reporting and Documentation
""",
            "code_development": """
Code Development Planning Template:
1. Requirements Analysis
2. Architecture Design
3. Technology Stack Selection
4. Implementation Planning
5. Testing Strategy
6. Security Considerations
7. Performance Optimization
8. Documentation Planning
9. Deployment Strategy
10. Maintenance Planning
""",
            "vulnerability_assessment": """
Vulnerability Assessment Planning Template:
1. Scope Definition
2. Asset Discovery
3. Service Enumeration
4. Vulnerability Scanning
5. Manual Testing
6. Exploit Verification
7. Risk Assessment
8. Impact Analysis
9. Remediation Planning
10. Report Generation
""",
            "debugging": """
Debugging Planning Template:
1. Problem Identification
2. Error Reproduction
3. Log Analysis
4. Code Review
5. Root Cause Analysis
6. Fix Development
7. Testing and Validation
8. Regression Testing
9. Documentation Update
10. Prevention Measures
"""
        }
    
    async def _execute_action(self, action: AgentAction) -> Any:
        """Execute planner-specific actions"""
        action_type = action.action_type
        parameters = action.parameters
        
        if action_type == "analyze_task":
            return await self._analyze_task_complexity(parameters.get('task', ''))
        elif action_type == "create_plan":
            return await self._create_detailed_plan(parameters.get('task', ''), parameters.get('context', {}))
        elif action_type == "decompose_task":
            return await self._decompose_task(parameters.get('task', ''))
        elif action_type == "assign_agents":
            return await self._assign_agents_to_steps(parameters.get('plan', {}))
        elif action_type == "estimate_resources":
            return await self._estimate_resource_requirements(parameters.get('plan', {}))
        elif action_type == "create_timeline":
            return await self._create_execution_timeline(parameters.get('plan', {}))
        else:
            return {"error": f"Unknown action type: {action_type}"}
    
    def get_available_tools(self) -> List[str]:
        """Return available tools for planning"""
        return [
            "task_analyzer",
            "plan_generator",
            "task_decomposer",
            "agent_assigner",
            "resource_estimator",
            "timeline_creator",
            "risk_assessor",
            "dependency_mapper"
        ]
    
    def _get_system_prompt(self) -> str:
        """System prompt for planner agent"""
        return """You are an expert strategic planning agent for OllamaX-AI. Your role is to:

1. Analyze complex tasks and break them down into manageable steps
2. Identify the optimal sequence of actions
3. Assign appropriate agents to each step
4. Estimate resource requirements and timelines
5. Identify potential risks and dependencies
6. Create comprehensive execution plans

You have access to multiple specialized agents:
- RedTeamAgent: Security testing, exploit development, vulnerability assessment
- CodeAgent: Code generation, modification, analysis
- TerminalAgent: Command execution, system interaction
- DebuggerAgent: Error analysis, troubleshooting, fixes
- SearchAgent: Information retrieval, knowledge lookup
- MemoryAgent: Context management, information storage
- TestAgent: Test creation, validation, quality assurance
- ReflectionAgent: Performance analysis, improvement suggestions
- UpgradeAgent: System enhancement, optimization
- VulnScannerAgent: Security scanning, vulnerability detection

Always consider:
- Task complexity and requirements
- Available resources and constraints
- Security implications
- Risk mitigation strategies
- Quality assurance needs
- Documentation requirements

Provide detailed, actionable plans with clear steps, agent assignments, and success criteria."""
    
    async def _analyze_task_complexity(self, task: str) -> Dict[str, Any]:
        """Analyze task complexity and requirements"""
        
        # Use model router to get best model for analysis
        routing_decision = self.model_router.route_task(
            f"analyze complexity of task: {task}",
            context={'agent_type': 'planner', 'task_type': 'analysis'}
        )
        
        analysis_prompt = f"""
Analyze the following task for complexity, requirements, and planning needs:

Task: {task}

Please provide analysis in the following format:

COMPLEXITY LEVEL: [Low/Medium/High/Extreme]
TASK CATEGORY: [Red Team/Code Development/Debugging/Analysis/Other]
ESTIMATED DURATION: [time estimate]
REQUIRED SKILLS: [list of required skills]
DEPENDENCIES: [external dependencies]
RISKS: [potential risks and challenges]
SUCCESS CRITERIA: [how to measure success]
RESOURCE REQUIREMENTS: [computational, time, expertise needs]

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
            analysis_text = response.response
            
            # Parse the analysis
            complexity = self._extract_field(analysis_text, "COMPLEXITY LEVEL")
            category = self._extract_field(analysis_text, "TASK CATEGORY")
            duration = self._extract_field(analysis_text, "ESTIMATED DURATION")
            skills = self._extract_field(analysis_text, "REQUIRED SKILLS")
            dependencies = self._extract_field(analysis_text, "DEPENDENCIES")
            risks = self._extract_field(analysis_text, "RISKS")
            success_criteria = self._extract_field(analysis_text, "SUCCESS CRITERIA")
            resources = self._extract_field(analysis_text, "RESOURCE REQUIREMENTS")
            
            return {
                "complexity": complexity,
                "category": category,
                "estimated_duration": duration,
                "required_skills": skills,
                "dependencies": dependencies,
                "risks": risks,
                "success_criteria": success_criteria,
                "resource_requirements": resources,
                "full_analysis": analysis_text
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {e}"}
    
    async def _create_detailed_plan(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a detailed execution plan"""
        
        # First analyze the task
        analysis = await self._analyze_task_complexity(task)
        
        # Select appropriate planning template
        category = analysis.get("category", "").lower()
        template = self.planning_templates.get("red_team", "")  # default
        
        for key in self.planning_templates:
            if key in category:
                template = self.planning_templates[key]
                break
        
        # Generate detailed plan
        routing_decision = self.model_router.route_task(
            f"create detailed plan for: {task}",
            context={'agent_type': 'planner', 'task_type': 'planning'}
        )
        
        planning_prompt = f"""
Create a detailed execution plan for the following task:

Task: {task}
Context: {json.dumps(context, indent=2)}
Task Analysis: {json.dumps(analysis, indent=2)}

Planning Template:
{template}

Please create a comprehensive plan with the following structure:

PLAN OVERVIEW:
- Objective: [clear objective statement]
- Approach: [high-level approach]
- Success Metrics: [measurable success criteria]

EXECUTION STEPS:
For each step, provide:
1. Step Name: [descriptive name]
   - Description: [detailed description]
   - Agent: [recommended agent type]
   - Input: [required inputs]
   - Output: [expected outputs]
   - Duration: [estimated time]
   - Dependencies: [prerequisite steps]
   - Risk Level: [Low/Medium/High]
   - Success Criteria: [how to verify completion]

RESOURCE REQUIREMENTS:
- Computational: [CPU, memory, storage needs]
- Time: [total estimated time]
- Expertise: [required knowledge areas]
- Tools: [required tools and software]

RISK MITIGATION:
- Identified Risks: [potential issues]
- Mitigation Strategies: [how to address risks]
- Contingency Plans: [backup approaches]

QUALITY ASSURANCE:
- Testing Strategy: [how to validate results]
- Review Process: [quality checks]
- Documentation: [required documentation]

Plan:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=planning_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            plan_text = response.response
            
            # Parse the plan into structured format
            structured_plan = await self._parse_plan_text(plan_text)
            
            return {
                "success": True,
                "plan": structured_plan,
                "raw_plan": plan_text,
                "analysis": analysis,
                "template_used": template
            }
            
        except Exception as e:
            return {"error": f"Plan creation failed: {e}"}
    
    async def _decompose_task(self, task: str) -> Dict[str, Any]:
        """Decompose task into smaller subtasks"""
        
        routing_decision = self.model_router.route_task(
            f"decompose task: {task}",
            context={'agent_type': 'planner', 'task_type': 'decomposition'}
        )
        
        decomposition_prompt = f"""
Break down the following complex task into smaller, manageable subtasks:

Task: {task}

Please decompose this into subtasks following these guidelines:
1. Each subtask should be independently executable
2. Subtasks should have clear inputs and outputs
3. Dependencies between subtasks should be minimal
4. Each subtask should be assignable to a specific agent type

Format your response as:

SUBTASK 1: [Name]
- Description: [what needs to be done]
- Agent Type: [which agent should handle this]
- Input Requirements: [what inputs are needed]
- Output: [what will be produced]
- Dependencies: [which other subtasks must complete first]
- Estimated Effort: [Low/Medium/High]

[Continue for all subtasks...]

EXECUTION ORDER:
[Recommended order of execution considering dependencies]

Decomposition:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=decomposition_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            decomposition_text = response.response
            
            # Parse subtasks
            subtasks = await self._parse_subtasks(decomposition_text)
            
            return {
                "success": True,
                "subtasks": subtasks,
                "raw_decomposition": decomposition_text
            }
            
        except Exception as e:
            return {"error": f"Task decomposition failed: {e}"}
    
    async def _assign_agents_to_steps(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Assign optimal agents to plan steps"""
        
        agent_capabilities = {
            "planner": ["planning", "coordination", "analysis"],
            "redteam": ["security_testing", "exploit_development", "vulnerability_assessment"],
            "code": ["code_generation", "code_modification", "code_analysis"],
            "terminal": ["command_execution", "system_interaction", "file_operations"],
            "debugger": ["error_analysis", "troubleshooting", "bug_fixing"],
            "search": ["information_retrieval", "knowledge_lookup", "research"],
            "memory": ["context_management", "information_storage", "retrieval"],
            "test": ["test_creation", "validation", "quality_assurance"],
            "reflection": ["performance_analysis", "improvement_suggestions"],
            "upgrade": ["system_enhancement", "optimization"],
            "vulnscanner": ["security_scanning", "vulnerability_detection"]
        }
        
        assignments = {}
        steps = plan.get("steps", [])
        
        for i, step in enumerate(steps):
            step_description = step.get("description", "").lower()
            step_name = step.get("name", f"step_{i}")
            
            # Score agents based on capability match
            agent_scores = {}
            for agent, capabilities in agent_capabilities.items():
                score = 0
                for capability in capabilities:
                    if capability.replace("_", " ") in step_description:
                        score += 1
                agent_scores[agent] = score
            
            # Select best agent
            best_agent = max(agent_scores, key=agent_scores.get)
            confidence = agent_scores[best_agent] / len(agent_capabilities[best_agent])
            
            assignments[step_name] = {
                "agent": best_agent,
                "confidence": confidence,
                "alternative_agents": sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)[1:3]
            }
        
        return {
            "success": True,
            "assignments": assignments,
            "agent_capabilities": agent_capabilities
        }
    
    async def _estimate_resource_requirements(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate computational and time resources needed"""
        
        steps = plan.get("steps", [])
        
        total_time = 0
        cpu_requirements = "medium"
        memory_requirements = "medium"
        storage_requirements = "low"
        
        complexity_weights = {
            "low": 1,
            "medium": 2,
            "high": 4,
            "extreme": 8
        }
        
        for step in steps:
            complexity = step.get("complexity", "medium").lower()
            weight = complexity_weights.get(complexity, 2)
            
            # Base time estimates (in minutes)
            base_time = 5
            step_time = base_time * weight
            total_time += step_time
            
            # Adjust resource requirements based on step type
            step_type = step.get("agent", "").lower()
            if step_type in ["code", "redteam", "vulnscanner"]:
                cpu_requirements = "high"
            if step_type in ["memory", "search"]:
                memory_requirements = "high"
            if step_type in ["terminal", "test"]:
                storage_requirements = "medium"
        
        return {
            "success": True,
            "estimates": {
                "total_time_minutes": total_time,
                "cpu_requirements": cpu_requirements,
                "memory_requirements": memory_requirements,
                "storage_requirements": storage_requirements,
                "parallel_execution_possible": len(steps) > 1,
                "estimated_cost": "low"  # Since we're using local models
            }
        }
    
    async def _create_execution_timeline(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Create execution timeline with dependencies"""
        
        steps = plan.get("steps", [])
        timeline = []
        
        for i, step in enumerate(steps):
            dependencies = step.get("dependencies", [])
            
            # Calculate start time based on dependencies
            start_time = 0
            if dependencies:
                # Find latest dependency completion time
                for dep in dependencies:
                    for timeline_item in timeline:
                        if timeline_item["step_name"] == dep:
                            start_time = max(start_time, timeline_item["end_time"])
            
            duration = step.get("estimated_duration", 10)  # default 10 minutes
            end_time = start_time + duration
            
            timeline.append({
                "step_name": step.get("name", f"step_{i}"),
                "start_time": start_time,
                "end_time": end_time,
                "duration": duration,
                "agent": step.get("agent", "unknown"),
                "dependencies": dependencies,
                "can_run_parallel": len(dependencies) == 0 or start_time == 0
            })
        
        return {
            "success": True,
            "timeline": timeline,
            "total_duration": max(item["end_time"] for item in timeline) if timeline else 0,
            "critical_path": self._find_critical_path(timeline)
        }
    
    def _find_critical_path(self, timeline: List[Dict[str, Any]]) -> List[str]:
        """Find the critical path through the timeline"""
        # Simple critical path - longest sequence
        sorted_timeline = sorted(timeline, key=lambda x: x["end_time"], reverse=True)
        return [item["step_name"] for item in sorted_timeline[:3]]
    
    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a specific field from structured text"""
        pattern = rf"{field_name}:\s*(.+?)(?=\n[A-Z]+:|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else "Not specified"
    
    async def _parse_plan_text(self, plan_text: str) -> Dict[str, Any]:
        """Parse plan text into structured format"""
        # Simple parsing - in production would use more sophisticated NLP
        lines = plan_text.split('\n')
        
        plan = {
            "overview": {},
            "steps": [],
            "resources": {},
            "risks": {},
            "quality_assurance": {}
        }
        
        current_section = None
        current_step = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("PLAN OVERVIEW:"):
                current_section = "overview"
            elif line.startswith("EXECUTION STEPS:"):
                current_section = "steps"
            elif line.startswith("RESOURCE REQUIREMENTS:"):
                current_section = "resources"
            elif line.startswith("RISK MITIGATION:"):
                current_section = "risks"
            elif line.startswith("QUALITY ASSURANCE:"):
                current_section = "quality_assurance"
            elif line.startswith(tuple("123456789")):
                # New step
                if current_section == "steps":
                    if current_step:
                        plan["steps"].append(current_step)
                    current_step = {
                        "name": line,
                        "description": "",
                        "agent": "unknown",
                        "dependencies": [],
                        "estimated_duration": 10
                    }
            elif current_step and line.startswith("-"):
                # Step detail
                if "Description:" in line:
                    current_step["description"] = line.split("Description:", 1)[1].strip()
                elif "Agent:" in line:
                    current_step["agent"] = line.split("Agent:", 1)[1].strip().lower()
                elif "Duration:" in line:
                    duration_text = line.split("Duration:", 1)[1].strip()
                    # Extract number from duration text
                    import re
                    duration_match = re.search(r'(\d+)', duration_text)
                    if duration_match:
                        current_step["estimated_duration"] = int(duration_match.group(1))
        
        # Add last step if exists
        if current_step:
            plan["steps"].append(current_step)
        
        return plan
    
    async def _parse_subtasks(self, decomposition_text: str) -> List[Dict[str, Any]]:
        """Parse subtasks from decomposition text"""
        subtasks = []
        lines = decomposition_text.split('\n')
        current_subtask = None
        
        for line in lines:
            line = line.strip()
            if line.startswith("SUBTASK"):
                if current_subtask:
                    subtasks.append(current_subtask)
                current_subtask = {
                    "name": line,
                    "description": "",
                    "agent_type": "unknown",
                    "dependencies": [],
                    "effort": "medium"
                }
            elif current_subtask and line.startswith("-"):
                if "Description:" in line:
                    current_subtask["description"] = line.split("Description:", 1)[1].strip()
                elif "Agent Type:" in line:
                    current_subtask["agent_type"] = line.split("Agent Type:", 1)[1].strip().lower()
                elif "Estimated Effort:" in line:
                    current_subtask["effort"] = line.split("Estimated Effort:", 1)[1].strip().lower()
        
        if current_subtask:
            subtasks.append(current_subtask)
        
        return subtasks
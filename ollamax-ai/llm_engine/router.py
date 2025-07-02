"""
Intelligent Model Router for OllamaX-AI
Routes tasks to optimal models based on task type, complexity, and context
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)

class TaskType(Enum):
    PLANNING = "planning"
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    RED_TEAM = "red_team"
    DEBUGGING = "debugging"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REASONING = "reasoning"
    SEARCH = "search"
    REFLECTION = "reflection"
    VULNERABILITY_SCAN = "vulnerability_scan"
    EXPLOIT_DEVELOPMENT = "exploit_development"

class ComplexityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

@dataclass
class ModelCapabilities:
    name: str
    strengths: List[TaskType]
    max_context: int
    reasoning_depth: ComplexityLevel
    code_quality: float  # 0.0 to 1.0
    speed: float  # 0.0 to 1.0 (higher is faster)
    memory_usage: float  # 0.0 to 1.0 (higher uses more memory)
    security_focus: float  # 0.0 to 1.0 (higher is better for security tasks)

@dataclass
class RoutingDecision:
    primary_model: str
    fallback_models: List[str]
    reasoning: str
    confidence: float
    estimated_tokens: int

class ModelRouter:
    """Intelligent router that selects optimal models for specific tasks"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.model_capabilities = self._load_model_capabilities(config_path)
        self.routing_history = []
        self.performance_metrics = {}
        
    def _load_model_capabilities(self, config_path: Optional[str]) -> Dict[str, ModelCapabilities]:
        """Load model capabilities from config or use defaults"""
        default_capabilities = {
            "mixtral": ModelCapabilities(
                name="mixtral",
                strengths=[TaskType.REASONING, TaskType.PLANNING, TaskType.CODE_ANALYSIS],
                max_context=32768,
                reasoning_depth=ComplexityLevel.HIGH,
                code_quality=0.85,
                speed=0.6,
                memory_usage=0.8,
                security_focus=0.7
            ),
            "openchat": ModelCapabilities(
                name="openchat",
                strengths=[TaskType.PLANNING, TaskType.REASONING, TaskType.DOCUMENTATION],
                max_context=8192,
                reasoning_depth=ComplexityLevel.MEDIUM,
                code_quality=0.7,
                speed=0.8,
                memory_usage=0.5,
                security_focus=0.6
            ),
            "codellama": ModelCapabilities(
                name="codellama",
                strengths=[TaskType.CODE_GENERATION, TaskType.CODE_ANALYSIS, TaskType.DEBUGGING],
                max_context=16384,
                reasoning_depth=ComplexityLevel.MEDIUM,
                code_quality=0.9,
                speed=0.7,
                memory_usage=0.6,
                security_focus=0.5
            ),
            "wizardcoder": ModelCapabilities(
                name="wizardcoder",
                strengths=[TaskType.CODE_GENERATION, TaskType.DEBUGGING, TaskType.TESTING],
                max_context=16384,
                reasoning_depth=ComplexityLevel.MEDIUM,
                code_quality=0.85,
                speed=0.75,
                memory_usage=0.6,
                security_focus=0.6
            ),
            "phi3": ModelCapabilities(
                name="phi3",
                strengths=[TaskType.REASONING, TaskType.SEARCH, TaskType.DOCUMENTATION],
                max_context=4096,
                reasoning_depth=ComplexityLevel.LOW,
                code_quality=0.6,
                speed=0.9,
                memory_usage=0.3,
                security_focus=0.5
            ),
            "deepseek-coder": ModelCapabilities(
                name="deepseek-coder",
                strengths=[TaskType.CODE_GENERATION, TaskType.VULNERABILITY_SCAN, TaskType.EXPLOIT_DEVELOPMENT],
                max_context=16384,
                reasoning_depth=ComplexityLevel.HIGH,
                code_quality=0.9,
                speed=0.65,
                memory_usage=0.7,
                security_focus=0.9
            )
        }
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    # Override defaults with config data
                    # Implementation would parse config and update capabilities
                    pass
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        return default_capabilities
    
    def analyze_task(self, task: str, context: Optional[Dict[str, Any]] = None) -> Tuple[TaskType, ComplexityLevel, int]:
        """Analyze task to determine type, complexity, and estimated token count"""
        task_lower = task.lower()
        
        # Determine task type
        task_type = TaskType.REASONING  # default
        
        if any(keyword in task_lower for keyword in ['exploit', 'vulnerability', 'attack', 'payload', 'injection']):
            if 'scan' in task_lower or 'find' in task_lower:
                task_type = TaskType.VULNERABILITY_SCAN
            else:
                task_type = TaskType.EXPLOIT_DEVELOPMENT
        elif any(keyword in task_lower for keyword in ['code', 'function', 'class', 'implement', 'write']):
            task_type = TaskType.CODE_GENERATION
        elif any(keyword in task_lower for keyword in ['debug', 'fix', 'error', 'bug']):
            task_type = TaskType.DEBUGGING
        elif any(keyword in task_lower for keyword in ['test', 'unit test', 'integration']):
            task_type = TaskType.TESTING
        elif any(keyword in task_lower for keyword in ['plan', 'strategy', 'approach']):
            task_type = TaskType.PLANNING
        elif any(keyword in task_lower for keyword in ['analyze', 'review', 'audit']):
            task_type = TaskType.CODE_ANALYSIS
        elif any(keyword in task_lower for keyword in ['search', 'find', 'lookup']):
            task_type = TaskType.SEARCH
        elif any(keyword in task_lower for keyword in ['reflect', 'improve', 'optimize']):
            task_type = TaskType.REFLECTION
        elif any(keyword in task_lower for keyword in ['document', 'explain', 'describe']):
            task_type = TaskType.DOCUMENTATION
        
        # Determine complexity
        complexity = ComplexityLevel.MEDIUM  # default
        
        complexity_indicators = {
            ComplexityLevel.LOW: ['simple', 'basic', 'quick', 'small'],
            ComplexityLevel.MEDIUM: ['moderate', 'standard', 'typical'],
            ComplexityLevel.HIGH: ['complex', 'advanced', 'sophisticated', 'comprehensive'],
            ComplexityLevel.EXTREME: ['extremely', 'highly complex', 'enterprise-level', 'production-grade']
        }
        
        for level, indicators in complexity_indicators.items():
            if any(indicator in task_lower for indicator in indicators):
                complexity = level
                break
        
        # Estimate token count
        estimated_tokens = len(task.split()) * 1.3  # rough estimate
        if context:
            estimated_tokens += len(str(context).split()) * 1.3
        
        # Adjust based on complexity
        complexity_multipliers = {
            ComplexityLevel.LOW: 1.0,
            ComplexityLevel.MEDIUM: 2.0,
            ComplexityLevel.HIGH: 4.0,
            ComplexityLevel.EXTREME: 8.0
        }
        estimated_tokens *= complexity_multipliers[complexity]
        
        return task_type, complexity, int(estimated_tokens)
    
    def route_task(self, task: str, context: Optional[Dict[str, Any]] = None, 
                   available_models: Optional[List[str]] = None) -> RoutingDecision:
        """Route a task to the optimal model"""
        
        task_type, complexity, estimated_tokens = self.analyze_task(task, context)
        
        if available_models is None:
            available_models = list(self.model_capabilities.keys())
        
        # Filter models that can handle the token count
        suitable_models = []
        for model_name in available_models:
            if model_name in self.model_capabilities:
                model = self.model_capabilities[model_name]
                if model.max_context >= estimated_tokens:
                    suitable_models.append(model_name)
        
        if not suitable_models:
            # Fallback to models with largest context
            suitable_models = sorted(
                available_models,
                key=lambda m: self.model_capabilities.get(m, ModelCapabilities("", [], 0, ComplexityLevel.LOW, 0, 0, 0, 0)).max_context,
                reverse=True
            )[:3]
        
        # Score models based on task requirements
        model_scores = {}
        for model_name in suitable_models:
            if model_name not in self.model_capabilities:
                continue
                
            model = self.model_capabilities[model_name]
            score = 0.0
            
            # Task type alignment
            if task_type in model.strengths:
                score += 3.0
            
            # Complexity handling
            complexity_scores = {
                ComplexityLevel.LOW: {ComplexityLevel.LOW: 1.0, ComplexityLevel.MEDIUM: 0.8, ComplexityLevel.HIGH: 0.6, ComplexityLevel.EXTREME: 0.4},
                ComplexityLevel.MEDIUM: {ComplexityLevel.LOW: 0.8, ComplexityLevel.MEDIUM: 1.0, ComplexityLevel.HIGH: 0.9, ComplexityLevel.EXTREME: 0.7},
                ComplexityLevel.HIGH: {ComplexityLevel.LOW: 0.5, ComplexityLevel.MEDIUM: 0.7, ComplexityLevel.HIGH: 1.0, ComplexityLevel.EXTREME: 0.9},
                ComplexityLevel.EXTREME: {ComplexityLevel.LOW: 0.3, ComplexityLevel.MEDIUM: 0.5, ComplexityLevel.HIGH: 0.8, ComplexityLevel.EXTREME: 1.0}
            }
            score += complexity_scores[complexity][model.reasoning_depth] * 2.0
            
            # Task-specific scoring
            if task_type in [TaskType.CODE_GENERATION, TaskType.CODE_ANALYSIS, TaskType.DEBUGGING]:
                score += model.code_quality * 2.0
            elif task_type in [TaskType.RED_TEAM, TaskType.VULNERABILITY_SCAN, TaskType.EXPLOIT_DEVELOPMENT]:
                score += model.security_focus * 2.0
            elif task_type in [TaskType.SEARCH, TaskType.DOCUMENTATION]:
                score += model.speed * 1.5
            
            # Performance history adjustment
            if model_name in self.performance_metrics:
                historical_performance = self.performance_metrics[model_name].get('success_rate', 0.5)
                score += historical_performance * 1.0
            
            model_scores[model_name] = score
        
        # Sort by score
        ranked_models = sorted(model_scores.items(), key=lambda x: x[1], reverse=True)
        
        if not ranked_models:
            # Ultimate fallback
            primary_model = available_models[0] if available_models else "mixtral"
            fallback_models = available_models[1:3] if len(available_models) > 1 else []
            reasoning = "No suitable models found, using fallback"
            confidence = 0.1
        else:
            primary_model = ranked_models[0][0]
            fallback_models = [model for model, _ in ranked_models[1:3]]
            
            # Generate reasoning
            primary_capabilities = self.model_capabilities[primary_model]
            reasoning = f"Selected {primary_model} for {task_type.value} task with {complexity.value} complexity. "
            reasoning += f"Model strengths: {[t.value for t in primary_capabilities.strengths]}. "
            reasoning += f"Score: {ranked_models[0][1]:.2f}"
            
            # Calculate confidence
            if len(ranked_models) > 1:
                score_diff = ranked_models[0][1] - ranked_models[1][1]
                confidence = min(0.9, 0.5 + (score_diff / 10.0))
            else:
                confidence = 0.8
        
        decision = RoutingDecision(
            primary_model=primary_model,
            fallback_models=fallback_models,
            reasoning=reasoning,
            confidence=confidence,
            estimated_tokens=estimated_tokens
        )
        
        # Log decision
        self.routing_history.append({
            'task': task[:100],  # truncate for logging
            'task_type': task_type.value,
            'complexity': complexity.value,
            'decision': decision,
            'timestamp': None  # would add timestamp in real implementation
        })
        
        return decision
    
    def update_performance(self, model_name: str, task_type: TaskType, success: bool, 
                          execution_time: float, quality_score: float):
        """Update performance metrics for a model"""
        if model_name not in self.performance_metrics:
            self.performance_metrics[model_name] = {
                'total_tasks': 0,
                'successful_tasks': 0,
                'success_rate': 0.0,
                'avg_execution_time': 0.0,
                'avg_quality_score': 0.0,
                'task_type_performance': {}
            }
        
        metrics = self.performance_metrics[model_name]
        metrics['total_tasks'] += 1
        
        if success:
            metrics['successful_tasks'] += 1
        
        metrics['success_rate'] = metrics['successful_tasks'] / metrics['total_tasks']
        
        # Update averages (simple moving average)
        alpha = 0.1  # learning rate
        metrics['avg_execution_time'] = (1 - alpha) * metrics['avg_execution_time'] + alpha * execution_time
        metrics['avg_quality_score'] = (1 - alpha) * metrics['avg_quality_score'] + alpha * quality_score
        
        # Update task-type specific performance
        task_key = task_type.value
        if task_key not in metrics['task_type_performance']:
            metrics['task_type_performance'][task_key] = {
                'count': 0,
                'success_rate': 0.0,
                'avg_quality': 0.0
            }
        
        task_metrics = metrics['task_type_performance'][task_key]
        task_metrics['count'] += 1
        
        if success:
            task_metrics['success_rate'] = (task_metrics['success_rate'] * (task_metrics['count'] - 1) + 1.0) / task_metrics['count']
        else:
            task_metrics['success_rate'] = (task_metrics['success_rate'] * (task_metrics['count'] - 1)) / task_metrics['count']
        
        task_metrics['avg_quality'] = (task_metrics['avg_quality'] * (task_metrics['count'] - 1) + quality_score) / task_metrics['count']
    
    def get_model_recommendations(self, task_type: TaskType) -> List[str]:
        """Get recommended models for a specific task type"""
        recommendations = []
        
        for model_name, capabilities in self.model_capabilities.items():
            if task_type in capabilities.strengths:
                recommendations.append(model_name)
        
        # Sort by overall capability for the task type
        def score_model(model_name):
            model = self.model_capabilities[model_name]
            base_score = 3.0 if task_type in model.strengths else 0.0
            
            if task_type in [TaskType.CODE_GENERATION, TaskType.CODE_ANALYSIS]:
                base_score += model.code_quality * 2.0
            elif task_type in [TaskType.RED_TEAM, TaskType.VULNERABILITY_SCAN]:
                base_score += model.security_focus * 2.0
            
            # Add performance history if available
            if model_name in self.performance_metrics:
                task_perf = self.performance_metrics[model_name].get('task_type_performance', {})
                if task_type.value in task_perf:
                    base_score += task_perf[task_type.value]['success_rate'] * 1.0
            
            return base_score
        
        recommendations.sort(key=score_model, reverse=True)
        return recommendations
    
    def export_performance_report(self) -> Dict[str, Any]:
        """Export performance metrics and routing history"""
        return {
            'performance_metrics': self.performance_metrics,
            'routing_history': self.routing_history[-100:],  # last 100 decisions
            'model_capabilities': {
                name: {
                    'strengths': [t.value for t in cap.strengths],
                    'max_context': cap.max_context,
                    'reasoning_depth': cap.reasoning_depth.value,
                    'code_quality': cap.code_quality,
                    'speed': cap.speed,
                    'security_focus': cap.security_focus
                }
                for name, cap in self.model_capabilities.items()
            }
        }
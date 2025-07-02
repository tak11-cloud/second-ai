"""
Debugger Agent - Specialized in error analysis, troubleshooting, and automated fixes
"""

import re
import json
import traceback
from typing import Dict, List, Optional, Any
from .base_agent import BaseAgent, AgentAction

class DebuggerAgent(BaseAgent):
    """
    Advanced debugging agent for error analysis and automated fixes
    """
    
    def __init__(self, ollama_client, model_router, vector_db, task_logger):
        super().__init__(ollama_client, model_router, vector_db, task_logger, "debugger")
        self.error_patterns = self._load_error_patterns()
        self.fix_strategies = self._load_fix_strategies()
        
    def _load_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load common error patterns and their solutions"""
        return {
            "python": {
                "SyntaxError": {
                    "patterns": [r"SyntaxError: (.+)", r"invalid syntax"],
                    "common_causes": ["Missing parentheses", "Incorrect indentation", "Missing colon"],
                    "fix_strategies": ["Check syntax", "Verify indentation", "Add missing punctuation"]
                },
                "NameError": {
                    "patterns": [r"NameError: name '(.+)' is not defined"],
                    "common_causes": ["Undefined variable", "Typo in variable name", "Import missing"],
                    "fix_strategies": ["Define variable", "Check spelling", "Add import statement"]
                },
                "TypeError": {
                    "patterns": [r"TypeError: (.+)"],
                    "common_causes": ["Wrong data type", "Missing arguments", "Incompatible operations"],
                    "fix_strategies": ["Type conversion", "Check function signature", "Validate inputs"]
                },
                "ImportError": {
                    "patterns": [r"ImportError: (.+)", r"ModuleNotFoundError: (.+)"],
                    "common_causes": ["Missing package", "Wrong module name", "Path issues"],
                    "fix_strategies": ["Install package", "Check module name", "Update PYTHONPATH"]
                }
            },
            "javascript": {
                "ReferenceError": {
                    "patterns": [r"ReferenceError: (.+) is not defined"],
                    "common_causes": ["Undefined variable", "Scope issues", "Typo"],
                    "fix_strategies": ["Declare variable", "Check scope", "Fix spelling"]
                },
                "TypeError": {
                    "patterns": [r"TypeError: (.+)"],
                    "common_causes": ["Wrong type", "Null/undefined access", "Method not found"],
                    "fix_strategies": ["Type checking", "Null checks", "Verify object structure"]
                }
            }
        }
    
    def _load_fix_strategies(self) -> Dict[str, List[str]]:
        """Load automated fix strategies"""
        return {
            "syntax_fixes": [
                "Add missing parentheses",
                "Fix indentation",
                "Add missing colons",
                "Close brackets/quotes"
            ],
            "import_fixes": [
                "Add import statement",
                "Install missing package",
                "Fix import path",
                "Use relative imports"
            ],
            "type_fixes": [
                "Add type conversion",
                "Validate input types",
                "Add null checks",
                "Use default values"
            ],
            "logic_fixes": [
                "Fix conditional logic",
                "Correct loop conditions",
                "Handle edge cases",
                "Add error handling"
            ]
        }
    
    async def _execute_action(self, action: AgentAction) -> Any:
        """Execute debugger-specific actions"""
        action_type = action.action_type
        parameters = action.parameters
        
        if action_type == "analyze_error":
            return await self._analyze_error(
                parameters.get('error_message', ''),
                parameters.get('code', ''),
                parameters.get('language', 'python'),
                parameters.get('context', {})
            )
        elif action_type == "suggest_fix":
            return await self._suggest_fix(
                parameters.get('error_analysis', {}),
                parameters.get('code', ''),
                parameters.get('language', 'python')
            )
        elif action_type == "apply_fix":
            return await self._apply_fix(
                parameters.get('fix_suggestion', {}),
                parameters.get('code', ''),
                parameters.get('language', 'python')
            )
        elif action_type == "trace_execution":
            return await self._trace_execution(
                parameters.get('code', ''),
                parameters.get('inputs', {}),
                parameters.get('language', 'python')
            )
        elif action_type == "validate_fix":
            return await self._validate_fix(
                parameters.get('original_code', ''),
                parameters.get('fixed_code', ''),
                parameters.get('test_cases', [])
            )
        else:
            return {"error": f"Unknown debugger action: {action_type}"}
    
    def get_available_tools(self) -> List[str]:
        """Return available debugging tools"""
        return [
            "error_analyzer",
            "fix_suggester",
            "code_tracer",
            "syntax_checker",
            "type_checker",
            "logic_analyzer",
            "performance_profiler",
            "memory_analyzer"
        ]
    
    def _get_system_prompt(self) -> str:
        """System prompt for debugger agent"""
        return """You are an expert debugging agent for OllamaX-AI. Your role is to:

1. Analyze errors and exceptions in code
2. Identify root causes of bugs and issues
3. Suggest specific fixes and improvements
4. Apply automated fixes when possible
5. Validate that fixes work correctly
6. Provide debugging strategies and best practices

You have expertise in:
- Error pattern recognition
- Root cause analysis
- Automated fix generation
- Code tracing and profiling
- Testing and validation
- Performance debugging
- Memory leak detection
- Security vulnerability analysis

Always provide:
- Clear explanation of the problem
- Step-by-step debugging approach
- Specific fix recommendations
- Code examples when helpful
- Testing strategies to prevent regression
- Best practices to avoid similar issues

Focus on practical, actionable solutions that developers can implement immediately."""
    
    async def _analyze_error(self, error_message: str, code: str, language: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze error message and code to identify the problem"""
        
        # Use debugging-focused model
        routing_decision = self.model_router.route_task(
            f"analyze {language} error: {error_message[:100]}",
            context={'agent_type': 'debugger', 'task_type': 'error_analysis'}
        )
        
        # Pattern matching for known errors
        error_classification = self._classify_error(error_message, language)
        
        analysis_prompt = f"""
Analyze the following error in {language} code:

Error Message:
{error_message}

Code:
```{language}
{code}
```

Context:
{json.dumps(context, indent=2)}

Please provide a comprehensive error analysis:

1. ERROR CLASSIFICATION:
   - Error type and category
   - Severity level (Critical/High/Medium/Low)
   - Error location in code

2. ROOT CAUSE ANALYSIS:
   - What caused this error?
   - Why did it occur at this point?
   - What conditions led to this failure?

3. IMPACT ASSESSMENT:
   - What functionality is affected?
   - Are there any side effects?
   - Data integrity concerns?

4. DEBUGGING STRATEGY:
   - Steps to reproduce the error
   - Information needed for diagnosis
   - Tools and techniques to use

5. IMMEDIATE ACTIONS:
   - Quick fixes to stop the error
   - Workarounds if available
   - Prevention measures

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
            
            return {
                "success": True,
                "error_message": error_message,
                "language": language,
                "error_classification": error_classification,
                "analysis": analysis_text,
                "severity": self._assess_severity(error_message, error_classification),
                "suggested_actions": self._extract_suggested_actions(analysis_text)
            }
            
        except Exception as e:
            return {"error": f"Error analysis failed: {e}"}
    
    async def _suggest_fix(self, error_analysis: Dict[str, Any], code: str, language: str) -> Dict[str, Any]:
        """Suggest specific fixes for the identified error"""
        
        routing_decision = self.model_router.route_task(
            f"suggest fix for {language} error",
            context={'agent_type': 'debugger', 'task_type': 'fix_suggestion'}
        )
        
        fix_prompt = f"""
Based on the error analysis, suggest specific fixes for the code:

Error Analysis:
{json.dumps(error_analysis, indent=2)}

Current Code:
```{language}
{code}
```

Please provide detailed fix suggestions:

1. PRIMARY FIX:
   - Specific changes needed
   - Modified code sections
   - Explanation of why this fixes the issue

2. ALTERNATIVE FIXES:
   - Other possible solutions
   - Trade-offs of each approach
   - When to use each alternative

3. CODE CHANGES:
   - Line-by-line modifications
   - New code to add
   - Code to remove or replace

4. TESTING STRATEGY:
   - How to verify the fix works
   - Test cases to run
   - Edge cases to check

5. PREVENTION MEASURES:
   - How to avoid this error in future
   - Code patterns to follow
   - Tools or practices to adopt

Fix Suggestions:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=fix_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            fix_suggestions = response.response
            
            # Extract specific fixes
            fixes = self._parse_fix_suggestions(fix_suggestions)
            
            return {
                "success": True,
                "error_analysis": error_analysis,
                "fix_suggestions": fix_suggestions,
                "parsed_fixes": fixes,
                "confidence": self._assess_fix_confidence(error_analysis, fixes)
            }
            
        except Exception as e:
            return {"error": f"Fix suggestion failed: {e}"}
    
    async def _apply_fix(self, fix_suggestion: Dict[str, Any], code: str, language: str) -> Dict[str, Any]:
        """Apply the suggested fix to the code"""
        
        routing_decision = self.model_router.route_task(
            f"apply fix to {language} code",
            context={'agent_type': 'debugger', 'task_type': 'fix_application'}
        )
        
        apply_prompt = f"""
Apply the following fix to the code:

Fix Suggestion:
{json.dumps(fix_suggestion, indent=2)}

Original Code:
```{language}
{code}
```

Please provide:

1. FIXED CODE:
   - Complete corrected version
   - All necessary changes applied
   - Proper formatting and style

2. CHANGE SUMMARY:
   - What was changed
   - Why each change was made
   - Impact of the changes

3. VALIDATION NOTES:
   - How to test the fix
   - Expected behavior after fix
   - Potential side effects

Fixed Code:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=apply_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            fix_result = response.response
            
            # Extract fixed code
            fixed_code = self._extract_fixed_code(fix_result, language)
            
            return {
                "success": True,
                "original_code": code,
                "fixed_code": fixed_code,
                "fix_applied": fix_suggestion,
                "change_summary": fix_result,
                "needs_testing": True
            }
            
        except Exception as e:
            return {"error": f"Fix application failed: {e}"}
    
    async def _trace_execution(self, code: str, inputs: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Trace code execution to identify issues"""
        
        routing_decision = self.model_router.route_task(
            f"trace {language} code execution",
            context={'agent_type': 'debugger', 'task_type': 'execution_tracing'}
        )
        
        trace_prompt = f"""
Trace the execution of the following code with given inputs:

Code:
```{language}
{code}
```

Inputs:
{json.dumps(inputs, indent=2)}

Please provide step-by-step execution trace:

1. EXECUTION FLOW:
   - Line-by-line execution order
   - Variable values at each step
   - Function calls and returns
   - Conditional branches taken

2. STATE CHANGES:
   - Variable assignments
   - Object modifications
   - Memory allocations
   - I/O operations

3. POTENTIAL ISSUES:
   - Unexpected values
   - Logic errors
   - Performance bottlenecks
   - Resource usage

4. DEBUGGING INSIGHTS:
   - Where problems might occur
   - Values to monitor
   - Breakpoint suggestions

Execution Trace:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=trace_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            trace_result = response.response
            
            return {
                "success": True,
                "code": code,
                "inputs": inputs,
                "execution_trace": trace_result,
                "language": language,
                "trace_insights": self._extract_trace_insights(trace_result)
            }
            
        except Exception as e:
            return {"error": f"Execution tracing failed: {e}"}
    
    async def _validate_fix(self, original_code: str, fixed_code: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that the fix works correctly"""
        
        routing_decision = self.model_router.route_task(
            "validate code fix",
            context={'agent_type': 'debugger', 'task_type': 'fix_validation'}
        )
        
        validation_prompt = f"""
Validate that the code fix is correct and doesn't introduce new issues:

Original Code:
```
{original_code}
```

Fixed Code:
```
{fixed_code}
```

Test Cases:
{json.dumps(test_cases, indent=2)}

Please validate:

1. CORRECTNESS:
   - Does the fix address the original issue?
   - Are all test cases passing?
   - Is the logic correct?

2. COMPLETENESS:
   - Are all edge cases handled?
   - Is error handling adequate?
   - Are there any missing scenarios?

3. QUALITY:
   - Code readability and maintainability
   - Performance implications
   - Security considerations

4. REGRESSION ANALYSIS:
   - New issues introduced?
   - Existing functionality affected?
   - Side effects identified?

5. RECOMMENDATIONS:
   - Additional improvements needed
   - Further testing required
   - Documentation updates

Validation Results:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=validation_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            validation_result = response.response
            
            return {
                "success": True,
                "original_code": original_code,
                "fixed_code": fixed_code,
                "test_cases": test_cases,
                "validation_result": validation_result,
                "fix_approved": self._assess_fix_approval(validation_result)
            }
            
        except Exception as e:
            return {"error": f"Fix validation failed: {e}"}
    
    # Helper methods
    def _classify_error(self, error_message: str, language: str) -> Dict[str, Any]:
        """Classify error based on patterns"""
        
        if language not in self.error_patterns:
            return {"type": "unknown", "category": "general", "confidence": 0.5}
        
        patterns = self.error_patterns[language]
        
        for error_type, error_info in patterns.items():
            for pattern in error_info["patterns"]:
                if re.search(pattern, error_message, re.IGNORECASE):
                    return {
                        "type": error_type,
                        "category": "syntax" if "syntax" in error_type.lower() else "runtime",
                        "confidence": 0.9,
                        "common_causes": error_info["common_causes"],
                        "fix_strategies": error_info["fix_strategies"]
                    }
        
        return {"type": "unknown", "category": "general", "confidence": 0.3}
    
    def _assess_severity(self, error_message: str, classification: Dict[str, Any]) -> str:
        """Assess error severity"""
        
        critical_indicators = ["segmentation fault", "memory error", "stack overflow", "security"]
        high_indicators = ["exception", "error", "failed", "crash"]
        
        error_lower = error_message.lower()
        
        if any(indicator in error_lower for indicator in critical_indicators):
            return "critical"
        elif any(indicator in error_lower for indicator in high_indicators):
            return "high"
        elif classification.get("category") == "syntax":
            return "medium"
        else:
            return "low"
    
    def _extract_suggested_actions(self, analysis_text: str) -> List[str]:
        """Extract suggested actions from analysis"""
        
        actions = []
        lines = analysis_text.split('\n')
        
        in_actions_section = False
        for line in lines:
            line = line.strip()
            if "immediate actions" in line.lower() or "suggested actions" in line.lower():
                in_actions_section = True
                continue
            elif in_actions_section and line.startswith('-'):
                actions.append(line[1:].strip())
            elif in_actions_section and line and not line.startswith('-'):
                in_actions_section = False
        
        return actions[:5]  # Return top 5 actions
    
    def _parse_fix_suggestions(self, fix_text: str) -> List[Dict[str, Any]]:
        """Parse fix suggestions into structured format"""
        
        fixes = []
        current_fix = None
        
        lines = fix_text.split('\n')
        for line in lines:
            line = line.strip()
            
            if line.startswith("1. PRIMARY FIX:") or line.startswith("PRIMARY FIX:"):
                if current_fix:
                    fixes.append(current_fix)
                current_fix = {"type": "primary", "description": "", "changes": []}
            elif line.startswith("2. ALTERNATIVE") or line.startswith("ALTERNATIVE"):
                if current_fix:
                    fixes.append(current_fix)
                current_fix = {"type": "alternative", "description": "", "changes": []}
            elif current_fix and line.startswith('-'):
                current_fix["changes"].append(line[1:].strip())
            elif current_fix and line:
                current_fix["description"] += line + " "
        
        if current_fix:
            fixes.append(current_fix)
        
        return fixes
    
    def _extract_fixed_code(self, fix_result: str, language: str) -> str:
        """Extract fixed code from fix result"""
        
        # Look for code blocks
        code_pattern = rf'```{language}(.*?)```'
        match = re.search(code_pattern, fix_result, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # Fallback: look for any code block
        code_pattern = r'```(.*?)```'
        match = re.search(code_pattern, fix_result, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return fix_result.strip()
    
    def _extract_trace_insights(self, trace_text: str) -> List[str]:
        """Extract insights from execution trace"""
        
        insights = []
        lines = trace_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['issue', 'problem', 'error', 'warning', 'concern']):
                insights.append(line)
        
        return insights[:5]  # Return top 5 insights
    
    def _assess_fix_confidence(self, error_analysis: Dict[str, Any], fixes: List[Dict[str, Any]]) -> float:
        """Assess confidence in the suggested fixes"""
        
        base_confidence = 0.7
        
        # Increase confidence for well-classified errors
        if error_analysis.get("error_classification", {}).get("confidence", 0) > 0.8:
            base_confidence += 0.1
        
        # Increase confidence for multiple fix options
        if len(fixes) > 1:
            base_confidence += 0.1
        
        # Decrease confidence for unknown error types
        if error_analysis.get("error_classification", {}).get("type") == "unknown":
            base_confidence -= 0.2
        
        return min(1.0, max(0.1, base_confidence))
    
    def _assess_fix_approval(self, validation_result: str) -> bool:
        """Assess if fix should be approved based on validation"""
        
        positive_indicators = ["correct", "passes", "successful", "approved", "good"]
        negative_indicators = ["incorrect", "fails", "error", "issue", "problem"]
        
        validation_lower = validation_result.lower()
        
        positive_count = sum(1 for indicator in positive_indicators if indicator in validation_lower)
        negative_count = sum(1 for indicator in negative_indicators if indicator in validation_lower)
        
        return positive_count > negative_count
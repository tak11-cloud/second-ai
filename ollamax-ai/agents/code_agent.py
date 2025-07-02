"""
Code Agent - Specialized in code generation, modification, and analysis using AST manipulation
"""

import ast
import json
import re
import os
from typing import Dict, List, Optional, Any, Tuple
from .base_agent import BaseAgent, AgentAction

class CodeAgent(BaseAgent):
    """
    Advanced code agent for generation, modification, and analysis
    Uses AST-level manipulation for precise code changes
    """
    
    def __init__(self, ollama_client, model_router, vector_db, task_logger):
        super().__init__(ollama_client, model_router, vector_db, task_logger, "code")
        self.supported_languages = ["python", "javascript", "typescript", "java", "c", "cpp", "go", "rust"]
        self.code_templates = self._load_code_templates()
        self.refactoring_patterns = self._load_refactoring_patterns()
        
    def _load_code_templates(self) -> Dict[str, str]:
        """Load code templates for different patterns"""
        return {
            "python_class": '''class {class_name}:
    """
    {description}
    """
    
    def __init__(self{init_params}):
        {init_body}
    
    {methods}
''',
            "python_function": '''def {function_name}({parameters}){return_type}:
    """
    {description}
    
    Args:
        {args_doc}
    
    Returns:
        {returns_doc}
    """
    {body}
''',
            "python_async_function": '''async def {function_name}({parameters}){return_type}:
    """
    {description}
    
    Args:
        {args_doc}
    
    Returns:
        {returns_doc}
    """
    {body}
''',
            "javascript_function": '''function {function_name}({parameters}) {{
    /**
     * {description}
     * {params_doc}
     * @returns {{{returns_doc}}}
     */
    {body}
}}''',
            "javascript_class": '''class {class_name} {{
    /**
     * {description}
     */
    constructor({constructor_params}) {{
        {constructor_body}
    }}
    
    {methods}
}}''',
            "api_endpoint": '''@app.{method}("{path}")
async def {function_name}({parameters}):
    """
    {description}
    """
    try:
        {body}
        return {{"success": True, "data": result}}
    except Exception as e:
        return {{"success": False, "error": str(e)}}
''',
            "test_function": '''def test_{function_name}():
    """Test {description}"""
    # Arrange
    {arrange}
    
    # Act
    {act}
    
    # Assert
    {assert_statements}
''',
            "security_wrapper": '''def secure_{function_name}({parameters}):
    """
    Security wrapper for {original_function}
    {description}
    """
    # Input validation
    {input_validation}
    
    # Security checks
    {security_checks}
    
    # Execute original function
    try:
        result = {original_function}({args})
        
        # Output sanitization
        {output_sanitization}
        
        return result
    except Exception as e:
        logger.error(f"Security wrapper error: {{e}}")
        raise SecurityError("Operation failed security validation")
'''
        }
    
    def _load_refactoring_patterns(self) -> Dict[str, Dict[str, str]]:
        """Load common refactoring patterns"""
        return {
            "extract_method": {
                "description": "Extract code block into separate method",
                "pattern": "Large method with distinct functionality blocks",
                "solution": "Create new method with extracted code"
            },
            "remove_duplication": {
                "description": "Remove duplicate code by creating shared functions",
                "pattern": "Identical or similar code blocks",
                "solution": "Extract common functionality into shared method"
            },
            "improve_naming": {
                "description": "Improve variable and function names",
                "pattern": "Unclear or misleading names",
                "solution": "Use descriptive, intention-revealing names"
            },
            "add_error_handling": {
                "description": "Add proper error handling",
                "pattern": "Missing try-catch blocks or error checks",
                "solution": "Add appropriate exception handling"
            },
            "optimize_performance": {
                "description": "Optimize code for better performance",
                "pattern": "Inefficient algorithms or data structures",
                "solution": "Use more efficient approaches"
            },
            "enhance_security": {
                "description": "Add security measures",
                "pattern": "Potential security vulnerabilities",
                "solution": "Add input validation, sanitization, and security checks"
            }
        }
    
    async def _execute_action(self, action: AgentAction) -> Any:
        """Execute code-specific actions"""
        action_type = action.action_type
        parameters = action.parameters
        
        if action_type == "generate_code":
            return await self._generate_code(
                parameters.get('description', ''),
                parameters.get('language', 'python'),
                parameters.get('code_type', 'function'),
                parameters.get('requirements', {})
            )
        elif action_type == "analyze_code":
            return await self._analyze_code(
                parameters.get('code', ''),
                parameters.get('language', 'python'),
                parameters.get('analysis_type', 'comprehensive')
            )
        elif action_type == "refactor_code":
            return await self._refactor_code(
                parameters.get('code', ''),
                parameters.get('refactoring_goals', []),
                parameters.get('language', 'python')
            )
        elif action_type == "fix_code":
            return await self._fix_code(
                parameters.get('code', ''),
                parameters.get('error_message', ''),
                parameters.get('language', 'python')
            )
        elif action_type == "optimize_code":
            return await self._optimize_code(
                parameters.get('code', ''),
                parameters.get('optimization_goals', ['performance']),
                parameters.get('language', 'python')
            )
        elif action_type == "add_security":
            return await self._add_security_measures(
                parameters.get('code', ''),
                parameters.get('security_requirements', []),
                parameters.get('language', 'python')
            )
        elif action_type == "generate_tests":
            return await self._generate_tests(
                parameters.get('code', ''),
                parameters.get('test_type', 'unit'),
                parameters.get('language', 'python')
            )
        elif action_type == "document_code":
            return await self._document_code(
                parameters.get('code', ''),
                parameters.get('documentation_style', 'google'),
                parameters.get('language', 'python')
            )
        elif action_type == "convert_language":
            return await self._convert_language(
                parameters.get('code', ''),
                parameters.get('source_language', 'python'),
                parameters.get('target_language', 'javascript')
            )
        else:
            return {"error": f"Unknown code action: {action_type}"}
    
    def get_available_tools(self) -> List[str]:
        """Return available code tools"""
        return [
            "code_generator",
            "code_analyzer",
            "ast_parser",
            "refactoring_engine",
            "code_optimizer",
            "security_enhancer",
            "test_generator",
            "documentation_generator",
            "language_converter",
            "syntax_checker",
            "complexity_analyzer",
            "dependency_analyzer"
        ]
    
    def _get_system_prompt(self) -> str:
        """System prompt for code agent"""
        return f"""You are an expert code generation and analysis agent for OllamaX-AI. Your role is to:

1. Generate high-quality, secure, and efficient code
2. Analyze existing code for issues and improvements
3. Refactor code following best practices
4. Fix bugs and errors in code
5. Optimize code for performance and security
6. Generate comprehensive tests
7. Create clear documentation
8. Convert between programming languages

Supported Languages: {', '.join(self.supported_languages)}

Code Quality Standards:
- Write clean, readable, and maintainable code
- Follow language-specific best practices and conventions
- Include proper error handling and input validation
- Add security measures for user inputs and sensitive operations
- Write comprehensive documentation and comments
- Ensure code is testable and modular
- Optimize for both performance and security

Security Considerations:
- Always validate and sanitize inputs
- Use parameterized queries for database operations
- Implement proper authentication and authorization
- Handle sensitive data securely
- Add logging for security events
- Follow OWASP guidelines

Testing Standards:
- Write unit tests for all functions
- Include integration tests for complex workflows
- Test edge cases and error conditions
- Ensure good test coverage
- Use appropriate testing frameworks

Documentation Standards:
- Write clear docstrings for all functions and classes
- Include parameter descriptions and return values
- Add usage examples where helpful
- Document any security considerations
- Explain complex algorithms or business logic

Always prioritize code security, maintainability, and performance."""
    
    async def _generate_code(self, description: str, language: str, code_type: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code based on description and requirements"""
        
        # Use code-focused model
        routing_decision = self.model_router.route_task(
            f"generate {language} {code_type}: {description}",
            context={'agent_type': 'code', 'task_type': 'code_generation'}
        )
        
        # Select appropriate template
        template_key = f"{language}_{code_type}"
        if template_key not in self.code_templates:
            template_key = f"{language}_function"  # fallback
        
        template = self.code_templates.get(template_key, "")
        
        generation_prompt = f"""
Generate {language} {code_type} based on the following requirements:

Description: {description}
Language: {language}
Code Type: {code_type}
Requirements: {json.dumps(requirements, indent=2)}

Template Reference:
{template}

Please generate complete, production-ready code that includes:

1. Proper function/class structure
2. Comprehensive documentation
3. Input validation and error handling
4. Security considerations
5. Type hints (where applicable)
6. Example usage
7. Unit tests (if requested)

Code Quality Requirements:
- Follow {language} best practices and conventions
- Include proper error handling
- Add input validation for security
- Write clear, self-documenting code
- Include comprehensive docstrings/comments
- Ensure code is modular and testable

Security Requirements:
- Validate all inputs
- Sanitize outputs
- Handle sensitive data securely
- Add appropriate logging
- Follow security best practices

Generated Code:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=generation_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            generated_code = response.response
            
            # Analyze generated code
            analysis = await self._analyze_generated_code(generated_code, language)
            
            return {
                "success": True,
                "language": language,
                "code_type": code_type,
                "generated_code": generated_code,
                "analysis": analysis,
                "template_used": template_key,
                "requirements_met": self._check_requirements_compliance(generated_code, requirements)
            }
            
        except Exception as e:
            return {"error": f"Code generation failed: {e}"}
    
    async def _analyze_code(self, code: str, language: str, analysis_type: str) -> Dict[str, Any]:
        """Analyze code for various aspects"""
        
        analysis_results = {
            "language": language,
            "analysis_type": analysis_type,
            "metrics": {},
            "issues": [],
            "suggestions": [],
            "security_findings": [],
            "complexity_score": 0
        }
        
        if language == "python":
            analysis_results.update(await self._analyze_python_code(code))
        elif language in ["javascript", "typescript"]:
            analysis_results.update(await self._analyze_javascript_code(code))
        else:
            analysis_results.update(await self._analyze_generic_code(code, language))
        
        # Use AI for deeper analysis
        routing_decision = self.model_router.route_task(
            f"analyze {language} code for {analysis_type}",
            context={'agent_type': 'code', 'task_type': 'code_analysis'}
        )
        
        analysis_prompt = f"""
Perform a {analysis_type} analysis of the following {language} code:

```{language}
{code}
```

Please analyze for:

1. CODE QUALITY:
   - Readability and maintainability
   - Adherence to best practices
   - Code organization and structure
   - Naming conventions

2. SECURITY ISSUES:
   - Input validation vulnerabilities
   - Potential injection attacks
   - Authentication/authorization issues
   - Data exposure risks

3. PERFORMANCE CONCERNS:
   - Algorithmic efficiency
   - Memory usage
   - I/O operations
   - Scalability issues

4. BUG RISKS:
   - Logic errors
   - Edge case handling
   - Error handling gaps
   - Type safety issues

5. MAINTAINABILITY:
   - Code complexity
   - Documentation quality
   - Testability
   - Modularity

Provide structured analysis:

OVERALL ASSESSMENT:
- Quality Score: [1-10]
- Security Score: [1-10]
- Performance Score: [1-10]
- Maintainability Score: [1-10]

IDENTIFIED ISSUES:
[List specific issues with severity levels]

RECOMMENDATIONS:
[Specific improvement suggestions]

SECURITY FINDINGS:
[Security vulnerabilities and risks]

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
            ai_analysis = response.response
            
            # Parse AI analysis
            parsed_analysis = await self._parse_code_analysis(ai_analysis)
            analysis_results.update(parsed_analysis)
            analysis_results["ai_analysis"] = ai_analysis
            
            return {
                "success": True,
                "analysis": analysis_results
            }
            
        except Exception as e:
            return {"error": f"Code analysis failed: {e}"}
    
    async def _refactor_code(self, code: str, refactoring_goals: List[str], language: str) -> Dict[str, Any]:
        """Refactor code based on specified goals"""
        
        # Use code-focused model
        routing_decision = self.model_router.route_task(
            f"refactor {language} code",
            context={'agent_type': 'code', 'task_type': 'code_refactoring'}
        )
        
        refactoring_prompt = f"""
Refactor the following {language} code to achieve these goals:
{', '.join(refactoring_goals)}

Original Code:
```{language}
{code}
```

Refactoring Goals:
{json.dumps(refactoring_goals, indent=2)}

Available Refactoring Patterns:
{json.dumps(self.refactoring_patterns, indent=2)}

Please provide:

1. REFACTORED CODE:
   - Complete refactored version
   - Maintain original functionality
   - Improve code quality based on goals

2. CHANGES MADE:
   - List of specific changes
   - Rationale for each change
   - Benefits achieved

3. BEFORE/AFTER COMPARISON:
   - Key improvements
   - Metrics comparison (if applicable)

4. TESTING RECOMMENDATIONS:
   - How to verify refactoring didn't break functionality
   - Additional tests needed

Refactored Code:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=refactoring_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            refactoring_result = response.response
            
            # Extract refactored code
            refactored_code = await self._extract_code_from_response(refactoring_result, language)
            
            # Analyze improvements
            original_analysis = await self._analyze_code(code, language, "basic")
            refactored_analysis = await self._analyze_code(refactored_code, language, "basic")
            
            return {
                "success": True,
                "original_code": code,
                "refactored_code": refactored_code,
                "refactoring_goals": refactoring_goals,
                "changes_summary": refactoring_result,
                "improvement_metrics": {
                    "original_analysis": original_analysis,
                    "refactored_analysis": refactored_analysis
                }
            }
            
        except Exception as e:
            return {"error": f"Code refactoring failed: {e}"}
    
    async def _fix_code(self, code: str, error_message: str, language: str) -> Dict[str, Any]:
        """Fix code based on error message"""
        
        # Use debugging-focused model
        routing_decision = self.model_router.route_task(
            f"fix {language} code error",
            context={'agent_type': 'code', 'task_type': 'debugging'}
        )
        
        fix_prompt = f"""
Fix the following {language} code that has an error:

Error Message:
{error_message}

Problematic Code:
```{language}
{code}
```

Please provide:

1. ERROR ANALYSIS:
   - Root cause of the error
   - Why the error occurred
   - Impact of the error

2. FIXED CODE:
   - Complete corrected version
   - Explanation of changes made
   - Additional improvements (if any)

3. PREVENTION MEASURES:
   - How to prevent similar errors
   - Best practices to follow
   - Testing recommendations

4. VALIDATION:
   - How to verify the fix works
   - Test cases to run

Fixed Code:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=fix_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            fix_result = response.response
            
            # Extract fixed code
            fixed_code = await self._extract_code_from_response(fix_result, language)
            
            return {
                "success": True,
                "original_code": code,
                "error_message": error_message,
                "fixed_code": fixed_code,
                "fix_explanation": fix_result,
                "validation_needed": True
            }
            
        except Exception as e:
            return {"error": f"Code fixing failed: {e}"}
    
    async def _add_security_measures(self, code: str, security_requirements: List[str], language: str) -> Dict[str, Any]:
        """Add security measures to existing code"""
        
        # Use security-focused model
        routing_decision = self.model_router.route_task(
            f"add security to {language} code",
            context={'agent_type': 'code', 'task_type': 'security_enhancement'}
        )
        
        security_prompt = f"""
Enhance the following {language} code with security measures:

Security Requirements:
{json.dumps(security_requirements, indent=2)}

Original Code:
```{language}
{code}
```

Please add security enhancements for:

1. INPUT VALIDATION:
   - Validate all user inputs
   - Sanitize data before processing
   - Check data types and ranges

2. OUTPUT SANITIZATION:
   - Escape output data
   - Prevent injection attacks
   - Safe data rendering

3. ERROR HANDLING:
   - Secure error messages
   - Proper exception handling
   - Logging security events

4. AUTHENTICATION/AUTHORIZATION:
   - Access control checks
   - Permission validation
   - Session management

5. DATA PROTECTION:
   - Encrypt sensitive data
   - Secure data storage
   - Safe data transmission

Provide:
- Secured version of the code
- Explanation of security measures added
- Security testing recommendations

Secured Code:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=security_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            security_result = response.response
            
            # Extract secured code
            secured_code = await self._extract_code_from_response(security_result, language)
            
            return {
                "success": True,
                "original_code": code,
                "secured_code": secured_code,
                "security_requirements": security_requirements,
                "security_enhancements": security_result,
                "security_testing_needed": True
            }
            
        except Exception as e:
            return {"error": f"Security enhancement failed: {e}"}
    
    async def _generate_tests(self, code: str, test_type: str, language: str) -> Dict[str, Any]:
        """Generate tests for the given code"""
        
        # Use testing-focused model
        routing_decision = self.model_router.route_task(
            f"generate {test_type} tests for {language} code",
            context={'agent_type': 'code', 'task_type': 'testing'}
        )
        
        test_prompt = f"""
Generate {test_type} tests for the following {language} code:

Code to Test:
```{language}
{code}
```

Test Type: {test_type}

Please generate comprehensive tests that include:

1. UNIT TESTS:
   - Test all public functions/methods
   - Test normal cases
   - Test edge cases
   - Test error conditions

2. TEST STRUCTURE:
   - Arrange-Act-Assert pattern
   - Clear test names
   - Good test coverage
   - Independent tests

3. TEST CASES:
   - Valid inputs
   - Invalid inputs
   - Boundary conditions
   - Error scenarios

4. ASSERTIONS:
   - Verify expected outputs
   - Check side effects
   - Validate error handling

Use appropriate testing framework for {language}.

Generated Tests:"""
        
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
            
            return {
                "success": True,
                "original_code": code,
                "test_type": test_type,
                "test_code": test_code,
                "language": language,
                "testing_framework": self._get_testing_framework(language),
                "coverage_estimate": "high"
            }
            
        except Exception as e:
            return {"error": f"Test generation failed: {e}"}
    
    # Helper methods
    async def _analyze_python_code(self, code: str) -> Dict[str, Any]:
        """Analyze Python code using AST"""
        try:
            tree = ast.parse(code)
            
            metrics = {
                "lines_of_code": len(code.split('\n')),
                "functions": len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]),
                "classes": len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]),
                "imports": len([node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]),
                "complexity": self._calculate_complexity(tree)
            }
            
            issues = []
            suggestions = []
            
            # Check for common issues
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if len(node.body) > 20:
                        issues.append(f"Function '{node.name}' is too long ({len(node.body)} statements)")
                        suggestions.append(f"Consider breaking down function '{node.name}' into smaller functions")
                
                if isinstance(node, ast.Name) and node.id in ['eval', 'exec']:
                    issues.append(f"Dangerous function '{node.id}' used")
                    suggestions.append(f"Avoid using '{node.id}' for security reasons")
            
            return {
                "metrics": metrics,
                "issues": issues,
                "suggestions": suggestions,
                "ast_available": True
            }
            
        except SyntaxError as e:
            return {
                "metrics": {"syntax_error": str(e)},
                "issues": [f"Syntax error: {e}"],
                "suggestions": ["Fix syntax errors before analysis"],
                "ast_available": False
            }
    
    async def _analyze_javascript_code(self, code: str) -> Dict[str, Any]:
        """Analyze JavaScript code"""
        metrics = {
            "lines_of_code": len(code.split('\n')),
            "functions": len(re.findall(r'function\s+\w+|=>\s*{|\w+\s*:\s*function', code)),
            "classes": len(re.findall(r'class\s+\w+', code)),
            "var_declarations": len(re.findall(r'\b(var|let|const)\s+\w+', code))
        }
        
        issues = []
        suggestions = []
        
        # Check for common JavaScript issues
        if 'eval(' in code:
            issues.append("Use of eval() detected")
            suggestions.append("Avoid eval() for security reasons")
        
        if 'var ' in code:
            issues.append("Use of 'var' detected")
            suggestions.append("Use 'let' or 'const' instead of 'var'")
        
        return {
            "metrics": metrics,
            "issues": issues,
            "suggestions": suggestions
        }
    
    async def _analyze_generic_code(self, code: str, language: str) -> Dict[str, Any]:
        """Generic code analysis for unsupported languages"""
        metrics = {
            "lines_of_code": len(code.split('\n')),
            "characters": len(code),
            "estimated_complexity": "medium"
        }
        
        return {
            "metrics": metrics,
            "issues": [],
            "suggestions": [f"Consider using language-specific analysis tools for {language}"]
        }
    
    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity of AST"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    async def _extract_code_from_response(self, response: str, language: str) -> str:
        """Extract code from AI response"""
        # Look for code blocks
        code_pattern = rf'```{language}(.*?)```'
        match = re.search(code_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # Fallback: look for any code block
        code_pattern = r'```(.*?)```'
        match = re.search(code_pattern, response, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        # If no code blocks found, return the response as-is
        return response.strip()
    
    async def _parse_code_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse AI code analysis into structured format"""
        parsed = {
            "quality_score": 7,  # default
            "security_score": 7,
            "performance_score": 7,
            "maintainability_score": 7,
            "issues": [],
            "recommendations": []
        }
        
        # Extract scores
        score_patterns = {
            "quality_score": r"Quality Score:\s*(\d+)",
            "security_score": r"Security Score:\s*(\d+)",
            "performance_score": r"Performance Score:\s*(\d+)",
            "maintainability_score": r"Maintainability Score:\s*(\d+)"
        }
        
        for key, pattern in score_patterns.items():
            match = re.search(pattern, analysis_text, re.IGNORECASE)
            if match:
                parsed[key] = int(match.group(1))
        
        return parsed
    
    def _check_requirements_compliance(self, code: str, requirements: Dict[str, Any]) -> Dict[str, bool]:
        """Check if generated code meets requirements"""
        compliance = {}
        
        for req_key, req_value in requirements.items():
            if req_key == "include_docstring":
                compliance[req_key] = '"""' in code or "'''" in code
            elif req_key == "include_error_handling":
                compliance[req_key] = 'try:' in code or 'except' in code
            elif req_key == "include_type_hints":
                compliance[req_key] = '->' in code or ': ' in code
            else:
                compliance[req_key] = True  # Default to compliant
        
        return compliance
    
    def _get_testing_framework(self, language: str) -> str:
        """Get appropriate testing framework for language"""
        frameworks = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "java": "junit",
            "c": "unity",
            "cpp": "gtest",
            "go": "testing",
            "rust": "cargo test"
        }
        return frameworks.get(language, "language-specific")
    
    async def _analyze_generated_code(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze quality of generated code"""
        analysis = await self._analyze_code(code, language, "basic")
        
        if analysis.get("success"):
            return analysis["analysis"]
        else:
            return {"error": "Analysis failed", "basic_metrics": {"lines": len(code.split('\n'))}}
    
    async def _document_code(self, code: str, documentation_style: str, language: str) -> Dict[str, Any]:
        """Generate documentation for code"""
        
        routing_decision = self.model_router.route_task(
            f"document {language} code",
            context={'agent_type': 'code', 'task_type': 'documentation'}
        )
        
        doc_prompt = f"""
Generate comprehensive documentation for the following {language} code using {documentation_style} style:

Code:
```{language}
{code}
```

Please provide:

1. OVERVIEW DOCUMENTATION:
   - Purpose and functionality
   - Key features
   - Usage examples

2. API DOCUMENTATION:
   - Function/method signatures
   - Parameter descriptions
   - Return value descriptions
   - Exception handling

3. INLINE COMMENTS:
   - Complex logic explanations
   - Algorithm descriptions
   - Important notes

4. USAGE EXAMPLES:
   - Basic usage
   - Advanced usage
   - Common patterns

Documentation:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=doc_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            documentation = response.response
            
            return {
                "success": True,
                "original_code": code,
                "documentation": documentation,
                "documentation_style": documentation_style,
                "language": language
            }
            
        except Exception as e:
            return {"error": f"Documentation generation failed: {e}"}
    
    async def _convert_language(self, code: str, source_language: str, target_language: str) -> Dict[str, Any]:
        """Convert code from one language to another"""
        
        routing_decision = self.model_router.route_task(
            f"convert {source_language} to {target_language}",
            context={'agent_type': 'code', 'task_type': 'language_conversion'}
        )
        
        conversion_prompt = f"""
Convert the following {source_language} code to {target_language}:

Source Code ({source_language}):
```{source_language}
{code}
```

Target Language: {target_language}

Please provide:

1. CONVERTED CODE:
   - Functionally equivalent {target_language} code
   - Follow {target_language} best practices
   - Maintain original logic and structure

2. CONVERSION NOTES:
   - Key differences between languages
   - Assumptions made during conversion
   - Manual adjustments needed

3. TESTING RECOMMENDATIONS:
   - How to verify conversion correctness
   - Important test cases

Converted Code:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=conversion_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            conversion_result = response.response
            
            # Extract converted code
            converted_code = await self._extract_code_from_response(conversion_result, target_language)
            
            return {
                "success": True,
                "source_code": code,
                "source_language": source_language,
                "target_language": target_language,
                "converted_code": converted_code,
                "conversion_notes": conversion_result
            }
            
        except Exception as e:
            return {"error": f"Language conversion failed: {e}"}
    
    async def _optimize_code(self, code: str, optimization_goals: List[str], language: str) -> Dict[str, Any]:
        """Optimize code for performance, memory, etc."""
        
        routing_decision = self.model_router.route_task(
            f"optimize {language} code",
            context={'agent_type': 'code', 'task_type': 'optimization'}
        )
        
        optimization_prompt = f"""
Optimize the following {language} code for: {', '.join(optimization_goals)}

Original Code:
```{language}
{code}
```

Optimization Goals:
{json.dumps(optimization_goals, indent=2)}

Please provide:

1. OPTIMIZED CODE:
   - Improved version focusing on specified goals
   - Maintain functionality while improving performance
   - Use efficient algorithms and data structures

2. OPTIMIZATION TECHNIQUES APPLIED:
   - Specific improvements made
   - Performance gains expected
   - Trade-offs considered

3. PERFORMANCE ANALYSIS:
   - Before/after comparison
   - Complexity analysis
   - Resource usage improvements

4. TESTING RECOMMENDATIONS:
   - Performance benchmarks
   - Correctness verification

Optimized Code:"""
        
        from llm_engine.ollama_client import GenerationRequest
        request = GenerationRequest(
            model=routing_decision.primary_model,
            prompt=optimization_prompt,
            system=self._get_system_prompt(),
            stream=False
        )
        
        try:
            response = await self.ollama_client.generate(request)
            optimization_result = response.response
            
            # Extract optimized code
            optimized_code = await self._extract_code_from_response(optimization_result, language)
            
            return {
                "success": True,
                "original_code": code,
                "optimized_code": optimized_code,
                "optimization_goals": optimization_goals,
                "optimization_details": optimization_result,
                "language": language
            }
            
        except Exception as e:
            return {"error": f"Code optimization failed: {e}"}
"""
Tree Parser for AST-level code analysis and manipulation
"""

import ast
import json
from typing import Dict, List, Optional, Any, Union
import logging

logger = logging.getLogger(__name__)

class TreeParser:
    """
    Advanced AST parser for code analysis and manipulation
    """
    
    def __init__(self):
        self.supported_languages = ['python']  # Can be extended
        
    def parse_python(self, code: str) -> Dict[str, Any]:
        """Parse Python code into AST"""
        
        try:
            tree = ast.parse(code)
            return {
                'success': True,
                'ast': tree,
                'analysis': self._analyze_python_ast(tree),
                'structure': self._extract_structure(tree)
            }
        except SyntaxError as e:
            return {
                'success': False,
                'error': str(e),
                'line': e.lineno,
                'offset': e.offset
            }
    
    def _analyze_python_ast(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze Python AST for metrics and patterns"""
        
        analysis = {
            'functions': [],
            'classes': [],
            'imports': [],
            'variables': [],
            'complexity': 0,
            'lines_of_code': 0,
            'security_issues': []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                analysis['functions'].append({
                    'name': node.name,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                    'complexity': self._calculate_function_complexity(node)
                })
                
            elif isinstance(node, ast.ClassDef):
                analysis['classes'].append({
                    'name': node.name,
                    'line': node.lineno,
                    'bases': [self._get_name(base) for base in node.bases],
                    'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                })
                
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis['imports'].append({
                            'module': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno
                        })
                else:  # ImportFrom
                    for alias in node.names:
                        analysis['imports'].append({
                            'module': node.module,
                            'name': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno
                        })
            
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        analysis['variables'].append({
                            'name': target.id,
                            'line': node.lineno,
                            'type': self._infer_type(node.value)
                        })
            
            # Security analysis
            if isinstance(node, ast.Call):
                func_name = self._get_name(node.func)
                if func_name in ['eval', 'exec', 'compile']:
                    analysis['security_issues'].append({
                        'type': 'dangerous_function',
                        'function': func_name,
                        'line': node.lineno,
                        'severity': 'high'
                    })
        
        analysis['complexity'] = self._calculate_total_complexity(tree)
        analysis['lines_of_code'] = self._count_lines(tree)
        
        return analysis
    
    def _extract_structure(self, tree: ast.AST) -> Dict[str, Any]:
        """Extract code structure"""
        
        structure = {
            'type': 'module',
            'children': []
        }
        
        for node in tree.body:
            structure['children'].append(self._node_to_structure(node))
        
        return structure
    
    def _node_to_structure(self, node: ast.AST) -> Dict[str, Any]:
        """Convert AST node to structure representation"""
        
        if isinstance(node, ast.FunctionDef):
            return {
                'type': 'function',
                'name': node.name,
                'line': node.lineno,
                'args': [arg.arg for arg in node.args.args],
                'children': [self._node_to_structure(child) for child in node.body]
            }
        
        elif isinstance(node, ast.ClassDef):
            return {
                'type': 'class',
                'name': node.name,
                'line': node.lineno,
                'children': [self._node_to_structure(child) for child in node.body]
            }
        
        elif isinstance(node, ast.If):
            return {
                'type': 'if',
                'line': node.lineno,
                'condition': ast.unparse(node.test) if hasattr(ast, 'unparse') else 'condition',
                'children': [self._node_to_structure(child) for child in node.body]
            }
        
        elif isinstance(node, ast.For):
            return {
                'type': 'for',
                'line': node.lineno,
                'target': self._get_name(node.target),
                'children': [self._node_to_structure(child) for child in node.body]
            }
        
        elif isinstance(node, ast.While):
            return {
                'type': 'while',
                'line': node.lineno,
                'children': [self._node_to_structure(child) for child in node.body]
            }
        
        else:
            return {
                'type': type(node).__name__.lower(),
                'line': getattr(node, 'lineno', 0)
            }
    
    def _calculate_function_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        
        complexity = 1  # Base complexity
        
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(node, ast.comprehension):
                complexity += 1
        
        return complexity
    
    def _calculate_total_complexity(self, tree: ast.AST) -> int:
        """Calculate total complexity of the module"""
        
        total_complexity = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_complexity += self._calculate_function_complexity(node)
        
        return total_complexity
    
    def _count_lines(self, tree: ast.AST) -> int:
        """Count lines of code"""
        
        lines = set()
        
        for node in ast.walk(tree):
            if hasattr(node, 'lineno'):
                lines.add(node.lineno)
        
        return len(lines)
    
    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node"""
        
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return str(type(node).__name__)
    
    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Get decorator name"""
        
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_name(decorator.value)}.{decorator.attr}"
        else:
            return "unknown"
    
    def _infer_type(self, node: ast.AST) -> str:
        """Infer variable type from assignment"""
        
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        elif isinstance(node, ast.List):
            return "list"
        elif isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.Set):
            return "set"
        elif isinstance(node, ast.Tuple):
            return "tuple"
        elif isinstance(node, ast.Call):
            func_name = self._get_name(node.func)
            if func_name in ['int', 'float', 'str', 'bool', 'list', 'dict', 'set', 'tuple']:
                return func_name
            return "unknown"
        else:
            return "unknown"
    
    def find_functions(self, code: str) -> List[Dict[str, Any]]:
        """Find all functions in code"""
        
        result = self.parse_python(code)
        if result['success']:
            return result['analysis']['functions']
        return []
    
    def find_classes(self, code: str) -> List[Dict[str, Any]]:
        """Find all classes in code"""
        
        result = self.parse_python(code)
        if result['success']:
            return result['analysis']['classes']
        return []
    
    def find_security_issues(self, code: str) -> List[Dict[str, Any]]:
        """Find security issues in code"""
        
        result = self.parse_python(code)
        if result['success']:
            return result['analysis']['security_issues']
        return []
    
    def extract_function(self, code: str, function_name: str) -> Optional[str]:
        """Extract specific function from code"""
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    # Get the source code for this function
                    lines = code.split('\n')
                    start_line = node.lineno - 1
                    
                    # Find end line by looking for next function/class or end of file
                    end_line = len(lines)
                    for other_node in tree.body:
                        if (hasattr(other_node, 'lineno') and 
                            other_node.lineno > node.lineno and
                            other_node.lineno - 1 < end_line):
                            end_line = other_node.lineno - 1
                    
                    return '\n'.join(lines[start_line:end_line])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract function {function_name}: {e}")
            return None
    
    def modify_function(self, code: str, function_name: str, new_function_code: str) -> str:
        """Replace function in code"""
        
        try:
            tree = ast.parse(code)
            lines = code.split('\n')
            
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    start_line = node.lineno - 1
                    
                    # Find end line
                    end_line = len(lines)
                    for other_node in tree.body:
                        if (hasattr(other_node, 'lineno') and 
                            other_node.lineno > node.lineno and
                            other_node.lineno - 1 < end_line):
                            end_line = other_node.lineno - 1
                    
                    # Replace function
                    new_lines = lines[:start_line] + new_function_code.split('\n') + lines[end_line:]
                    return '\n'.join(new_lines)
            
            # Function not found, append it
            return code + '\n\n' + new_function_code
            
        except Exception as e:
            logger.error(f"Failed to modify function {function_name}: {e}")
            return code
    
    def add_import(self, code: str, import_statement: str) -> str:
        """Add import statement to code"""
        
        try:
            tree = ast.parse(code)
            lines = code.split('\n')
            
            # Find where to insert import (after existing imports)
            insert_line = 0
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    insert_line = node.lineno
                else:
                    break
            
            # Insert import
            lines.insert(insert_line, import_statement)
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"Failed to add import: {e}")
            return import_statement + '\n' + code
    
    def get_dependencies(self, code: str) -> List[str]:
        """Get list of dependencies from imports"""
        
        result = self.parse_python(code)
        if result['success']:
            imports = result['analysis']['imports']
            dependencies = set()
            
            for imp in imports:
                if imp.get('module'):
                    # Extract top-level module name
                    module = imp['module'].split('.')[0]
                    dependencies.add(module)
            
            return list(dependencies)
        
        return []
    
    def validate_syntax(self, code: str) -> Dict[str, Any]:
        """Validate code syntax"""
        
        try:
            ast.parse(code)
            return {'valid': True, 'errors': []}
        except SyntaxError as e:
            return {
                'valid': False,
                'errors': [{
                    'type': 'SyntaxError',
                    'message': str(e),
                    'line': e.lineno,
                    'offset': e.offset
                }]
            }
    
    def format_code(self, code: str) -> str:
        """Basic code formatting"""
        
        try:
            # Parse and unparse to normalize formatting
            tree = ast.parse(code)
            if hasattr(ast, 'unparse'):
                return ast.unparse(tree)
            else:
                # Fallback: basic indentation fix
                lines = code.split('\n')
                formatted_lines = []
                indent_level = 0
                
                for line in lines:
                    stripped = line.strip()
                    if not stripped:
                        formatted_lines.append('')
                        continue
                    
                    # Decrease indent for certain keywords
                    if stripped.startswith(('except', 'elif', 'else', 'finally')):
                        indent_level = max(0, indent_level - 1)
                    
                    formatted_lines.append('    ' * indent_level + stripped)
                    
                    # Increase indent after certain keywords
                    if stripped.endswith(':'):
                        indent_level += 1
                
                return '\n'.join(formatted_lines)
                
        except Exception as e:
            logger.error(f"Failed to format code: {e}")
            return code
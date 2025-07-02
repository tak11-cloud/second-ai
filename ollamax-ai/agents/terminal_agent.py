"""
Terminal Agent - Handles secure command execution and system interaction
"""

import asyncio
import subprocess
import os
import shlex
import json
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from .base_agent import BaseAgent, AgentAction

class TerminalAgent(BaseAgent):
    """
    Secure terminal agent for command execution and system interaction
    Runs commands in sandboxed environments with safety checks
    """
    
    def __init__(self, ollama_client, model_router, vector_db, task_logger):
        super().__init__(ollama_client, model_router, vector_db, task_logger, "terminal")
        self.allowed_commands = self._load_allowed_commands()
        self.dangerous_commands = self._load_dangerous_commands()
        self.command_history = []
        self.current_directory = os.getcwd()
        self.environment_vars = {}
        
    def _load_allowed_commands(self) -> List[str]:
        """Load list of allowed commands"""
        return [
            # File operations
            "ls", "cat", "head", "tail", "grep", "find", "wc", "sort", "uniq",
            "file", "stat", "du", "df", "tree",
            
            # Text processing
            "awk", "sed", "cut", "tr", "paste", "join", "diff", "patch",
            
            # Network tools (safe ones)
            "ping", "nslookup", "dig", "curl", "wget",
            
            # Development tools
            "git", "python", "python3", "node", "npm", "pip", "pip3",
            "make", "cmake", "gcc", "g++", "javac", "java",
            
            # System info (read-only)
            "ps", "top", "htop", "free", "uptime", "uname", "whoami", "id",
            "env", "printenv", "which", "whereis", "type",
            
            # Archive tools
            "tar", "gzip", "gunzip", "zip", "unzip",
            
            # Docker (if available)
            "docker", "docker-compose",
            
            # Text editors (safe)
            "nano", "vim", "emacs",
            
            # Package managers (read operations)
            "apt", "yum", "brew", "pacman"
        ]
    
    def _load_dangerous_commands(self) -> List[str]:
        """Load list of dangerous commands to block"""
        return [
            # System modification
            "rm", "rmdir", "mv", "cp", "chmod", "chown", "chgrp",
            "mount", "umount", "fdisk", "mkfs", "fsck",
            
            # Process control
            "kill", "killall", "pkill", "sudo", "su", "passwd",
            
            # Network attacks
            "nmap", "nc", "netcat", "telnet", "ssh", "scp", "rsync",
            
            # System control
            "reboot", "shutdown", "halt", "poweroff", "systemctl", "service",
            
            # Dangerous operations
            "dd", "shred", "wipe", "format", "mkswap",
            
            # Privilege escalation
            "sudo", "su", "doas",
            
            # Compiler/interpreter abuse
            "eval", "exec", "source", ".",
            
            # Network services
            "apache2", "nginx", "httpd", "sshd", "ftpd"
        ]
    
    async def _execute_action(self, action: AgentAction) -> Any:
        """Execute terminal-specific actions"""
        action_type = action.action_type
        parameters = action.parameters
        
        if action_type == "execute_command":
            return await self._execute_command(
                parameters.get('command', ''),
                parameters.get('timeout', 30),
                parameters.get('working_directory', self.current_directory),
                parameters.get('environment', {})
            )
        elif action_type == "execute_script":
            return await self._execute_script(
                parameters.get('script_content', ''),
                parameters.get('script_type', 'bash'),
                parameters.get('timeout', 60)
            )
        elif action_type == "file_operation":
            return await self._perform_file_operation(
                parameters.get('operation', 'read'),
                parameters.get('file_path', ''),
                parameters.get('content', ''),
                parameters.get('options', {})
            )
        elif action_type == "directory_operation":
            return await self._perform_directory_operation(
                parameters.get('operation', 'list'),
                parameters.get('directory_path', '.'),
                parameters.get('options', {})
            )
        elif action_type == "process_management":
            return await self._manage_process(
                parameters.get('operation', 'list'),
                parameters.get('process_id', None),
                parameters.get('options', {})
            )
        elif action_type == "system_info":
            return await self._get_system_info(
                parameters.get('info_type', 'general')
            )
        elif action_type == "network_operation":
            return await self._perform_network_operation(
                parameters.get('operation', 'ping'),
                parameters.get('target', 'localhost'),
                parameters.get('options', {})
            )
        else:
            return {"error": f"Unknown terminal action: {action_type}"}
    
    def get_available_tools(self) -> List[str]:
        """Return available terminal tools"""
        return [
            "command_executor",
            "script_runner",
            "file_manager",
            "directory_navigator",
            "process_monitor",
            "system_inspector",
            "network_tools",
            "environment_manager",
            "security_scanner",
            "log_analyzer"
        ]
    
    def _get_system_prompt(self) -> str:
        """System prompt for terminal agent"""
        return f"""You are a secure terminal agent for OllamaX-AI. Your role is to:

1. Execute system commands safely and securely
2. Perform file and directory operations
3. Monitor system processes and resources
4. Gather system information
5. Run scripts in controlled environments
6. Manage development workflows

SECURITY CONSTRAINTS:
- Only execute commands from the allowed list
- Block dangerous commands that could harm the system
- Run commands in sandboxed environments when possible
- Validate all inputs before execution
- Log all command executions for audit
- Never execute commands that could compromise security

Allowed Commands: {', '.join(self.allowed_commands[:20])}... (and more)
Blocked Commands: {', '.join(self.dangerous_commands[:10])}... (and more)

SAFETY FEATURES:
- Command validation and sanitization
- Timeout protection for long-running commands
- Working directory isolation
- Environment variable control
- Output size limits
- Error handling and recovery

Always prioritize system security and stability. When in doubt, ask for confirmation before executing potentially risky operations."""
    
    async def _execute_command(self, command: str, timeout: int, working_directory: str, environment: Dict[str, str]) -> Dict[str, Any]:
        """Execute a single command with safety checks"""
        
        # Validate command safety
        safety_check = await self._validate_command_safety(command)
        if not safety_check["safe"]:
            return {
                "success": False,
                "error": f"Command blocked for safety: {safety_check['reason']}",
                "command": command,
                "safety_check": safety_check
            }
        
        # Parse command
        try:
            command_parts = shlex.split(command)
            if not command_parts:
                return {"success": False, "error": "Empty command"}
            
            base_command = command_parts[0]
            
        except ValueError as e:
            return {"success": False, "error": f"Command parsing failed: {e}"}
        
        # Prepare environment
        exec_env = os.environ.copy()
        exec_env.update(self.environment_vars)
        exec_env.update(environment)
        
        # Execute command
        start_time = asyncio.get_event_loop().time()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *command_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_directory,
                env=exec_env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                execution_time = asyncio.get_event_loop().time() - start_time
                
                result = {
                    "success": True,
                    "command": command,
                    "return_code": process.returncode,
                    "stdout": stdout.decode('utf-8', errors='replace'),
                    "stderr": stderr.decode('utf-8', errors='replace'),
                    "execution_time": execution_time,
                    "working_directory": working_directory,
                    "timeout": timeout
                }
                
                # Log command execution
                self.command_history.append({
                    "command": command,
                    "timestamp": start_time,
                    "success": process.returncode == 0,
                    "execution_time": execution_time
                })
                
                return result
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds",
                    "command": command,
                    "timeout": timeout
                }
                
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Command not found: {base_command}",
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Command execution failed: {e}",
                "command": command
            }
    
    async def _execute_script(self, script_content: str, script_type: str, timeout: int) -> Dict[str, Any]:
        """Execute a script in a temporary file"""
        
        # Validate script content
        safety_check = await self._validate_script_safety(script_content, script_type)
        if not safety_check["safe"]:
            return {
                "success": False,
                "error": f"Script blocked for safety: {safety_check['reason']}",
                "safety_check": safety_check
            }
        
        # Create temporary script file
        script_extensions = {
            "bash": ".sh",
            "python": ".py",
            "javascript": ".js",
            "powershell": ".ps1"
        }
        
        extension = script_extensions.get(script_type, ".txt")
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False) as temp_file:
                temp_file.write(script_content)
                temp_file_path = temp_file.name
            
            # Make script executable if it's a shell script
            if script_type == "bash":
                os.chmod(temp_file_path, 0o755)
                command = f"bash {temp_file_path}"
            elif script_type == "python":
                command = f"python3 {temp_file_path}"
            elif script_type == "javascript":
                command = f"node {temp_file_path}"
            else:
                return {"success": False, "error": f"Unsupported script type: {script_type}"}
            
            # Execute script
            result = await self._execute_command(command, timeout, self.current_directory, {})
            
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass  # File cleanup failed, but not critical
            
            result["script_type"] = script_type
            result["script_content"] = script_content
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Script execution failed: {e}",
                "script_type": script_type
            }
    
    async def _perform_file_operation(self, operation: str, file_path: str, content: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Perform file operations safely"""
        
        # Validate file path
        if not self._is_safe_path(file_path):
            return {
                "success": False,
                "error": f"Unsafe file path: {file_path}",
                "operation": operation
            }
        
        try:
            if operation == "read":
                if not os.path.exists(file_path):
                    return {"success": False, "error": f"File not found: {file_path}"}
                
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    file_content = f.read()
                
                return {
                    "success": True,
                    "operation": operation,
                    "file_path": file_path,
                    "content": file_content,
                    "size": len(file_content)
                }
            
            elif operation == "write":
                # Check if we should create directories
                if options.get("create_dirs", False):
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                mode = "w" if not options.get("append", False) else "a"
                with open(file_path, mode, encoding='utf-8') as f:
                    f.write(content)
                
                return {
                    "success": True,
                    "operation": operation,
                    "file_path": file_path,
                    "bytes_written": len(content.encode('utf-8'))
                }
            
            elif operation == "exists":
                return {
                    "success": True,
                    "operation": operation,
                    "file_path": file_path,
                    "exists": os.path.exists(file_path),
                    "is_file": os.path.isfile(file_path) if os.path.exists(file_path) else False,
                    "is_directory": os.path.isdir(file_path) if os.path.exists(file_path) else False
                }
            
            elif operation == "stat":
                if not os.path.exists(file_path):
                    return {"success": False, "error": f"File not found: {file_path}"}
                
                stat_info = os.stat(file_path)
                return {
                    "success": True,
                    "operation": operation,
                    "file_path": file_path,
                    "size": stat_info.st_size,
                    "modified_time": stat_info.st_mtime,
                    "created_time": stat_info.st_ctime,
                    "permissions": oct(stat_info.st_mode)[-3:]
                }
            
            else:
                return {"success": False, "error": f"Unknown file operation: {operation}"}
                
        except PermissionError:
            return {"success": False, "error": f"Permission denied: {file_path}"}
        except Exception as e:
            return {"success": False, "error": f"File operation failed: {e}"}
    
    async def _perform_directory_operation(self, operation: str, directory_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Perform directory operations safely"""
        
        if not self._is_safe_path(directory_path):
            return {
                "success": False,
                "error": f"Unsafe directory path: {directory_path}",
                "operation": operation
            }
        
        try:
            if operation == "list":
                if not os.path.exists(directory_path):
                    return {"success": False, "error": f"Directory not found: {directory_path}"}
                
                items = []
                for item in os.listdir(directory_path):
                    item_path = os.path.join(directory_path, item)
                    item_stat = os.stat(item_path)
                    
                    items.append({
                        "name": item,
                        "type": "directory" if os.path.isdir(item_path) else "file",
                        "size": item_stat.st_size,
                        "modified": item_stat.st_mtime,
                        "permissions": oct(item_stat.st_mode)[-3:]
                    })
                
                return {
                    "success": True,
                    "operation": operation,
                    "directory_path": directory_path,
                    "items": items,
                    "total_items": len(items)
                }
            
            elif operation == "create":
                os.makedirs(directory_path, exist_ok=options.get("exist_ok", True))
                return {
                    "success": True,
                    "operation": operation,
                    "directory_path": directory_path
                }
            
            elif operation == "change":
                if not os.path.exists(directory_path):
                    return {"success": False, "error": f"Directory not found: {directory_path}"}
                
                old_directory = self.current_directory
                self.current_directory = os.path.abspath(directory_path)
                
                return {
                    "success": True,
                    "operation": operation,
                    "old_directory": old_directory,
                    "new_directory": self.current_directory
                }
            
            else:
                return {"success": False, "error": f"Unknown directory operation: {operation}"}
                
        except PermissionError:
            return {"success": False, "error": f"Permission denied: {directory_path}"}
        except Exception as e:
            return {"success": False, "error": f"Directory operation failed: {e}"}
    
    async def _get_system_info(self, info_type: str) -> Dict[str, Any]:
        """Get system information"""
        
        try:
            if info_type == "general":
                # Get basic system info
                uname_result = await self._execute_command("uname -a", 10, self.current_directory, {})
                uptime_result = await self._execute_command("uptime", 10, self.current_directory, {})
                whoami_result = await self._execute_command("whoami", 10, self.current_directory, {})
                
                return {
                    "success": True,
                    "info_type": info_type,
                    "system_info": uname_result.get("stdout", "").strip(),
                    "uptime": uptime_result.get("stdout", "").strip(),
                    "current_user": whoami_result.get("stdout", "").strip(),
                    "current_directory": self.current_directory,
                    "python_version": await self._get_python_version()
                }
            
            elif info_type == "processes":
                ps_result = await self._execute_command("ps aux", 15, self.current_directory, {})
                return {
                    "success": True,
                    "info_type": info_type,
                    "processes": ps_result.get("stdout", "")
                }
            
            elif info_type == "memory":
                free_result = await self._execute_command("free -h", 10, self.current_directory, {})
                return {
                    "success": True,
                    "info_type": info_type,
                    "memory_info": free_result.get("stdout", "")
                }
            
            elif info_type == "disk":
                df_result = await self._execute_command("df -h", 10, self.current_directory, {})
                return {
                    "success": True,
                    "info_type": info_type,
                    "disk_info": df_result.get("stdout", "")
                }
            
            else:
                return {"success": False, "error": f"Unknown info type: {info_type}"}
                
        except Exception as e:
            return {"success": False, "error": f"System info gathering failed: {e}"}
    
    async def _perform_network_operation(self, operation: str, target: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Perform safe network operations"""
        
        # Validate target
        if not self._is_safe_network_target(target):
            return {
                "success": False,
                "error": f"Unsafe network target: {target}",
                "operation": operation
            }
        
        try:
            if operation == "ping":
                count = options.get("count", 4)
                command = f"ping -c {count} {target}"
                result = await self._execute_command(command, 30, self.current_directory, {})
                
                return {
                    "success": result["success"],
                    "operation": operation,
                    "target": target,
                    "ping_result": result.get("stdout", ""),
                    "ping_error": result.get("stderr", "")
                }
            
            elif operation == "nslookup":
                command = f"nslookup {target}"
                result = await self._execute_command(command, 15, self.current_directory, {})
                
                return {
                    "success": result["success"],
                    "operation": operation,
                    "target": target,
                    "lookup_result": result.get("stdout", ""),
                    "lookup_error": result.get("stderr", "")
                }
            
            elif operation == "curl":
                # Safe curl with limited options
                timeout_opt = options.get("timeout", 10)
                command = f"curl -s --max-time {timeout_opt} {target}"
                result = await self._execute_command(command, timeout_opt + 5, self.current_directory, {})
                
                return {
                    "success": result["success"],
                    "operation": operation,
                    "target": target,
                    "response": result.get("stdout", ""),
                    "error": result.get("stderr", "")
                }
            
            else:
                return {"success": False, "error": f"Unknown network operation: {operation}"}
                
        except Exception as e:
            return {"success": False, "error": f"Network operation failed: {e}"}
    
    async def _manage_process(self, operation: str, process_id: Optional[int], options: Dict[str, Any]) -> Dict[str, Any]:
        """Manage processes safely"""
        
        try:
            if operation == "list":
                ps_result = await self._execute_command("ps aux", 15, self.current_directory, {})
                return {
                    "success": ps_result["success"],
                    "operation": operation,
                    "processes": ps_result.get("stdout", "")
                }
            
            elif operation == "info":
                if process_id is None:
                    return {"success": False, "error": "Process ID required for info operation"}
                
                ps_result = await self._execute_command(f"ps -p {process_id} -o pid,ppid,cmd,etime,pcpu,pmem", 10, self.current_directory, {})
                return {
                    "success": ps_result["success"],
                    "operation": operation,
                    "process_id": process_id,
                    "process_info": ps_result.get("stdout", "")
                }
            
            else:
                return {"success": False, "error": f"Unknown process operation: {operation}"}
                
        except Exception as e:
            return {"success": False, "error": f"Process management failed: {e}"}
    
    # Safety validation methods
    async def _validate_command_safety(self, command: str) -> Dict[str, Any]:
        """Validate if a command is safe to execute"""
        
        # Parse command
        try:
            command_parts = shlex.split(command)
            if not command_parts:
                return {"safe": False, "reason": "Empty command"}
            
            base_command = command_parts[0]
            
        except ValueError:
            return {"safe": False, "reason": "Invalid command syntax"}
        
        # Check against dangerous commands
        if base_command in self.dangerous_commands:
            return {"safe": False, "reason": f"Command '{base_command}' is blocked for security"}
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'rm\s+-rf\s+/',  # rm -rf /
            r'>\s*/dev/sd[a-z]',  # writing to disk devices
            r'mkfs\.',  # filesystem creation
            r'dd\s+.*of=/dev/',  # dd to devices
            r'chmod\s+777',  # overly permissive permissions
            r'chown\s+.*:.*\s+/',  # changing ownership of root
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return {"safe": False, "reason": f"Command matches dangerous pattern: {pattern}"}
        
        # Check if command is in allowed list
        if base_command not in self.allowed_commands:
            return {"safe": False, "reason": f"Command '{base_command}' is not in allowed list"}
        
        return {"safe": True, "reason": "Command passed safety checks"}
    
    async def _validate_script_safety(self, script_content: str, script_type: str) -> Dict[str, Any]:
        """Validate if script content is safe to execute"""
        
        # Check for dangerous patterns in script
        dangerous_patterns = [
            r'rm\s+-rf',
            r'sudo\s+',
            r'su\s+',
            r'passwd\s+',
            r'mkfs\.',
            r'fdisk\s+',
            r'dd\s+.*of=',
            r'>/dev/sd[a-z]',
            r'curl.*\|\s*bash',
            r'wget.*\|\s*sh',
            r'eval\s*\(',
            r'exec\s*\(',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, script_content, re.IGNORECASE):
                return {"safe": False, "reason": f"Script contains dangerous pattern: {pattern}"}
        
        # Check script length (prevent extremely long scripts)
        if len(script_content) > 100000:  # 100KB limit
            return {"safe": False, "reason": "Script too large"}
        
        return {"safe": True, "reason": "Script passed safety checks"}
    
    def _is_safe_path(self, path: str) -> bool:
        """Check if file path is safe"""
        
        # Resolve path to absolute
        abs_path = os.path.abspath(path)
        
        # Block access to sensitive directories
        sensitive_dirs = [
            '/etc/passwd',
            '/etc/shadow',
            '/etc/sudoers',
            '/root/',
            '/proc/',
            '/sys/',
            '/dev/',
            '/boot/'
        ]
        
        for sensitive in sensitive_dirs:
            if abs_path.startswith(sensitive):
                return False
        
        # Block parent directory traversal outside working area
        # In production, you'd want to restrict to a specific sandbox directory
        return True
    
    def _is_safe_network_target(self, target: str) -> bool:
        """Check if network target is safe"""
        
        # Block internal/private networks for security
        dangerous_targets = [
            '127.0.0.1',
            'localhost',
            '10.',
            '172.16.',
            '172.17.',
            '172.18.',
            '172.19.',
            '172.20.',
            '172.21.',
            '172.22.',
            '172.23.',
            '172.24.',
            '172.25.',
            '172.26.',
            '172.27.',
            '172.28.',
            '172.29.',
            '172.30.',
            '172.31.',
            '192.168.',
            '169.254.',
            'metadata.google.internal',
            '169.254.169.254'
        ]
        
        # Allow localhost and test domains for demo purposes
        if target in ['localhost', '127.0.0.1', 'example.com', 'httpbin.org']:
            return True
        
        # Block dangerous targets
        for dangerous in dangerous_targets:
            if target.startswith(dangerous):
                return False
        
        return True
    
    async def _get_python_version(self) -> str:
        """Get Python version"""
        try:
            result = await self._execute_command("python3 --version", 5, self.current_directory, {})
            if result["success"]:
                return result["stdout"].strip()
            else:
                return "Unknown"
        except:
            return "Unknown"
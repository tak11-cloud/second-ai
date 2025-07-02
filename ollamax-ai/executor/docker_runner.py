"""
Docker Runner for secure sandboxed execution
"""

import asyncio
import docker
import tempfile
import os
import json
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class DockerRunner:
    """
    Secure Docker-based execution environment for OllamaX-AI
    """
    
    def __init__(self):
        self.client = None
        self.default_images = {
            'python': 'python:3.11-slim',
            'node': 'node:18-slim',
            'ubuntu': 'ubuntu:22.04'
        }
        
    async def initialize(self):
        """Initialize Docker client"""
        
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            logger.info("Docker client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Docker: {e}")
            return False
    
    async def run_python_code(self, code: str, timeout: int = 30, requirements: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run Python code in Docker container"""
        
        if not self.client:
            return {"error": "Docker not initialized"}
        
        # Create temporary directory for code
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write code to file
            code_file = os.path.join(temp_dir, "script.py")
            with open(code_file, 'w') as f:
                f.write(code)
            
            # Create requirements file if needed
            if requirements:
                req_file = os.path.join(temp_dir, "requirements.txt")
                with open(req_file, 'w') as f:
                    f.write('\n'.join(requirements))
            
            # Create Dockerfile
            dockerfile_content = f"""
FROM {self.default_images['python']}
WORKDIR /app
COPY . /app
"""
            
            if requirements:
                dockerfile_content += """
RUN pip install --no-cache-dir -r requirements.txt
"""
            
            dockerfile_content += """
CMD ["python", "script.py"]
"""
            
            dockerfile_path = os.path.join(temp_dir, "Dockerfile")
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            try:
                # Build image
                image_tag = f"ollamax-python-{os.urandom(8).hex()}"
                image, build_logs = self.client.images.build(
                    path=temp_dir,
                    tag=image_tag,
                    rm=True
                )
                
                # Run container
                container = self.client.containers.run(
                    image_tag,
                    detach=True,
                    mem_limit="256m",
                    cpu_quota=50000,  # 50% CPU
                    network_disabled=True,
                    read_only=True,
                    tmpfs={'/tmp': 'noexec,nosuid,size=100m'}
                )
                
                # Wait for completion with timeout
                try:
                    result = container.wait(timeout=timeout)
                    logs = container.logs().decode('utf-8')
                    
                    return {
                        "success": result['StatusCode'] == 0,
                        "exit_code": result['StatusCode'],
                        "output": logs,
                        "timeout": False
                    }
                    
                except Exception as e:
                    # Timeout or other error
                    container.kill()
                    return {
                        "success": False,
                        "error": str(e),
                        "timeout": True
                    }
                
                finally:
                    # Cleanup
                    try:
                        container.remove()
                        self.client.images.remove(image_tag)
                    except:
                        pass
                        
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Docker execution failed: {e}"
                }
    
    async def run_javascript_code(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Run JavaScript code in Docker container"""
        
        if not self.client:
            return {"error": "Docker not initialized"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write code to file
            code_file = os.path.join(temp_dir, "script.js")
            with open(code_file, 'w') as f:
                f.write(code)
            
            # Create Dockerfile
            dockerfile_content = f"""
FROM {self.default_images['node']}
WORKDIR /app
COPY script.js /app/
CMD ["node", "script.js"]
"""
            
            dockerfile_path = os.path.join(temp_dir, "Dockerfile")
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            try:
                # Build and run
                image_tag = f"ollamax-node-{os.urandom(8).hex()}"
                image, build_logs = self.client.images.build(
                    path=temp_dir,
                    tag=image_tag,
                    rm=True
                )
                
                container = self.client.containers.run(
                    image_tag,
                    detach=True,
                    mem_limit="256m",
                    cpu_quota=50000,
                    network_disabled=True,
                    read_only=True,
                    tmpfs={'/tmp': 'noexec,nosuid,size=100m'}
                )
                
                try:
                    result = container.wait(timeout=timeout)
                    logs = container.logs().decode('utf-8')
                    
                    return {
                        "success": result['StatusCode'] == 0,
                        "exit_code": result['StatusCode'],
                        "output": logs,
                        "timeout": False
                    }
                    
                except Exception as e:
                    container.kill()
                    return {
                        "success": False,
                        "error": str(e),
                        "timeout": True
                    }
                
                finally:
                    try:
                        container.remove()
                        self.client.images.remove(image_tag)
                    except:
                        pass
                        
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Docker execution failed: {e}"
                }
    
    async def run_shell_command(self, command: str, timeout: int = 30, image: str = "ubuntu:22.04") -> Dict[str, Any]:
        """Run shell command in Docker container"""
        
        if not self.client:
            return {"error": "Docker not initialized"}
        
        try:
            container = self.client.containers.run(
                image,
                command=["bash", "-c", command],
                detach=True,
                mem_limit="256m",
                cpu_quota=50000,
                network_disabled=True,
                read_only=True,
                tmpfs={'/tmp': 'noexec,nosuid,size=100m'}
            )
            
            try:
                result = container.wait(timeout=timeout)
                logs = container.logs().decode('utf-8')
                
                return {
                    "success": result['StatusCode'] == 0,
                    "exit_code": result['StatusCode'],
                    "output": logs,
                    "command": command,
                    "timeout": False
                }
                
            except Exception as e:
                container.kill()
                return {
                    "success": False,
                    "error": str(e),
                    "timeout": True
                }
            
            finally:
                try:
                    container.remove()
                except:
                    pass
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Docker execution failed: {e}"
            }
    
    async def create_sandbox_environment(self, environment_type: str = "python") -> Dict[str, Any]:
        """Create persistent sandbox environment"""
        
        if not self.client:
            return {"error": "Docker not initialized"}
        
        try:
            image = self.default_images.get(environment_type, self.default_images['ubuntu'])
            
            container = self.client.containers.run(
                image,
                command=["sleep", "3600"],  # Keep alive for 1 hour
                detach=True,
                mem_limit="512m",
                cpu_quota=100000,  # 100% CPU
                network_disabled=True,
                tmpfs={'/tmp': 'noexec,nosuid,size=200m'}
            )
            
            return {
                "success": True,
                "container_id": container.id,
                "environment_type": environment_type,
                "image": image
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create sandbox: {e}"
            }
    
    async def execute_in_sandbox(self, container_id: str, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute command in existing sandbox"""
        
        if not self.client:
            return {"error": "Docker not initialized"}
        
        try:
            container = self.client.containers.get(container_id)
            
            if container.status != 'running':
                return {"error": "Container is not running"}
            
            exec_result = container.exec_run(
                command,
                stdout=True,
                stderr=True,
                stream=False,
                timeout=timeout
            )
            
            return {
                "success": exec_result.exit_code == 0,
                "exit_code": exec_result.exit_code,
                "output": exec_result.output.decode('utf-8'),
                "command": command
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Execution failed: {e}"
            }
    
    async def destroy_sandbox(self, container_id: str) -> Dict[str, Any]:
        """Destroy sandbox environment"""
        
        if not self.client:
            return {"error": "Docker not initialized"}
        
        try:
            container = self.client.containers.get(container_id)
            container.kill()
            container.remove()
            
            return {"success": True, "message": "Sandbox destroyed"}
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to destroy sandbox: {e}"
            }
    
    async def list_sandboxes(self) -> Dict[str, Any]:
        """List active sandbox environments"""
        
        if not self.client:
            return {"error": "Docker not initialized"}
        
        try:
            containers = self.client.containers.list(
                filters={"label": "ollamax-sandbox"}
            )
            
            sandboxes = []
            for container in containers:
                sandboxes.append({
                    "id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else "unknown",
                    "created": container.attrs['Created']
                })
            
            return {
                "success": True,
                "sandboxes": sandboxes,
                "count": len(sandboxes)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list sandboxes: {e}"
            }
    
    async def pull_image(self, image_name: str) -> Dict[str, Any]:
        """Pull Docker image"""
        
        if not self.client:
            return {"error": "Docker not initialized"}
        
        try:
            image = self.client.images.pull(image_name)
            
            return {
                "success": True,
                "image_id": image.id,
                "image_name": image_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to pull image: {e}"
            }
    
    async def cleanup_old_containers(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """Clean up old containers"""
        
        if not self.client:
            return {"error": "Docker not initialized"}
        
        try:
            import datetime
            
            cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=max_age_hours)
            containers = self.client.containers.list(all=True)
            
            cleaned_count = 0
            for container in containers:
                created_time = datetime.datetime.fromisoformat(
                    container.attrs['Created'].replace('Z', '+00:00')
                )
                
                if created_time < cutoff_time:
                    try:
                        if container.status == 'running':
                            container.kill()
                        container.remove()
                        cleaned_count += 1
                    except:
                        pass
            
            return {
                "success": True,
                "cleaned_containers": cleaned_count
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Cleanup failed: {e}"
            }
    
    async def get_container_stats(self, container_id: str) -> Dict[str, Any]:
        """Get container resource usage stats"""
        
        if not self.client:
            return {"error": "Docker not initialized"}
        
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            
            cpu_percent = 0.0
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * 100.0
            
            # Memory usage
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100.0
            
            return {
                "success": True,
                "container_id": container_id,
                "cpu_percent": cpu_percent,
                "memory_usage_mb": memory_usage / (1024 * 1024),
                "memory_limit_mb": memory_limit / (1024 * 1024),
                "memory_percent": memory_percent,
                "network_rx_bytes": stats['networks']['eth0']['rx_bytes'] if 'networks' in stats else 0,
                "network_tx_bytes": stats['networks']['eth0']['tx_bytes'] if 'networks' in stats else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get stats: {e}"
            }
    
    def close(self):
        """Close Docker client"""
        
        if self.client:
            self.client.close()
            self.client = None
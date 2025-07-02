"""
FastAPI Backend for OllamaX-AI
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import logging

logger = logging.getLogger(__name__)

# Request/Response Models
class TaskRequest(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None
    agent_type: Optional[str] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AgentStatusResponse(BaseModel):
    agent_id: str
    agent_type: str
    status: str
    current_task: Optional[str] = None

class SystemStatusResponse(BaseModel):
    status: str
    agents_active: int
    tasks_completed: int
    uptime: float

class APIServer:
    """
    FastAPI server for OllamaX-AI web interface
    """
    
    def __init__(self, ollamax_system):
        self.ollamax_system = ollamax_system
        self.app = FastAPI(
            title="OllamaX-AI API",
            description="God-level AI red team and software engineering platform",
            version="1.0.0"
        )
        
        # WebSocket connections
        self.websocket_connections = []
        
        # Setup middleware
        self.setup_middleware()
        
        # Setup routes
        self.setup_routes()
    
    def setup_middleware(self):
        """Setup CORS and other middleware"""
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/")
        async def root():
            return {"message": "OllamaX-AI API Server", "status": "running"}
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}
        
        @self.app.get("/system/status", response_model=SystemStatusResponse)
        async def get_system_status():
            """Get system status"""
            
            try:
                metrics = self.ollamax_system.task_logger.get_metrics()
                
                return SystemStatusResponse(
                    status="running",
                    agents_active=len(self.ollamax_system.agents),
                    tasks_completed=metrics.get('total_tasks', 0),
                    uptime=asyncio.get_event_loop().time()
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/agents/status")
        async def get_agents_status():
            """Get status of all agents"""
            
            try:
                agents_status = []
                
                for agent_name, agent in self.ollamax_system.agents.items():
                    agents_status.append(AgentStatusResponse(
                        agent_id=agent.agent_id,
                        agent_type=agent.agent_type,
                        status=agent.state.status,
                        current_task=agent.state.current_task
                    ))
                
                return {"agents": agents_status}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/tasks/submit", response_model=TaskResponse)
        async def submit_task(request: TaskRequest):
            """Submit a new task"""
            
            try:
                # Generate task ID
                import uuid
                task_id = str(uuid.uuid4())
                
                # Process task
                result = await self.ollamax_system.process_task(
                    request.task,
                    mode="api"
                )
                
                # Broadcast to WebSocket clients
                await self.broadcast_task_update({
                    "type": "task_submitted",
                    "task_id": task_id,
                    "task": request.task,
                    "result": result
                })
                
                return TaskResponse(
                    task_id=task_id,
                    status="completed" if result.get('success', False) else "failed",
                    result=result
                )
                
            except Exception as e:
                logger.error(f"Task submission failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/tasks/{task_id}")
        async def get_task_status(task_id: str):
            """Get task status"""
            
            # In a real implementation, you'd track tasks in a database
            return {"task_id": task_id, "status": "completed", "message": "Task tracking not implemented"}
        
        @self.app.get("/logs/recent")
        async def get_recent_logs(limit: int = 100, agent_type: Optional[str] = None):
            """Get recent logs"""
            
            try:
                logs = self.ollamax_system.task_logger.get_recent_logs(limit, agent_type)
                return {"logs": logs}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get system metrics"""
            
            try:
                metrics = self.ollamax_system.task_logger.get_metrics()
                agent_performance = self.ollamax_system.task_logger.get_agent_performance()
                
                return {
                    "system_metrics": metrics,
                    "agent_performance": agent_performance
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/models/available")
        async def get_available_models():
            """Get available Ollama models"""
            
            try:
                models = await self.ollamax_system.ollama_client.list_models()
                return {"models": [model.name for model in models]}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/models/route")
        async def route_task_to_model(task: str, context: Optional[Dict[str, Any]] = None):
            """Get model routing decision for a task"""
            
            try:
                routing_decision = self.ollamax_system.model_router.route_task(task, context)
                
                return {
                    "primary_model": routing_decision.primary_model,
                    "fallback_models": routing_decision.fallback_models,
                    "reasoning": routing_decision.reasoning,
                    "confidence": routing_decision.confidence,
                    "estimated_tokens": routing_decision.estimated_tokens
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Keep connection alive and handle incoming messages
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    elif message.get("type") == "subscribe_logs":
                        # Send recent logs
                        logs = self.ollamax_system.task_logger.get_recent_logs(50)
                        await websocket.send_text(json.dumps({
                            "type": "logs_update",
                            "logs": logs
                        }))
                    
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)
        
        # Agent-specific endpoints
        @self.app.post("/agents/redteam/scan")
        async def redteam_scan(target: str, scan_type: str = "basic"):
            """Perform red team vulnerability scan"""
            
            try:
                result = await self.ollamax_system.agents['redteam'].process(
                    f"Perform {scan_type} vulnerability scan on {target}"
                )
                return {"result": result}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/agents/code/generate")
        async def generate_code(description: str, language: str = "python", code_type: str = "function"):
            """Generate code using code agent"""
            
            try:
                result = await self.ollamax_system.agents['code'].process(
                    f"Generate {language} {code_type}: {description}"
                )
                return {"result": result}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/agents/terminal/execute")
        async def execute_command(command: str, timeout: int = 30):
            """Execute command using terminal agent"""
            
            try:
                result = await self.ollamax_system.agents['terminal'].process(
                    f"Execute command: {command}"
                )
                return {"result": result}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        # Memory/Vector DB endpoints
        @self.app.post("/memory/store")
        async def store_information(data: Dict[str, Any]):
            """Store information in vector database"""
            
            try:
                doc_id = await self.ollamax_system.vector_db.store(data)
                return {"doc_id": doc_id, "success": True}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/memory/search")
        async def search_memory(query: str, limit: int = 10):
            """Search vector database"""
            
            try:
                results = await self.ollamax_system.vector_db.search(query, limit)
                return {"results": results}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/memory/stats")
        async def get_memory_stats():
            """Get vector database statistics"""
            
            try:
                stats = await self.ollamax_system.vector_db.get_stats()
                return {"stats": stats}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    async def broadcast_task_update(self, message: Dict[str, Any]):
        """Broadcast message to all WebSocket connections"""
        
        if not self.websocket_connections:
            return
        
        message_json = json.dumps(message)
        disconnected = []
        
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message_json)
            except:
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.websocket_connections.remove(websocket)
    
    async def start(self, host: str = "0.0.0.0", port: int = 12000):
        """Start the API server"""
        
        logger.info(f"Starting OllamaX-AI API server on {host}:{port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    
    def run_sync(self, host: str = "0.0.0.0", port: int = 12000):
        """Run server synchronously"""
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
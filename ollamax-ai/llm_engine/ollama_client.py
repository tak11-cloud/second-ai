"""
Ollama Client for local LLM inference
"""

import asyncio
import json
import aiohttp
import httpx
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    name: str
    size: str
    modified: str
    digest: str
    details: Dict[str, Any]

@dataclass
class GenerationRequest:
    model: str
    prompt: str
    system: Optional[str] = None
    template: Optional[str] = None
    context: Optional[List[int]] = None
    stream: bool = False
    raw: bool = False
    format: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

@dataclass
class GenerationResponse:
    model: str
    created_at: str
    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None

class OllamaClient:
    """High-performance Ollama client for local LLM inference"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.available_models = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """Ensure we have an active session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def test_connection(self) -> bool:
        """Test connection to Ollama server"""
        try:
            await self._ensure_session()
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            return False
    
    async def list_models(self) -> List[ModelInfo]:
        """List available models"""
        try:
            await self._ensure_session()
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = []
                    for model_data in data.get('models', []):
                        models.append(ModelInfo(
                            name=model_data['name'],
                            size=model_data.get('size', ''),
                            modified=model_data.get('modified_at', ''),
                            digest=model_data.get('digest', ''),
                            details=model_data.get('details', {})
                        ))
                    self.available_models = models
                    return models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry"""
        try:
            await self._ensure_session()
            payload = {"name": model_name}
            async with self.session.post(
                f"{self.base_url}/api/pull",
                json=payload
            ) as response:
                if response.status == 200:
                    # Stream the pull progress
                    async for line in response.content:
                        if line:
                            try:
                                progress = json.loads(line.decode())
                                if progress.get('status'):
                                    logger.info(f"Pull progress: {progress['status']}")
                            except json.JSONDecodeError:
                                continue
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using specified model"""
        try:
            await self._ensure_session()
            
            payload = {
                "model": request.model,
                "prompt": request.prompt,
                "stream": request.stream,
                "raw": request.raw
            }
            
            if request.system:
                payload["system"] = request.system
            if request.template:
                payload["template"] = request.template
            if request.context:
                payload["context"] = request.context
            if request.format:
                payload["format"] = request.format
            if request.options:
                payload["options"] = request.options
            
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status == 200:
                    if request.stream:
                        # Handle streaming response
                        full_response = ""
                        context = None
                        async for line in response.content:
                            if line:
                                try:
                                    chunk = json.loads(line.decode())
                                    if chunk.get('response'):
                                        full_response += chunk['response']
                                    if chunk.get('done'):
                                        context = chunk.get('context')
                                        break
                                except json.JSONDecodeError:
                                    continue
                        
                        return GenerationResponse(
                            model=request.model,
                            created_at="",
                            response=full_response,
                            done=True,
                            context=context
                        )
                    else:
                        # Handle non-streaming response
                        data = await response.json()
                        return GenerationResponse(
                            model=data.get('model', request.model),
                            created_at=data.get('created_at', ''),
                            response=data.get('response', ''),
                            done=data.get('done', True),
                            context=data.get('context'),
                            total_duration=data.get('total_duration'),
                            load_duration=data.get('load_duration'),
                            prompt_eval_count=data.get('prompt_eval_count'),
                            prompt_eval_duration=data.get('prompt_eval_duration'),
                            eval_count=data.get('eval_count'),
                            eval_duration=data.get('eval_duration')
                        )
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    async def generate_stream(self, request: GenerationRequest) -> AsyncGenerator[str, None]:
        """Generate text with streaming response"""
        try:
            await self._ensure_session()
            
            payload = {
                "model": request.model,
                "prompt": request.prompt,
                "stream": True,
                "raw": request.raw
            }
            
            if request.system:
                payload["system"] = request.system
            if request.template:
                payload["template"] = request.template
            if request.context:
                payload["context"] = request.context
            if request.format:
                payload["format"] = request.format
            if request.options:
                payload["options"] = request.options
            
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line.decode())
                                if chunk.get('response'):
                                    yield chunk['response']
                                if chunk.get('done'):
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            raise
    
    async def chat(self, model: str, messages: List[Dict[str, str]], stream: bool = False) -> Dict[str, Any]:
        """Chat completion using Ollama chat API"""
        try:
            await self._ensure_session()
            
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream
            }
            
            async with self.session.post(
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                if response.status == 200:
                    if stream:
                        full_response = ""
                        async for line in response.content:
                            if line:
                                try:
                                    chunk = json.loads(line.decode())
                                    if chunk.get('message', {}).get('content'):
                                        full_response += chunk['message']['content']
                                    if chunk.get('done'):
                                        break
                                except json.JSONDecodeError:
                                    continue
                        return {"message": {"content": full_response}}
                    else:
                        return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise
    
    async def embed(self, model: str, prompt: str) -> List[float]:
        """Generate embeddings for text"""
        try:
            await self._ensure_session()
            
            payload = {
                "model": model,
                "prompt": prompt
            }
            
            async with self.session.post(
                f"{self.base_url}/api/embeddings",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('embedding', [])
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise
    
    async def show_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get detailed information about a model"""
        try:
            await self._ensure_session()
            
            payload = {"name": model_name}
            
            async with self.session.post(
                f"{self.base_url}/api/show",
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"Show model info failed: {e}")
            raise
    
    async def delete_model(self, model_name: str) -> bool:
        """Delete a model"""
        try:
            await self._ensure_session()
            
            payload = {"name": model_name}
            
            async with self.session.delete(
                f"{self.base_url}/api/delete",
                json=payload
            ) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Delete model failed: {e}")
            return False
    
    async def close(self):
        """Close the client session"""
        if self.session:
            await self.session.close()
            self.session = None
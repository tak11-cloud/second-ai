#!/usr/bin/env python3
"""
Quick test script for OllamaX-AI system
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_system():
    """Test basic system functionality"""
    
    print("🧪 Testing OllamaX-AI System...")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from llm_engine.ollama_client import OllamaClient
        from llm_engine.router import ModelRouter
        from memory.vector_db import VectorDB
        from tools.task_logger import TaskLogger
        from agents.planner_agent import PlannerAgent
        print("✅ All imports successful")
        
        # Test Ollama client
        print("\n🤖 Testing Ollama client...")
        ollama_client = OllamaClient()
        
        # Test connection (will fail if Ollama not running, but that's expected)
        connection_test = await ollama_client.test_connection()
        if connection_test:
            print("✅ Ollama connection successful")
            
            # Test model listing
            models = await ollama_client.list_models()
            print(f"📋 Available models: {len(models)}")
            for model in models[:3]:  # Show first 3
                print(f"   - {model.name}")
        else:
            print("⚠️  Ollama not running (expected in test environment)")
        
        # Test model router
        print("\n🧭 Testing model router...")
        router = ModelRouter()
        
        # Test task analysis
        task_type, complexity, tokens = router.analyze_task("Generate a Python function")
        print(f"✅ Task analysis: {task_type.value}, {complexity.value}, ~{tokens} tokens")
        
        # Test routing decision
        decision = router.route_task("Generate secure Python code for user authentication")
        print(f"✅ Routing decision: {decision.primary_model} (confidence: {decision.confidence:.2f})")
        
        # Test vector database
        print("\n💾 Testing vector database...")
        vector_db = VectorDB()
        await vector_db.initialize()
        
        # Test document storage
        doc_id = await vector_db.store({
            "content": "This is a test document for OllamaX-AI",
            "metadata": {"type": "test", "category": "system_test"}
        })
        print(f"✅ Document stored with ID: {doc_id}")
        
        # Test search
        results = await vector_db.search("test document", limit=1)
        print(f"✅ Search results: {len(results)} documents found")
        
        # Test task logger
        print("\n📝 Testing task logger...")
        logger = TaskLogger()
        
        await logger.log_task_start("test_task_123", "Test task execution", "test_agent")
        await logger.log_task_complete("test_task_123", "test_agent", True, 1.5, {"result": "success"})
        
        metrics = logger.get_metrics()
        print(f"✅ Logger metrics: {metrics['total_tasks']} tasks logged")
        
        # Test agent initialization
        print("\n🤖 Testing agent initialization...")
        planner = PlannerAgent(ollama_client, router, vector_db, logger)
        print(f"✅ PlannerAgent initialized: {planner.agent_id}")
        print(f"   Available tools: {len(planner.get_available_tools())}")
        
        # Cleanup
        await vector_db.close()
        await ollama_client.close()
        
        print("\n🎉 All tests passed!")
        print("=" * 50)
        print("✅ OllamaX-AI system is ready for use!")
        print("\nNext steps:")
        print("1. Start Ollama: ollama serve")
        print("2. Pull models: ollama pull mixtral")
        print("3. Run system: python main.py interactive")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_system())
    sys.exit(0 if success else 1)
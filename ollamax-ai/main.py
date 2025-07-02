#!/usr/bin/env python3
"""
OllamaX-AI: God-level, offline, self-healing, multi-modal AI red team + software engineering platform
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from llm_engine.ollama_client import OllamaClient
from llm_engine.router import ModelRouter
from agents.planner_agent import PlannerAgent
from agents.redteam_agent import RedTeamAgent
from agents.code_agent import CodeAgent
from agents.terminal_agent import TerminalAgent
from agents.debugger_agent import DebuggerAgent
from agents.search_agent import SearchAgent
from agents.memory_agent import MemoryAgent
from agents.test_agent import TestAgent
from agents.reflection_agent import ReflectionAgent
from agents.upgrade_agent import UpgradeAgent
from agents.vulnscanner_agent import VulnScannerAgent
from memory.vector_db import VectorDB
from tools.task_logger import TaskLogger
from ui.backend.api_server import APIServer

console = Console()
app = typer.Typer(rich_markup_mode="rich")

class OllamaXAI:
    """Main orchestrator for the OllamaX-AI system"""
    
    def __init__(self):
        self.console = Console()
        self.ollama_client = None
        self.model_router = None
        self.vector_db = None
        self.task_logger = None
        self.agents = {}
        self.api_server = None
        
    async def initialize(self):
        """Initialize all system components"""
        self.console.print(Panel.fit(
            "[bold cyan]🚀 Initializing OllamaX-AI System[/bold cyan]",
            border_style="cyan"
        ))
        
        # Initialize core components
        self.ollama_client = OllamaClient()
        self.model_router = ModelRouter()
        self.vector_db = VectorDB()
        self.task_logger = TaskLogger()
        
        # Test Ollama connection
        if not await self.ollama_client.test_connection():
            self.console.print("[red]❌ Ollama not available. Please start Ollama first.[/red]")
            return False
            
        # Initialize vector database
        await self.vector_db.initialize()
        
        # Initialize agents
        await self._initialize_agents()
        
        self.console.print("[green]✅ OllamaX-AI System initialized successfully![/green]")
        return True
        
    async def _initialize_agents(self):
        """Initialize all AI agents"""
        agent_configs = {
            'planner': PlannerAgent,
            'redteam': RedTeamAgent,
            'code': CodeAgent,
            'terminal': TerminalAgent,
            'debugger': DebuggerAgent,
            'search': SearchAgent,
            'memory': MemoryAgent,
            'test': TestAgent,
            'reflection': ReflectionAgent,
            'upgrade': UpgradeAgent,
            'vulnscanner': VulnScannerAgent
        }
        
        for name, agent_class in agent_configs.items():
            self.agents[name] = agent_class(
                ollama_client=self.ollama_client,
                model_router=self.model_router,
                vector_db=self.vector_db,
                task_logger=self.task_logger
            )
            self.console.print(f"[green]✓[/green] {name.title()}Agent initialized")
    
    async def process_task(self, task: str, mode: str = "interactive") -> Dict[str, Any]:
        """Process a user task through the agent system"""
        self.console.print(Panel(
            f"[bold yellow]🎯 Processing Task:[/bold yellow]\n{task}",
            border_style="yellow"
        ))
        
        # Start with planner agent
        plan = await self.agents['planner'].process(task)
        
        # Execute the plan through appropriate agents
        results = {
            'task': task,
            'plan': plan,
            'execution_results': [],
            'final_output': None
        }
        
        # Route to appropriate agents based on plan
        for step in plan.get('steps', []):
            agent_name = step.get('agent', 'planner')
            if agent_name in self.agents:
                step_result = await self.agents[agent_name].execute_step(step)
                results['execution_results'].append(step_result)
        
        # Reflection and improvement
        reflection = await self.agents['reflection'].analyze_results(results)
        results['reflection'] = reflection
        
        return results
    
    async def start_api_server(self, host: str = "0.0.0.0", port: int = 12000):
        """Start the FastAPI server"""
        self.api_server = APIServer(self)
        await self.api_server.start(host, port)

@app.command()
def interactive():
    """Start OllamaX-AI in interactive mode"""
    async def run_interactive():
        system = OllamaXAI()
        if not await system.initialize():
            return
            
        console.print(Panel.fit(
            "[bold green]🤖 OllamaX-AI Interactive Mode[/bold green]\n"
            "Type your tasks, 'help' for commands, or 'exit' to quit",
            border_style="green"
        ))
        
        while True:
            try:
                task = console.input("\n[bold cyan]OllamaX-AI>[/bold cyan] ")
                
                if task.lower() in ['exit', 'quit', 'q']:
                    console.print("[yellow]👋 Goodbye![/yellow]")
                    break
                elif task.lower() == 'help':
                    console.print(Panel(
                        "[bold]Available Commands:[/bold]\n"
                        "• help - Show this help\n"
                        "• exit/quit/q - Exit the system\n"
                        "• Any task description for AI processing",
                        title="Help",
                        border_style="blue"
                    ))
                    continue
                elif task.strip():
                    results = await system.process_task(task)
                    console.print(Panel(
                        f"[green]✅ Task completed![/green]\n"
                        f"Results: {results.get('final_output', 'See execution logs')}",
                        title="Results",
                        border_style="green"
                    ))
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]👋 Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
    
    asyncio.run(run_interactive())

@app.command()
def server(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(12000, help="Port to bind to")
):
    """Start OllamaX-AI API server"""
    async def run_server():
        system = OllamaXAI()
        if not await system.initialize():
            return
        await system.start_api_server(host, port)
    
    asyncio.run(run_server())

@app.command()
def task(task_description: str):
    """Execute a single task"""
    async def run_task():
        system = OllamaXAI()
        if not await system.initialize():
            return
        results = await system.process_task(task_description)
        console.print(results)
    
    asyncio.run(run_task())

if __name__ == "__main__":
    app()
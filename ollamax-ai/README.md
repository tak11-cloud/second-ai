# OllamaX-AI

**God-level, offline, self-healing, multi-modal AI red team + software engineering platform**

OllamaX-AI is a hyper-advanced, multi-agent AI system designed for secure, autonomous, agentic execution. It runs 100% offline using local LLMs via Ollama and is capable of full red teaming, AI-assisted code modification, exploit development, sandboxed execution, debugging, and self-reflection.

## 🚀 Features

### 🧠 Core Capabilities
- **100% Offline Operation** - No API keys or internet required
- **Multi-Agent Architecture** - Specialized agents for different tasks
- **Intelligent Model Routing** - Automatic selection of optimal models
- **Self-Healing & Reflection** - Continuous improvement and error recovery
- **Secure Sandboxed Execution** - Docker-based isolation for safety
- **Long-term Memory** - Vector database for context and knowledge retention

### 🤖 AI Agents

1. **PlannerAgent** - Task decomposition & strategic planning
2. **RedTeamAgent** - Security testing & exploit development
3. **CodeAgent** - Code generation, analysis & modification (AST-level)
4. **TerminalAgent** - Secure command execution & system interaction
5. **DebuggerAgent** - Error analysis & automated fixes
6. **SearchAgent** - Information retrieval & knowledge lookup
7. **MemoryAgent** - Context management & information storage
8. **TestAgent** - Test creation & quality assurance
9. **ReflectionAgent** - Performance analysis & improvement suggestions
10. **UpgradeAgent** - System enhancement & optimization
11. **VulnScannerAgent** - Security scanning & vulnerability detection

### 🔧 Technical Stack

- **LLM Engine**: Ollama with dynamic model routing
- **Models**: Mixtral, OpenChat, CodeLlama, WizardCoder, Phi3, DeepSeek-Coder
- **Memory**: ChromaDB/FAISS vector database with sentence transformers
- **Execution**: Docker containers for secure sandboxing
- **Backend**: FastAPI with WebSocket support
- **Frontend**: React with Tailwind CSS
- **Tools**: AST parsing, Git integration, comprehensive logging

## 📦 Installation

### Prerequisites

1. **Ollama** - Install from [ollama.ai](https://ollama.ai)
2. **Docker** - For secure code execution
3. **Python 3.11+**
4. **Node.js 18+** (for frontend)

### Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd ollamax-ai
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Install and start Ollama**
```bash
# Install Ollama (see ollama.ai for your platform)
# Pull required models
ollama pull mixtral
ollama pull codellama
ollama pull deepseek-coder
ollama pull openchat
ollama pull phi3
```

4. **Start Docker** (if not running)
```bash
sudo systemctl start docker
# or
sudo dockerd > /tmp/docker.log 2>&1 &
```

5. **Install frontend dependencies** (optional)
```bash
cd ui/frontend
npm install
cd ../..
```

## 🚀 Usage

### Command Line Interface

**Interactive Mode**
```bash
python main.py interactive
```

**Single Task Execution**
```bash
python main.py task "Generate a secure login function in Python"
```

**API Server Mode**
```bash
python main.py server --host 0.0.0.0 --port 12000
```

### Web Interface

1. Start the API server:
```bash
python main.py server
```

2. Start the frontend (in another terminal):
```bash
cd ui/frontend
npm run dev
```

3. Open your browser to `http://localhost:12001`

### Example Tasks

**Red Team Security Testing**
```bash
python main.py task "Perform a comprehensive vulnerability scan on a NodeJS application and generate an SSRF exploit chain"
```

**Code Generation & Analysis**
```bash
python main.py task "Generate a Python class for secure file handling with encryption and create comprehensive unit tests"
```

**System Analysis**
```bash
python main.py task "Analyze the current system for performance bottlenecks and security vulnerabilities"
```

**Automated Debugging**
```bash
python main.py task "Debug this Python code and fix any errors: [paste your code here]"
```

## 🏗️ Architecture

### Agent Communication Flow

```
User Task → PlannerAgent → Task Decomposition
    ↓
Specialized Agents (RedTeam, Code, Terminal, etc.)
    ↓
Execution & Results → ReflectionAgent → Improvements
    ↓
UpgradeAgent → System Enhancement
```

### Model Routing

The system intelligently routes tasks to optimal models based on:
- Task type (code generation, security analysis, reasoning)
- Complexity level
- Token requirements
- Historical performance

### Memory System

- **Vector Database**: ChromaDB for semantic search
- **Context Retrieval**: Automatic relevant information lookup
- **Knowledge Base**: Stores code, documentation, and learned patterns
- **Long-term Memory**: Persistent across sessions

## 🔐 Security Features

### Ethical Guidelines
- Built-in ethical constraints for red team operations
- Responsible disclosure emphasis
- Educational and defensive focus only
- No malicious exploit generation

### Sandboxing
- Docker-based execution isolation
- Network restrictions
- Resource limits (CPU, memory)
- Read-only filesystems where appropriate

### Input Validation
- Command sanitization
- Path traversal prevention
- Dangerous operation blocking
- Security pattern detection

## 📊 Monitoring & Logging

### Real-time Monitoring
- Agent status tracking
- Task execution metrics
- Performance analytics
- Error tracking and recovery

### Comprehensive Logging
- Structured JSON logs
- Security event logging
- Agent decision tracking
- Performance metrics

### Web Dashboard
- Live system status
- Agent performance metrics
- Task history and results
- Real-time log streaming

## 🛠️ Configuration

### Model Configuration
Edit `configs/model_routes.json` to customize:
- Model capabilities and strengths
- Routing rules and preferences
- Performance thresholds
- Fallback strategies

### Agent Configuration
Each agent can be configured for:
- Specialized prompts and behavior
- Tool availability
- Security constraints
- Performance parameters

## 🧪 Development

### Adding New Agents

1. Create agent class inheriting from `BaseAgent`
2. Implement required methods:
   - `_execute_action()`
   - `get_available_tools()`
   - `_get_system_prompt()`
3. Register in main system

### Custom Tools

1. Add tool to appropriate agent's `get_available_tools()`
2. Implement tool logic in agent's `_execute_action()`
3. Update system prompts as needed

### Testing

```bash
# Run agent tests
python -m pytest tests/

# Test specific agent
python -m pytest tests/test_redteam_agent.py

# Integration tests
python -m pytest tests/integration/
```

## 📈 Performance Optimization

### Model Caching
- Automatic model loading optimization
- Context caching for repeated tasks
- Memory-efficient model switching

### Parallel Execution
- Multi-agent task parallelization
- Async/await throughout the system
- Non-blocking I/O operations

### Resource Management
- Docker container lifecycle management
- Memory usage monitoring
- Automatic cleanup of old resources

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Guidelines
- Follow Python PEP 8 style guide
- Add comprehensive docstrings
- Include unit tests for new features
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

OllamaX-AI is designed for educational and defensive security purposes only. Users are responsible for ensuring all activities comply with applicable laws and ethical guidelines. The developers are not responsible for any misuse of this software.

## 🙏 Acknowledgments

- Ollama team for the excellent local LLM platform
- ChromaDB for vector database capabilities
- The open-source AI community for model development
- Security researchers for vulnerability patterns and methodologies

## 📞 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check the documentation in `/docs`
- Review example configurations in `/examples`

---

**Built with ❤️ for the AI and security communities**
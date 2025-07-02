#!/bin/bash

# OllamaX-AI Installation Script
# God-level, offline, self-healing, multi-modal AI red team + software engineering platform

set -e

echo "🚀 Installing OllamaX-AI..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check Python version
print_status "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    print_error "Python 3.11+ is required. Current version: $PYTHON_VERSION"
    exit 1
fi

print_success "Python $PYTHON_VERSION detected"

# Check if Ollama is installed
print_status "Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    print_warning "Ollama not found. Installing Ollama..."
    
    # Install Ollama
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -fsSL https://ollama.ai/install.sh | sh
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_warning "Please install Ollama manually from https://ollama.ai"
        print_warning "Then run this script again"
        exit 1
    else
        print_error "Unsupported operating system"
        exit 1
    fi
else
    print_success "Ollama is already installed"
fi

# Check if Docker is installed
print_status "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    print_warning "Docker not found. Installing Docker..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Install Docker on Linux
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        sudo usermod -aG docker $USER
        rm get-docker.sh
        print_warning "Please log out and log back in for Docker group changes to take effect"
    else
        print_error "Please install Docker manually from https://docker.com"
        exit 1
    fi
else
    print_success "Docker is already installed"
fi

# Start Docker if not running
print_status "Starting Docker..."
if ! docker info &> /dev/null; then
    if command -v systemctl &> /dev/null; then
        sudo systemctl start docker
    else
        sudo dockerd > /tmp/docker.log 2>&1 &
        sleep 5
    fi
fi

if docker info &> /dev/null; then
    print_success "Docker is running"
else
    print_error "Failed to start Docker"
    exit 1
fi

# Install Python dependencies
print_status "Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
else
    python3 -m pip install -r requirements.txt
fi

print_success "Python dependencies installed"

# Check if Node.js is installed (for frontend)
print_status "Checking Node.js installation..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION detected"
    
    # Install frontend dependencies
    print_status "Installing frontend dependencies..."
    cd ui/frontend
    npm install
    cd ../..
    print_success "Frontend dependencies installed"
else
    print_warning "Node.js not found. Frontend will not be available."
    print_warning "Install Node.js 18+ from https://nodejs.org to enable the web interface"
fi

# Start Ollama service
print_status "Starting Ollama service..."
if ! pgrep -x "ollama" > /dev/null; then
    ollama serve > /tmp/ollama.log 2>&1 &
    sleep 3
fi

# Pull required models
print_status "Pulling required AI models (this may take a while)..."

MODELS=("mixtral" "codellama" "deepseek-coder" "openchat" "phi3")

for model in "${MODELS[@]}"; do
    print_status "Pulling $model..."
    if ollama pull $model; then
        print_success "$model pulled successfully"
    else
        print_warning "Failed to pull $model - you can pull it manually later with: ollama pull $model"
    fi
done

# Create necessary directories
print_status "Creating directories..."
mkdir -p logs memory/vector_store

# Set permissions
chmod +x main.py

print_success "Installation completed successfully!"
echo ""
echo "🎉 OllamaX-AI is ready to use!"
echo "=================================="
echo ""
echo "Quick Start:"
echo "  Interactive mode:    python main.py interactive"
echo "  Single task:         python main.py task 'your task here'"
echo "  API server:          python main.py server"
echo ""
echo "Web Interface:"
echo "  1. Start API server: python main.py server"
echo "  2. Start frontend:   cd ui/frontend && npm run dev"
echo "  3. Open browser:     http://localhost:12001"
echo ""
echo "Example tasks:"
echo "  • 'Generate a secure login function in Python'"
echo "  • 'Perform vulnerability scan on localhost'"
echo "  • 'Debug this code: [paste your code]'"
echo "  • 'Create a red team payload for testing SSRF'"
echo ""
echo "Documentation: README.md"
echo "Support: https://github.com/ollamax-ai/ollamax-ai"
echo ""
print_success "Happy hacking! 🔥"
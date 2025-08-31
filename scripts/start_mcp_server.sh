#!/bin/bash
# MCP Crypto Trading Server - Production Startup Script
# Kaayaan Infrastructure Integration
# Last Updated: 2025-08-31

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="crypto-trading"
MCP_VERSION="2.0.0"
CONTAINER_NAME="kaayaan-${PROJECT_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
check_user() {
    if [[ $EUID -eq 0 ]]; then
        warning "Running as root. Consider using a non-root user for security."
    fi
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check Python version
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log "Python version: ${PYTHON_VERSION}"
        
        # Check if version is 3.11+
        if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
            error "Python 3.11+ required. Current version: ${PYTHON_VERSION}"
            exit 1
        fi
    else
        error "Python 3 not found. Please install Python 3.11+"
        exit 1
    fi
    
    # Check Docker (for container deployment)
    if command -v docker >/dev/null 2>&1; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
        log "Docker version: ${DOCKER_VERSION}"
    else
        warning "Docker not found. Container deployment will not be available."
    fi
    
    success "System requirements check passed"
}

# Validate environment configuration
validate_environment() {
    log "Validating environment configuration..."
    
    # Check for environment file
    if [[ -f "${SCRIPT_DIR}/.env.production" ]]; then
        log "Found production environment file"
        source "${SCRIPT_DIR}/.env.production"
    elif [[ -f "${SCRIPT_DIR}/.env.production.example" ]]; then
        warning "Using example environment file. Copy .env.production.example to .env.production and configure."
        source "${SCRIPT_DIR}/.env.production.example"
    else
        error "No environment configuration found. Create .env.production file."
        exit 1
    fi
    
    # Validate critical environment variables
    local required_vars=(
        "MONGODB_URI"
        "REDIS_URL" 
        "DATABASE_URL"
        "WHATSAPP_BASE_URL"
        "WHATSAPP_SESSION"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Required environment variable ${var} is not set"
            exit 1
        fi
    done
    
    success "Environment validation passed"
}

# Test infrastructure connectivity
test_infrastructure() {
    log "Testing Kaayaan infrastructure connectivity..."
    
    cd "${SCRIPT_DIR}"
    
    # Test with Python script
    if python3 -c "
import asyncio
import sys
sys.path.append('${SCRIPT_DIR}')
from infrastructure.kaayaan_factory import quick_health_check

async def test():
    try:
        health = await quick_health_check()
        if health.errors:
            print('Infrastructure issues:', health.errors)
            return False
        return True
    except Exception as e:
        print(f'Infrastructure test failed: {e}')
        return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
"; then
        success "Infrastructure connectivity test passed"
    else
        error "Infrastructure connectivity test failed. Check Kaayaan services."
        exit 1
    fi
}

# Install dependencies
install_dependencies() {
    log "Installing/updating dependencies..."
    
    cd "${SCRIPT_DIR}"
    
    # Check for virtual environment
    if [[ ! -d "venv" ]]; then
        log "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [[ -f "requirements_mcp.txt" ]]; then
        log "Installing MCP requirements..."
        pip install -r requirements_mcp.txt
    else
        error "requirements_mcp.txt not found"
        exit 1
    fi
    
    success "Dependencies installed successfully"
}

# Start MCP server
start_server() {
    local mode="$1"
    
    cd "${SCRIPT_DIR}"
    
    case $mode in
        "docker")
            start_docker_server
            ;;
        "python")
            start_python_server
            ;;
        "auto")
            if command -v docker >/dev/null 2>&1; then
                start_docker_server
            else
                start_python_server
            fi
            ;;
        *)
            error "Invalid start mode: $mode"
            exit 1
            ;;
    esac
}

# Start via Docker (recommended for production)
start_docker_server() {
    log "Starting MCP server via Docker..."
    
    # Check if container already exists
    if docker ps -a --format "table {{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        log "Stopping existing container..."
        docker stop "${CONTAINER_NAME}" || true
        docker rm "${CONTAINER_NAME}" || true
    fi
    
    # Build and start container
    log "Building Docker image..."
    docker build -f Dockerfile.production -t "kaayaan/mcp-${PROJECT_NAME}:${MCP_VERSION}" .
    
    log "Starting container..."
    docker-compose -f docker-compose.kaayaan.yml up -d
    
    # Wait for container to be ready
    log "Waiting for container to be ready..."
    sleep 5
    
    # Check container health
    if docker ps --filter "name=${CONTAINER_NAME}" --filter "status=running" | grep -q "${CONTAINER_NAME}"; then
        success "MCP server container started successfully"
        log "Container name: ${CONTAINER_NAME}"
        log "Check logs with: docker logs ${CONTAINER_NAME}"
        log "Stop with: docker stop ${CONTAINER_NAME}"
    else
        error "Failed to start MCP server container"
        docker logs "${CONTAINER_NAME}"
        exit 1
    fi
}

# Start via Python (development/testing)
start_python_server() {
    log "Starting MCP server via Python..."
    
    # Activate virtual environment if it exists
    if [[ -f "venv/bin/activate" ]]; then
        source venv/bin/activate
    fi
    
    # Set environment variables
    export PYTHONPATH="${SCRIPT_DIR}"
    export ENVIRONMENT="production"
    export TZ="Asia/Kuwait"
    
    # Start server
    log "Executing: python3 mcp_server_standalone.py"
    python3 mcp_server_standalone.py
}

# Show usage information
show_usage() {
    echo "MCP Crypto Trading Server - Startup Script"
    echo ""
    echo "Usage: $0 [OPTIONS] [MODE]"
    echo ""
    echo "Modes:"
    echo "  docker    - Start via Docker container (recommended for production)"
    echo "  python    - Start via Python directly (development/testing)"
    echo "  auto      - Auto-detect best mode (default)"
    echo ""
    echo "Options:"
    echo "  --no-deps       Skip dependency installation"
    echo "  --no-test       Skip infrastructure connectivity test"
    echo "  --no-validate   Skip environment validation"
    echo "  --help, -h      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Auto-detect mode with full validation"
    echo "  $0 docker           # Force Docker mode"
    echo "  $0 python --no-deps # Python mode without dependency check"
    echo ""
}

# Main execution
main() {
    local mode="auto"
    local skip_deps=false
    local skip_test=false
    local skip_validate=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-deps)
                skip_deps=true
                shift
                ;;
            --no-test)
                skip_test=true
                shift
                ;;
            --no-validate)
                skip_validate=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            docker|python|auto)
                mode="$1"
                shift
                ;;
            *)
                error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Banner
    echo -e "${GREEN}"
    echo "======================================================================="
    echo "  MCP Crypto Trading Server v${MCP_VERSION}"
    echo "  Production-Ready Kaayaan Infrastructure Integration"
    echo "======================================================================="
    echo -e "${NC}"
    
    # Execution steps
    check_user
    check_requirements
    
    if [[ "$skip_validate" != true ]]; then
        validate_environment
    fi
    
    if [[ "$skip_deps" != true && "$mode" != "docker" ]]; then
        install_dependencies
    fi
    
    if [[ "$skip_test" != true ]]; then
        test_infrastructure
    fi
    
    # Start the server
    log "Starting MCP server in ${mode} mode..."
    start_server "$mode"
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}Script interrupted by user${NC}"; exit 130' INT

# Run main function
main "$@"
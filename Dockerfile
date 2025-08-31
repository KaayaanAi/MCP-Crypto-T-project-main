# Multi-stage build for optimized production image - 2025+ Standards
FROM python:3.12-slim-bookworm AS builder

# Set build arguments for metadata
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Enhanced metadata labels following OCI specification
LABEL maintainer="Kaayaan Infrastructure <dev@kaayaan.ai>" \
      org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.source="https://github.com/kaayaan/mcp-crypto-trading" \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.vendor="Kaayaan Infrastructure" \
      org.opencontainers.image.title="MCP Crypto Trading Server" \
      org.opencontainers.image.description="Production-ready MCP cryptocurrency trading analysis with institutional-grade indicators" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.documentation="https://docs.kaayaan.ai/mcp-crypto"

# Set environment variables for build optimization (2025+ standards)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHON_VERSION=3.12 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_REQUIRE_HASHES=0 \
    UV_SYSTEM_PYTHON=1 \
    DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Install system dependencies with enhanced security (2025+ updates)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build essentials
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libc6-dev \
    make \
    pkg-config \
    # Network and security tools
    curl \
    wget \
    gnupg2 \
    ca-certificates \
    apt-transport-https \
    # Mathematical libraries for numpy/scipy
    gfortran \
    libblas-dev \
    liblapack-dev \
    # Additional crypto libraries
    libsodium-dev \
    && apt-get upgrade -y \
    && apt-get autoremove -y \
    && apt-get autoclean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install uv package manager for 10-100x faster dependency resolution
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Create optimized virtual environment using uv
RUN uv venv /opt/venv --python 3.12
ENV PATH="/opt/venv/bin:$PATH" \
    VIRTUAL_ENV="/opt/venv"

# Copy requirements first for optimal Docker layer caching
COPY requirements_mcp.txt /tmp/requirements_mcp.txt

# Install Python dependencies with uv for maximum speed
RUN uv pip install --no-cache --compile -r /tmp/requirements_mcp.txt && \
    # Clean up compiled cache to reduce image size
    find /opt/venv -name "*.pyc" -delete && \
    find /opt/venv -name "__pycache__" -type d -exec rm -rf {} + && \
    find /opt/venv -name "*.pyo" -delete && \
    # Remove temporary files
    rm -rf /tmp/* /var/tmp/* /root/.cache

# Production stage - minimal and secure runtime (2025+ standards)
FROM python:3.12-slim-bookworm AS production

# Enhanced security and runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONPATH="/app" \
    PATH="/opt/venv/bin:$PATH" \
    VIRTUAL_ENV="/opt/venv" \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=UTC \
    # Security hardening
    HOME="/home/mcp" \
    USER=mcp \
    UID=1001 \
    GID=1001 \
    # Performance tuning
    MALLOC_ARENA_MAX=2 \
    # Application specific
    MCP_SERVER_NAME="mcp-crypto-trading" \
    MCP_SERVER_VERSION="2.0.0" \
    ENVIRONMENT="production"

# Install only essential runtime dependencies (security-focused 2025+ selection)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Essential runtime utilities
    curl \
    ca-certificates \
    # Process management and signal handling
    dumb-init \
    tini \
    # Network tools for health checks
    netcat-openbsd \
    # Time zone data
    tzdata \
    # Security updates
    && apt-get upgrade -y \
    # Clean up package manager
    && apt-get autoremove -y \
    && apt-get autoclean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && apt-get clean

# Create non-root user with specific UID/GID for enhanced security
RUN groupadd --gid $GID --system $USER && \
    useradd --uid $UID --gid $GID --system --home-dir $HOME --create-home \
           --shell /sbin/nologin $USER

# Copy optimized virtual environment from builder stage
COPY --from=builder --chown=root:root /opt/venv /opt/venv

# Set working directory
WORKDIR /app

# Copy startup scripts with proper ownership and permissions
COPY --chown=root:root --chmod=755 docker-entrypoint.sh /usr/local/bin/
COPY --chown=root:root --chmod=755 start_server.sh /usr/local/bin/

# Copy application code with proper ownership
COPY --chown=$USER:$USER . .

# Create necessary directories with optimal security permissions
RUN install -d -o $USER -g $USER -m 0750 /app/logs /app/data /app/tmp /app/cache && \
    # Set proper permissions on application files
    find /app -type d -exec chmod 755 {} + && \
    find /app -type f -exec chmod 644 {} + && \
    # Make Python files executable
    find /app -name "*.py" -exec chmod 755 {} + && \
    # Remove development and build artifacts
    find /app -name "*.pyc" -delete && \
    find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find /app -name "*.pyo" -delete && \
    find /app -name ".DS_Store" -delete && \
    # Remove unnecessary files to minimize attack surface
    rm -rf /app/.git* /app/tests /app/docs /app/validate_*.py 2>/dev/null || true

# Switch to non-root user for security
USER $USER

# Configure proper signal handling
STOPSIGNAL SIGTERM

# Enhanced health check with multiple validation methods
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import socket; s=socket.socket(); s.settimeout(3); result=s.connect_ex(('127.0.0.1', 8080)); s.close(); exit(0 if result == 0 else 1)" \
        || curl -f --max-time 5 http://127.0.0.1:8080/health 2>/dev/null \
        || exit 1

# Expose MCP server port (using non-privileged port)
EXPOSE 8080

# Security scanning metadata
LABEL security.scan="trivy,snyk" \
      security.cve-check="enabled" \
      security.updates="2025-08-31"

# Use tini for proper init system with PID 1 responsibility
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/docker-entrypoint.sh"]

# Default command to start the MCP server
CMD ["/usr/local/bin/start_server.sh"]
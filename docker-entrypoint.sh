#!/bin/bash
set -euo pipefail
set -o errtrace

# ======================================================================
# MCP Crypto Trading Server - Docker Entrypoint (2025+ Enhanced)
# Production-ready container initialization with advanced security & monitoring
# Version: 2.0 | Last Updated: $(date -u '+%Y-%m-%d')
# ======================================================================

# Bash version check for modern features
if [[ ${BASH_VERSION%%.*} -lt 4 ]]; then
    echo "ERROR: Bash 4.0+ required for modern shell features" >&2
    exit 1
fi

# Enhanced color codes with 256-color support
readonly RED='\033[38;5;196m'
readonly GREEN='\033[38;5;46m'
readonly YELLOW='\033[38;5;226m'
readonly BLUE='\033[38;5;33m'
readonly PURPLE='\033[38;5;129m'
readonly CYAN='\033[38;5;51m'
readonly ORANGE='\033[38;5;214m'
readonly NC='\033[0m' # No Color

# Security and performance constants
readonly SCRIPT_NAME="${0##*/}"
readonly SCRIPT_PID=$$
readonly SCRIPT_START_TIME=$(date -u '+%s')
readonly MAX_RETRY_ATTEMPTS=5
readonly CONNECTION_TIMEOUT=10
readonly HEALTH_CHECK_INTERVAL=30

# Enhanced logging with structured JSON support and performance metrics
log_structured() {
    local level="$1"
    local message="$2"
    local extra="${3:-}"
    local timestamp=$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')
    local runtime=$(($(date -u '+%s') - SCRIPT_START_TIME))
    
    if [[ "${ENABLE_JSON_LOGGING:-false}" == "true" ]]; then
        printf '{"timestamp":"%s","level":"%s","message":"%s","script":"%s","pid":%d,"runtime":%d%s}\n' \
            "$timestamp" "$level" "$message" "$SCRIPT_NAME" "$SCRIPT_PID" "$runtime" "${extra:+,$extra}"
    else
        local color_map=(["INFO"]="$BLUE" ["WARN"]="$YELLOW" ["ERROR"]="$RED" ["SUCCESS"]="$GREEN" ["DEBUG"]="$CYAN" ["SECURITY"]="$PURPLE")
        echo -e "${color_map[$level]:-$NC}[$level]${NC} $timestamp - $message ${extra:+($extra)}"
    fi
}

log_info() { log_structured "INFO" "$1" "${2:-}"; }
log_warn() { log_structured "WARN" "$1" "${2:-}" >&2; }
log_error() { log_structured "ERROR" "$1" "${2:-}" >&2; }
log_success() { log_structured "SUCCESS" "$1" "${2:-}"; }
log_debug() { [[ "${DEBUG:-false}" == "true" ]] && log_structured "DEBUG" "$1" "${2:-}"; }
log_security() { log_structured "SECURITY" "$1" "${2:-}" >&2; }

# Performance timing utilities
start_timer() {
    local timer_name="$1"
    declare -g "timer_${timer_name}=$(date -u '+%s%3N')"
}

end_timer() {
    local timer_name="$1"
    local start_var="timer_${timer_name}"
    local start_time="${!start_var:-}"
    if [[ -n "$start_time" ]]; then
        local end_time=$(date -u '+%s%3N')
        local duration=$((end_time - start_time))
        log_info "$timer_name completed" "duration=${duration}ms"
        unset "timer_${timer_name}"
    fi
}

# Enhanced error handling with stack trace and recovery
handle_error() {
    local exit_code=$?
    local line_number=$1
    local bash_command="$2"
    
    log_error "Fatal error at line $line_number" "exit_code=$exit_code,command='$bash_command'"
    
    # Generate stack trace
    log_error "Call stack:"
    local frame=1
    while caller $frame 2>/dev/null; do
        ((frame++))
    done | while IFS=' ' read -r line func file; do
        log_error "  at $func() [$file:$line]"
    done
    
    # Attempt cleanup and graceful shutdown
    cleanup_on_error
    exit $exit_code
}

# Enhanced error trapping with function names
trap 'handle_error $LINENO "$BASH_COMMAND"' ERR
trap 'log_debug "Exiting with code $?"' EXIT

# Enhanced signal handling with graceful shutdown and resource cleanup
cleanup() {
    local signal="${1:-UNKNOWN}"
    log_info "Received $signal signal, initiating graceful shutdown..."
    
    # Set cleanup flag to prevent recursive calls
    if [[ "${CLEANUP_IN_PROGRESS:-false}" == "true" ]]; then
        log_warn "Cleanup already in progress, forcing exit"
        exit 1
    fi
    export CLEANUP_IN_PROGRESS=true
    
    # Stop background processes gracefully
    local pids=($(jobs -p 2>/dev/null || true))
    if [[ ${#pids[@]} -gt 0 ]]; then
        log_info "Terminating ${#pids[@]} background processes..."
        printf '%s\n' "${pids[@]}" | xargs -I {} -P 0 sh -c 'kill -TERM "$1" 2>/dev/null || true; sleep 2; kill -KILL "$1" 2>/dev/null || true' _ {}
    fi
    
    # Clean up temporary files and resources
    cleanup_resources
    
    log_success "Graceful shutdown completed"
    exit 0
}

cleanup_on_error() {
    log_security "Emergency cleanup due to error"
    cleanup_resources
}

cleanup_resources() {
    # Remove sensitive temporary files
    find /tmp -name "${SCRIPT_NAME}_*" -user "$(whoami)" -delete 2>/dev/null || true
    
    # Clear prometheus metrics directory
    if [[ -d "/tmp/prometheus_multiproc_dir" ]]; then
        rm -rf "/tmp/prometheus_multiproc_dir/"* 2>/dev/null || true
    fi
    
    # Flush any pending logs
    sync 2>/dev/null || true
}

# Register signal handlers
trap 'cleanup SIGTERM' SIGTERM
trap 'cleanup SIGINT' SIGINT
trap 'cleanup SIGQUIT' SIGQUIT
trap 'cleanup SIGHUP' SIGHUP

# ======================================================================
# ENHANCED ENVIRONMENT VALIDATION WITH SECURITY CHECKS
# ======================================================================

# Input sanitization function
sanitize_input() {
    local input="$1"
    local max_length="${2:-256}"
    
    # Remove control characters and limit length
    input=$(printf '%s' "$input" | tr -d '\000-\037\177' | cut -c1-"$max_length")
    printf '%s' "$input"
}

# Enhanced environment validation with security checks
validate_environment() {
    start_timer "env_validation"
    log_info "Performing enhanced environment validation with security checks..."
    
    # Define required environment variables with validation patterns
    declare -A required_vars=(
        ["ENVIRONMENT"]="^(production|staging|development)$"
        ["MONGODB_URI"]="^mongodb(\+srv)?://.*"
        ["REDIS_URL"]="^redis(s)?://.*"
        ["MCP_SERVER_PORT"]="^[1-9][0-9]{3,4}$"
    )
    
    # Optional but recommended variables
    declare -A optional_vars=(
        ["SENTRY_DSN"]="^https://.*@.*\.ingest\.sentry\.io/.*"
        ["POSTGRES_DSN"]="^postgresql://.*"
        ["JWT_SECRET"]="^.{32,}$"
        ["API_RATE_LIMIT"]="^[1-9][0-9]*$"
    )
    
    local validation_errors=()
    local security_warnings=()
    
    # Validate required variables
    for var in "${!required_vars[@]}"; do
        local value="${!var:-}"
        local pattern="${required_vars[$var]}"
        
        if [[ -z "$value" ]]; then
            validation_errors+=("Missing required environment variable: $var")
            continue
        fi
        
        # Sanitize and validate format
        local sanitized_value
        sanitized_value=$(sanitize_input "$value" 512)
        
        if [[ ! "$sanitized_value" =~ $pattern ]]; then
            validation_errors+=("Invalid format for $var (does not match pattern: $pattern)")
        else
            log_debug "Environment variable validated: $var" "length=${#sanitized_value}"
        fi
        
        # Security checks for sensitive variables
        case "$var" in
            *URI|*URL|*DSN)
                if [[ "$value" =~ (password|token|key|secret)=([^&@/]+) ]]; then
                    local cred_length=${#BASH_REMATCH[2]}
                    if [[ $cred_length -lt 16 ]]; then
                        security_warnings+=("Weak credential detected in $var (length: $cred_length)")
                    fi
                fi
                ;;
        esac
    done
    
    # Validate optional variables if present
    for var in "${!optional_vars[@]}"; do
        local value="${!var:-}"
        if [[ -n "$value" ]]; then
            local pattern="${optional_vars[$var]}"
            local sanitized_value
            sanitized_value=$(sanitize_input "$value" 1024)
            
            if [[ ! "$sanitized_value" =~ $pattern ]]; then
                security_warnings+=("Optional variable $var has invalid format")
            else
                log_debug "Optional variable validated: $var"
            fi
        fi
    done
    
    # Report validation results
    if [[ ${#validation_errors[@]} -gt 0 ]]; then
        log_error "Environment validation failed:"
        printf '  - %s\n' "${validation_errors[@]}"
        exit 1
    fi
    
    if [[ ${#security_warnings[@]} -gt 0 ]]; then
        log_security "Security warnings detected:"
        printf '  - %s\n' "${security_warnings[@]}"
    fi
    
    # Environment-specific security validation
    case "${ENVIRONMENT}" in
        "production")
            validate_production_security
            ;;
        "staging")
            log_info "Running in staging mode with enhanced logging"
            export DEBUG=false
            ;;
        "development")
            log_warn "Development mode - security checks relaxed"
            ;;
    esac
    
    end_timer "env_validation"
    log_success "Environment validation completed with enhanced security checks"
}

# Production-specific security validation
validate_production_security() {
    log_security "Performing production security validation..."
    
    # Check for debug flags in production
    if [[ "${DEBUG:-false}" == "true" ]]; then
        log_error "DEBUG mode is enabled in production environment"
        exit 1
    fi
    
    # Validate SSL/TLS requirements
    if [[ ! "${MONGODB_URI}" =~ \+srv ]]; then
        log_security "MongoDB URI does not use SRV record (recommended for production)"
    fi
    
    if [[ ! "${REDIS_URL}" =~ ^rediss:// ]]; then
        log_security "Redis connection is not using SSL (rediss://)"
    fi
    
    # Check for proper secret management
    if [[ -z "${JWT_SECRET:-}" ]]; then
        log_error "JWT_SECRET is required in production environment"
        exit 1
    fi
    
    # Validate monitoring requirements
    if [[ -z "${SENTRY_DSN:-}" ]]; then
        log_warn "SENTRY_DSN not configured - error tracking disabled"
    fi
    
    log_success "Production security validation passed"
}

# ======================================================================
# SYSTEM CHECKS
# ======================================================================

# Enhanced system resource monitoring with predictive alerts
check_system_resources() {
    start_timer "resource_check"
    log_info "Performing comprehensive system resource analysis..."
    
    # Memory analysis with detailed breakdown
    if [[ -r "/proc/meminfo" ]]; then
        local -A memory_info
        while IFS=':' read -r key value; do
            [[ "$key" =~ ^(MemTotal|MemAvailable|MemFree|Buffers|Cached|SwapTotal|SwapFree)$ ]] && \
                memory_info["$key"]=$(echo "$value" | awk '{print $1}')
        done < /proc/meminfo
        
        local mem_total_mb=$((memory_info["MemTotal"] / 1024))
        local mem_available_mb=$((memory_info["MemAvailable"] / 1024))
        local mem_usage_percent=$(( (mem_total_mb - mem_available_mb) * 100 / mem_total_mb ))
        
        log_info "Memory analysis" "total=${mem_total_mb}MB,available=${mem_available_mb}MB,usage=${mem_usage_percent}%"
        
        # Memory thresholds with predictive alerting
        if [[ $mem_available_mb -lt 128 ]]; then
            log_error "Critical memory shortage: ${mem_available_mb}MB available"
            exit 1
        elif [[ $mem_usage_percent -gt 85 ]]; then
            log_warn "High memory usage: ${mem_usage_percent}% (${mem_available_mb}MB available)"
        elif [[ $mem_usage_percent -gt 70 ]]; then
            log_info "Elevated memory usage: ${mem_usage_percent}% - monitoring closely"
        fi
        
        # Swap analysis
        if [[ ${memory_info["SwapTotal"]-0} -gt 0 ]]; then
            local swap_usage_percent=$(( (memory_info["SwapTotal"] - memory_info["SwapFree"]) * 100 / memory_info["SwapTotal"] ))
            if [[ $swap_usage_percent -gt 50 ]]; then
                log_warn "High swap usage detected: ${swap_usage_percent}%"
            fi
        fi
    else
        log_warn "Cannot read /proc/meminfo - memory analysis skipped"
    fi
    
    # Enhanced disk space monitoring with multiple mount points
    local critical_paths=("/app" "/tmp" "/var/log" "/" "/var/lib/docker")
    
    for path in "${critical_paths[@]}"; do
        if [[ -d "$path" ]]; then
            local disk_info
            disk_info=$(df "$path" 2>/dev/null | awk 'NR==2 {print $2,$3,$4,$5}' | tr -d '%')
            
            if [[ -n "$disk_info" ]]; then
                read -r total used available usage_percent <<< "$disk_info"
                local total_gb=$((total / 1024 / 1024))
                local available_gb=$((available / 1024 / 1024))
                
                log_info "Disk space: $path" "total=${total_gb}GB,available=${available_gb}GB,usage=${usage_percent}%"
                
                if [[ $usage_percent -gt 95 ]]; then
                    log_error "Critical disk space on $path: ${usage_percent}% used (${available_gb}GB free)"
                    exit 1
                elif [[ $usage_percent -gt 85 ]]; then
                    log_warn "High disk usage on $path: ${usage_percent}% used (${available_gb}GB free)"
                elif [[ $available_gb -lt 1 ]]; then
                    log_warn "Low disk space on $path: ${available_gb}GB available"
                fi
            fi
        fi
    done
    
    # CPU and load average monitoring
    if [[ -r "/proc/loadavg" ]]; then
        local load_avg
        load_avg=$(cut -d' ' -f1-3 < /proc/loadavg)
        local cpu_count
        cpu_count=$(nproc 2>/dev/null || echo "1")
        log_info "System load" "avg='$load_avg',cpus=$cpu_count"
        
        local load_1min
        load_1min=$(echo "$load_avg" | cut -d' ' -f1)
        if (( $(echo "$load_1min > $cpu_count * 2" | bc -l 2>/dev/null || echo 0) )); then
            log_warn "High system load: $load_1min (CPUs: $cpu_count)"
        fi
    fi
    
    # File descriptor limits
    local fd_limit
    fd_limit=$(ulimit -n)
    local fd_soft_limit
    fd_soft_limit=$(ulimit -Sn)
    local fd_hard_limit
    fd_hard_limit=$(ulimit -Hn)
    
    log_info "File descriptor limits" "current=$fd_limit,soft=$fd_soft_limit,hard=$fd_hard_limit"
    
    if [[ $fd_limit -lt 4096 ]]; then
        log_warn "Low file descriptor limit: $fd_limit (recommended: 8192+)"
    fi
    
    end_timer "resource_check"
    log_success "System resource analysis completed"
}

# ======================================================================
# DIRECTORY SETUP
# ======================================================================

setup_directories() {
    log_info "Setting up application directories..."
    
    # Create required directories with proper permissions
    local directories=(
        "/app/logs"
        "/app/data"
        "/app/tmp"
        "/app/backups"
        "/tmp/prometheus_multiproc_dir"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
        chmod 750 "$dir" 2>/dev/null || true
    done
    
    # Set up log rotation if logrotate is available
    if command -v logrotate >/dev/null 2>&1; then
        log_info "Configuring log rotation..."
        # Note: In production, this would be handled by the system's logrotate
    fi
    
    log_success "Directory setup completed"
}

# ======================================================================
# ENHANCED CONNECTIVITY CHECKS WITH MODERN NETWORK TOOLS
# ======================================================================

# Advanced URI parsing function
parse_uri() {
    local uri="$1"
    local -n result="$2"
    
    # Enhanced regex for modern URI formats including SRV records
    if [[ "$uri" =~ ^([^:]+)://(([^:/@]+)(:([^@]+))?@)?([^:/?]+)(:([0-9]+))?(/.*)?$ ]]; then
        result["scheme"]="${BASH_REMATCH[1]}"
        result["username"]="${BASH_REMATCH[3]}"
        result["password"]="${BASH_REMATCH[5]}"
        result["host"]="${BASH_REMATCH[6]}"
        result["port"]="${BASH_REMATCH[8]}"
        result["path"]="${BASH_REMATCH[9]}"
        return 0
    else
        log_error "Failed to parse URI: $uri"
        return 1
    fi
}

# Enhanced network connectivity test with multiple methods
test_network_connectivity() {
    local host="$1"
    local port="$2"
    local timeout="${3:-$CONNECTION_TIMEOUT}"
    local service_name="${4:-service}"
    
    log_debug "Testing connectivity to $service_name" "host=$host,port=$port,timeout=${timeout}s"
    
    # Method 1: Modern netcat (preferred)
    if command -v nc >/dev/null 2>&1; then
        if timeout "$timeout" nc -z "$host" "$port" 2>/dev/null; then
            return 0
        fi
    fi
    
    # Method 2: Modern bash TCP test
    if timeout "$timeout" bash -c "exec 3<>/dev/tcp/$host/$port" 2>/dev/null; then
        exec 3<&-
        return 0
    fi
    
    # Method 3: curl (for HTTP services)
    if [[ "$port" =~ ^(80|443|8080|8443)$ ]] && command -v curl >/dev/null 2>&1; then
        local protocol="http"
        [[ "$port" =~ ^(443|8443)$ ]] && protocol="https"
        if timeout "$timeout" curl -f -s "$protocol://$host:$port/health" >/dev/null 2>&1; then
            return 0
        fi
    fi
    
    return 1
}

# Enhanced MongoDB connectivity with SRV record support
check_mongodb_connectivity() {
    start_timer "mongodb_check"
    log_info "Performing enhanced MongoDB connectivity analysis..."
    
    declare -A mongo_uri
    if ! parse_uri "$MONGODB_URI" mongo_uri; then
        log_error "Invalid MongoDB URI format"
        exit 1
    fi
    
    local host="${mongo_uri[host]}"
    local port="${mongo_uri[port]:-27017}"
    local is_srv="false"
    
    # Handle MongoDB SRV records
    if [[ "${mongo_uri[scheme]}" == "mongodb+srv" ]]; then
        is_srv="true"
        log_info "MongoDB SRV connection detected" "host=$host"
        
        # Resolve SRV records if dig is available
        if command -v dig >/dev/null 2>&1; then
            local srv_records
            srv_records=$(dig +short SRV "_mongodb._tcp.$host" 2>/dev/null)
            if [[ -n "$srv_records" ]]; then
                log_info "SRV records found" "count=$(echo "$srv_records" | wc -l)"
            else
                log_warn "No SRV records found for $host"
            fi
        fi
    fi
    
    # Connection retry logic with exponential backoff
    local attempt=1
    local max_attempts="${MAX_RETRY_ATTEMPTS}"
    local backoff_base=2
    
    while [[ $attempt -le $max_attempts ]]; do
        local wait_time=$((backoff_base ** (attempt - 1)))
        
        log_debug "MongoDB connection attempt $attempt/$max_attempts" "wait_time=${wait_time}s"
        
        if [[ "$is_srv" == "true" ]] || test_network_connectivity "$host" "$port" "$CONNECTION_TIMEOUT" "MongoDB"; then
            # Additional MongoDB-specific validation using Python
            if validate_mongodb_auth; then
                end_timer "mongodb_check"
                log_success "MongoDB connectivity validated" "host=$host,port=$port,srv=$is_srv"
                return 0
            fi
        fi
        
        if [[ $attempt -lt $max_attempts ]]; then
            log_warn "MongoDB connection attempt $attempt failed, retrying in ${wait_time}s..."
            sleep "$wait_time"
        fi
        ((attempt++))
    done
    
    log_error "Failed to establish MongoDB connection after $max_attempts attempts"
    exit 1
}

# MongoDB authentication validation
validate_mongodb_auth() {
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "
import os, sys
try:
    import motor.motor_asyncio as motor
    import asyncio
    async def test():
        client = motor.AsyncIOMotorClient(os.getenv('MONGODB_URI'), serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        await client.close()
        return True
    result = asyncio.run(test())
    sys.exit(0)
except Exception as e:
    print(f'MongoDB auth failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null
        return $?
    fi
    return 0
}

# Enhanced Redis connectivity with SSL/TLS support
check_redis_connectivity() {
    start_timer "redis_check"
    log_info "Performing enhanced Redis connectivity analysis..."
    
    declare -A redis_uri
    if ! parse_uri "$REDIS_URL" redis_uri; then
        log_error "Invalid Redis URL format"
        exit 1
    fi
    
    local host="${redis_uri[host]}"
    local port="${redis_uri[port]:-6379}"
    local is_ssl="false"
    
    [[ "${redis_uri[scheme]}" == "rediss" ]] && is_ssl="true"
    
    log_info "Redis connection details" "host=$host,port=$port,ssl=$is_ssl"
    
    # Connection retry with exponential backoff
    local attempt=1
    local max_attempts="${MAX_RETRY_ATTEMPTS}"
    
    while [[ $attempt -le $max_attempts ]]; do
        local wait_time=$((2 ** (attempt - 1)))
        
        log_debug "Redis connection attempt $attempt/$max_attempts" "wait_time=${wait_time}s"
        
        # Test basic connectivity
        if test_network_connectivity "$host" "$port" "$CONNECTION_TIMEOUT" "Redis"; then
            # Additional Redis-specific validation
            if validate_redis_auth; then
                end_timer "redis_check"
                log_success "Redis connectivity validated" "host=$host,port=$port,ssl=$is_ssl"
                return 0
            fi
        fi
        
        if [[ $attempt -lt $max_attempts ]]; then
            log_warn "Redis connection attempt $attempt failed, retrying in ${wait_time}s..."
            sleep "$wait_time"
        fi
        ((attempt++))
    done
    
    log_error "Failed to establish Redis connection after $max_attempts attempts"
    exit 1
}

# Redis authentication validation
validate_redis_auth() {
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "
import os, sys
try:
    import aioredis
    import asyncio
    async def test():
        redis = aioredis.from_url(os.getenv('REDIS_URL'), socket_timeout=5)
        await redis.ping()
        await redis.close()
        return True
    result = asyncio.run(test())
    sys.exit(0)
except Exception as e:
    print(f'Redis auth failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null
        return $?
    fi
    return 0
}

# Enhanced PostgreSQL connectivity with SSL validation
check_postgresql_connectivity() {
    if [[ -n "${POSTGRES_DSN:-}" ]]; then
        start_timer "postgres_check"
        log_info "Performing enhanced PostgreSQL connectivity analysis..."
        
        declare -A pg_uri
        if ! parse_uri "$POSTGRES_DSN" pg_uri; then
            log_error "Invalid PostgreSQL DSN format"
            exit 1
        fi
        
        local host="${pg_uri[host]}"
        local port="${pg_uri[port]:-5432}"
        local database="${pg_uri[path]#/}"
        
        log_info "PostgreSQL connection details" "host=$host,port=$port,database=$database"
        
        # Connection retry with exponential backoff
        local attempt=1
        local max_attempts="${MAX_RETRY_ATTEMPTS}"
        
        while [[ $attempt -le $max_attempts ]]; do
            local wait_time=$((2 ** (attempt - 1)))
            
            log_debug "PostgreSQL connection attempt $attempt/$max_attempts" "wait_time=${wait_time}s"
            
            if test_network_connectivity "$host" "$port" "$CONNECTION_TIMEOUT" "PostgreSQL"; then
                # Additional PostgreSQL-specific validation
                if validate_postgresql_auth; then
                    end_timer "postgres_check"
                    log_success "PostgreSQL connectivity validated" "host=$host,port=$port,database=$database"
                    return 0
                fi
            fi
            
            if [[ $attempt -lt $max_attempts ]]; then
                log_warn "PostgreSQL connection attempt $attempt failed, retrying in ${wait_time}s..."
                sleep "$wait_time"
            fi
            ((attempt++))
        done
        
        log_error "Failed to establish PostgreSQL connection after $max_attempts attempts"
        exit 1
    else
        log_info "PostgreSQL connection not configured, skipping check"
    fi
}

# PostgreSQL authentication validation
validate_postgresql_auth() {
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "
import os, sys
try:
    import asyncpg
    import asyncio
    async def test():
        conn = await asyncpg.connect(os.getenv('POSTGRES_DSN'), timeout=5)
        await conn.execute('SELECT 1')
        await conn.close()
        return True
    result = asyncio.run(test())
    sys.exit(0)
except Exception as e:
    print(f'PostgreSQL auth failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null
        return $?
    fi
    return 0
}

# ======================================================================
# PYTHON ENVIRONMENT SETUP
# ======================================================================

# Enhanced Python environment setup with security and performance checks
setup_python_environment() {
    start_timer "python_setup"
    log_info "Performing comprehensive Python environment analysis..."
    
    # Verify Python installation with version requirements
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python3 is not installed or not in PATH"
        exit 1
    fi
    
    local python_version
    python_version=$(python3 --version | cut -d' ' -f2)
    local python_major
    python_major=$(echo "$python_version" | cut -d. -f1)
    local python_minor
    python_minor=$(echo "$python_version" | cut -d. -f2)
    
    log_info "Python environment" "version=$python_version,executable=$(which python3)"
    
    # Validate Python version (require 3.8+)
    if [[ $python_major -lt 3 ]] || [[ $python_major -eq 3 && $python_minor -lt 8 ]]; then
        log_error "Python 3.8+ required, found: $python_version"
        exit 1
    fi
    
    # Check Python security flags
    local python_flags=()
    [[ "${PYTHONHASHSEED:-}" != "random" ]] && python_flags+=("PYTHONHASHSEED not randomized")
    [[ "${PYTHONDONTWRITEBYTECODE:-}" != "1" ]] && python_flags+=("Bytecode writing enabled")
    [[ "${PYTHONUNBUFFERED:-}" != "1" ]] && python_flags+=("Python output buffering enabled")
    
    if [[ ${#python_flags[@]} -gt 0 ]]; then
        log_security "Python security recommendations:" "flags='$(IFS=','; echo "${python_flags[*]}")'"
    fi
    
    # Enhanced module validation with version checks
    declare -A required_modules=(
        ["asyncio"]="builtin"
        ["aiohttp"]="3.8.0"
        ["motor"]="2.5.0"
        ["aioredis"]="2.0.0"
        ["mcp"]="0.1.0"
        ["pydantic"]="1.10.0"
        ["uvloop"]="optional"
        ["prometheus_client"]="optional"
    )
    
    local missing_modules=()
    local optional_missing=()
    
    for module in "${!required_modules[@]}"; do
        local min_version="${required_modules[$module]}"
        
        if [[ "$min_version" == "builtin" ]]; then
            if ! python3 -c "import $module" >/dev/null 2>&1; then
                missing_modules+=("$module (builtin)")
            fi
        elif [[ "$min_version" == "optional" ]]; then
            if ! python3 -c "import $module" >/dev/null 2>&1; then
                optional_missing+=("$module")
            else
                log_debug "Optional module available: $module"
            fi
        else
            local check_script="
try:
    import $module
    version = getattr($module, '__version__', 'unknown')
    print(f'{module}:{version}')
except ImportError as e:
    print(f'MISSING:{module}')
    exit(1)
except Exception as e:
    print(f'ERROR:{module}:{e}')
    exit(1)"
            
            local result
            result=$(python3 -c "$check_script" 2>/dev/null)
            
            if [[ "$result" =~ ^MISSING: ]]; then
                missing_modules+=("$module (>=$min_version)")
            elif [[ "$result" =~ ^ERROR: ]]; then
                missing_modules+=("$module (error: ${result#ERROR:*:})")
            else
                local installed_version="${result#*:}"
                log_debug "Module validated" "module=$module,version=$installed_version"
            fi
        fi
    done
    
    # Report module validation results
    if [[ ${#missing_modules[@]} -gt 0 ]]; then
        log_error "Missing required Python modules:"
        printf '  - %s\n' "${missing_modules[@]}"
        exit 1
    fi
    
    if [[ ${#optional_missing[@]} -gt 0 ]]; then
        log_info "Optional modules not available" "modules='$(IFS=','; echo "${optional_missing[*]}")'"
    fi
    
    # Check pip and package manager
    if command -v pip3 >/dev/null 2>&1; then
        local pip_version
        pip_version=$(pip3 --version | awk '{print $2}')
        log_debug "Package manager" "pip_version=$pip_version"
    fi
    
    # Validate PYTHONPATH
    if [[ -n "${PYTHONPATH:-}" ]]; then
        log_debug "PYTHONPATH configured" "path='$PYTHONPATH'"
        # Verify PYTHONPATH directories exist
        IFS=':' read -ra path_dirs <<< "$PYTHONPATH"
        for dir in "${path_dirs[@]}"; do
            if [[ ! -d "$dir" ]]; then
                log_warn "PYTHONPATH directory does not exist: $dir"
            fi
        done
    fi
    
    end_timer "python_setup"
    log_success "Python environment analysis completed" "version=$python_version,modules_validated=${#required_modules[@]}"
}

# ======================================================================
# ENHANCED HEALTH CHECK AND MONITORING SETUP
# ======================================================================

# Advanced health check system with multiple validation layers
setup_health_check() {
    start_timer "health_setup"
    log_info "Setting up comprehensive health monitoring system..."
    
    # Create enhanced health check script
    local health_check_file="/app/health_check.py"
    
    cat > "$health_check_file" << 'EOF'
#!/usr/bin/env python3
"""
Enhanced Health Check System for MCP Crypto Trading Server
Provides multi-layer health validation with detailed reporting
"""

import asyncio
import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

class HealthChecker:
    def __init__(self):
        self.port = int(os.getenv('MCP_SERVER_PORT', 8080))
        self.host = os.getenv('MCP_SERVER_HOST', 'localhost')
        self.timeout = int(os.getenv('HEALTH_CHECK_TIMEOUT', 10))
        self.start_time = time.time()
        
    async def check_service_port(self) -> Dict[str, Any]:
        """Check if main service port is responding"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            return {
                'status': 'healthy' if result == 0 else 'unhealthy',
                'port': self.port,
                'response_time_ms': round((time.time() - self.start_time) * 1000, 2)
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'port': self.port
            }
    
    async def check_database_connections(self) -> Dict[str, Any]:
        """Validate database connectivity"""
        results = {}
        
        # MongoDB check
        if mongodb_uri := os.getenv('MONGODB_URI'):
            try:
                import motor.motor_asyncio as motor
                client = motor.AsyncIOMotorClient(mongodb_uri, serverSelectionTimeoutMS=5000)
                await client.admin.command('ping')
                await client.close()
                results['mongodb'] = {'status': 'healthy'}
            except Exception as e:
                results['mongodb'] = {'status': 'unhealthy', 'error': str(e)}
        
        # Redis check
        if redis_url := os.getenv('REDIS_URL'):
            try:
                import aioredis
                redis = aioredis.from_url(redis_url, socket_timeout=5)
                await redis.ping()
                await redis.close()
                results['redis'] = {'status': 'healthy'}
            except Exception as e:
                results['redis'] = {'status': 'unhealthy', 'error': str(e)}
        
        return results
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """Monitor system resource usage"""
        try:
            # Memory check
            with open('/proc/meminfo', 'r') as f:
                mem_info = {}
                for line in f:
                    if line.startswith(('MemTotal:', 'MemAvailable:')):
                        key, value = line.split(':')
                        mem_info[key.strip()] = int(value.strip().split()[0])
            
            mem_usage_percent = ((mem_info['MemTotal'] - mem_info['MemAvailable']) / mem_info['MemTotal']) * 100
            
            # Disk check
            import shutil
            disk_usage = shutil.disk_usage('/app')
            disk_usage_percent = ((disk_usage.total - disk_usage.free) / disk_usage.total) * 100
            
            return {
                'memory': {
                    'usage_percent': round(mem_usage_percent, 2),
                    'available_mb': round(mem_info['MemAvailable'] / 1024, 2),
                    'status': 'healthy' if mem_usage_percent < 85 else 'warning' if mem_usage_percent < 95 else 'critical'
                },
                'disk': {
                    'usage_percent': round(disk_usage_percent, 2),
                    'free_gb': round(disk_usage.free / (1024**3), 2),
                    'status': 'healthy' if disk_usage_percent < 80 else 'warning' if disk_usage_percent < 90 else 'critical'
                }
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def run_health_check(self) -> Dict[str, Any]:
        """Execute comprehensive health check"""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Run all checks concurrently
        service_check, db_checks, resource_checks = await asyncio.gather(
            self.check_service_port(),
            self.check_database_connections(),
            self.check_system_resources(),
            return_exceptions=True
        )
        
        # Determine overall health status
        overall_status = 'healthy'
        
        if service_check.get('status') != 'healthy':
            overall_status = 'unhealthy'
        elif any(db.get('status') == 'unhealthy' for db in db_checks.values()):
            overall_status = 'degraded'
        elif any(res.get('status') == 'critical' for res in resource_checks.values() if isinstance(res, dict)):
            overall_status = 'critical'
        
        return {
            'timestamp': timestamp,
            'overall_status': overall_status,
            'checks': {
                'service': service_check,
                'databases': db_checks,
                'resources': resource_checks
            },
            'environment': os.getenv('ENVIRONMENT', 'unknown'),
            'version': os.getenv('APP_VERSION', '1.0.0')
        }

async def main():
    checker = HealthChecker()
    
    try:
        result = await checker.run_health_check()
        
        # Output format based on environment
        if os.getenv('HEALTH_CHECK_FORMAT') == 'json':
            print(json.dumps(result, indent=2))
        else:
            status = result['overall_status']
            print(f"Health Status: {status.upper()}")
            if status != 'healthy':
                print("Issues detected:")
                for check_type, checks in result['checks'].items():
                    if isinstance(checks, dict):
                        for name, check in checks.items():
                            if check.get('status') not in ['healthy', 'ok']:
                                print(f"  - {check_type}.{name}: {check.get('status', 'unknown')}")
        
        # Exit codes: 0=healthy, 1=unhealthy, 2=degraded, 3=critical
        exit_codes = {'healthy': 0, 'unhealthy': 1, 'degraded': 2, 'critical': 3}
        sys.exit(exit_codes.get(result['overall_status'], 1))
        
    except Exception as e:
        print(f"Health check failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
EOF
    
    chmod +x "$health_check_file"
    log_info "Enhanced health check script created" "file=$health_check_file"
    
    # Create health check endpoint for HTTP access
    local health_endpoint="/app/health_endpoint.py"
    
    cat > "$health_endpoint" << 'EOF'
#!/usr/bin/env python3
"""
HTTP Health Check Endpoint
Provides web-accessible health status for load balancers and monitoring
"""

import json
import subprocess
from aiohttp import web, ClientTimeout
import aiohttp

async def health_handler(request):
    """HTTP health check endpoint"""
    try:
        # Run the comprehensive health check
        result = subprocess.run(
            ['python3', '/app/health_check.py'],
            capture_output=True,
            text=True,
            timeout=30,
            env={**dict(request.app['env']), 'HEALTH_CHECK_FORMAT': 'json'}
        )
        
        if result.returncode == 0:
            health_data = json.loads(result.stdout)
            return web.json_response(health_data, status=200)
        else:
            return web.json_response(
                {'status': 'unhealthy', 'error': result.stderr},
                status=503
            )
    except Exception as e:
        return web.json_response(
            {'status': 'error', 'error': str(e)},
            status=500
        )

async def readiness_handler(request):
    """Kubernetes readiness probe endpoint"""
    # Quick check for readiness
    try:
        result = subprocess.run(
            ['python3', '-c', 'import socket; s=socket.socket(); s.connect(("localhost", int(os.getenv("MCP_SERVER_PORT", "8080")))); s.close()'],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return web.json_response({'status': 'ready'}, status=200)
        else:
            return web.json_response({'status': 'not_ready'}, status=503)
    except Exception:
        return web.json_response({'status': 'error'}, status=500)

async def liveness_handler(request):
    """Kubernetes liveness probe endpoint"""
    return web.json_response({'status': 'alive', 'timestamp': time.time()}, status=200)

if __name__ == '__main__':
    import os
    import time
    
    app = web.Application()
    app['env'] = os.environ.copy()
    
    app.router.add_get('/health', health_handler)
    app.router.add_get('/ready', readiness_handler)
    app.router.add_get('/alive', liveness_handler)
    
    # Start health endpoint on different port
    health_port = int(os.getenv('HEALTH_PORT', 9090))
    web.run_app(app, host='0.0.0.0', port=health_port)
EOF
    
    chmod +x "$health_endpoint"
    log_info "HTTP health endpoint created" "file=$health_endpoint"
    
    end_timer "health_setup"
    log_success "Comprehensive health monitoring system configured"
}

# ======================================================================
# APPLICATION INITIALIZATION
# ======================================================================

initialize_application() {
    log_info "Initializing MCP Crypto Trading Server..."
    
    # Set additional environment variables for the application
    export PYTHONPATH="/app:${PYTHONPATH:-}"
    export PYTHONUNBUFFERED=1
    export PYTHONDONTWRITEBYTECODE=1
    
    # Set up prometheus multiprocess directory
    if [[ "${ENABLE_METRICS:-true}" == "true" ]]; then
        export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc_dir"
        rm -rf "${PROMETHEUS_MULTIPROC_DIR:?}"/*
        log_info "Prometheus metrics directory initialized"
    fi
    
    # Validate application configuration
    if [[ -f "/app/mcp_crypto_server.py" ]]; then
        log_info "Main application file found"
    else
        log_error "Main application file 'mcp_crypto_server.py' not found"
        exit 1
    fi
    
    log_success "Application initialization completed"
}

# ======================================================================
# ADVANCED MONITORING AND OBSERVABILITY SETUP
# ======================================================================

# Comprehensive monitoring system with metrics, logging, and alerting
setup_monitoring() {
    start_timer "monitoring_setup"
    log_info "Configuring advanced monitoring and observability stack..."
    
    # Prometheus metrics configuration
    if [[ "${ENABLE_METRICS:-true}" == "true" ]]; then
        export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc_dir"
        mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
        chmod 755 "$PROMETHEUS_MULTIPROC_DIR"
        
        # Clean up any existing metrics
        find "$PROMETHEUS_MULTIPROC_DIR" -name "*.db" -delete 2>/dev/null || true
        
        log_info "Prometheus metrics configured" "dir=$PROMETHEUS_MULTIPROC_DIR"
        
        # Start metrics collection in background if enabled
        if [[ "${BACKGROUND_METRICS:-false}" == "true" ]]; then
            start_metrics_collector &
            local metrics_pid=$!
            log_info "Background metrics collector started" "pid=$metrics_pid"
        fi
    fi
    
    # Enhanced structured logging configuration
    if [[ "${ENABLE_STRUCTURED_LOGGING:-true}" == "true" ]]; then
        export PYTHONUNBUFFERED=1
        
        # Configure log rotation and retention
        local log_config="/app/logging_config.json"
        cat > "$log_config" << EOF
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "structured": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "${LOG_LEVEL:-INFO}",
            "formatter": "structured",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "${LOG_LEVEL:-INFO}",
            "formatter": "structured",
            "filename": "/app/logs/application.log",
            "maxBytes": 10485760,
            "backupCount": 5
        }
    },
    "root": {
        "level": "${LOG_LEVEL:-INFO}",
        "handlers": ["console", "file"]
    }
}
EOF
        export LOGGING_CONFIG="$log_config"
        log_info "Structured logging configured" "config=$log_config,level=${LOG_LEVEL:-INFO}"
    fi
    
    # Sentry error tracking configuration
    if [[ -n "${SENTRY_DSN:-}" ]]; then
        export SENTRY_ENVIRONMENT="${ENVIRONMENT}"
        export SENTRY_RELEASE="${APP_VERSION:-unknown}"
        export SENTRY_TRACES_SAMPLE_RATE="${SENTRY_SAMPLE_RATE:-0.1}"
        
        log_info "Sentry error tracking configured" "env=$SENTRY_ENVIRONMENT,release=$SENTRY_RELEASE,sample_rate=$SENTRY_TRACES_SAMPLE_RATE"
    else
        log_warn "Sentry DSN not configured - error tracking disabled"
    fi
    
    # OpenTelemetry configuration (if enabled)
    if [[ "${ENABLE_TRACING:-false}" == "true" ]]; then
        export OTEL_SERVICE_NAME="mcp-crypto-trading"
        export OTEL_SERVICE_VERSION="${APP_VERSION:-1.0.0}"
        export OTEL_RESOURCE_ATTRIBUTES="environment=${ENVIRONMENT},service.instance.id=$(hostname)"
        
        if [[ -n "${OTEL_EXPORTER_JAEGER_ENDPOINT:-}" ]]; then
            export OTEL_TRACES_EXPORTER="jaeger"
            log_info "OpenTelemetry tracing configured" "service=$OTEL_SERVICE_NAME,exporter=jaeger"
        elif [[ -n "${OTEL_EXPORTER_OTLP_ENDPOINT:-}" ]]; then
            export OTEL_TRACES_EXPORTER="otlp"
            log_info "OpenTelemetry tracing configured" "service=$OTEL_SERVICE_NAME,exporter=otlp"
        fi
    fi
    
    # Security monitoring setup
    if [[ "${ENABLE_SECURITY_MONITORING:-true}" == "true" ]]; then
        # Configure security event logging
        export SECURITY_LOG_LEVEL="${SECURITY_LOG_LEVEL:-WARNING}"
        
        # Start security monitor in background
        if [[ "${BACKGROUND_SECURITY_MONITOR:-false}" == "true" ]]; then
            start_security_monitor &
            local security_pid=$!
            log_security "Security monitoring enabled" "pid=$security_pid"
        fi
    fi
    
    # Health check monitoring setup
    local health_interval="${HEALTH_CHECK_INTERVAL:-30}"
    if [[ "${ENABLE_HEALTH_MONITORING:-true}" == "true" ]] && [[ $health_interval -gt 0 ]]; then
        start_health_monitor "$health_interval" &
        local health_pid=$!
        log_info "Health monitoring started" "pid=$health_pid,interval=${health_interval}s"
    fi
    
    end_timer "monitoring_setup"
    log_success "Advanced monitoring and observability stack configured"
}

# Background metrics collection
start_metrics_collector() {
    while [[ "${CLEANUP_IN_PROGRESS:-false}" != "true" ]]; do
        sleep "${METRICS_COLLECTION_INTERVAL:-60}"
        
        # Collect system metrics
        if [[ -r "/proc/meminfo" ]] && [[ -r "/proc/loadavg" ]]; then
            local timestamp=$(date -u '+%s')
            local mem_available
            mem_available=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
            local load_avg
            load_avg=$(cut -d' ' -f1 < /proc/loadavg)
            
            log_debug "System metrics collected" "timestamp=$timestamp,memory_kb=$mem_available,load=$load_avg"
        fi
    done
}

# Background security monitoring
start_security_monitor() {
    while [[ "${CLEANUP_IN_PROGRESS:-false}" != "true" ]]; do
        sleep "${SECURITY_CHECK_INTERVAL:-300}"
        
        # Check for suspicious activities
        local failed_connections
        failed_connections=$(ss -tuln 2>/dev/null | wc -l)
        
        if [[ $failed_connections -gt 100 ]]; then
            log_security "High connection count detected" "connections=$failed_connections"
        fi
    done
}

# Health monitoring background process
start_health_monitor() {
    local interval="$1"
    
    while [[ "${CLEANUP_IN_PROGRESS:-false}" != "true" ]]; do
        sleep "$interval"
        
        # Run health check and log results
        if python3 /app/health_check.py >/dev/null 2>&1; then
            log_debug "Health check passed"
        else
            log_warn "Health check failed"
        fi
    done
}

# ======================================================================
# ENHANCED MAIN EXECUTION WITH PARALLEL PROCESSING
# ======================================================================

# Display startup banner
display_startup_banner() {
    cat << 'EOF'

 ███╗   ███╗ ██████╗██████╗      ██████╗██████╗ ██╗   ██╗██████╗ ████████╗ ██████╗ 
 ████╗ ████║██╔════╝██╔══██╗    ██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝██╔═══██╗
 ██╔████╔██║██║     ██████╔╝    ██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   ██║   ██║
 ██║╚██╔╝██║██║     ██╔═══╝     ██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ██║   ██║
 ██║ ╚═╝ ██║╚██████╗██║         ╚██████╗██║  ██║   ██║   ██║        ██║   ╚██████╔╝
 ╚═╝     ╚═╝ ╚═════╝╚═╝          ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝    ╚═════╝ 
                                                                                      
    ████████╗██████╗  █████╗ ██████╗ ██╗███╗   ██╗ ██████╗     ███████╗███████╗██████╗ ██╗   ██╗███████╗██████╗ 
    ╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║██╔════╝     ██╔════╝██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗
       ██║   ██████╔╝███████║██║  ██║██║██╔██╗ ██║██║  ███╗    ███████╗█████╗  ██████╔╝██║   ██║█████╗  ██████╔╝
       ██║   ██╔══██╗██╔══██║██║  ██║██║██║╚██╗██║██║   ██║    ╚════██║██╔══╝  ██╔══██╗╚██╗ ██╔╝██╔══╝  ██╔══██╗
       ██║   ██║  ██║██║  ██║██████╔╝██║██║ ╚████║╚██████╔╝    ███████║███████╗██║  ██║ ╚████╔╝ ███████╗██║  ██║
       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝     ╚══════╝╚══════╝╚═╝  ╚═╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝

EOF

    echo -e "${GREEN}                    🚀 Production-Ready Cryptocurrency Trading Analysis Server 🚀${NC}"
    echo -e "${BLUE}                                Enhanced 2025+ Edition with Advanced Security${NC}"
    echo ""
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC} Environment: ${ENVIRONMENT^^}"
    echo -e "${CYAN}│${NC} Version: ${APP_VERSION:-2.0.0}"
    echo -e "${CYAN}│${NC} Host: ${MCP_SERVER_HOST:-0.0.0.0}:${MCP_SERVER_PORT:-8080}"
    echo -e "${CYAN}│${NC} User: $(whoami) (PID: $$)"
    echo -e "${CYAN}│${NC} Started: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo -e "${CYAN}│${NC} Features: Enhanced Security, Advanced Monitoring, Performance Optimization"
    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# Parallel initialization for improved performance
run_parallel_checks() {
    log_info "Running connectivity checks in parallel for optimal performance..."
    
    local pids=()
    local results=()
    
    # Start connectivity checks in parallel
    {
        check_mongodb_connectivity
        echo "mongodb:$?" > "/tmp/check_mongodb_$$"
    } &
    pids+=("$!")
    
    {
        check_redis_connectivity
        echo "redis:$?" > "/tmp/check_redis_$$"
    } &
    pids+=("$!")
    
    {
        check_postgresql_connectivity
        echo "postgresql:$?" > "/tmp/check_postgresql_$$"
    } &
    pids+=("$!")
    
    # Wait for all parallel checks to complete
    local failed_checks=()
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            failed_checks+=("PID:$pid")
        fi
    done
    
    # Collect and verify results
    for check in mongodb redis postgresql; do
        local result_file="/tmp/check_${check}_$$"
        if [[ -f "$result_file" ]]; then
            local result
            result=$(cat "$result_file")
            local service="${result%%:*}"
            local exit_code="${result##*:}"
            
            if [[ "$exit_code" -ne 0 ]]; then
                failed_checks+=("$service")
            fi
            
            rm -f "$result_file"
        fi
    done
    
    if [[ ${#failed_checks[@]} -gt 0 ]]; then
        log_error "Parallel connectivity checks failed" "services='$(IFS=','; echo "${failed_checks[*]}")'"
        return 1
    fi
    
    log_success "All parallel connectivity checks completed successfully"
    return 0
}

# Enhanced main execution with comprehensive initialization
main() {
    start_timer "total_initialization"
    
    # Display enhanced startup banner
    display_startup_banner
    
    log_info "Initiating MCP Crypto Trading Server with enhanced 2025+ features..."
    log_info "Initialization details" "pid=$$,user=$(whoami),cwd=$(pwd),bash_version=${BASH_VERSION}"
    
    # Phase 1: Critical system validation (sequential for reliability)
    log_info "Phase 1: Critical system validation"
    validate_environment
    check_system_resources
    setup_directories
    setup_python_environment
    
    # Phase 2: External dependencies (parallel for performance)
    log_info "Phase 2: External dependency validation"
    if ! run_parallel_checks; then
        log_error "Critical dependency checks failed - aborting initialization"
        exit 1
    fi
    
    # Phase 3: Application setup (sequential for proper ordering)
    log_info "Phase 3: Application and monitoring setup"
    setup_health_check
    initialize_application
    setup_monitoring
    
    # Calculate and report initialization performance
    end_timer "total_initialization"
    
    # Final validation and readiness check
    log_info "Performing final readiness validation..."
    if python3 /app/health_check.py >/dev/null 2>&1; then
        log_success "🎉 All initialization checks passed - system ready for production!"
    else
        log_error "Final readiness check failed - system not ready"
        exit 1
    fi
    
    # Security audit log
    log_security "Container initialization completed" "environment=${ENVIRONMENT},user=$(whoami),security_validated=true"
    
    log_info "🚀 Transferring control to application startup..."
    
    # Execute the provided command with proper signal forwarding
    exec "$@"
}

# Script entry point with enhanced error handling
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Validate script arguments
    if [[ $# -eq 0 ]]; then
        log_error "No command specified for execution"
        echo "Usage: $0 <command> [args...]" >&2
        echo "Example: $0 python3 mcp_crypto_server.py" >&2
        exit 1
    fi
    
    # Validate that the command exists
    if ! command -v "$1" >/dev/null 2>&1; then
        log_error "Command not found: $1"
        exit 1
    fi
    
    # Execute main initialization
    main "$@"
fi
#!/bin/bash
set -euo pipefail
set -o errtrace
set -o functrace

# ======================================================================
# MCP Crypto Trading Server - Enhanced Production Startup (2025+ Edition)
# Ultra-high-performance production server launcher with advanced features
# Version: 2.0 | Last Updated: $(date -u '+%Y-%m-%d')
# ======================================================================

# Bash version and feature compatibility check
if [[ ${BASH_VERSION%%.*} -lt 4 ]]; then
    echo "FATAL: Bash 4.0+ required for modern shell features" >&2
    exit 1
fi

# Enhanced color palette with 256-color support and semantic meaning
readonly RED='\033[38;5;196m'      # Critical errors
readonly GREEN='\033[38;5;46m'     # Success states
readonly YELLOW='\033[38;5;226m'   # Warnings
readonly BLUE='\033[38;5;33m'      # Information
readonly PURPLE='\033[38;5;129m'   # Startup/lifecycle
readonly CYAN='\033[38;5;51m'      # Debug/trace
readonly ORANGE='\033[38;5;214m'   # Performance metrics
readonly MAGENTA='\033[38;5;201m'  # Security events
readonly NC='\033[0m'              # No Color

# Performance and security constants
readonly SCRIPT_NAME="${0##*/}"
readonly SCRIPT_PID=$$
readonly SCRIPT_START_TIME=$(date -u '+%s%3N')
readonly MAX_STARTUP_TIME=300
readonly HEALTH_CHECK_RETRIES=10
readonly PERFORMANCE_BASELINE_CPU=2.0

# Enhanced configuration with auto-detection and validation
readonly DEFAULT_HOST="${MCP_SERVER_HOST:-0.0.0.0}"
readonly DEFAULT_PORT="${MCP_SERVER_PORT:-8080}"
readonly AUTO_DETECTED_WORKERS=$(nproc 2>/dev/null || echo "2")
readonly DEFAULT_WORKERS="${MAX_WORKERS:-$AUTO_DETECTED_WORKERS}"
readonly DEFAULT_TIMEOUT="${WORKER_TIMEOUT:-60}"
readonly DEFAULT_LOG_LEVEL="${LOG_LEVEL:-INFO}"
readonly DEFAULT_KEEPALIVE="${KEEPALIVE_TIMEOUT:-5}"
readonly DEFAULT_MAX_REQUESTS="${MAX_REQUESTS:-2000}"
readonly DEFAULT_MAX_REQUESTS_JITTER="${MAX_REQUESTS_JITTER:-200}"

# Advanced performance tuning
readonly MEMORY_THRESHOLD_MB="${MEMORY_THRESHOLD_MB:-1024}"
readonly CPU_THRESHOLD_PERCENT="${CPU_THRESHOLD_PERCENT:-80}"
readonly DISK_THRESHOLD_PERCENT="${DISK_THRESHOLD_PERCENT:-85}"

# Advanced structured logging with performance metrics and context
log_structured() {
    local level="$1"
    local message="$2"
    local context="${3:-}"
    local timestamp=$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')
    local runtime_ms=$(($(date -u '+%s%3N') - SCRIPT_START_TIME))
    local memory_mb
    memory_mb=$(ps -o rss= -p $$ 2>/dev/null | awk '{print int($1/1024)}' || echo "0")
    
    # Structured JSON logging for production environments
    if [[ "${ENABLE_JSON_LOGGING:-false}" == "true" ]]; then
        local json_context=""
        [[ -n "$context" ]] && json_context=",\"context\":{$context}"
        printf '{"timestamp":"%s","level": "%s","message":"%s","script":"%s","pid":%d,"runtime_ms":%d,"memory_mb":%d%s}\n' \
            "$timestamp" "$level" "$message" "$SCRIPT_NAME" "$SCRIPT_PID" "$runtime_ms" "$memory_mb" "$json_context"
    else
        # Enhanced console logging with performance data
        local color_map=(["INFO"]="$BLUE" ["WARN"]="$YELLOW" ["ERROR"]="$RED" ["SUCCESS"]="$GREEN" \
                        ["DEBUG"]="$CYAN" ["STARTUP"]="$PURPLE" ["PERF"]="$ORANGE" ["SECURITY"]="$MAGENTA")
        local perf_info="[${runtime_ms}ms|${memory_mb}MB]"
        echo -e "${color_map[$level]:-$NC}[$level]${NC} $timestamp $perf_info - $message ${context:+($context)}"
    fi
}

log_info() { log_structured "INFO" "$1" "${2:-}"; }
log_warn() { log_structured "WARN" "$1" "${2:-}" >&2; }
log_error() { log_structured "ERROR" "$1" "${2:-}" >&2; }
log_success() { log_structured "SUCCESS" "$1" "${2:-}"; }
log_debug() { [[ "${DEBUG:-false}" == "true" ]] && log_structured "DEBUG" "$1" "${2:-}"; }
log_startup() { log_structured "STARTUP" "$1" "${2:-}"; }
log_perf() { log_structured "PERF" "$1" "${2:-}"; }
log_security() { log_structured "SECURITY" "$1" "${2:-}" >&2; }

# Performance monitoring utilities
start_perf_timer() {
    local timer_name="$1"
    declare -g "perf_timer_${timer_name}=$(date -u '+%s%3N')"
}

end_perf_timer() {
    local timer_name="$1"
    local start_var="perf_timer_${timer_name}"
    local start_time="${!start_var:-}"
    if [[ -n "$start_time" ]]; then
        local end_time=$(date -u '+%s%3N')
        local duration=$((end_time - start_time))
        log_perf "$timer_name completed" "\"duration_ms\":$duration"
        unset "perf_timer_${timer_name}"
        echo "$duration"
    fi
}

# Enhanced error handling with forensic logging and recovery
handle_error() {
    local exit_code=$?
    local line_number=$1
    local function_name="${FUNCNAME[1]:-main}"
    local command="${BASH_COMMAND}"
    
    log_error "Fatal error in function '$function_name' at line $line_number" "\"exit_code\":$exit_code,\"command\":\"$command\""
    
    # Enhanced stack trace with function context
    log_error "Detailed call stack:"
    local frame=1
    while caller $frame 2>/dev/null; do
        ((frame++))
    done | while IFS=' ' read -r line func file; do
        log_error "  Frame $((frame-1)): $func() at $file:$line"
    done
    
    # System state at time of error
    local load_avg
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | cut -d',' -f1 | xargs || echo "unknown")
    local mem_usage
    mem_usage=$(free | awk 'NR==2{printf "%.1f%%", $3*100/$2}' 2>/dev/null || echo "unknown")
    
    log_error "System state at error" "\"load_avg\":\"$load_avg\",\"memory_usage\":\"$mem_usage\""
    
    # Attempt emergency cleanup
    emergency_cleanup
    exit $exit_code
}

# Enhanced error trapping with function tracing
trap 'handle_error $LINENO' ERR
trap 'log_debug "Function ${FUNCNAME[0]} entered" "line=$LINENO"' DEBUG

# Enhanced cleanup with resource monitoring and recovery
cleanup_and_exit() {
    local exit_code=${1:-1}
    local cleanup_reason="${2:-unknown}"
    
    # Prevent recursive cleanup
    if [[ "${CLEANUP_IN_PROGRESS:-false}" == "true" ]]; then
        log_warn "Cleanup already in progress, forcing immediate exit"
        exit $exit_code
    fi
    export CLEANUP_IN_PROGRESS=true
    
    start_perf_timer "cleanup"
    log_info "Initiating enhanced graceful shutdown" "\"reason\":\"$cleanup_reason\",\"exit_code\":$exit_code"
    
    # Collect final system metrics
    local final_uptime
    final_uptime=$(awk '{print int($1)}' /proc/uptime 2>/dev/null || echo "0")
    local final_load
    final_load=$(cut -d' ' -f1 /proc/loadavg 2>/dev/null || echo "0")
    
    log_perf "Final system state" "\"uptime_seconds\":$final_uptime,\"load_avg\":\"$final_load\""
    
    # Graceful process termination with timeout
    local pids=($(jobs -p 2>/dev/null || true))
    if [[ ${#pids[@]} -gt 0 ]]; then
        log_info "Gracefully terminating ${#pids[@]} background processes..."
        
        # Send SIGTERM to all processes
        printf '%s\n' "${pids[@]}" | xargs -I {} -P 0 kill -TERM {} 2>/dev/null || true
        
        # Wait for graceful shutdown with timeout
        local wait_timeout=10
        local waited=0
        while [[ $waited -lt $wait_timeout ]] && jobs %% &>/dev/null; do
            sleep 1
            ((waited++))
        done
        
        # Force kill remaining processes
        local remaining_pids=($(jobs -p 2>/dev/null || true))
        if [[ ${#remaining_pids[@]} -gt 0 ]]; then
            log_warn "Force terminating ${#remaining_pids[@]} remaining processes"
            printf '%s\n' "${remaining_pids[@]}" | xargs -I {} -P 0 kill -KILL {} 2>/dev/null || true
        fi
    fi
    
    # Clean up resources
    cleanup_resources
    
    local cleanup_duration
    cleanup_duration=$(end_perf_timer "cleanup")
    log_success "Graceful shutdown completed" "\"duration_ms\":$cleanup_duration,\"exit_code\":$exit_code"
    
    exit $exit_code
}

# Emergency cleanup for error conditions
emergency_cleanup() {
    log_security "Emergency cleanup initiated - system instability detected"
    
    # Kill all child processes immediately
    pkill -P $$ 2>/dev/null || true
    
    # Force cleanup resources
    cleanup_resources
    
    log_security "Emergency cleanup completed"
}

# Resource cleanup function
cleanup_resources() {
    # Remove temporary files created by this script
    find /tmp -name "${SCRIPT_NAME}_*" -user "$(whoami)" -delete 2>/dev/null || true
    
    # Clear shared memory segments if any
    ipcs -m 2>/dev/null | awk -v user="$(whoami)" '$3==user && $6==0 {print $2}' | xargs -r ipcrm -m 2>/dev/null || true
    
    # Flush file system buffers
    sync 2>/dev/null || true
}

# Enhanced signal handling
trap 'cleanup_and_exit 0 "SIGTERM"' SIGTERM
trap 'cleanup_and_exit 130 "SIGINT"' SIGINT
trap 'cleanup_and_exit 131 "SIGQUIT"' SIGQUIT
trap 'cleanup_and_exit 129 "SIGHUP"' SIGHUP

# ======================================================================
# COMPREHENSIVE PRE-FLIGHT SYSTEM ANALYSIS
# ======================================================================

# Advanced port availability check with detailed analysis
check_port_availability() {
    local port="$1"
    local service_name="${2:-service}"
    
    log_debug "Checking port availability" "\"port\":$port,\"service\":\"$service_name\""
    
    # Multiple methods for port checking
    local port_in_use=false
    
    # Method 1: netstat (if available)
    if command -v netstat >/dev/null 2>&1; then
        if netstat -tuln 2>/dev/null | grep -q ":${port} "; then
            port_in_use=true
        fi
    fi
    
    # Method 2: ss (modern replacement for netstat)
    if command -v ss >/dev/null 2>&1; then
        if ss -tuln 2>/dev/null | grep -q ":${port} "; then
            port_in_use=true
        fi
    fi
    
    # Method 3: Direct socket test
    if exec 3<>"/dev/tcp/localhost/$port" 2>/dev/null; then
        exec 3<&-
        port_in_use=true
    fi
    
    if [[ "$port_in_use" == "true" ]]; then
        # Get detailed information about what's using the port
        local port_info
        if command -v lsof >/dev/null 2>&1; then
            port_info=$(lsof -ti :"$port" 2>/dev/null | head -1)
            if [[ -n "$port_info" ]]; then
                local process_info
                process_info=$(ps -p "$port_info" -o pid,ppid,cmd --no-headers 2>/dev/null || echo "unknown process")
                log_error "Port $port is in use by: $process_info"
            fi
        fi
        return 1
    fi
    
    return 0
}

# Enhanced system resource validation
validate_system_resources() {
    log_startup "Performing comprehensive system resource validation..."
    
    local validation_errors=()
    local performance_warnings=()
    
    # Memory validation with detailed analysis
    if [[ -r "/proc/meminfo" ]]; then
        local -A mem_info
        while IFS=':' read -r key value; do
            [[ "$key" =~ ^(MemTotal|MemAvailable|MemFree|SwapTotal|SwapFree|Buffers|Cached)$ ]] && \
                mem_info["$key"]=$(echo "$value" | awk '{print $1}')
        done < /proc/meminfo
        
        local mem_available_mb=$((mem_info["MemAvailable"] / 1024))
        local mem_total_mb=$((mem_info["MemTotal"] / 1024))
        local mem_usage_percent=$(( (mem_total_mb - mem_available_mb) * 100 / mem_total_mb ))
        
        log_perf "Memory analysis" "\"total_mb\":$mem_total_mb,\"available_mb\":$mem_available_mb,\"usage_percent\":$mem_usage_percent"
        
        if [[ $mem_available_mb -lt 512 ]]; then
            validation_errors+=("Insufficient memory: ${mem_available_mb}MB available (minimum: 512MB)")
        elif [[ $mem_available_mb -lt 1024 ]]; then
            performance_warnings+=("Low memory: ${mem_available_mb}MB available (recommended: 1GB+)")
        fi
        
        # Check swap configuration
        if [[ ${mem_info["SwapTotal"]-0} -eq 0 ]] && [[ $mem_total_mb -lt 2048 ]]; then
            performance_warnings+=("No swap configured with limited RAM (${mem_total_mb}MB)")
        fi
    else
        validation_errors+=("Cannot read memory information from /proc/meminfo")
    fi
    
    # CPU validation
    local cpu_count
    cpu_count=$(nproc 2>/dev/null || echo "1")
    local load_avg
    load_avg=$(cut -d' ' -f1-3 < /proc/loadavg 2>/dev/null || echo "unknown")
    
    log_perf "CPU analysis" "\"cores\":$cpu_count,\"load_avg\":\"$load_avg\""
    
    if [[ $cpu_count -lt 2 ]]; then
        performance_warnings+=("Single CPU core detected (recommended: 2+ cores)")
    fi
    
    # Disk space validation for critical paths
    local critical_paths=("/app:/tmp:/var/log")
    IFS=':' read -ra paths <<< "${critical_paths[0]}"
    
    for path in "${paths[@]}"; do
        if [[ -d "$path" ]]; then
            local disk_info
            disk_info=$(df "$path" 2>/dev/null | awk 'NR==2 {print $2,$3,$4,$5}' | tr -d '%')
            
            if [[ -n "$disk_info" ]]; then
                read -r total used available usage_percent <<< "$disk_info"
                local available_gb=$((available / 1024 / 1024))
                
                log_perf "Disk space: $path" "\"available_gb\":$available_gb,\"usage_percent\":$usage_percent"
                
                if [[ $usage_percent -gt 90 ]]; then
                    validation_errors+=("Critical disk space on $path: ${usage_percent}% used")
                elif [[ $usage_percent -gt 80 ]]; then
                    performance_warnings+=("High disk usage on $path: ${usage_percent}% used")
                fi
                
                if [[ $available_gb -lt 1 ]]; then
                    validation_errors+=("Insufficient disk space on $path: ${available_gb}GB available")
                fi
            fi
        fi
    done
    
    # File descriptor limits
    local fd_soft_limit
    fd_soft_limit=$(ulimit -Sn)
    local fd_hard_limit
    fd_hard_limit=$(ulimit -Hn)
    
    log_perf "File descriptor limits" "\"soft\":$fd_soft_limit,\"hard\":$fd_hard_limit"
    
    if [[ $fd_soft_limit -lt 4096 ]]; then
        performance_warnings+=("Low file descriptor soft limit: $fd_soft_limit (recommended: 8192+)")
    fi
    
    # Report validation results
    if [[ ${#validation_errors[@]} -gt 0 ]]; then
        log_error "System resource validation failed:"
        printf '  - %s\n' "${validation_errors[@]}"
        return 1
    fi
    
    if [[ ${#performance_warnings[@]} -gt 0 ]]; then
        log_warn "Performance warnings detected:"
        printf '  - %s\n' "${performance_warnings[@]}"
    fi
    
    return 0
}

# Comprehensive pre-flight checks with enhanced security
perform_preflight_checks() {
    start_perf_timer "preflight"
    log_startup "Initiating comprehensive pre-flight system analysis..."
    
    local check_failures=()
    
    # Security validation
    log_startup "Phase 1: Security validation"
    if [[ "$(whoami)" == "root" ]]; then
        if [[ "${ALLOW_ROOT:-false}" != "true" ]]; then
            check_failures+=("Running as root user (security risk - set ALLOW_ROOT=true to override)")
        else
            log_security "Running as root user with explicit override" "\"allow_root\":true"
        fi
    fi
    
    # Python environment validation
    log_startup "Phase 2: Python environment validation"
    if ! command -v python3 >/dev/null 2>&1; then
        check_failures+=("Python3 not found in PATH")
    else
        local python_version
        python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        local python_major
        python_major=$(echo "$python_version" | cut -d. -f1)
        local python_minor
        python_minor=$(echo "$python_version" | cut -d. -f2)
        
        log_info "Python environment validated" "\"version\":\"$python_version\",\"executable\":\"$(which python3)\""
        
        if [[ $python_major -lt 3 ]] || [[ $python_major -eq 3 && $python_minor -lt 8 ]]; then
            check_failures+=("Python 3.8+ required, found: $python_version")
        fi
    fi
    
    # Application file validation
    log_startup "Phase 3: Application file validation"
    local app_files=("mcp_crypto_server.py" "mcp_crypto_main.py")
    local main_app_file=""
    
    for file in "${app_files[@]}"; do
        if [[ -f "/app/$file" ]]; then
            main_app_file="/app/$file"
            break
        fi
    done
    
    if [[ -z "$main_app_file" ]]; then
        check_failures+=("No main application file found (checked: ${app_files[*]})")
    else
        log_info "Main application file located" "\"file\":\"$main_app_file\""
        
        # Validate Python syntax
        if ! python3 -m py_compile "$main_app_file" 2>/dev/null; then
            check_failures+=("Main application file has syntax errors: $main_app_file")
        fi
    fi
    
    # Environment variables validation
    log_startup "Phase 4: Environment variables validation"
    declare -A required_vars=(
        ["ENVIRONMENT"]="^(production|staging|development)$"
        ["MONGODB_URI"]="^mongodb(\\+srv)?://.*"
        ["REDIS_URL"]="^redis(s)?://.*"
        ["MCP_SERVER_PORT"]="^[1-9][0-9]{3,4}$"
    )
    
    for var in "${!required_vars[@]}"; do
        local value="${!var:-}"
        local pattern="${required_vars[$var]}"
        
        if [[ -z "$value" ]]; then
            check_failures+=("Required environment variable not set: $var")
        elif [[ ! "$value" =~ $pattern ]]; then
            check_failures+=("Invalid format for environment variable $var")
        else
            log_debug "Environment variable validated" "\"var\":\"$var\",\"format\":\"valid\""
        fi
    done
    
    # System resources validation
    log_startup "Phase 5: System resources validation"
    if ! validate_system_resources; then
        check_failures+=("System resource validation failed")
    fi
    
    # Network port validation
    log_startup "Phase 6: Network port validation"
    if ! check_port_availability "$DEFAULT_PORT" "MCP Server"; then
        check_failures+=("Port $DEFAULT_PORT is already in use")
    fi
    
    # Health check port validation (if different)
    local health_port="${HEALTH_PORT:-9090}"
    if [[ "$health_port" != "$DEFAULT_PORT" ]]; then
        if ! check_port_availability "$health_port" "Health Check"; then
            check_failures+=("Health check port $health_port is already in use")
        fi
    fi
    
    # Report pre-flight results
    local preflight_duration
    preflight_duration=$(end_perf_timer "preflight")
    
    if [[ ${#check_failures[@]} -gt 0 ]]; then
        log_error "Pre-flight checks failed (${#check_failures[@]} issues):" "\"duration_ms\":$preflight_duration"
        printf '  - %s\n' "${check_failures[@]}"
        return 1
    fi
    
    log_success "All pre-flight checks passed" "\"duration_ms\":$preflight_duration,\"checks\":6"
    return 0
}

# ======================================================================
# ADVANCED DATABASE CONNECTION VALIDATION WITH HEALTH METRICS
# ======================================================================

# Enhanced database connection validator with performance metrics
validate_database_connections() {
    start_perf_timer "db_validation"
    log_startup "Initiating comprehensive database connectivity validation..."
    
    # Create enhanced connection test script with metrics
    local test_script="/tmp/enhanced_db_test_$$.py"
    
    cat > "$test_script" << 'EOF'
import asyncio
import json
import os
import sys
import time
from typing import Dict, Any, Optional

class DatabaseTester:
    def __init__(self):
        self.results = {}
        self.start_time = time.time()
    
    async def test_mongodb(self) -> Dict[str, Any]:
        """Test MongoDB connection with detailed metrics"""
        test_start = time.time()
        result = {
            'service': 'mongodb',
            'status': 'unknown',
            'response_time_ms': 0,
            'error': None,
            'metadata': {}
        }
        
        try:
            import motor.motor_asyncio as motor
            
            uri = os.getenv('MONGODB_URI')
            if not uri:
                result.update({'status': 'skipped', 'error': 'MONGODB_URI not configured'})
                return result
            
            # Connection with timeout and detailed config
            client = motor.AsyncIOMotorClient(
                uri,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                maxPoolSize=10
            )
            
            # Ping test
            ping_result = await client.admin.command('ping')
            
            # Get server info
            server_info = await client.admin.command('serverStatus')
            
            # Test write operation
            test_db = client.test_connection
            test_collection = test_db.test
            await test_collection.insert_one({'test': True, 'timestamp': time.time()})
            await test_collection.delete_many({'test': True})
            
            await client.close()
            
            result.update({
                'status': 'healthy',
                'response_time_ms': round((time.time() - test_start) * 1000, 2),
                'metadata': {
                    'server_version': server_info.get('version', 'unknown'),
                    'uptime_seconds': server_info.get('uptime', 0),
                    'connections': server_info.get('connections', {})
                }
            })
            
        except Exception as e:
            result.update({
                'status': 'unhealthy',
                'response_time_ms': round((time.time() - test_start) * 1000, 2),
                'error': str(e)
            })
        
        return result
    
    async def test_redis(self) -> Dict[str, Any]:
        """Test Redis connection with detailed metrics"""
        test_start = time.time()
        result = {
            'service': 'redis',
            'status': 'unknown',
            'response_time_ms': 0,
            'error': None,
            'metadata': {}
        }
        
        try:
            import aioredis
            
            url = os.getenv('REDIS_URL')
            if not url:
                result.update({'status': 'skipped', 'error': 'REDIS_URL not configured'})
                return result
            
            # Connection with timeout
            redis = aioredis.from_url(
                url,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                max_connections=10
            )
            
            # Ping test
            await redis.ping()
            
            # Get server info
            info = await redis.info()
            
            # Test write/read operations
            test_key = f'connection_test_{time.time()}'
            await redis.set(test_key, 'test_value', ex=60)
            test_value = await redis.get(test_key)
            await redis.delete(test_key)
            
            await redis.close()
            
            result.update({
                'status': 'healthy',
                'response_time_ms': round((time.time() - test_start) * 1000, 2),
                'metadata': {
                    'redis_version': info.get('redis_version', 'unknown'),
                    'uptime_seconds': info.get('uptime_in_seconds', 0),
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory_human': info.get('used_memory_human', '0B')
                }
            })
            
        except Exception as e:
            result.update({
                'status': 'unhealthy',
                'response_time_ms': round((time.time() - test_start) * 1000, 2),
                'error': str(e)
            })
        
        return result
    
    async def test_postgresql(self) -> Dict[str, Any]:
        """Test PostgreSQL connection with detailed metrics"""
        test_start = time.time()
        result = {
            'service': 'postgresql',
            'status': 'unknown',
            'response_time_ms': 0,
            'error': None,
            'metadata': {}
        }
        
        try:
            dsn = os.getenv('POSTGRES_DSN')
            if not dsn:
                result.update({'status': 'skipped', 'error': 'POSTGRES_DSN not configured'})
                return result
            
            import asyncpg
            
            # Connection with timeout
            conn = await asyncpg.connect(
                dsn,
                timeout=10,
                command_timeout=5
            )
            
            # Basic connectivity test
            await conn.execute('SELECT 1')
            
            # Get server version and stats
            version_result = await conn.fetchval('SELECT version()')
            stats_result = await conn.fetch('''
                SELECT 
                    setting as max_connections,
                    (SELECT count(*) FROM pg_stat_activity) as current_connections
                FROM pg_settings 
                WHERE name = 'max_connections'
            ''')
            
            await conn.close()
            
            result.update({
                'status': 'healthy',
                'response_time_ms': round((time.time() - test_start) * 1000, 2),
                'metadata': {
                    'server_version': version_result.split()[1] if version_result else 'unknown',
                    'max_connections': stats_result[0]['max_connections'] if stats_result else 0,
                    'current_connections': stats_result[0]['current_connections'] if stats_result else 0
                }
            })
            
        except Exception as e:
            result.update({
                'status': 'unhealthy',
                'response_time_ms': round((time.time() - test_start) * 1000, 2),
                'error': str(e)
            })
        
        return result
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all database tests concurrently"""
        tests = await asyncio.gather(
            self.test_mongodb(),
            self.test_redis(),
            self.test_postgresql(),
            return_exceptions=True
        )
        
        total_time = round((time.time() - self.start_time) * 1000, 2)
        
        # Process results
        all_results = {
            'total_time_ms': total_time,
            'tests_run': len([t for t in tests if isinstance(t, dict)]),
            'databases': {}
        }
        
        healthy_count = 0
        for test_result in tests:
            if isinstance(test_result, dict):
                service = test_result['service']
                all_results['databases'][service] = test_result
                if test_result['status'] == 'healthy':
                    healthy_count += 1
        
        all_results['summary'] = {
            'healthy': healthy_count,
            'total': len(all_results['databases']),
            'overall_status': 'healthy' if healthy_count == len([t for t in tests if isinstance(t, dict) and t.get('status') != 'skipped']) else 'degraded'
        }
        
        return all_results

async def main():
    tester = DatabaseTester()
    results = await tester.run_all_tests()
    
    print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    if results['summary']['overall_status'] == 'healthy':
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
EOF
    
    # Execute the enhanced database tests
    log_info "Running parallel database connectivity tests..."
    
    local test_output
    local test_exit_code
    
    if test_output=$(python3 "$test_script" 2>&1); then
        test_exit_code=0
    else
        test_exit_code=$?
    fi
    
    # Parse and log results
    if command -v jq >/dev/null 2>&1 && [[ "$test_output" =~ ^\{ ]]; then
        # JSON output available, parse it
        local total_time
        total_time=$(echo "$test_output" | jq -r '.total_time_ms // 0')
        local healthy_count
        healthy_count=$(echo "$test_output" | jq -r '.summary.healthy // 0')
        local total_count
        total_count=$(echo "$test_output" | jq -r '.summary.total // 0')
        
        log_perf "Database validation completed" "\"duration_ms\":$total_time,\"healthy\":$healthy_count,\"total\":$total_count"
        
        # Log individual database results
        echo "$test_output" | jq -r '.databases | to_entries[] | "\(.key): \(.value.status) (\(.value.response_time_ms)ms)"' | while read -r db_result; do
            if [[ "$db_result" =~ healthy ]]; then
                log_success "Database connection validated: $db_result"
            else
                log_error "Database connection failed: $db_result"
            fi
        done
    else
        # Fallback for non-JSON output
        log_info "Database test output: $test_output"
    fi
    
    # Clean up test script
    rm -f "$test_script"
    
    local validation_duration
    validation_duration=$(end_perf_timer "db_validation")
    
    if [[ $test_exit_code -eq 0 ]]; then
        log_success "All database connections validated successfully" "\"duration_ms\":$validation_duration"
        return 0
    else
        log_error "Database connection validation failed" "\"duration_ms\":$validation_duration,\"exit_code\":$test_exit_code"
        return 1
    fi
}

# ======================================================================
# ADVANCED PERFORMANCE OPTIMIZATION WITH SYSTEM TUNING
# ======================================================================

# System-level performance tuning
optimize_system_performance() {
    log_startup "Applying advanced system-level performance optimizations..."
    
    local optimization_applied=0
    local performance_warnings=()
    
    # Memory management optimizations
    if [[ -w "/proc/sys/vm/swappiness" ]]; then
        echo 10 > /proc/sys/vm/swappiness 2>/dev/null && {
            log_perf "Swappiness optimized" "\"value\":10"
            ((optimization_applied++))
        }
    else
        performance_warnings+=("Cannot optimize swappiness (insufficient privileges)")
    fi
    
    # Network performance optimizations
    if [[ -w "/proc/sys/net/core/somaxconn" ]]; then
        echo 32768 > /proc/sys/net/core/somaxconn 2>/dev/null && {
            log_perf "Socket backlog optimized" "\"value\":32768"
            ((optimization_applied++))
        }
    fi
    
    if [[ -w "/proc/sys/net/core/netdev_max_backlog" ]]; then
        echo 16384 > /proc/sys/net/core/netdev_max_backlog 2>/dev/null && {
            log_perf "Network device backlog optimized" "\"value\":16384"
            ((optimization_applied++))
        }
    fi
    
    # File descriptor optimizations
    local current_soft_limit
    current_soft_limit=$(ulimit -Sn)
    local current_hard_limit
    current_hard_limit=$(ulimit -Hn)
    
    # Attempt to increase soft limit to match hard limit
    if [[ $current_soft_limit -lt $current_hard_limit ]]; then
        if ulimit -Sn "$current_hard_limit" 2>/dev/null; then
            log_perf "File descriptor soft limit increased" "\"from\":$current_soft_limit,\"to\":$current_hard_limit"
            ((optimization_applied++))
        fi
    fi
    
    # CPU affinity optimization (if taskset available)
    if command -v taskset >/dev/null 2>&1; then
        local cpu_count
        cpu_count=$(nproc)
        if [[ $cpu_count -gt 4 ]]; then
            # Reserve first CPU for system, use others for application
            local cpu_mask="1-$((cpu_count-1))"
            if taskset -cp "$cpu_mask" $$ >/dev/null 2>&1; then
                log_perf "CPU affinity optimized" "\"mask\":\"$cpu_mask\",\"cpus\":$cpu_count"
                ((optimization_applied++))
            fi
        fi
    fi
    
    # Report optimization results
    if [[ $optimization_applied -gt 0 ]]; then
        log_success "System performance optimizations applied" "\"count\":$optimization_applied"
    fi
    
    if [[ ${#performance_warnings[@]} -gt 0 ]]; then
        log_warn "Performance optimization warnings:"
        printf '  - %s\n' "${performance_warnings[@]}"
    fi
}

# Enhanced Python performance optimization
optimize_performance() {
    start_perf_timer "performance_optimization"
    log_startup "Initiating comprehensive performance optimization..."
    
    # Apply system-level optimizations
    optimize_system_performance
    
    # Python runtime optimizations
    log_info "Configuring Python runtime optimizations..."
    
    # Core Python settings
    export PYTHONHASHSEED=random
    export PYTHONUNBUFFERED=1
    export PYTHONDONTWRITEBYTECODE=1
    export PYTHONOPTIMIZE=2
    
    # Advanced asyncio configuration
    export PYTHONASYNCIODEBUG=0
    
    # Enable aggressive garbage collection for production
    case "${ENVIRONMENT}" in
        "production")
            export PYTHONGC="700,10,10"
            log_perf "Production GC thresholds set" "\"gen0\":700,\"gen1\":10,\"gen2\":10"
            ;;
        "staging")
            export PYTHONGC="500,8,8"
            log_perf "Staging GC thresholds set" "\"gen0\":500,\"gen1\":8,\"gen2\":8"
            ;;
        *)
            export PYTHONGC="0,0,0"  # Disable automatic GC in development
            log_perf "Development GC disabled" "\"automatic_gc\":false"
            ;;
    esac
    
    # High-performance event loop detection and configuration
    local event_loop_info
    if python3 -c "import uvloop; print('uvloop available')" >/dev/null 2>&1; then
        export ENABLE_UVLOOP=true
        event_loop_info="uvloop (high-performance)"
        log_success "uvloop detected - enabling high-performance event loop"
        
        # Additional uvloop optimizations
        export UV_THREADPOOL_SIZE="${UV_THREADPOOL_SIZE:-32}"
        log_perf "uvloop thread pool configured" "\"size\":${UV_THREADPOOL_SIZE}"
    else
        event_loop_info="asyncio (standard)"
        log_info "uvloop not available - using standard asyncio event loop"
        
        # Standard asyncio optimizations
        export ASYNCIO_DEFAULT_EXECUTOR_WORKERS="${ASYNCIO_DEFAULT_EXECUTOR_WORKERS:-16}"
    fi
    
    # Memory management optimization
    local total_memory_mb
    total_memory_mb=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo "1024")
    
    # Set Python memory limits based on available system memory
    if [[ $total_memory_mb -gt 4096 ]]; then
        export MALLOC_MMAP_THRESHOLD_=131072
        export MALLOC_MMAP_MAX_=65536
        log_perf "High-memory malloc optimizations" "\"mmap_threshold\":131072,\"mmap_max\":65536"
    fi
    
    # Configure Python path optimizations
    export PYTHONPATH="/app:${PYTHONPATH:-}"
    export PYTHONSTARTUP=""
    
    # Disable Python user site-packages for security and performance
    if [[ "${ENVIRONMENT}" == "production" ]]; then
        export PYTHONNOUSERSITE=1
        log_security "Python user site-packages disabled" "\"security\":true"
    fi
    
    # Configure profiling (if enabled)
    if [[ "${ENABLE_PROFILING:-false}" == "true" ]]; then
        export PYTHONPROFILEIMPORTTIME=1
        log_info "Python import profiling enabled"
    fi
    
    # Set up performance monitoring hooks
    if [[ "${ENABLE_PERFORMANCE_MONITORING:-true}" == "true" ]]; then
        export PERFORMANCE_MONITORING=true
        log_info "Performance monitoring hooks enabled"
    fi
    
    # Report current system performance baseline
    local current_load
    current_load=$(cut -d' ' -f1 < /proc/loadavg 2>/dev/null || echo "0")
    local available_memory_mb
    available_memory_mb=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo "0")
    
    local optimization_duration
    optimization_duration=$(end_perf_timer "performance_optimization")
    
    log_success "Performance optimization completed" \
        "\"duration_ms\":$optimization_duration,\"event_loop\":\"$event_loop_info\",\"baseline_load\":\"$current_load\",\"available_memory_mb\":$available_memory_mb"
    
    # Performance validation
    if (( $(echo "$current_load > $PERFORMANCE_BASELINE_CPU" | bc -l 2>/dev/null || echo 0) )); then
        log_warn "High system load detected" "\"current\":\"$current_load\",\"threshold\":$PERFORMANCE_BASELINE_CPU"
    fi
    
    if [[ $available_memory_mb -lt 256 ]]; then
        log_warn "Low available memory" "\"available_mb\":$available_memory_mb,\"threshold\":256"
    fi
}

# ======================================================================
# ADVANCED MONITORING AND OBSERVABILITY STACK
# ======================================================================

# Enhanced monitoring with multi-tier observability
setup_monitoring() {
    start_perf_timer "monitoring_setup"
    log_startup "Configuring advanced multi-tier monitoring and observability stack..."
    
    local monitoring_features=()
    
    # Tier 1: Metrics Collection (Prometheus)
    if [[ "${ENABLE_METRICS:-true}" == "true" ]]; then
        setup_prometheus_metrics
        monitoring_features+=("prometheus")
    fi
    
    # Tier 2: Distributed Tracing
    if [[ "${ENABLE_TRACING:-false}" == "true" ]]; then
        setup_distributed_tracing
        monitoring_features+=("tracing")
    fi
    
    # Tier 3: Health Monitoring
    if [[ "${ENABLE_HEALTH_MONITORING:-true}" == "true" ]]; then
        setup_health_monitoring
        monitoring_features+=("health_monitoring")
    fi
    
    # Tier 4: Performance Profiling
    if [[ "${ENABLE_PROFILING:-false}" == "true" ]]; then
        setup_performance_profiling
        monitoring_features+=("profiling")
    fi
    
    # Tier 5: Security Monitoring
    if [[ "${ENABLE_SECURITY_MONITORING:-true}" == "true" ]]; then
        setup_security_monitoring
        monitoring_features+=("security")
    fi
    
    local monitoring_duration
    monitoring_duration=$(end_perf_timer "monitoring_setup")
    
    log_success "Advanced monitoring stack configured" \
        "\"duration_ms\":$monitoring_duration,\"features\":[$(IFS=','; printf '\"%s\"' "${monitoring_features[*]}")],\"count\":${#monitoring_features[@]}"
}

# Prometheus metrics configuration
setup_prometheus_metrics() {
    log_info "Configuring Prometheus metrics collection..."
    
    export PROMETHEUS_MULTIPROC_DIR="/tmp/prometheus_multiproc_dir"
    mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
    chmod 755 "$PROMETHEUS_MULTIPROC_DIR"
    
    # Clean up any existing metrics
    find "$PROMETHEUS_MULTIPROC_DIR" -name "*.db" -delete 2>/dev/null || true
    
    # Configure custom metrics
    export PROMETHEUS_METRICS_PORT="${METRICS_PORT:-9090}"
    export ENABLE_CUSTOM_METRICS=true
    
    # Set up metrics collection intervals
    export METRICS_COLLECTION_INTERVAL="${METRICS_COLLECTION_INTERVAL:-15}"
    
    log_success "Prometheus metrics configured" \
        "\"multiproc_dir\":\"$PROMETHEUS_MULTIPROC_DIR\",\"port\":$PROMETHEUS_METRICS_PORT,\"interval\":${METRICS_COLLECTION_INTERVAL}s"
}

# Distributed tracing setup
setup_distributed_tracing() {
    log_info "Configuring distributed tracing..."
    
    export OTEL_SERVICE_NAME="mcp-crypto-trading"
    export OTEL_SERVICE_VERSION="${APP_VERSION:-2.0.0}"
    export OTEL_RESOURCE_ATTRIBUTES="environment=${ENVIRONMENT},service.instance.id=$(hostname),deployment.environment=${ENVIRONMENT}"
    
    # Configure tracing endpoints
    if [[ -n "${JAEGER_ENDPOINT:-}" ]]; then
        export OTEL_TRACES_EXPORTER="jaeger"
        export OTEL_EXPORTER_JAEGER_ENDPOINT="$JAEGER_ENDPOINT"
        log_info "Jaeger tracing endpoint configured" "\"endpoint\":\"$JAEGER_ENDPOINT\""
    elif [[ -n "${OTEL_ENDPOINT:-}" ]]; then
        export OTEL_TRACES_EXPORTER="otlp"
        export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="$OTEL_ENDPOINT"
        log_info "OTLP tracing endpoint configured" "\"endpoint\":\"$OTEL_ENDPOINT\""
    fi
    
    # Configure sampling
    export OTEL_TRACES_SAMPLER="${OTEL_TRACES_SAMPLER:-traceidratio}"
    export OTEL_TRACES_SAMPLER_ARG="${TRACE_SAMPLE_RATE:-0.1}"
    
    log_success "Distributed tracing configured" "\"sampler\":\"$OTEL_TRACES_SAMPLER\",\"sample_rate\":$OTEL_TRACES_SAMPLER_ARG"
}

# Enhanced health monitoring
setup_health_monitoring() {
    log_info "Setting up comprehensive health monitoring..."
    
    # Health check configuration
    export HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-30}"
    export HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-10}"
    export HEALTH_CHECK_RETRIES="${HEALTH_CHECK_RETRIES:-3}"
    
    # Start multi-tier health monitoring
    start_system_health_monitor &
    local system_monitor_pid=$!
    
    start_application_health_monitor &
    local app_monitor_pid=$!
    
    start_resource_monitor &
    local resource_monitor_pid=$!
    
    log_success "Health monitoring started" \
        "\"system_monitor_pid\":$system_monitor_pid,\"app_monitor_pid\":$app_monitor_pid,\"resource_monitor_pid\":$resource_monitor_pid,\"interval\":${HEALTH_CHECK_INTERVAL}s"
}

# Performance profiling setup
setup_performance_profiling() {
    log_info "Configuring performance profiling..."
    
    # Create profiling directory
    local profile_dir="/app/profiles"
    mkdir -p "$profile_dir"
    
    export PROFILE_DIR="$profile_dir"
    export ENABLE_MEMORY_PROFILING="${ENABLE_MEMORY_PROFILING:-true}"
    export ENABLE_CPU_PROFILING="${ENABLE_CPU_PROFILING:-true}"
    export PROFILE_SAMPLE_RATE="${PROFILE_SAMPLE_RATE:-0.01}"
    
    log_success "Performance profiling configured" \
        "\"profile_dir\":\"$profile_dir\",\"memory_profiling\":$ENABLE_MEMORY_PROFILING,\"cpu_profiling\":$ENABLE_CPU_PROFILING"
}

# Security monitoring setup
setup_security_monitoring() {
    log_security "Configuring security monitoring..."
    
    export SECURITY_LOG_LEVEL="${SECURITY_LOG_LEVEL:-WARNING}"
    export ENABLE_AUDIT_LOGGING="${ENABLE_AUDIT_LOGGING:-true}"
    export ENABLE_INTRUSION_DETECTION="${ENABLE_INTRUSION_DETECTION:-false}"
    
    # Start security monitoring
    if [[ "${ENABLE_INTRUSION_DETECTION}" == "true" ]]; then
        start_intrusion_monitor &
        local intrusion_monitor_pid=$!
        log_security "Intrusion detection started" "\"pid\":$intrusion_monitor_pid"
    fi
    
    log_success "Security monitoring configured" "\"audit_logging\":$ENABLE_AUDIT_LOGGING,\"intrusion_detection\":$ENABLE_INTRUSION_DETECTION"
}

# System health monitor
start_system_health_monitor() {
    local monitor_name="system_health"
    
    while [[ "${CLEANUP_IN_PROGRESS:-false}" != "true" ]]; do
        sleep "$HEALTH_CHECK_INTERVAL"
        
        # CPU monitoring
        local load_avg
        load_avg=$(cut -d' ' -f1 < /proc/loadavg 2>/dev/null || echo "0")
        
        if (( $(echo "$load_avg > $CPU_THRESHOLD_PERCENT" | bc -l 2>/dev/null || echo 0) )); then
            log_warn "High system load detected" "\"load\":\"$load_avg\",\"threshold\":$CPU_THRESHOLD_PERCENT"
        fi
        
        # Memory monitoring
        if [[ -r "/proc/meminfo" ]]; then
            local mem_available
            mem_available=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
            local mem_total
            mem_total=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
            local mem_usage_percent=$(( (mem_total - mem_available) * 100 / mem_total ))
            
            if [[ $mem_usage_percent -gt 90 ]]; then
                log_warn "Critical memory usage" "\"usage_percent\":$mem_usage_percent,\"available_mb\":$((mem_available/1024))"
            fi
        fi
        
        log_debug "System health check completed" "\"monitor\":\"$monitor_name\",\"load\":\"$load_avg\""
    done
}

# Application health monitor
start_application_health_monitor() {
    while [[ "${CLEANUP_IN_PROGRESS:-false}" != "true" ]]; do
        sleep "$((HEALTH_CHECK_INTERVAL * 2))"
        
        # Application-specific health checks
        if [[ -f "/app/health_check.py" ]]; then
            if ! python3 /app/health_check.py >/dev/null 2>&1; then
                log_warn "Application health check failed"
            else
                log_debug "Application health check passed"
            fi
        fi
        
        # Check application process health
        local process_count
        process_count=$(pgrep -f "mcp_crypto" | wc -l)
        
        if [[ $process_count -eq 0 ]]; then
            log_error "No application processes detected"
        fi
    done
}

# Resource monitor
start_resource_monitor() {
    while [[ "${CLEANUP_IN_PROGRESS:-false}" != "true" ]]; do
        sleep "$((HEALTH_CHECK_INTERVAL * 3))"
        
        # Disk space monitoring
        local disk_usage
        disk_usage=$(df /app | awk 'NR==2 {print $5}' | sed 's/%//')
        
        if [[ $disk_usage -gt $DISK_THRESHOLD_PERCENT ]]; then
            log_warn "High disk usage detected" "\"usage_percent\":$disk_usage,\"threshold\":$DISK_THRESHOLD_PERCENT"
        fi
        
        # File descriptor monitoring
        local fd_count
        fd_count=$(lsof -p $$ 2>/dev/null | wc -l || echo "0")
        local fd_limit
        fd_limit=$(ulimit -n)
        
        if [[ $fd_count -gt $((fd_limit * 80 / 100)) ]]; then
            log_warn "High file descriptor usage" "\"count\":$fd_count,\"limit\":$fd_limit"
        fi
        
        log_debug "Resource monitoring completed" "\"disk_usage\":$disk_usage,\"fd_count\":$fd_count"
    done
}

# Intrusion detection monitor
start_intrusion_monitor() {
    while [[ "${CLEANUP_IN_PROGRESS:-false}" != "true" ]]; do
        sleep 300  # Check every 5 minutes
        
        # Check for suspicious network connections
        local connection_count
        connection_count=$(ss -tuln 2>/dev/null | wc -l)
        
        if [[ $connection_count -gt 200 ]]; then
            log_security "High network connection count" "\"count\":$connection_count"
        fi
        
        # Check for unusual process activity
        local process_count
        process_count=$(ps aux | wc -l)
        
        if [[ $process_count -gt 500 ]]; then
            log_security "High process count detected" "\"count\":$process_count"
        fi
    done
}

# ======================================================================
# INTELLIGENT SERVER MODE SELECTION WITH PERFORMANCE ANALYSIS
# ======================================================================

# Advanced server capability detection
detect_server_capabilities() {
    local -A server_capabilities
    
    # Check uvicorn availability and version
    if command -v uvicorn >/dev/null 2>&1; then
        local uvicorn_version
        uvicorn_version=$(uvicorn --version 2>&1 | head -1 | awk '{print $2}' || echo "unknown")
        server_capabilities["uvicorn"]="available:$uvicorn_version"
        
        # Check for uvicorn workers support
        if uvicorn --help 2>&1 | grep -q "\-\-workers"; then
            server_capabilities["uvicorn_workers"]="supported"
        fi
    else
        server_capabilities["uvicorn"]="unavailable"
    fi
    
    # Check gunicorn availability and version
    if command -v gunicorn >/dev/null 2>&1; then
        local gunicorn_version
        gunicorn_version=$(gunicorn --version 2>&1 | head -1 | awk '{print $2}' || echo "unknown")
        server_capabilities["gunicorn"]="available:$gunicorn_version"
    else
        server_capabilities["gunicorn"]="unavailable"
    fi
    
    # Check hypercorn availability (modern ASGI server)
    if command -v hypercorn >/dev/null 2>&1; then
        local hypercorn_version
        hypercorn_version=$(hypercorn --version 2>&1 | awk '{print $2}' || echo "unknown")
        server_capabilities["hypercorn"]="available:$hypercorn_version"
    else
        server_capabilities["hypercorn"]="unavailable"
    fi
    
    # Check for HTTP/3 support (if quart available)
    if python3 -c "import quart" >/dev/null 2>&1; then
        server_capabilities["http3"]="supported"
    else
        server_capabilities["http3"]="unavailable"
    fi
    
    # Return capabilities as JSON-like string
    local caps_json="{}"
    for key in "${!server_capabilities[@]}"; do
        caps_json=$(echo "$caps_json" | sed 's/}/,"'$key'":"'${server_capabilities[$key]}'"}/')
    done
    caps_json=$(echo "$caps_json" | sed 's/^{,/{/')
    
    echo "$caps_json"
}

# Performance-based server selection
determine_optimal_server() {
    local cpu_count
    cpu_count=$(nproc)
    local memory_mb
    memory_mb=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo "1024")
    local environment="${ENVIRONMENT}"
    
    log_perf "System specifications for server selection" \
        "\"cpu_cores\":$cpu_count,\"memory_mb\":$memory_mb,\"environment\":\"$environment\""
    
    # Decision matrix based on resources and environment
    case "$environment" in
        "production")
            if [[ $cpu_count -ge 4 ]] && [[ $memory_mb -ge 2048 ]]; then
                echo "gunicorn"  # Best for high-load production
            elif command -v uvicorn >/dev/null 2>&1; then
                echo "uvicorn"   # Good performance, lighter weight
            else
                echo "direct"    # Fallback
            fi
            ;;
        "staging")
            if command -v uvicorn >/dev/null 2>&1; then
                echo "uvicorn"   # Balanced performance for staging
            elif command -v gunicorn >/dev/null 2>&1; then
                echo "gunicorn"
            else
                echo "direct"
            fi
            ;;
        *)
            echo "direct"      # Development - simplest setup
            ;;
    esac
}

# Enhanced server mode selection with intelligent defaults
determine_server_mode() {
    start_perf_timer "server_selection"
    log_startup "Performing intelligent server configuration selection..."
    
    # Get server capabilities
    local capabilities
    capabilities=$(detect_server_capabilities)
    log_info "Server capabilities detected" "\"capabilities\":$capabilities"
    
    # Determine server mode
    local server_mode="${SERVER_MODE:-auto}"
    local selected_server
    
    case "$server_mode" in
        "uvicorn")
            if [[ "$capabilities" =~ "uvicorn":"available" ]]; then
                selected_server="uvicorn"
            else
                log_error "Uvicorn requested but not available"
                exit 1
            fi
            ;;
        "gunicorn")
            if [[ "$capabilities" =~ "gunicorn":"available" ]]; then
                selected_server="gunicorn"
            else
                log_error "Gunicorn requested but not available"
                exit 1
            fi
            ;;
        "hypercorn")
            if [[ "$capabilities" =~ "hypercorn":"available" ]]; then
                selected_server="hypercorn"
            else
                log_error "Hypercorn requested but not available"
                exit 1
            fi
            ;;
        "direct")
            selected_server="direct"
            ;;
        "auto"|*)
            selected_server=$(determine_optimal_server)
            log_info "Auto-selected server mode" "\"selected\":\"$selected_server\",\"reason\":\"performance_optimization\""
            ;;
    esac
    
    local selection_duration
    selection_duration=$(end_perf_timer "server_selection")
    
    log_success "Server mode selected" "\"mode\":\"$selected_server\",\"duration_ms\":$selection_duration"
    
    # Start the selected server
    case "$selected_server" in
        "uvicorn")
            start_with_uvicorn
            ;;
        "gunicorn")
            start_with_gunicorn
            ;;
        "hypercorn")
            start_with_hypercorn
            ;;
        "direct")
            start_direct_python
            ;;
        *)
            log_error "Unknown server mode: $selected_server"
            exit 1
            ;;
    esac
}

# ======================================================================
# ENHANCED SERVER STARTUP METHODS WITH ADVANCED CONFIGURATIONS
# ======================================================================

# Uvicorn startup with performance tuning
start_with_uvicorn() {
    log_startup "Launching MCP Crypto Server with optimized Uvicorn configuration..."
    
    local uvicorn_args=(
        "--host" "$DEFAULT_HOST"
        "--port" "$DEFAULT_PORT"
        "--log-level" "${DEFAULT_LOG_LEVEL,,}"
        "--access-log"
        "--no-use-colors"
    )
    
    # Intelligent worker configuration based on system resources
    local optimal_workers
    local cpu_count
    cpu_count=$(nproc)
    
    case "${ENVIRONMENT}" in
        "production")
            # Conservative approach for production stability
            optimal_workers=$((cpu_count > 8 ? 8 : cpu_count))
            uvicorn_args+=("--workers" "$optimal_workers")
            uvicorn_args+=("--worker-class" "uvicorn.workers.UvicornWorker")
            ;;
        "staging")
            # Balanced approach for staging
            optimal_workers=$((cpu_count > 4 ? cpu_count / 2 : cpu_count))
            uvicorn_args+=("--workers" "$optimal_workers")
            ;;
        *)
            # Single worker for development
            uvicorn_args+=("--workers" "1")
            uvicorn_args+=("--reload")
            uvicorn_args+=("--reload-dir" "/app")
            ;;
    esac
    
    # Advanced performance configurations
    uvicorn_args+=(
        "--loop" "${EVENT_LOOP:-auto}"
        "--http" "${HTTP_PROTOCOL:-auto}"
        "--ws" "${WS_PROTOCOL:-auto}"
        "--lifespan" "on"
        "--server-header"
        "--date-header"
    )
    
    # Production-specific optimizations
    if [[ "${ENVIRONMENT}" == "production" ]]; then
        uvicorn_args+=(
            "--max-requests" "$DEFAULT_MAX_REQUESTS"
            "--max-requests-jitter" "$DEFAULT_MAX_REQUESTS_JITTER"
            "--keepalive" "$DEFAULT_KEEPALIVE"
            "--limit-concurrency" "${CONCURRENCY_LIMIT:-1000}"
            "--limit-max-requests" "${MAX_REQUESTS_LIMIT:-10000}"
        )
        
        # Enable SSL if certificates are available
        if [[ -f "${SSL_CERT_FILE:-}" ]] && [[ -f "${SSL_KEY_FILE:-}" ]]; then
            uvicorn_args+=("--ssl-certfile" "$SSL_CERT_FILE")
            uvicorn_args+=("--ssl-keyfile" "$SSL_KEY_FILE")
            log_security "SSL/TLS enabled" "\"cert_file\":\"$SSL_CERT_FILE\""
        fi
    fi
    
    log_info "Uvicorn configuration optimized" "\"workers\":$optimal_workers,\"environment\":\"${ENVIRONMENT}\""
    log_debug "Full uvicorn arguments" "\\\"args\\\":[$(printf '\\\"%s\\\",' "${uvicorn_args[@]}" | sed 's/,$//')]]"
    
    # Find the main application module
    local app_module
    if [[ -f "/app/mcp_crypto_server.py" ]]; then
        app_module="mcp_crypto_server:app"
    elif [[ -f "/app/mcp_crypto_main.py" ]]; then
        app_module="mcp_crypto_main:app"
    else
        log_error "No suitable application module found"
        exit 1
    fi
    
    log_startup "Executing uvicorn with module: $app_module"
    exec uvicorn "${uvicorn_args[@]}" "$app_module"
}

# Gunicorn startup with advanced worker management
start_with_gunicorn() {
    log_startup "Launching MCP Crypto Server with optimized Gunicorn configuration..."
    
    local cpu_count
    cpu_count=$(nproc)
    local memory_mb
    memory_mb=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo || echo "1024")
    
    # Intelligent worker calculation
    local optimal_workers
    case "${ENVIRONMENT}" in
        "production")
            # Formula: (2 x CPU cores) + 1, capped at available memory
            optimal_workers=$(((cpu_count * 2) + 1))
            # Limit based on memory (assume 128MB per worker)
            local max_workers_by_memory=$((memory_mb / 128))
            optimal_workers=$((optimal_workers > max_workers_by_memory ? max_workers_by_memory : optimal_workers))
            ;;
        *)
            optimal_workers=$((cpu_count > 4 ? 4 : cpu_count))
            ;;
    esac
    
    local gunicorn_args=(
        "--bind" "${DEFAULT_HOST}:${DEFAULT_PORT}"
        "--workers" "$optimal_workers"
        "--worker-class" "uvicorn.workers.UvicornWorker"
        "--timeout" "$DEFAULT_TIMEOUT"
        "--keepalive" "$DEFAULT_KEEPALIVE"
        "--max-requests" "$DEFAULT_MAX_REQUESTS"
        "--max-requests-jitter" "$DEFAULT_MAX_REQUESTS_JITTER"
        "--preload-app"
        "--log-level" "${DEFAULT_LOG_LEVEL,,}"
        "--access-logfile" "-"
        "--error-logfile" "-"
        "--access-logformat" '%(h)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
    )
    
    # Advanced worker configurations
    gunicorn_args+=(
        "--worker-connections" "${WORKER_CONNECTIONS:-1000}"
        "--worker-tmp-dir" "/tmp"
        "--enable-stdio-inheritance"
    )
    
    # Production-specific settings
    if [[ "${ENVIRONMENT}" == "production" ]]; then
        gunicorn_args+=(
            "--graceful-timeout" "30"
            "--reload-extra-file" "/app/mcp_crypto_server.py"
            "--capture-output"
        )
        
        # Memory monitoring for workers
        gunicorn_args+=("--max-requests-jitter" "$((DEFAULT_MAX_REQUESTS_JITTER * 2))")
    else
        gunicorn_args+=("--reload")
    fi
    
    log_info "Gunicorn configuration optimized" \
        "\"workers\":$optimal_workers,\"memory_mb\":$memory_mb,\"cpu_cores\":$cpu_count"
    
    # Find the main application module
    local app_module
    if [[ -f "/app/mcp_crypto_server.py" ]]; then
        app_module="mcp_crypto_server:app"
    elif [[ -f "/app/mcp_crypto_main.py" ]]; then
        app_module="mcp_crypto_main:app"
    else
        log_error "No suitable application module found"
        exit 1
    fi
    
    log_startup "Executing gunicorn with module: $app_module"
    exec gunicorn "${gunicorn_args[@]}" "$app_module"
}

# Hypercorn startup (modern ASGI server with HTTP/3 support)
start_with_hypercorn() {
    log_startup "Launching MCP Crypto Server with Hypercorn (HTTP/3 capable)..."
    
    local hypercorn_args=(
        "--bind" "${DEFAULT_HOST}:${DEFAULT_PORT}"
        "--workers" "$DEFAULT_WORKERS"
        "--log-level" "${DEFAULT_LOG_LEVEL,,}"
        "--access-log" "-"
        "--error-log" "-"
        "--keep-alive" "$DEFAULT_KEEPALIVE"
    )
    
    # HTTP/3 support if enabled
    if [[ "${ENABLE_HTTP3:-false}" == "true" ]] && [[ "${ENVIRONMENT}" == "production" ]]; then
        hypercorn_args+=("--quic-bind" "${DEFAULT_HOST}:$((DEFAULT_PORT + 1000))")
        log_info "HTTP/3 (QUIC) enabled" "\"quic_port\":$((DEFAULT_PORT + 1000))"
    fi
    
    # Find the main application module
    local app_module
    if [[ -f "/app/mcp_crypto_server.py" ]]; then
        app_module="mcp_crypto_server:app"
    else
        log_error "No suitable application module found for Hypercorn"
        exit 1
    fi
    
    log_startup "Executing hypercorn with module: $app_module"
    exec hypercorn "${hypercorn_args[@]}" "$app_module"
}

# Direct Python execution with enhanced configuration
start_direct_python() {
    log_startup "Launching MCP Crypto Server with optimized direct Python execution..."
    
    # Enhanced Python optimizations for direct execution
    export PYTHONOPTIMIZE=1
    export PYTHONBUFFERED=0
    
    # Development-specific settings
    if [[ "${ENVIRONMENT}" == "development" ]]; then
        export PYTHONDEBUG=1
        export PYTHONVERBOSE=1 if [[ "${VERBOSE:-false}" == "true" ]]
    fi
    
    # Find the main application file
    local app_file
    if [[ -f "/app/mcp_crypto_server.py" ]]; then
        app_file="mcp_crypto_server.py"
    elif [[ -f "/app/mcp_crypto_main.py" ]]; then
        app_file="mcp_crypto_main.py"
    else
        log_error "No main application file found"
        exit 1
    fi
    
    log_info "Direct Python execution configuration" \
        "\"file\":\"$app_file\",\"host\":\"$DEFAULT_HOST\",\"port\":$DEFAULT_PORT,\"environment\":\"${ENVIRONMENT}\""
    
    # Set application-specific environment variables
    export MCP_SERVER_HOST="$DEFAULT_HOST"
    export MCP_SERVER_PORT="$DEFAULT_PORT"
    export MCP_LOG_LEVEL="$DEFAULT_LOG_LEVEL"
    
    log_startup "Executing Python application: $app_file"
    exec python3 "/app/$app_file"
}

# ======================================================================
# ENHANCED STARTUP BANNER WITH SYSTEM INFORMATION
# ======================================================================

# Dynamic system information collection
get_system_info() {
    local -A sys_info
    
    # Basic system information
    sys_info["hostname"]=$(hostname 2>/dev/null || echo "unknown")
    sys_info["kernel"]=$(uname -r 2>/dev/null || echo "unknown")
    sys_info["arch"]=$(uname -m 2>/dev/null || echo "unknown")
    sys_info["cpu_cores"]=$(nproc 2>/dev/null || echo "1")
    
    # Memory information
    if [[ -r "/proc/meminfo" ]]; then
        sys_info["total_memory_gb"]=$(awk '/MemTotal/ {printf "%.1f", $2/1024/1024}' /proc/meminfo)
        sys_info["available_memory_gb"]=$(awk '/MemAvailable/ {printf "%.1f", $2/1024/1024}' /proc/meminfo)
    else
        sys_info["total_memory_gb"]="unknown"
        sys_info["available_memory_gb"]="unknown"
    fi
    
    # Load average
    sys_info["load_avg"]=$(cut -d' ' -f1 < /proc/loadavg 2>/dev/null || echo "0.00")
    
    # Container detection
    if [[ -f "/.dockerenv" ]] || [[ -n "${KUBERNETES_SERVICE_HOST:-}" ]]; then
        sys_info["container"]="true"
        if [[ -n "${KUBERNETES_SERVICE_HOST:-}" ]]; then
            sys_info["orchestrator"]="kubernetes"
        else
            sys_info["orchestrator"]="docker"
        fi
    else
        sys_info["container"]="false"
        sys_info["orchestrator"]="none"
    fi
    
    # Return as JSON-like string for logging
    printf '{"hostname":"%s","kernel":"%s","arch":"%s","cpu_cores":%s,"total_memory_gb":%s,"available_memory_gb":%s,"load_avg":"%s","container":%s,"orchestrator":"%s"}' \
        "${sys_info[hostname]}" "${sys_info[kernel]}" "${sys_info[arch]}" "${sys_info[cpu_cores]}" \
        "${sys_info[total_memory_gb]}" "${sys_info[available_memory_gb]}" "${sys_info[load_avg]}" \
        "${sys_info[container]}" "${sys_info[orchestrator]}"
}

# Enhanced startup banner with real-time system information
display_startup_banner() {
    local sys_info
    sys_info=$(get_system_info)
    
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

    echo -e "${GREEN}                    🚀 Ultra-High-Performance Cryptocurrency Trading Server 🚀${NC}"
    echo -e "${BLUE}                                2025+ Enhanced Edition with Advanced Security${NC}"
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC} ${PURPLE}DEPLOYMENT INFORMATION${NC}                                                            ${CYAN}║${NC}"
    echo -e "${CYAN}╠═══════════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC} Environment: ${ENVIRONMENT^^} | Version: ${APP_VERSION:-2.0.0} | PID: $$ ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} Endpoint: ${DEFAULT_HOST}:${DEFAULT_PORT} | Workers: ${DEFAULT_WORKERS} | Log Level: ${DEFAULT_LOG_LEVEL} ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} Started: $(date -u '+%Y-%m-%d %H:%M:%S UTC') | User: $(whoami) ${CYAN}║${NC}"
    echo -e "${CYAN}╠═══════════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC} ${PURPLE}SYSTEM SPECIFICATIONS${NC}                                                            ${CYAN}║${NC}"
    echo -e "${CYAN}╠═══════════════════════════════════════════════════════════════════════════════════╣${NC}"
    
    # Parse and display system information
    local hostname arch cpu_cores total_mem available_mem load_avg container orchestrator
    hostname=$(echo "$sys_info" | grep -o '"hostname":"[^"]*"' | cut -d'"' -f4)
    arch=$(echo "$sys_info" | grep -o '"arch":"[^"]*"' | cut -d'"' -f4)
    cpu_cores=$(echo "$sys_info" | grep -o '"cpu_cores":[0-9]*' | cut -d':' -f2)
    total_mem=$(echo "$sys_info" | grep -o '"total_memory_gb":[0-9.]*' | cut -d':' -f2)
    available_mem=$(echo "$sys_info" | grep -o '"available_memory_gb":[0-9.]*' | cut -d':' -f2)
    load_avg=$(echo "$sys_info" | grep -o '"load_avg":"[^"]*"' | cut -d'"' -f4)
    container=$(echo "$sys_info" | grep -o '"container":[^,}]*' | cut -d':' -f2)
    orchestrator=$(echo "$sys_info" | grep -o '"orchestrator":"[^"]*"' | cut -d'"' -f4)
    
    echo -e "${CYAN}║${NC} Host: $hostname | Architecture: $arch | CPU Cores: $cpu_cores ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} Memory: ${available_mem}GB Available / ${total_mem}GB Total | Load: $load_avg ${CYAN}║${NC}"
    
    if [[ "$container" == "true" ]]; then
        echo -e "${CYAN}║${NC} Container: ${GREEN}Yes${NC} | Orchestrator: ${orchestrator^} ${CYAN}║${NC}"
    else
        echo -e "${CYAN}║${NC} Container: ${YELLOW}No${NC} | Runtime: Native Linux ${CYAN}║${NC}"
    fi
    
    echo -e "${CYAN}╠═══════════════════════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC} ${PURPLE}ENHANCED FEATURES${NC}                                                               ${CYAN}║${NC}"
    echo -e "${CYAN}╠═══════════════════════════════════════════════════════════════════════════════════╣${NC}"
    
    local features=()
    [[ "${ENABLE_METRICS:-true}" == "true" ]] && features+=("Prometheus Metrics")
    [[ "${ENABLE_TRACING:-false}" == "true" ]] && features+=("Distributed Tracing")
    [[ "${ENABLE_HEALTH_MONITORING:-true}" == "true" ]] && features+=("Health Monitoring")
    [[ "${ENABLE_SECURITY_MONITORING:-true}" == "true" ]] && features+=("Security Monitoring")
    [[ "${ENABLE_UVLOOP:-false}" == "true" ]] && features+=("uvloop Event Loop")
    [[ "${ENABLE_JSON_LOGGING:-false}" == "true" ]] && features+=("Structured Logging")
    
    echo -e "${CYAN}║${NC} Active: $(IFS=', '; echo "${features[*]}") ${CYAN}║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Log system information for monitoring
    log_info "System information collected" "$sys_info"
}

# ======================================================================
# ENHANCED MAIN EXECUTION WITH COMPREHENSIVE INITIALIZATION
# ======================================================================

# Final readiness validation
validate_final_readiness() {
    log_startup "Performing final readiness validation..."
    
    local readiness_checks=()
    local readiness_passed=0
    local readiness_failed=0
    
    # Check 1: Application files accessible
    if [[ -f "/app/mcp_crypto_server.py" ]] || [[ -f "/app/mcp_crypto_main.py" ]]; then
        readiness_checks+=("✓ Application files accessible")
        ((readiness_passed++))
    else
        readiness_checks+=("✗ Application files missing")
        ((readiness_failed++))
    fi
    
    # Check 2: Python environment ready
    if python3 -c "import asyncio, aiohttp" >/dev/null 2>&1; then
        readiness_checks+=("✓ Python environment ready")
        ((readiness_passed++))
    else
        readiness_checks+=("✗ Python environment incomplete")
        ((readiness_failed++))
    fi
    
    # Check 3: Network port available
    if check_port_availability "$DEFAULT_PORT" "final-check" >/dev/null 2>&1; then
        readiness_checks+=("✓ Network port $DEFAULT_PORT available")
        ((readiness_passed++))
    else
        readiness_checks+=("✗ Network port $DEFAULT_PORT unavailable")
        ((readiness_failed++))
    fi
    
    # Check 4: System resources adequate
    local available_memory_mb
    available_memory_mb=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo "0")
    if [[ $available_memory_mb -gt 256 ]]; then
        readiness_checks+=("✓ System resources adequate (${available_memory_mb}MB available)")
        ((readiness_passed++))
    else
        readiness_checks+=("✗ Insufficient system resources (${available_memory_mb}MB available)")
        ((readiness_failed++))
    fi
    
    # Report readiness status
    log_info "Readiness validation results:"
    printf '  %s\n' "${readiness_checks[@]}"
    
    if [[ $readiness_failed -gt 0 ]]; then
        log_error "Readiness validation failed" "\"passed\":$readiness_passed,\"failed\":$readiness_failed"
        return 1
    else
        log_success "All readiness checks passed" "\"total\":$readiness_passed"
        return 0
    fi
}

# Comprehensive main execution flow
main() {
    start_perf_timer "total_startup"
    
    # Phase 0: Display enhanced startup banner
    display_startup_banner
    
    log_startup "Initiating MCP Crypto Trading Server with 2025+ enhanced features..."
    log_info "Startup initiated" "\"pid\":$$,\"user\":\"$(whoami)\",\"cwd\":\"$(pwd)\",\"bash_version\":\"${BASH_VERSION}\""
    
    # Phase 1: Critical pre-flight validation
    log_startup "Phase 1/5: Critical system pre-flight checks"
    start_perf_timer "preflight"
    if ! perform_preflight_checks; then
        log_error "Pre-flight checks failed - aborting startup"
        exit 1
    fi
    local preflight_duration
    preflight_duration=$(end_perf_timer "preflight")
    
    # Phase 2: Database connectivity validation
    log_startup "Phase 2/5: Database connectivity validation"
    start_perf_timer "database_validation"
    if ! validate_database_connections; then
        log_error "Database validation failed - aborting startup"
        exit 1
    fi
    local db_validation_duration
    db_validation_duration=$(end_perf_timer "database_validation")
    
    # Phase 3: Performance optimization
    log_startup "Phase 3/5: Performance optimization and tuning"
    start_perf_timer "optimization"
    optimize_performance
    local optimization_duration
    optimization_duration=$(end_perf_timer "optimization")
    
    # Phase 4: Monitoring and observability setup
    log_startup "Phase 4/5: Advanced monitoring and observability configuration"
    start_perf_timer "monitoring"
    setup_monitoring
    local monitoring_duration
    monitoring_duration=$(end_perf_timer "monitoring")
    
    # Phase 5: Final readiness validation
    log_startup "Phase 5/5: Final readiness validation"
    start_perf_timer "readiness"
    if ! validate_final_readiness; then
        log_error "Final readiness validation failed - aborting startup"
        exit 1
    fi
    local readiness_duration
    readiness_duration=$(end_perf_timer "readiness")
    
    # Calculate total initialization time
    local total_startup_duration
    total_startup_duration=$(end_perf_timer "total_startup")
    
    # Comprehensive startup completion report
    log_success "🎉 MCP Crypto Trading Server initialization completed successfully!" \
        "\"total_duration_ms\":$total_startup_duration"
    
    log_perf "Initialization phase breakdown" \
        "\"preflight_ms\":$preflight_duration,\"database_ms\":$db_validation_duration,\"optimization_ms\":$optimization_duration,\"monitoring_ms\":$monitoring_duration,\"readiness_ms\":$readiness_duration"
    
    # Security audit log
    log_security "Production server startup authorized" \
        "\"environment\":\"${ENVIRONMENT}\",\"user\":\"$(whoami)\",\"host\":\"$(hostname)\",\"validation_passed\":true"
    
    # Launch sequence
    echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                   🚀 LAUNCH SEQUENCE INITIATED 🚀          ║${NC}"
    echo -e "${GREEN}║                                                           ║${NC}"
    echo -e "${GREEN}║  All systems validated and optimized for production      ║${NC}"
    echo -e "${GREEN}║  Transferring control to high-performance server...      ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}\n"
    
    log_startup "🚀 Launching MCP Crypto Trading Server with optimal configuration..."
    
    # Hand control to the server
    determine_server_mode
}

# Script entry point with argument validation
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Validate script execution environment
    if [[ $EUID -eq 0 ]] && [[ "${ALLOW_ROOT:-false}" != "true" ]]; then
        echo "ERROR: This script should not be run as root (set ALLOW_ROOT=true to override)" >&2
        exit 1
    fi
    
    # Validate required environment
    if [[ -z "${ENVIRONMENT:-}" ]]; then
        echo "ERROR: ENVIRONMENT variable must be set (production, staging, development)" >&2
        exit 1
    fi
    
    # Execute main function
    main "$@"
fi
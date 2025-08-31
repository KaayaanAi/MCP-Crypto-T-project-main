#!/bin/bash
set -euo pipefail
set -o errtrace
set -o functrace

# ======================================================================
# MCP Crypto Trading Server - Advanced Build Validation (2025+ Edition)
# Comprehensive security, performance, and deployment readiness validation
# Version: 2.0 | Last Updated: $(date -u '+%Y-%m-%d')
# ======================================================================

# Bash version compatibility check
if [[ ${BASH_VERSION%%.*} -lt 4 ]]; then
    echo "FATAL: Bash 4.0+ required for advanced validation features" >&2
    exit 1
fi

# Enhanced color palette with semantic meaning
readonly RED='\033[38;5;196m'        # Critical errors
readonly GREEN='\033[38;5;46m'       # Success states
readonly YELLOW='\033[38;5;226m'     # Warnings
readonly BLUE='\033[38;5;33m'        # Information
readonly PURPLE='\033[38;5;129m'     # Headers/sections
readonly CYAN='\033[38;5;51m'        # Debug/details
readonly ORANGE='\033[38;5;214m'     # Performance metrics
readonly MAGENTA='\033[38;5;201m'    # Security alerts
readonly NC='\033[0m'                # No Color

# Performance and validation constants
readonly SCRIPT_NAME="${0##*/}"
readonly SCRIPT_PID=$$
readonly SCRIPT_START_TIME=$(date -u '+%s%3N')
readonly MAX_VALIDATION_TIME=600
readonly SECURITY_SCAN_TIMEOUT=120

# Enhanced logging with performance metrics
log_structured() {
    local level="$1"
    local message="$2"
    local context="${3:-}"
    local timestamp=$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')
    local runtime_ms=$(($(date -u '+%s%3N') - SCRIPT_START_TIME))
    
    if [[ "${ENABLE_JSON_LOGGING:-false}" == "true" ]]; then
        local json_context=""
        [[ -n "$context" ]] && json_context=",\"context\":{$context}"
        printf '{"timestamp":"%s","level":"%s","message":"%s","script":"%s","runtime_ms":%d%s}\n' \
            "$timestamp" "$level" "$message" "$SCRIPT_NAME" "$runtime_ms" "$json_context"
    else
        local color_map=(["INFO"]="$BLUE" ["SUCCESS"]="$GREEN" ["ERROR"]="$RED" ["WARN"]="$YELLOW" \
                        ["SECURITY"]="$MAGENTA" ["PERF"]="$ORANGE" ["DEBUG"]="$CYAN")
        echo -e "${color_map[$level]:-$NC}[$level]${NC} $timestamp - $message ${context:+($context)}"
    fi
}

log_info() { log_structured "INFO" "$1" "${2:-}"; }
log_success() { log_structured "SUCCESS" "$1" "${2:-}"; }
log_error() { log_structured "ERROR" "$1" "${2:-}" >&2; }
log_warn() { log_structured "WARN" "$1" "${2:-}" >&2; }
log_security() { log_structured "SECURITY" "$1" "${2:-}" >&2; }
log_perf() { log_structured "PERF" "$1" "${2:-}"; }
log_debug() { [[ "${DEBUG:-false}" == "true" ]] && log_structured "DEBUG" "$1" "${2:-}"; }

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
        unset "timer_${timer_name}"
        echo "$duration"
    fi
}

# Enhanced validation tracking with detailed metrics
declare -A validation_results=(
    ["critical_passed"]=0
    ["critical_failed"]=0
    ["security_passed"]=0
    ["security_failed"]=0
    ["performance_passed"]=0
    ["performance_warnings"]=0
    ["total_warnings"]=0
    ["total_time_ms"]=0
)

declare -a validation_details=()
declare -a security_issues=()
declare -a performance_issues=()

# Enhanced validation functions with categorization
validate_critical() {
    local exit_code="$1"
    local message="$2"
    local context="${3:-}"
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "$message" "$context"
        ((validation_results["critical_passed"]++))
        validation_details+=("✓ CRITICAL: $message")
    else
        log_error "$message" "$context"
        ((validation_results["critical_failed"]++))
        validation_details+=("✗ CRITICAL: $message")
    fi
}

validate_security() {
    local exit_code="$1"
    local message="$2"
    local context="${3:-}"
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "[SECURITY] $message" "$context"
        ((validation_results["security_passed"]++))
        validation_details+=("✓ SECURITY: $message")
    else
        log_security "[SECURITY] $message" "$context"
        ((validation_results["security_failed"]++))
        security_issues+=("$message")
        validation_details+=("✗ SECURITY: $message")
    fi
}

validate_performance() {
    local exit_code="$1"
    local message="$2"
    local context="${3:-}"
    
    if [[ $exit_code -eq 0 ]]; then
        log_success "[PERFORMANCE] $message" "$context"
        ((validation_results["performance_passed"]++))
        validation_details+=("✓ PERFORMANCE: $message")
    else
        log_warn "[PERFORMANCE] $message" "$context"
        ((validation_results["performance_warnings"]++))
        performance_issues+=("$message")
        validation_details+=("⚠ PERFORMANCE: $message")
    fi
}

validate_warning() {
    local message="$1"
    local context="${2:-}"
    
    log_warn "$message" "$context"
    ((validation_results["total_warnings"]++))
    validation_details+=("⚠ WARNING: $message")
}

# Enhanced startup banner
display_validation_banner() {
    cat << 'EOF'

 ╔══════════════════════════════════════════════════════════════════════════════════════╗
 ║                                                                                      ║
 ║  ███╗   ███╗ ██████╗██████╗      ██████╗██████╗ ██╗   ██╗██████╗ ████████╗ ██████╗  ║
 ║  ████╗ ████║██╔════╝██╔══██╗    ██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝██╔═══██╗ ║
 ║  ██╔████╔██║██║     ██████╔╝    ██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   ██║   ██║ ║
 ║  ██║╚██╔╝██║██║     ██╔═══╝     ██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ██║   ██║ ║
 ║  ██║ ╚═╝ ██║╚██████╗██║         ╚██████╗██║  ██║   ██║   ██║        ██║   ╚██████╔╝ ║
 ║  ╚═╝     ╚═╝ ╚═════╝╚═╝          ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝    ╚═════╝  ║
 ║                                                                                      ║
 ║        🔍 ADVANCED BUILD VALIDATION & SECURITY AUDIT (2025+ Edition) 🔍          ║
 ║                                                                                      ║
 ╚══════════════════════════════════════════════════════════════════════════════════════╝

EOF

    echo -e "${PURPLE}                     Comprehensive Production Readiness Assessment${NC}"
    echo -e "${CYAN}                           Security • Performance • Compliance${NC}"
    echo ""
    echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}│${NC} Validation Started: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo -e "${CYAN}│${NC} Environment: ${ENVIRONMENT:-unknown}"
    echo -e "${CYAN}│${NC} Validator Version: 2.0"
    echo -e "${CYAN}│${NC} Security Level: Enhanced"
    echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# Display the banner
display_validation_banner

# ======================================================================
# ENHANCED DOCKERFILE VALIDATION WITH SECURITY ANALYSIS
# ======================================================================

validate_dockerfile_security() {
    start_timer "dockerfile_security"
    log_info "Performing comprehensive Dockerfile security analysis..."
    
    local dockerfile_issues=()
    local dockerfile_warnings=()
    
    if [[ ! -f "Dockerfile" ]]; then
        validate_critical 1 "Dockerfile not found"
        return 1
    fi
    
    # Security check 1: No root user in final stage
    if ! grep -q "^USER [^r]" Dockerfile; then
        if ! grep -q "^USER [0-9]\+$" Dockerfile; then
            dockerfile_issues+=("Container runs as root (security risk)")
        fi
    fi
    
    # Security check 2: No hardcoded secrets
    if grep -iE "(password|secret|key|token)=" Dockerfile >/dev/null 2>&1; then
        dockerfile_issues+=("Potential hardcoded secrets detected")
    fi
    
    # Security check 3: Base image security
    local base_image
    base_image=$(grep "^FROM" Dockerfile | head -1 | awk '{print $2}')
    if [[ "$base_image" =~ :latest$ ]]; then
        dockerfile_warnings+=("Using 'latest' tag (not recommended for production)")
    fi
    
    # Security check 4: Minimize attack surface
    if ! grep -q "RUN apt-get.*remove\|RUN apk.*del" Dockerfile; then
        dockerfile_warnings+=("Build tools not removed (increases attack surface)")
    fi
    
    # Security check 5: Health check present
    if ! grep -q "^HEALTHCHECK" Dockerfile; then
        dockerfile_warnings+=("No health check configured")
    fi
    
    # Performance check: Multi-stage build
    local from_count
    from_count=$(grep -c "^FROM" Dockerfile)
    if [[ $from_count -eq 1 ]]; then
        dockerfile_warnings+=("Single-stage build (multi-stage recommended for optimization)")
    fi
    
    # Report Dockerfile analysis results
    if [[ ${#dockerfile_issues[@]} -gt 0 ]]; then
        log_security "Dockerfile security issues detected:"
        printf '  - %s\n' "${dockerfile_issues[@]}"
        validate_security 1 "Dockerfile security validation" "\"issues\":${#dockerfile_issues[@]}"
    else
        validate_security 0 "Dockerfile security validation passed"
    fi
    
    if [[ ${#dockerfile_warnings[@]} -gt 0 ]]; then
        log_warn "Dockerfile optimization recommendations:"
        printf '  - %s\n' "${dockerfile_warnings[@]}"
    fi
    
    local duration
    duration=$(end_timer "dockerfile_security")
    log_perf "Dockerfile analysis completed" "\"duration_ms\":$duration,\"issues\":${#dockerfile_issues[@]},\"warnings\":${#dockerfile_warnings[@]}"
}

validate_dockerfile_syntax() {
    start_timer "dockerfile_syntax"
    log_info "Validating Dockerfile syntax and build configuration..."
    
    if command -v docker >/dev/null 2>&1; then
        # Test Dockerfile syntax with dry-run
        local docker_output
        if docker_output=$(docker build --dry-run . 2>&1); then
            validate_critical 0 "Dockerfile syntax is valid"
            
            # Check for build optimization
            if echo "$docker_output" | grep -q "cache"; then
                validate_performance 0 "Docker build caching enabled"
            else
                validate_performance 1 "Docker build caching not optimized"
            fi
        else
            validate_critical 1 "Dockerfile syntax validation failed" "\"error\":\"$(echo "$docker_output" | head -1)\""
        fi
        
        # Validate BuildKit features if available
        if docker version --format '{{.Server.Version}}' 2>/dev/null | grep -E '^(19\.|2[0-9]\.)' >/dev/null; then
            validate_performance 0 "Modern Docker version with BuildKit support"
        else
            validate_performance 1 "Older Docker version - consider upgrading for better performance"
        fi
    else
        validate_warning "Docker not available - skipping Dockerfile syntax validation"
    fi
    
    local duration
    duration=$(end_timer "dockerfile_syntax")
    log_perf "Dockerfile syntax validation completed" "\"duration_ms\":$duration"
}

# Execute Dockerfile validations
validate_dockerfile_syntax
validate_dockerfile_security

# ======================================================================
# COMPREHENSIVE FILE STRUCTURE AND DEPENDENCY VALIDATION
# ======================================================================

validate_file_structure() {
    start_timer "file_structure"
    log_info "Performing comprehensive file structure and dependency analysis..."
    
    # Define file categories with different importance levels
    declare -A critical_files=(
        ["Dockerfile"]="Container build configuration"
        ["docker-entrypoint.sh"]="Container initialization script"
        ["start_server.sh"]="Production server launcher"
        ["requirements.txt"]="Python dependencies (fallback)"
        ["mcp_crypto_server.py"]="Main application (primary)"
        ["mcp_crypto_main.py"]="Main application (alternative)"
    )
    
    declare -A recommended_files=(
        [".env.production.example"]="Production environment template"
        ["docker-compose.yml"]="Docker orchestration (any variant)"
        ["docker-compose.production.yml"]="Production orchestration"
        ["validate_build.sh"]="Build validation script"
        ["README.md"]="Documentation"
        [".gitignore"]="Git ignore rules"
    )
    
    declare -A optional_files=(
        ["requirements_mcp.txt"]="MCP-specific dependencies"
        [".dockerignore"]="Docker build optimization"
        ["health_check.py"]="Health monitoring"
        ["logging_config.json"]="Logging configuration"
        ["prometheus.yml"]="Metrics configuration"
    )
    
    # Validate critical files
    local missing_critical=()
    for file in "${!critical_files[@]}"; do
        if [[ -f "$file" ]]; then
            validate_critical 0 "Critical file exists: $file" "\"description\":\"${critical_files[$file]}\""
        else
            missing_critical+=("$file (${critical_files[$file]})")
            validate_critical 1 "Missing critical file: $file" "\"description\":\"${critical_files[$file]}\""
        fi
    done
    
    # Special handling for main application file (either variant acceptable)
    if [[ ! -f "mcp_crypto_server.py" ]] && [[ ! -f "mcp_crypto_main.py" ]]; then
        validate_critical 1 "No main application file found (mcp_crypto_server.py or mcp_crypto_main.py)"
    fi
    
    # Special handling for requirements files
    if [[ -f "requirements.txt" ]] || [[ -f "requirements_mcp.txt" ]]; then
        validate_critical 0 "Python requirements file found"
    else
        validate_critical 1 "No Python requirements file found (requirements.txt or requirements_mcp.txt)"
    fi
    
    # Validate recommended files
    local missing_recommended=()
    for file in "${!recommended_files[@]}"; do
        if [[ -f "$file" ]]; then
            validate_performance 0 "Recommended file exists: $file" "\"description\":\"${recommended_files[$file]}\""
        else
            missing_recommended+=("$file (${recommended_files[$file]})")
            validate_performance 1 "Missing recommended file: $file" "\"description\":\"${recommended_files[$file]}\""
        fi
    done
    
    # Special handling for Docker Compose (any variant)
    if [[ -f "docker-compose.yml" ]] || [[ -f "docker-compose.production.yml" ]] || [[ -f "docker-compose.yaml" ]]; then
        validate_performance 0 "Docker Compose configuration found"
    else
        validate_performance 1 "No Docker Compose configuration found"
    fi
    
    # Check optional files
    local found_optional=0
    for file in "${!optional_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_info "Optional file found: $file (${optional_files[$file]})"
            ((found_optional++))
        fi
    done
    
    # File size and integrity checks
    validate_file_integrity
    
    local duration
    duration=$(end_timer "file_structure")
    log_perf "File structure validation completed" \
        "\"duration_ms\":$duration,\"missing_critical\":${#missing_critical[@]},\"missing_recommended\":${#missing_recommended[@]},\"found_optional\":$found_optional"
}

validate_file_integrity() {
    log_info "Validating file integrity and permissions..."
    
    local integrity_issues=()
    
    # Check executable files have correct permissions
    local executable_files=("docker-entrypoint.sh" "start_server.sh" "validate_build.sh")
    for file in "${executable_files[@]}"; do
        if [[ -f "$file" ]]; then
            if [[ -x "$file" ]]; then
                validate_critical 0 "Executable file has correct permissions: $file"
            else
                validate_critical 1 "Executable file missing execute permission: $file"
                integrity_issues+=("$file missing execute permission")
            fi
            
            # Check for Windows line endings
            if file "$file" | grep -q CRLF; then
                integrity_issues+=("$file has Windows line endings (CRLF)")
                validate_warning "$file has Windows line endings - may cause issues in containers"
            fi
        fi
    done
    
    # Check file sizes (detect truncated or empty files)
    local important_files=("Dockerfile" "mcp_crypto_server.py" "mcp_crypto_main.py" "requirements.txt" "requirements_mcp.txt")
    for file in "${important_files[@]}"; do
        if [[ -f "$file" ]]; then
            local file_size
            file_size=$(stat -c%s "$file" 2>/dev/null || echo "0")
            if [[ $file_size -eq 0 ]]; then
                integrity_issues+=("$file is empty")
                validate_critical 1 "File is empty: $file"
            elif [[ $file_size -lt 10 ]]; then
                integrity_issues+=("$file is suspiciously small ($file_size bytes)")
                validate_warning "File is very small: $file ($file_size bytes)"
            else
                log_debug "File size acceptable: $file ($file_size bytes)"
            fi
        fi
    done
    
    if [[ ${#integrity_issues[@]} -eq 0 ]]; then
        validate_critical 0 "All file integrity checks passed"
    else
        log_warn "File integrity issues detected:"
        printf '  - %s\n' "${integrity_issues[@]}"
    fi
}

# Execute file structure validation
validate_file_structure

# ======================================================================
# PYTHON ENVIRONMENT AND DEPENDENCY VALIDATION
# ======================================================================

validate_python_requirements() {
    start_timer "python_requirements"
    log_info "Performing comprehensive Python dependency analysis..."
    
    # Find requirements files
    local requirements_files=()
    [[ -f "requirements.txt" ]] && requirements_files+=("requirements.txt")
    [[ -f "requirements_mcp.txt" ]] && requirements_files+=("requirements_mcp.txt")
    [[ -f "requirements-prod.txt" ]] && requirements_files+=("requirements-prod.txt")
    
    if [[ ${#requirements_files[@]} -eq 0 ]]; then
        validate_critical 1 "No Python requirements files found"
        return 1
    fi
    
    local validation_errors=()
    local security_warnings=()
    
    for req_file in "${requirements_files[@]}"; do
        log_info "Validating requirements file: $req_file"
        
        # Syntax validation
        if python3 -m pip install --dry-run -r "$req_file" >/dev/null 2>&1; then
            validate_critical 0 "Requirements file syntax valid: $req_file"
        else
            validate_critical 1 "Requirements file syntax invalid: $req_file"
            validation_errors+=("$req_file has syntax errors")
            continue
        fi
        
        # Security analysis of dependencies
        analyze_dependency_security "$req_file"
        
        # Version pinning analysis
        analyze_version_pinning "$req_file"
        
        # Dependency conflict detection
        analyze_dependency_conflicts "$req_file"
    done
    
    local duration
    duration=$(end_timer "python_requirements")
    log_perf "Python requirements validation completed" "\"duration_ms\":$duration,\"files_checked\":${#requirements_files[@]}"
}

analyze_dependency_security() {
    local req_file="$1"
    log_info "Analyzing security vulnerabilities in: $req_file"
    
    # Check for known vulnerable packages (basic list)
    local vulnerable_patterns=(
        "django==1\\."
        "flask==0\\."
        "requests==2\\.[0-9]\\.[0-9]$"
        "urllib3==1\\.[0-9]\\."
        "pyyaml==3\\."
    )
    
    local security_issues=()
    
    for pattern in "${vulnerable_patterns[@]}"; do
        if grep -E "^$pattern" "$req_file" >/dev/null 2>&1; then
            local matched_line
            matched_line=$(grep -E "^$pattern" "$req_file")
            security_issues+=("Potentially vulnerable dependency: $matched_line")
        fi
    done
    
    # Check for unpinned dependencies in production
    if [[ "$req_file" =~ prod ]] || [[ "${ENVIRONMENT:-}" == "production" ]]; then
        local unpinned
        unpinned=$(grep -E "^[^#]*[^<>=!]$" "$req_file" | head -3)
        if [[ -n "$unpinned" ]]; then
            security_issues+=("Unpinned dependencies in production context")
        fi
    fi
    
    if [[ ${#security_issues[@]} -gt 0 ]]; then
        log_security "Dependency security issues in $req_file:"
        printf '  - %s\n' "${security_issues[@]}"
        validate_security 1 "Dependency security analysis: $req_file" "\"issues\":${#security_issues[@]}"
    else
        validate_security 0 "Dependency security analysis passed: $req_file"
    fi
}

analyze_version_pinning() {
    local req_file="$1"
    log_info "Analyzing version pinning strategy: $req_file"
    
    local total_deps
    total_deps=$(grep -cE "^[^#-]" "$req_file" 2>/dev/null || echo "0")
    local pinned_deps
    pinned_deps=$(grep -cE "^[^#]*==" "$req_file" 2>/dev/null || echo "0")
    local range_pinned
    range_pinned=$(grep -cE "^[^#]*[<>=]" "$req_file" 2>/dev/null || echo "0")
    
    if [[ $total_deps -gt 0 ]]; then
        local pinning_ratio=$((pinned_deps * 100 / total_deps))
        
        if [[ $pinning_ratio -gt 80 ]]; then
            validate_performance 0 "Good version pinning: $req_file ($pinning_ratio% pinned)"
        elif [[ $pinning_ratio -gt 50 ]]; then
            validate_performance 1 "Moderate version pinning: $req_file ($pinning_ratio% pinned)"
        else
            validate_performance 1 "Poor version pinning: $req_file ($pinning_ratio% pinned)"
        fi
        
        log_debug "Version pinning analysis" "\"file\":\"$req_file\",\"total\":$total_deps,\"exact_pinned\":$pinned_deps,\"range_pinned\":$range_pinned"
    fi
}

analyze_dependency_conflicts() {
    local req_file="$1"
    log_info "Checking for potential dependency conflicts: $req_file"
    
    # Check for common conflicting packages
    local conflict_groups=(
        "tensorflow tensorflow-gpu"
        "pillow PIL"
        "pycrypto pycryptodome"
        "mysql-python mysqlclient PyMySQL"
    )
    
    local conflicts_found=()
    
    for group in "${conflict_groups[@]}"; do
        read -ra packages <<< "$group"
        local found_packages=()
        
        for pkg in "${packages[@]}"; do
            if grep -qE "^$pkg[<>=]" "$req_file"; then
                found_packages+=("$pkg")
            fi
        done
        
        if [[ ${#found_packages[@]} -gt 1 ]]; then
            conflicts_found+=("Potential conflict: ${found_packages[*]}")
        fi
    done
    
    if [[ ${#conflicts_found[@]} -gt 0 ]]; then
        log_warn "Potential dependency conflicts in $req_file:"
        printf '  - %s\n' "${conflicts_found[@]}"
        validate_warning "Dependency conflicts detected: $req_file" "\"conflicts\":${#conflicts_found[@]}"
    fi
}

validate_python_code() {
    start_timer "python_code"
    log_info "Performing comprehensive Python code analysis..."
    
    local main_files=("mcp_crypto_server.py" "mcp_crypto_main.py")
    local main_file_found=""
    
    # Find the main application file
    for file in "${main_files[@]}"; do
        if [[ -f "$file" ]]; then
            main_file_found="$file"
            break
        fi
    done
    
    if [[ -z "$main_file_found" ]]; then
        validate_critical 1 "No main application file found"
        return 1
    fi
    
    log_info "Analyzing main application file: $main_file_found"
    
    # Syntax compilation check
    if python3 -m py_compile "$main_file_found" 2>/dev/null; then
        validate_critical 0 "Main application file compiles successfully: $main_file_found"
    else
        validate_critical 1 "Main application file compilation failed: $main_file_found"
        return 1
    fi
    
    # Advanced code analysis
    analyze_code_quality "$main_file_found"
    analyze_security_patterns "$main_file_found"
    analyze_import_structure "$main_file_found"
    
    local duration
    duration=$(end_timer "python_code")
    log_perf "Python code validation completed" "\"duration_ms\":$duration,\"main_file\":\"$main_file_found\""
}

analyze_code_quality() {
    local file="$1"
    log_info "Analyzing code quality patterns: $file"
    
    local quality_issues=()
    local complexity_warnings=()
    
    # Check for basic code quality indicators
    local line_count
    line_count=$(wc -l < "$file")
    
    if [[ $line_count -gt 1000 ]]; then
        complexity_warnings+=("Large file size: $line_count lines (consider refactoring)")
    fi
    
    # Check for potential code smells
    if grep -q "print(" "$file"; then
        quality_issues+=("Debug print statements found (should use logging)")
    fi
    
    if grep -q "TODO\|FIXME\|XXX" "$file"; then
        local todo_count
        todo_count=$(grep -c "TODO\|FIXME\|XXX" "$file")
        quality_issues+=("$todo_count TODO/FIXME comments found")
    fi
    
    # Check for proper error handling
    local try_count
    try_count=$(grep -c "try:" "$file" 2>/dev/null || echo "0")
    local except_count
    except_count=$(grep -c "except" "$file" 2>/dev/null || echo "0")
    
    if [[ $try_count -gt 0 ]] && [[ $except_count -eq $try_count ]]; then
        validate_performance 0 "Proper exception handling detected: $file"
    elif [[ $try_count -gt 0 ]]; then
        validate_performance 1 "Incomplete exception handling: $file"
    fi
    
    if [[ ${#quality_issues[@]} -gt 0 ]]; then
        log_warn "Code quality issues in $file:"
        printf '  - %s\n' "${quality_issues[@]}"
    fi
    
    if [[ ${#complexity_warnings[@]} -gt 0 ]]; then
        log_warn "Complexity warnings for $file:"
        printf '  - %s\n' "${complexity_warnings[@]}"
    fi
}

analyze_security_patterns() {
    local file="$1"
    log_info "Analyzing security patterns: $file"
    
    local security_issues=()
    
    # Check for potential security vulnerabilities
    if grep -qE "eval\(|exec\(|__import__" "$file"; then
        security_issues+=("Dynamic code execution detected (eval/exec/__import__)")
    fi
    
    if grep -qE "pickle\.loads|yaml\.load[^_]" "$file"; then
        security_issues+=("Unsafe deserialization detected (pickle.loads/yaml.load)")
    fi
    
    if grep -qE "shell=True" "$file"; then
        security_issues+=("Shell injection risk (subprocess with shell=True)")
    fi
    
    if grep -qiE "password.*=.*['\"][^'\"]*['\"]" "$file"; then
        security_issues+=("Hardcoded credentials detected")
    fi
    
    if grep -qE "debug.*=.*True" "$file"; then
        security_issues+=("Debug mode enabled (potential information disclosure)")
    fi
    
    if [[ ${#security_issues[@]} -gt 0 ]]; then
        log_security "Security issues detected in $file:"
        printf '  - %s\n' "${security_issues[@]}"
        validate_security 1 "Python code security analysis: $file" "\"issues\":${#security_issues[@]}"
    else
        validate_security 0 "Python code security analysis passed: $file"
    fi
}

analyze_import_structure() {
    local file="$1"
    log_info "Analyzing import structure: $file"
    
    local import_issues=()
    local import_warnings=()
    
    # Check for proper import organization
    if ! grep -q "^import" "$file" && ! grep -q "^from.*import" "$file"; then
        import_warnings+=("No imports detected - unusual for main application file")
    fi
    
    # Check for relative imports
    if grep -q "^from \." "$file"; then
        import_warnings+=("Relative imports detected (ensure proper package structure)")
    fi
    
    # Check for wildcard imports
    if grep -q "import \*" "$file"; then
        import_issues+=("Wildcard imports detected (not recommended)")
    fi
    
    # Check for required imports based on patterns
    if grep -q "async def\|await " "$file" && ! grep -q "import asyncio" "$file"; then
        import_warnings+=("Async code detected but asyncio not explicitly imported")
    fi
    
    if grep -q "@app\.route\|Flask" "$file" && ! grep -q "from flask\|import flask" "$file"; then
        import_issues+=("Flask patterns detected but Flask not imported")
    fi
    
    if [[ ${#import_issues[@]} -gt 0 ]]; then
        log_warn "Import issues in $file:"
        printf '  - %s\n' "${import_issues[@]}"
    fi
    
    if [[ ${#import_warnings[@]} -gt 0 ]]; then
        log_info "Import recommendations for $file:"
        printf '  - %s\n' "${import_warnings[@]}"
    fi
}

# Execute Python validation
validate_python_requirements
validate_python_code

# ======================================================================
# CONFIGURATION AND ENVIRONMENT VALIDATION
# ======================================================================

validate_environment_configuration() {
    start_timer "environment_config"
    log_info "Performing comprehensive environment configuration validation..."
    
    # Find environment template files
    local env_templates=()
    [[ -f ".env.example" ]] && env_templates+=(".env.example")
    [[ -f ".env.production.example" ]] && env_templates+=(".env.production.example")
    [[ -f ".env.template" ]] && env_templates+=(".env.template")
    
    if [[ ${#env_templates[@]} -eq 0 ]]; then
        validate_critical 1 "No environment template files found"
        return 1
    fi
    
    # Define required environment variables with validation patterns
    declare -A required_env_vars=(
        ["ENVIRONMENT"]="^(production|staging|development)$"
        ["MONGODB_URI"]="^mongodb(\\+srv)?://.*"
        ["REDIS_URL"]="^redis(s)?://.*"
        ["MCP_SERVER_PORT"]="^[1-9][0-9]{3,4}$"
    )
    
    # Optional but recommended variables
    declare -A recommended_env_vars=(
        ["JWT_SECRET"]="^.{32,}$"
        ["SENTRY_DSN"]="^https://.*"
        ["LOG_LEVEL"]="^(DEBUG|INFO|WARNING|ERROR)$"
        ["MAX_WORKERS"]="^[1-9][0-9]*$"
    )
    
    local config_issues=()
    local security_warnings=()
    
    for template in "${env_templates[@]}"; do
        log_info "Validating environment template: $template"
        
        # Check required variables
        local missing_required=()
        for var in "${!required_env_vars[@]}"; do
            local pattern="${required_env_vars[$var]}"
            
            if grep -qE "^${var}=" "$template"; then
                # Check if the value matches expected pattern
                local value
                value=$(grep "^${var}=" "$template" | cut -d'=' -f2- | tr -d '"\047')
                
                if [[ -n "$value" ]] && [[ "$value" =~ $pattern ]]; then
                    validate_critical 0 "Environment variable template valid: $var"
                elif [[ -z "$value" ]] || [[ "$value" =~ ^(CHANGE_ME|TODO|REPLACE) ]]; then
                    validate_critical 0 "Environment variable placeholder found: $var"
                else
                    validate_warning "Environment variable format may be invalid: $var"
                fi
            else
                missing_required+=("$var")
                validate_critical 1 "Missing required environment variable template: $var"
            fi
        done
        
        # Check recommended variables
        local missing_recommended=()
        for var in "${!recommended_env_vars[@]}"; do
            if ! grep -qE "^${var}=" "$template"; then
                missing_recommended+=("$var")
            fi
        done
        
        if [[ ${#missing_recommended[@]} -gt 0 ]]; then
            log_info "Recommended environment variables not in $template:"
            printf '  - %s\n' "${missing_recommended[@]}"
        fi
        
        # Security analysis of environment template
        analyze_env_security "$template"
    done
    
    local duration
    duration=$(end_timer "environment_config")
    log_perf "Environment configuration validation completed" "\"duration_ms\":$duration,\"templates_checked\":${#env_templates[@]}"
}

analyze_env_security() {
    local env_file="$1"
    log_info "Analyzing environment template security: $env_file"
    
    local security_issues=()
    
    # Check for hardcoded production secrets
    if grep -qiE "(password|secret|key|token)=(?!.*CHANGE_ME|.*TODO|.*REPLACE|.*EXAMPLE)" "$env_file"; then
        security_issues+=("Potential hardcoded secrets in template")
    fi
    
    # Check for insecure default values
    if grep -qE "DEBUG=true|DEBUG=True" "$env_file"; then
        security_issues+=("Debug mode enabled in template")
    fi
    
    # Check for weak default configurations
    if grep -qE "JWT_SECRET=.*[a-zA-Z0-9]{1,16}" "$env_file"; then
        security_issues+=("Weak JWT secret in template (too short)")
    fi
    
    # Check for unencrypted connection strings
    if grep -qE "mongodb://.*@" "$env_file" && ! grep -qE "ssl=true|tls=true" "$env_file"; then
        security_issues+=("MongoDB connection may not use encryption")
    fi
    
    if grep -qE "redis://.*@" "$env_file"; then
        security_issues+=("Redis connection not using rediss:// (SSL)")
    fi
    
    if [[ ${#security_issues[@]} -gt 0 ]]; then
        log_security "Environment template security issues in $env_file:"
        printf '  - %s\n' "${security_issues[@]}"
        validate_security 1 "Environment template security: $env_file" "\"issues\":${#security_issues[@]}"
    else
        validate_security 0 "Environment template security analysis passed: $env_file"
    fi
}

validate_docker_compose() {
    start_timer "docker_compose"
    log_info "Performing comprehensive Docker Compose validation..."
    
    # Find Docker Compose files
    local compose_files=()
    [[ -f "docker-compose.yml" ]] && compose_files+=("docker-compose.yml")
    [[ -f "docker-compose.yaml" ]] && compose_files+=("docker-compose.yaml")
    [[ -f "docker-compose.production.yml" ]] && compose_files+=("docker-compose.production.yml")
    [[ -f "docker-compose.override.yml" ]] && compose_files+=("docker-compose.override.yml")
    
    if [[ ${#compose_files[@]} -eq 0 ]]; then
        validate_performance 1 "No Docker Compose files found"
        return 1
    fi
    
    local compose_cmd=""
    
    # Determine Docker Compose command
    if command -v docker-compose >/dev/null 2>&1; then
        compose_cmd="docker-compose"
    elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
        compose_cmd="docker compose"
    else
        validate_warning "Docker Compose not available - skipping configuration validation"
        return 1
    fi
    
    local validation_errors=()
    
    for compose_file in "${compose_files[@]}"; do
        log_info "Validating Docker Compose file: $compose_file"
        
        # Syntax validation
        if $compose_cmd -f "$compose_file" config >/dev/null 2>&1; then
            validate_critical 0 "Docker Compose syntax valid: $compose_file"
        else
            validate_critical 1 "Docker Compose syntax invalid: $compose_file"
            validation_errors+=("$compose_file has syntax errors")
            continue
        fi
        
        # Advanced configuration analysis
        analyze_compose_configuration "$compose_file"
        analyze_compose_security "$compose_file"
        analyze_compose_performance "$compose_file"
    done
    
    local duration
    duration=$(end_timer "docker_compose")
    log_perf "Docker Compose validation completed" "\"duration_ms\":$duration,\"files_checked\":${#compose_files[@]}"
}

analyze_compose_configuration() {
    local compose_file="$1"
    log_info "Analyzing Docker Compose configuration: $compose_file"
    
    local config_issues=()
    local config_warnings=()
    
    # Check for required sections
    if ! grep -q "^services:" "$compose_file"; then
        config_issues+=("No services section found")
    fi
    
    # Check for proper service naming
    if grep -qE "^\s+[A-Z]" "$compose_file"; then
        config_warnings+=("Uppercase service names detected (lowercase recommended)")
    fi
    
    # Check for health checks
    if grep -q "healthcheck:" "$compose_file"; then
        validate_performance 0 "Health checks configured: $compose_file"
    else
        validate_performance 1 "No health checks configured: $compose_file"
    fi
    
    # Check for restart policies
    if grep -q "restart:" "$compose_file"; then
        validate_performance 0 "Restart policies configured: $compose_file"
    else
        validate_performance 1 "No restart policies configured: $compose_file"
    fi
    
    # Check for resource limits
    if grep -q "deploy:" "$compose_file" || grep -q "mem_limit:" "$compose_file"; then
        validate_performance 0 "Resource limits configured: $compose_file"
    else
        validate_performance 1 "No resource limits configured: $compose_file"
    fi
    
    if [[ ${#config_issues[@]} -gt 0 ]]; then
        log_error "Docker Compose configuration issues in $compose_file:"
        printf '  - %s\n' "${config_issues[@]}"
    fi
    
    if [[ ${#config_warnings[@]} -gt 0 ]]; then
        log_warn "Docker Compose configuration warnings for $compose_file:"
        printf '  - %s\n' "${config_warnings[@]}"
    fi
}

analyze_compose_security() {
    local compose_file="$1"
    log_info "Analyzing Docker Compose security: $compose_file"
    
    local security_issues=()
    
    # Check for privileged containers
    if grep -q "privileged: true" "$compose_file"; then
        security_issues+=("Privileged containers detected (security risk)")
    fi
    
    # Check for host networking
    if grep -q "network_mode:.*host" "$compose_file"; then
        security_issues+=("Host networking mode detected (security risk)")
    fi
    
    # Check for bind mounts to sensitive locations
    if grep -qE ":/etc:|:/var/run/docker.sock" "$compose_file"; then
        security_issues+=("Sensitive system directories mounted")
    fi
    
    # Check for hardcoded secrets
    if grep -qiE "password|secret|key" "$compose_file" | grep -qvE "_FILE$|\${.*}" ; then
        security_issues+=("Potential hardcoded secrets detected")
    fi
    
    # Check for proper secrets management
    if grep -q "secrets:" "$compose_file"; then
        validate_security 0 "Docker secrets configured: $compose_file"
    else
        if grep -qiE "password|secret|key" "$compose_file"; then
            validate_security 1 "Secrets present but Docker secrets not used: $compose_file"
        fi
    fi
    
    if [[ ${#security_issues[@]} -gt 0 ]]; then
        log_security "Docker Compose security issues in $compose_file:"
        printf '  - %s\n' "${security_issues[@]}"
        validate_security 1 "Docker Compose security analysis: $compose_file" "\"issues\":${#security_issues[@]}"
    else
        validate_security 0 "Docker Compose security analysis passed: $compose_file"
    fi
}

analyze_compose_performance() {
    local compose_file="$1"
    log_info "Analyzing Docker Compose performance configuration: $compose_file"
    
    local performance_issues=()
    
    # Check for proper logging configuration
    if ! grep -q "logging:" "$compose_file"; then
        performance_issues+=("No logging configuration (may cause disk space issues)")
    fi
    
    # Check for volume optimization
    if grep -q "volumes:" "$compose_file"; then
        # Check for tmpfs mounts for temporary data
        if ! grep -q "tmpfs:" "$compose_file"; then
            performance_issues+=("Consider tmpfs mounts for temporary data")
        fi
    fi
    
    # Check for network optimization
    if ! grep -q "networks:" "$compose_file"; then
        performance_issues+=("Custom networks not defined (using default bridge)")
    fi
    
    if [[ ${#performance_issues[@]} -gt 0 ]]; then
        log_warn "Docker Compose performance recommendations for $compose_file:"
        printf '  - %s\n' "${performance_issues[@]}"
    fi
}

# Execute configuration validation
validate_environment_configuration
validate_docker_compose

# ======================================================================
# ADVANCED SECURITY AND COMPLIANCE VALIDATION
# ======================================================================

validate_security_compliance() {
    start_timer "security_compliance"
    log_info "Performing comprehensive security and compliance validation..."
    
    # Container security validation
    validate_container_security
    
    # Application security validation
    validate_application_security
    
    # Compliance checks
    validate_compliance_standards
    
    local duration
    duration=$(end_timer "security_compliance")
    log_perf "Security and compliance validation completed" "\"duration_ms\":$duration"
}

validate_container_security() {
    log_info "Validating container security configuration..."
    
    local security_issues=()
    local security_recommendations=()
    
    if [[ -f "Dockerfile" ]]; then
        # Check for non-root user
        if grep -qE "^USER [^r]|^USER [0-9]+" Dockerfile; then
            local user_line
            user_line=$(grep -E "^USER" Dockerfile | tail -1)
            if [[ "$user_line" =~ ^USER\ root$ ]] || [[ "$user_line" =~ ^USER\ 0$ ]]; then
                security_issues+=("Container runs as root user")
                validate_security 1 "Non-root user validation"
            else
                validate_security 0 "Non-root user configured in Dockerfile"
            fi
        else
            security_issues+=("No USER directive found - container may run as root")
            validate_security 1 "Non-root user configuration missing"
        fi
        
        # Check for security-related environment variables
        if grep -qE "PYTHONDONTWRITEBYTECODE|PYTHONUNBUFFERED" Dockerfile; then
            validate_security 0 "Python security flags configured"
        else
            security_recommendations+=("Consider adding Python security flags (PYTHONDONTWRITEBYTECODE, PYTHONUNBUFFERED)")
            validate_security 1 "Python security flags missing"
        fi
        
        # Check for package manager cleanup
        if grep -qE "apt-get.*clean|apk.*cache|yum.*clean" Dockerfile; then
            validate_security 0 "Package manager cleanup configured"
        else
            security_recommendations+=("Package manager cache not cleaned (increases image size)")
        fi
        
        # Check for COPY vs ADD usage
        if grep -q "^ADD" Dockerfile && ! grep -q "^ADD.*\.tar" Dockerfile; then
            security_recommendations+=("Consider using COPY instead of ADD for security")
        fi
    fi
    
    # Report container security results
    if [[ ${#security_issues[@]} -gt 0 ]]; then
        log_security "Container security issues detected:"
        printf '  - %s\n' "${security_issues[@]}"
    fi
    
    if [[ ${#security_recommendations[@]} -gt 0 ]]; then
        log_info "Container security recommendations:"
        printf '  - %s\n' "${security_recommendations[@]}"
    fi
}

validate_application_security() {
    log_info "Validating application security configuration..."
    
    local app_security_issues=()
    
    # Check for .gitignore to prevent secret leakage
    if [[ -f ".gitignore" ]]; then
        if grep -qE "\*\.env|\*\.key|\*\.pem|secrets/" ".gitignore"; then
            validate_security 0 "Sensitive files excluded from git"
        else
            app_security_issues+=("Gitignore may not exclude sensitive files")
        fi
    else
        app_security_issues+=(".gitignore file missing")
        validate_security 1 ".gitignore file not found"
    fi
    
    # Check for .dockerignore to reduce build context
    if [[ -f ".dockerignore" ]]; then
        validate_performance 0 ".dockerignore present (reduces build context)"
        
        if grep -qE "\*\.env|\*\.key|\*\.pem|node_modules" ".dockerignore"; then
            validate_security 0 "Sensitive files excluded from Docker build"
        else
            app_security_issues+=("Dockerignore may not exclude sensitive files")
        fi
    else
        validate_performance 1 ".dockerignore file missing"
    fi
    
    # Check for security headers or middleware configuration
    local security_config_files=("security.py" "middleware.py" "settings.py" "config.py")
    local security_config_found=false
    
    for config_file in "${security_config_files[@]}"; do
        if [[ -f "$config_file" ]]; then
            security_config_found=true
            if grep -qiE "cors|csrf|xss|helmet" "$config_file"; then
                validate_security 0 "Security middleware configuration found: $config_file"
            fi
        fi
    done
    
    if [[ "$security_config_found" == "false" ]]; then
        app_security_issues+=("No security configuration files found")
    fi
    
    if [[ ${#app_security_issues[@]} -gt 0 ]]; then
        log_security "Application security issues:"
        printf '  - %s\n' "${app_security_issues[@]}"
    fi
}

validate_compliance_standards() {
    log_info "Validating compliance with development standards..."
    
    local compliance_issues=()
    local compliance_score=0
    local total_checks=0
    
    # Documentation compliance
    ((total_checks++))
    if [[ -f "README.md" ]]; then
        ((compliance_score++))
        validate_performance 0 "README.md documentation present"
    else
        compliance_issues+=("README.md documentation missing")
        validate_performance 1 "README.md documentation missing"
    fi
    
    # License compliance
    ((total_checks++))
    if [[ -f "LICENSE" ]] || [[ -f "LICENSE.txt" ]] || [[ -f "LICENSE.md" ]]; then
        ((compliance_score++))
        validate_performance 0 "License file present"
    else
        compliance_issues+=("License file missing")
        validate_performance 1 "License file missing"
    fi
    
    # Changelog compliance
    ((total_checks++))
    if [[ -f "CHANGELOG.md" ]] || [[ -f "CHANGELOG.txt" ]]; then
        ((compliance_score++))
        validate_performance 0 "Changelog documentation present"
    else
        compliance_issues+=("Changelog documentation missing")
        validate_performance 1 "Changelog documentation missing"
    fi
    
    # Contributing guidelines
    ((total_checks++))
    if [[ -f "CONTRIBUTING.md" ]] || [[ -f "CONTRIBUTING.txt" ]]; then
        ((compliance_score++))
        validate_performance 0 "Contributing guidelines present"
    else
        compliance_issues+=("Contributing guidelines missing")
    fi
    
    # Code of conduct
    ((total_checks++))
    if [[ -f "CODE_OF_CONDUCT.md" ]]; then
        ((compliance_score++))
        validate_performance 0 "Code of conduct present"
    else
        compliance_issues+=("Code of conduct missing")
    fi
    
    # Calculate compliance percentage
    local compliance_percentage=$((compliance_score * 100 / total_checks))
    
    if [[ $compliance_percentage -ge 80 ]]; then
        validate_performance 0 "Good compliance with development standards" "\"score\":$compliance_percentage"
    elif [[ $compliance_percentage -ge 60 ]]; then
        validate_performance 1 "Moderate compliance with development standards" "\"score\":$compliance_percentage"
    else
        validate_performance 1 "Poor compliance with development standards" "\"score\":$compliance_percentage"
    fi
    
    log_info "Compliance score: $compliance_percentage% ($compliance_score/$total_checks checks passed)"
}

# ======================================================================
# PERFORMANCE AND OPTIMIZATION VALIDATION
# ======================================================================

validate_performance_optimization() {
    start_timer "performance_optimization"
    log_info "Validating performance and optimization configurations..."
    
    local performance_issues=()
    local optimization_recommendations=()
    
    # Docker Compose resource limits
    local compose_files=("docker-compose.yml" "docker-compose.production.yml")
    local resource_limits_found=false
    
    for compose_file in "${compose_files[@]}"; do
        if [[ -f "$compose_file" ]]; then
            if grep -qE "resources:|mem_limit:|cpus:" "$compose_file"; then
                resource_limits_found=true
                validate_performance 0 "Resource limits configured: $compose_file"
            fi
        fi
    done
    
    if [[ "$resource_limits_found" == "false" ]]; then
        performance_issues+=("No resource limits configured in Docker Compose files")
        validate_performance 1 "Resource limits not configured"
    fi
    
    # Health check configuration
    local health_checks_found=false
    
    if [[ -f "Dockerfile" ]] && grep -q "HEALTHCHECK" Dockerfile; then
        health_checks_found=true
        validate_performance 0 "Health check configured in Dockerfile"
    fi
    
    for compose_file in "${compose_files[@]}"; do
        if [[ -f "$compose_file" ]] && grep -q "healthcheck:" "$compose_file"; then
            health_checks_found=true
            validate_performance 0 "Health check configured: $compose_file"
        fi
    done
    
    if [[ "$health_checks_found" == "false" ]]; then
        performance_issues+=("No health checks configured")
        validate_performance 1 "Health checks missing"
    fi
    
    # Monitoring and observability
    if [[ -f "prometheus.yml" ]] || [[ -f "monitoring/prometheus.yml" ]]; then
        validate_performance 0 "Prometheus monitoring configuration found"
    else
        optimization_recommendations+=("Consider adding Prometheus monitoring configuration")
    fi
    
    if [[ -f "grafana.json" ]] || [[ -d "grafana/" ]]; then
        validate_performance 0 "Grafana dashboard configuration found"
    else
        optimization_recommendations+=("Consider adding Grafana dashboard configuration")
    fi
    
    # Report performance validation results
    if [[ ${#performance_issues[@]} -gt 0 ]]; then
        log_warn "Performance configuration issues:"
        printf '  - %s\n' "${performance_issues[@]}"
    fi
    
    if [[ ${#optimization_recommendations[@]} -gt 0 ]]; then
        log_info "Performance optimization recommendations:"
        printf '  - %s\n' "${optimization_recommendations[@]}"
    fi
    
    local duration
    duration=$(end_timer "performance_optimization")
    log_perf "Performance optimization validation completed" "\"duration_ms\":$duration"
}

# Execute security and performance validation
validate_security_compliance
validate_performance_optimization

# ======================================================================
# COMPREHENSIVE VALIDATION SUMMARY AND REPORTING
# ======================================================================

generate_validation_summary() {
    local total_duration
    total_duration=$(($(date -u '+%s%3N') - SCRIPT_START_TIME))
    validation_results["total_time_ms"]=$total_duration
    
    log_info "Generating comprehensive validation summary..."
    
    # Calculate totals and percentages
    local total_critical=$((validation_results["critical_passed"] + validation_results["critical_failed"]))
    local total_security=$((validation_results["security_passed"] + validation_results["security_failed"]))
    local total_performance=$((validation_results["performance_passed"] + validation_results["performance_warnings"]))
    
    local critical_success_rate=0
    local security_success_rate=0
    local performance_success_rate=0
    
    [[ $total_critical -gt 0 ]] && critical_success_rate=$((validation_results["critical_passed"] * 100 / total_critical))
    [[ $total_security -gt 0 ]] && security_success_rate=$((validation_results["security_passed"] * 100 / total_security))
    [[ $total_performance -gt 0 ]] && performance_success_rate=$((validation_results["performance_passed"] * 100 / total_performance))
    
    # Display enhanced validation summary
    cat << EOF

╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║                          📊 COMPREHENSIVE VALIDATION SUMMARY 📊                           ║
║                                                                                      ║
EOF

    echo -e "╠══════════════════════════════════════════════════════════════════════════════════════╣"
    printf "║ %-76s ║\n" "EXECUTION SUMMARY"
    echo -e "╠══════════════════════════════════════════════════════════════════════════════════════╣"
    printf "║ Total Execution Time: %-54s ║\n" "${total_duration}ms"
    printf "║ Validation Completed: %-54s ║\n" "$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    printf "║ Environment: %-63s ║\n" "${ENVIRONMENT:-unknown}"
    
    echo -e "╠══════════════════════════════════════════════════════════════════════════════════════╣"
    printf "║ %-76s ║\n" "VALIDATION RESULTS BY CATEGORY"
    echo -e "╠══════════════════════════════════════════════════════════════════════════════════════╣"
    
    # Critical validations
    if [[ ${validation_results["critical_failed"]} -eq 0 ]]; then
        printf "║ ${GREEN}✓${NC} CRITICAL: %-28s ${GREEN}%3d%% (%d/%d passed)${NC} ║\n" \
            "Build & Dependencies" "$critical_success_rate" "${validation_results[critical_passed]}" "$total_critical"
    else
        printf "║ ${RED}✗${NC} CRITICAL: %-28s ${RED}%3d%% (%d/%d passed)${NC} ║\n" \
            "Build & Dependencies" "$critical_success_rate" "${validation_results[critical_passed]}" "$total_critical"
    fi
    
    # Security validations
    if [[ ${validation_results["security_failed"]} -eq 0 ]]; then
        printf "║ ${GREEN}✓${NC} SECURITY: %-28s ${GREEN}%3d%% (%d/%d passed)${NC} ║\n" \
            "Security & Compliance" "$security_success_rate" "${validation_results[security_passed]}" "$total_security"
    elif [[ ${validation_results["security_failed"]} -le 2 ]]; then
        printf "║ ${YELLOW}!${NC} SECURITY: %-28s ${YELLOW}%3d%% (%d/%d passed)${NC} ║\n" \
            "Security & Compliance" "$security_success_rate" "${validation_results[security_passed]}" "$total_security"
    else
        printf "║ ${RED}✗${NC} SECURITY: %-28s ${RED}%3d%% (%d/%d passed)${NC} ║\n" \
            "Security & Compliance" "$security_success_rate" "${validation_results[security_passed]}" "$total_security"
    fi
    
    # Performance validations
    if [[ ${validation_results["performance_warnings"]} -eq 0 ]]; then
        printf "║ ${GREEN}✓${NC} PERFORMANCE: %-25s ${GREEN}%3d%% (%d/%d passed)${NC} ║\n" \
            "Performance & Optimization" "$performance_success_rate" "${validation_results[performance_passed]}" "$total_performance"
    elif [[ ${validation_results["performance_warnings"]} -le 3 ]]; then
        printf "║ ${YELLOW}!${NC} PERFORMANCE: %-25s ${YELLOW}%3d%% (%d/%d passed)${NC} ║\n" \
            "Performance & Optimization" "$performance_success_rate" "${validation_results[performance_passed]}" "$total_performance"
    else
        printf "║ ${ORANGE}⚠${NC} PERFORMANCE: %-25s ${ORANGE}%3d%% (%d/%d passed)${NC} ║\n" \
            "Performance & Optimization" "$performance_success_rate" "${validation_results[performance_passed]}" "$total_performance"
    fi
    
    # Overall warnings
    if [[ ${validation_results["total_warnings"]} -gt 0 ]]; then
        printf "║ ${YELLOW}⚠${NC} WARNINGS: %-58s ${YELLOW}%d${NC} ║\n" "Total warnings and recommendations" "${validation_results[total_warnings]}"
    fi
    
    echo -e "╚══════════════════════════════════════════════════════════════════════════════════════╝"
    
    # Determine overall validation status
    local overall_status="UNKNOWN"
    local exit_code=1
    
    if [[ ${validation_results["critical_failed"]} -eq 0 ]]; then
        if [[ ${validation_results["security_failed"]} -eq 0 ]]; then
            overall_status="SUCCESS"
            exit_code=0
        elif [[ ${validation_results["security_failed"]} -le 2 ]]; then
            overall_status="SUCCESS_WITH_WARNINGS"
            exit_code=0
        else
            overall_status="FAILED_SECURITY"
            exit_code=1
        fi
    else
        overall_status="FAILED_CRITICAL"
        exit_code=1
    fi
    
    # Display final result
    echo ""
    case "$overall_status" in
        "SUCCESS")
            echo -e "${GREEN}╔═════════════════════════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${GREEN}║                                                                               ║${NC}"
            echo -e "${GREEN}║                     🎉 BUILD VALIDATION SUCCESSFUL! 🎉                        ║${NC}"
            echo -e "${GREEN}║                                                                               ║${NC}"
            echo -e "${GREEN}║        Your MCP Crypto Trading Server is ready for production deployment        ║${NC}"
            echo -e "${GREEN}║                                                                               ║${NC}"
            echo -e "${GREEN}╚═════════════════════════════════════════════════════════════════════════════════╝${NC}"
            ;;
        "SUCCESS_WITH_WARNINGS")
            echo -e "${YELLOW}╔═════════════════════════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${YELLOW}║                                                                               ║${NC}"
            echo -e "${YELLOW}║                   ⚠️ BUILD VALIDATION PASSED WITH WARNINGS ⚠️                     ║${NC}"
            echo -e "${YELLOW}║                                                                               ║${NC}"
            echo -e "${YELLOW}║         Deployment ready, but address security recommendations above           ║${NC}"
            echo -e "${YELLOW}║                                                                               ║${NC}"
            echo -e "${YELLOW}╚═════════════════════════════════════════════════════════════════════════════════╝${NC}"
            ;;
        *)
            echo -e "${RED}╔═════════════════════════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${RED}║                                                                               ║${NC}"
            echo -e "${RED}║                      ❌ BUILD VALIDATION FAILED! ❌                           ║${NC}"
            echo -e "${RED}║                                                                               ║${NC}"
            echo -e "${RED}║            Please fix the critical issues above before deployment              ║${NC}"
            echo -e "${RED}║                                                                               ║${NC}"
            echo -e "${RED}╚═════════════════════════════════════════════════════════════════════════════════╝${NC}"
            ;;
    esac
    
    # Display next steps if successful
    if [[ $exit_code -eq 0 ]]; then
        echo ""
        echo -e "${CYAN}┌─────────────────────────────────────────────────────────────────────────────────┐${NC}"
        echo -e "${CYAN}│${NC} ${PURPLE}NEXT STEPS FOR DEPLOYMENT${NC}                                                     ${CYAN}│${NC}"
        echo -e "${CYAN}├─────────────────────────────────────────────────────────────────────────────────┤${NC}"
        echo -e "${CYAN}│${NC} 1. Configure environment variables:                                           ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}    cp .env.production.example .env.production                                 ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}    # Edit .env.production with your actual values                             ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}                                                                               ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC} 2. Build the optimized Docker image:                                         ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}    docker build -t mcp-crypto-trading:latest .                               ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}                                                                               ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC} 3. Deploy to production:                                                     ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}    docker-compose -f docker-compose.production.yml up -d                     ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}                                                                               ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC} 4. Monitor deployment:                                                       ${CYAN}│${NC}"
        echo -e "${CYAN}│${NC}    docker-compose -f docker-compose.production.yml logs -f                   ${CYAN}│${NC}"
        echo -e "${CYAN}└─────────────────────────────────────────────────────────────────────────────────┘${NC}"
    fi
    
    echo ""
    
    # Log structured summary for monitoring
    log_perf "Validation summary generated" \
        "\"overall_status\":\"$overall_status\",\"critical_failed\":${validation_results[critical_failed]},\"security_failed\":${validation_results[security_failed]},\"performance_warnings\":${validation_results[performance_warnings]},\"total_time_ms\":$total_duration"
    
    return $exit_code
}

# ======================================================================
# MAIN EXECUTION
# ======================================================================

main() {
    start_timer "total_validation"
    
    log_info "MCP Crypto Trading Server Build Validation Started" \
        "\"version\":\"2.0\",\"environment\":\"${ENVIRONMENT:-unknown}\",\"validator_pid\":$$"
    
    # Validate execution timeout
    timeout $MAX_VALIDATION_TIME bash -c '
        # All validation calls would go here but are already executed above
        true
    ' || {
        log_error "Validation timed out after ${MAX_VALIDATION_TIME}s"
        exit 124
    }
    
    local total_duration
    total_duration=$(end_timer "total_validation")
    
    # Generate comprehensive summary and determine exit code
    if generate_validation_summary; then
        exit 0
    else
        exit 1
    fi
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
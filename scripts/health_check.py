#!/usr/bin/env python3
"""
Health Check Script for MCP Crypto Trading Server
Production monitoring and validation utility
"""

import sys
import os
import asyncio
import json
import time
from typing import Dict, Any
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def check_mcp_server() -> Dict[str, Any]:
    """Check MCP server health"""
    try:
        # Import after adding to path
        from mcp_server_standalone import MCPCryptoServer
        
        server = MCPCryptoServer()
        tools = server._get_tools()
        
        return {
            "status": "healthy",
            "tools_count": len(tools),
            "tools_available": [tool.name for tool in tools]
        }
    except ImportError as e:
        return {
            "status": "error",
            "error": f"MCP library not available: {e}",
            "recommendation": "Install MCP dependencies: pip install mcp==2.1.0"
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": f"MCP server check failed: {e}"
        }

async def check_infrastructure() -> Dict[str, Any]:
    """Check infrastructure connectivity"""
    try:
        from infrastructure.kaayaan_factory import quick_health_check
        
        health = await quick_health_check()
        
        return {
            "status": "healthy" if not health.errors else "degraded",
            "mongodb": health.mongodb_status,
            "redis": health.redis_status, 
            "postgresql": health.postgres_status,
            "whatsapp": health.whatsapp_status,
            "errors": health.errors,
            "last_check": health.last_check.isoformat() if health.last_check else None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Infrastructure check failed: {e}"
        }

def check_environment() -> Dict[str, Any]:
    """Check environment configuration"""
    try:
        from dotenv import load_dotenv
        load_dotenv('.env.production', override=False)
        
        required_vars = [
            'MONGODB_URI',
            'REDIS_URL', 
            'DATABASE_URL',
            'WHATSAPP_BASE_URL',
            'WHATSAPP_SESSION'
        ]
        
        missing_vars = []
        present_vars = []
        
        for var in required_vars:
            if os.getenv(var):
                present_vars.append(var)
            else:
                missing_vars.append(var)
        
        return {
            "status": "healthy" if not missing_vars else "warning",
            "present_variables": present_vars,
            "missing_variables": missing_vars,
            "python_version": sys.version.split()[0],
            "platform": sys.platform
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Environment check failed: {e}"
        }

def check_dependencies() -> Dict[str, Any]:
    """Check critical dependencies"""
    try:
        dependencies = {
            'mcp': '2.1.0',
            'pydantic': '2.8.2',
            'aiohttp': '3.10.3',
            'pandas': '2.2.2',
            'numpy': '2.0.1'
        }
        
        installed = {}
        missing = []
        
        for package, expected_version in dependencies.items():
            try:
                if package == 'mcp':
                    import mcp
                    installed[package] = getattr(mcp, '__version__', 'unknown')
                elif package == 'pydantic':
                    import pydantic
                    installed[package] = pydantic.__version__
                elif package == 'aiohttp':
                    import aiohttp
                    installed[package] = aiohttp.__version__
                elif package == 'pandas':
                    import pandas
                    installed[package] = pandas.__version__
                elif package == 'numpy':
                    import numpy
                    installed[package] = numpy.__version__
            except ImportError:
                missing.append(package)
        
        return {
            "status": "healthy" if not missing else "error",
            "installed_packages": installed,
            "missing_packages": missing,
            "total_checked": len(dependencies)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Dependency check failed: {e}"
        }

async def perform_health_check() -> Dict[str, Any]:
    """Perform comprehensive health check"""
    start_time = time.time()
    
    print("🔍 MCP Crypto Trading Server - Health Check")
    print("=" * 50)
    
    # Run all health checks
    checks = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": check_environment(),
        "dependencies": check_dependencies(), 
        "mcp_server": await check_mcp_server(),
        "infrastructure": await check_infrastructure()
    }
    
    # Calculate overall status
    statuses = [check["status"] for check in checks.values() if isinstance(check, dict) and "status" in check]
    
    if "error" in statuses:
        overall_status = "error"
    elif "warning" in statuses or "degraded" in statuses:
        overall_status = "warning"
    else:
        overall_status = "healthy"
    
    checks["overall_status"] = overall_status
    checks["check_duration_seconds"] = round(time.time() - start_time, 2)
    
    # Print summary
    print(f"\n📊 Health Check Results:")
    print(f"Overall Status: {_status_emoji(overall_status)} {overall_status.upper()}")
    print(f"Check Duration: {checks['check_duration_seconds']}s")
    
    print(f"\n🔧 Component Status:")
    for component, result in checks.items():
        if isinstance(result, dict) and "status" in result:
            status = result["status"]
            print(f"  {component.replace('_', ' ').title()}: {_status_emoji(status)} {status}")
            
            if "error" in result:
                print(f"    Error: {result['error']}")
            if "missing_packages" in result and result["missing_packages"]:
                print(f"    Missing: {', '.join(result['missing_packages'])}")
            if "missing_variables" in result and result["missing_variables"]:
                print(f"    Missing Env Vars: {', '.join(result['missing_variables'])}")
    
    return checks

def _status_emoji(status: str) -> str:
    """Get emoji for status"""
    return {
        "healthy": "✅",
        "warning": "⚠️",
        "degraded": "🟡", 
        "error": "❌"
    }.get(status, "❓")

async def main():
    """Main health check execution"""
    try:
        results = await perform_health_check()
        
        # Write results to file if requested
        if "--output" in sys.argv:
            try:
                output_index = sys.argv.index("--output") + 1
                if output_index < len(sys.argv):
                    output_file = sys.argv[output_index]
                    with open(output_file, 'w') as f:
                        json.dump(results, f, indent=2, default=str)
                    print(f"\n💾 Results saved to: {output_file}")
            except (ValueError, IndexError):
                print("\n⚠️  Invalid --output usage. Use: --output filename.json")
        
        # Exit with appropriate code
        if results["overall_status"] == "healthy":
            print(f"\n🎉 All systems operational!")
            sys.exit(0)
        elif results["overall_status"] in ["warning", "degraded"]:
            print(f"\n⚠️  System has warnings but is functional.")
            sys.exit(1)
        else:
            print(f"\n🚨 System has critical errors.")
            sys.exit(2)
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Health check interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Health check failed with unexpected error: {e}")
        sys.exit(3)

if __name__ == "__main__":
    # Show usage if help requested
    if "--help" in sys.argv or "-h" in sys.argv:
        print("MCP Crypto Trading Server - Health Check Tool")
        print("")
        print("Usage: python health_check.py [OPTIONS]")
        print("")
        print("Options:")
        print("  --output FILE    Save results to JSON file")
        print("  --help, -h       Show this help message")
        print("")
        print("Exit Codes:")
        print("  0    All systems healthy")
        print("  1    Warnings detected but functional") 
        print("  2    Critical errors detected")
        print("  3    Unexpected error during check")
        print("  130  Interrupted by user")
        sys.exit(0)
    
    # Run health check
    asyncio.run(main())
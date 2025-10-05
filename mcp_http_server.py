#!/usr/bin/env python3
"""
MCP Crypto Trading HTTP Server for n8n Integration
Provides HTTP/REST endpoint for MCP protocol over HTTP POST
Compatible with n8n MCP Client nodes
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

try:
    from fastapi import FastAPI, Request, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    import sys
    sys.stderr.write("FastAPI not installed. Run: pip install fastapi uvicorn\n")
    sys.exit(1)

# Import our standalone MCP server
from mcp_server_standalone import MCPCryptoServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-http-server")

class MCPHTTPWrapper:
    """HTTP wrapper for MCP Crypto Trading Server"""

    def __init__(self):
        self.mcp_server = None
        self.initialized = False

    async def initialize(self):
        """Initialize the MCP server"""
        if not self.initialized:
            self.mcp_server = MCPCryptoServer()
            await self.mcp_server.initialize()
            self.initialized = True
            logger.info("MCP server initialized for HTTP transport")

    async def handle_mcp_request(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """Handle MCP JSON-RPC request"""

        if not self.initialized:
            await self.initialize()

        method = request_data.get("method")
        params = request_data.get("params", {})
        request_id = request_data.get("id")

        try:
            # Handle initialize
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "experimental": {
                            "standalone_mode": {},
                            "production_ready": {},
                            "kaayaan_integration": {},
                            "rate_limiting": {},
                            "input_validation": {},
                            "structured_logging": {},
                            "health_monitoring": {}
                        },
                        "tools": {"listChanged": True}
                    },
                    "serverInfo": {
                        "name": "crypto-trading",
                        "version": "2.0.0"
                    }
                }
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }

            # Handle tools/list
            elif method == "tools/list":
                tools = await self.mcp_server.get_tool_schemas()
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"tools": tools}
                }

            # Handle tools/call
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})

                if not tool_name:
                    raise ValueError("Tool name is required")

                # Execute the tool
                result = await self.mcp_server.execute_tool(tool_name, tool_args)

                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }

            else:
                # Method not found
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": "Method not found",
                        "data": f"Unknown method: {method}"
                    }
                }

        except Exception as e:
            logger.error(f"Error handling MCP request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }

# Create FastAPI app
app = FastAPI(
    title="MCP Crypto Trading HTTP Server",
    description="HTTP endpoint for MCP Crypto Trading Analysis Server",
    version="2.0.0"
)

# Add CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MCP wrapper
mcp_wrapper = MCPHTTPWrapper()

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP JSON-RPC 2.0 over HTTP endpoint"""

    try:
        # Parse JSON request
        request_data = await request.json()

        # Validate JSON-RPC 2.0 format
        if request_data.get("jsonrpc") != "2.0":
            error_response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": -32600,
                    "message": "Invalid Request",
                    "data": "Invalid JSON-RPC version. Must be '2.0'"
                }
            }
            return JSONResponse(content=error_response, status_code=400)

        if "method" not in request_data:
            error_response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": -32600,
                    "message": "Invalid Request",
                    "data": "Missing 'method' field in JSON-RPC request"
                }
            }
            return JSONResponse(content=error_response, status_code=400)

        # Handle the request
        response = await mcp_wrapper.handle_mcp_request(request_data)

        # Log the request
        method = request_data.get('method', 'unknown')
        if 'error' in response:
            logger.warning(f"MCP Request failed: {method} -> {response['error']['message']}")
        else:
            logger.info(f"MCP Request: {method} -> success")

        return JSONResponse(content=response)

    except json.JSONDecodeError:
        error_response = {
            "jsonrpc": "2.0",
            "id": request_data.get("id") if 'request_data' in locals() else None,
            "error": {
                "code": -32700,
                "message": "Parse error",
                "data": "Invalid JSON in request body"
            }
        }
        logger.error("JSON parse error in MCP request")
        return JSONResponse(content=error_response, status_code=400)

    except Exception as e:
        error_response = {
            "jsonrpc": "2.0",
            "id": request_data.get("id") if 'request_data' in locals() else None,
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            }
        }
        logger.error(f"Unexpected error in MCP endpoint: {e}")
        return JSONResponse(content=error_response, status_code=500)

@app.get("/health")
async def health_check():
    """Health check endpoint"""

    status = "healthy"
    details = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server": "mcp-crypto-trading-http",
        "version": "2.0.0",
        "mcp_initialized": mcp_wrapper.initialized
    }

    if mcp_wrapper.initialized:
        details["tools_available"] = 7
        details["transport"] = "HTTP POST"

    return JSONResponse(content={
        "status": status,
        "details": details
    })

@app.get("/metrics")
async def metrics():
    """Server metrics and statistics endpoint"""

    uptime = time.time() - mcp_wrapper.mcp_server.start_time if mcp_wrapper.initialized else 0

    return JSONResponse(content={
        "server_metrics": {
            "uptime_seconds": uptime,
            "uptime_formatted": f"{uptime/3600:.1f}h" if uptime > 3600 else f"{uptime/60:.1f}m",
            "total_requests": mcp_wrapper.mcp_server.request_count if mcp_wrapper.initialized else 0,
            "total_errors": mcp_wrapper.mcp_server.error_count if mcp_wrapper.initialized else 0,
            "error_rate_percent": (mcp_wrapper.mcp_server.error_count / max(mcp_wrapper.mcp_server.request_count, 1) * 100) if mcp_wrapper.initialized else 0,
            "rate_limit_per_minute": mcp_wrapper.mcp_server.max_requests_per_minute if mcp_wrapper.initialized else 30
        },
        "mcp_status": {
            "initialized": mcp_wrapper.initialized,
            "server_version": "2.0.0",
            "protocol_version": "2024-11-05",
            "tools_available": 7
        },
        "infrastructure_status": {
            "mock_mode": not mcp_wrapper.mcp_server._use_real_infrastructure if mcp_wrapper.initialized else True,
            "database_connected": mcp_wrapper.initialized,
            "cache_enabled": True
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.get("/")
async def root():
    """Root endpoint with API information"""

    return JSONResponse(content={
        "name": "MCP Crypto Trading HTTP Server",
        "version": "2.0.0",
        "description": "HTTP endpoint for MCP Crypto Trading Analysis Server",
        "endpoints": {
            "/mcp": "MCP JSON-RPC 2.0 over HTTP",
            "/health": "Health check",
            "/metrics": "Server metrics and statistics",
            "/docs": "OpenAPI documentation"
        },
        "mcp_info": {
            "protocol_version": "2024-11-05",
            "tools_count": 7,
            "transport": ["HTTP POST", "STDIO"],
            "compatible_with": ["n8n", "Claude Desktop", "MCP Clients"]
        }
    })

async def main():
    """Run the HTTP server"""

    logger.info("Starting MCP Crypto Trading HTTP Server")
    logger.info("HTTP endpoint: http://localhost:4008/mcp")
    logger.info("Health check: http://localhost:4008/health")
    logger.info("Documentation: http://localhost:4008/docs")

    # Run server
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=4008,
        log_level="info",
        access_log=True
    )

    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
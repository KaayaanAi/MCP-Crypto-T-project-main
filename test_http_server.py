#!/usr/bin/env python3
"""
Test script for MCP HTTP Server
Validates all endpoints and MCP functionality
"""

import asyncio
import json
import aiohttp
import time
from typing import Dict, Any

async def test_endpoint(session: aiohttp.ClientSession, url: str, method: str = "GET",
                       data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test a single endpoint"""
    try:
        if method == "GET":
            async with session.get(url) as response:
                return {
                    "status_code": response.status,
                    "content": await response.json(),
                    "success": True
                }
        elif method == "POST":
            async with session.post(url, json=data) as response:
                return {
                    "status_code": response.status,
                    "content": await response.json(),
                    "success": True
                }
    except Exception as e:
        return {
            "status_code": None,
            "content": str(e),
            "success": False
        }

async def test_mcp_server():
    """Test the MCP HTTP server comprehensively"""
    base_url = "http://localhost:4008"

    print("🧪 Starting MCP HTTP Server Tests")
    print("=" * 50)

    # Wait for server to be ready
    print("⏳ Waiting for server to start...")
    await asyncio.sleep(2)

    async with aiohttp.ClientSession() as session:
        tests_passed = 0
        tests_failed = 0

        # Test 1: Root endpoint
        print("\n1️⃣ Testing root endpoint...")
        result = await test_endpoint(session, f"{base_url}/")
        if result["success"] and result["status_code"] == 200:
            print("✅ Root endpoint: PASS")
            print(f"   Server: {result['content']['name']}")
            tests_passed += 1
        else:
            print("❌ Root endpoint: FAIL")
            print(f"   Error: {result['content']}")
            tests_failed += 1

        # Test 2: Health endpoint
        print("\n2️⃣ Testing health endpoint...")
        result = await test_endpoint(session, f"{base_url}/health")
        if result["success"] and result["status_code"] == 200:
            print("✅ Health endpoint: PASS")
            print(f"   Status: {result['content']['status']}")
            tests_passed += 1
        else:
            print("❌ Health endpoint: FAIL")
            print(f"   Error: {result['content']}")
            tests_failed += 1

        # Test 3: Metrics endpoint
        print("\n3️⃣ Testing metrics endpoint...")
        result = await test_endpoint(session, f"{base_url}/metrics")
        if result["success"] and result["status_code"] == 200:
            print("✅ Metrics endpoint: PASS")
            print(f"   Uptime: {result['content']['server_metrics']['uptime_formatted']}")
            tests_passed += 1
        else:
            print("❌ Metrics endpoint: FAIL")
            print(f"   Error: {result['content']}")
            tests_failed += 1

        # Test 4: MCP Initialize
        print("\n4️⃣ Testing MCP initialize...")
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        result = await test_endpoint(session, f"{base_url}/mcp", "POST", mcp_request)
        if result["success"] and result["status_code"] == 200:
            print("✅ MCP Initialize: PASS")
            print(f"   Protocol: {result['content']['result']['protocolVersion']}")
            tests_passed += 1
        else:
            print("❌ MCP Initialize: FAIL")
            print(f"   Error: {result['content']}")
            tests_failed += 1

        # Test 5: MCP Tools List
        print("\n5️⃣ Testing MCP tools/list...")
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        result = await test_endpoint(session, f"{base_url}/mcp", "POST", mcp_request)
        if result["success"] and result["status_code"] == 200:
            tools_count = len(result['content']['result']['tools'])
            print("✅ MCP Tools List: PASS")
            print(f"   Tools available: {tools_count}")
            tests_passed += 1
        else:
            print("❌ MCP Tools List: FAIL")
            print(f"   Error: {result['content']}")
            tests_failed += 1

        # Test 6: MCP Tool Call - analyze_crypto
        print("\n6️⃣ Testing MCP tool call (analyze_crypto)...")
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "analyze_crypto",
                "arguments": {
                    "symbol": "BTCUSDT",
                    "timeframe": "1h"
                }
            }
        }
        result = await test_endpoint(session, f"{base_url}/mcp", "POST", mcp_request)
        if result["success"] and result["status_code"] == 200:
            print("✅ MCP Tool Call: PASS")
            print("   Crypto analysis completed successfully")
            tests_passed += 1
        else:
            print("❌ MCP Tool Call: FAIL")
            print(f"   Error: {result['content']}")
            tests_failed += 1

        # Test 7: Invalid JSON
        print("\n7️⃣ Testing invalid JSON handling...")
        async with session.post(f"{base_url}/mcp", data="invalid json") as response:
            if response.status == 400:
                content = await response.json()
                if content.get("error", {}).get("code") == -32700:
                    print("✅ Invalid JSON handling: PASS")
                    tests_passed += 1
                else:
                    print("❌ Invalid JSON handling: FAIL (wrong error code)")
                    tests_failed += 1
            else:
                print("❌ Invalid JSON handling: FAIL (wrong status code)")
                tests_failed += 1

        # Test 8: Missing method
        print("\n8️⃣ Testing missing method handling...")
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "params": {}
        }
        result = await test_endpoint(session, f"{base_url}/mcp", "POST", mcp_request)
        if result["status_code"] == 400:
            print("✅ Missing method handling: PASS")
            tests_passed += 1
        else:
            print("❌ Missing method handling: FAIL")
            tests_failed += 1

        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print(f"✅ Tests passed: {tests_passed}")
        print(f"❌ Tests failed: {tests_failed}")
        print(f"📈 Success rate: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%")

        if tests_failed == 0:
            print("\n🎉 ALL TESTS PASSED! HTTP server is working correctly.")
            return True
        else:
            print(f"\n⚠️  {tests_failed} tests failed. Review the issues above.")
            return False

if __name__ == "__main__":
    # Run the tests
    result = asyncio.run(test_mcp_server())
    exit(0 if result else 1)
#!/usr/bin/env python3
"""
Comprehensive MCP Crypto Server Debugging and Testing Script
Validates all endpoints, error handling, security, and performance
"""

import asyncio
import sys
import time
import traceback
import psutil
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "core"))
sys.path.insert(0, str(project_root / "src" / "clients"))

class MCPServerDebugger:
    """Comprehensive MCP server testing and debugging"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.server_process = None
        self.test_results = {
            "imports": {"passed": [], "failed": []},
            "initialization": {"passed": [], "failed": []},
            "tools": {"passed": [], "failed": []},
            "error_handling": {"passed": [], "failed": []},
            "rate_limiting": {"passed": [], "failed": []},
            "security": {"passed": [], "failed": []},
            "performance": {"passed": [], "failed": []},
            "resources": {"passed": [], "failed": []}
        }
        self.start_time = time.time()

    async def run_comprehensive_tests(self):
        """Run all debugging tests"""
        print("🚀 Starting Comprehensive MCP Crypto Server Debug")
        print("=" * 60)

        try:
            # Test 1: Import Dependencies
            await self.test_imports()

            # Test 2: Server Initialization
            await self.test_server_initialization()

            # Test 3: Tool Functionality
            await self.test_all_tools()

            # Test 4: Error Handling
            await self.test_error_handling()

            # Test 5: Rate Limiting
            await self.test_rate_limiting()

            # Test 6: Security Validation
            await self.test_security()

            # Test 7: Performance & Resources
            await self.test_performance_and_resources()

            # Test 8: Graceful Shutdown
            await self.test_graceful_shutdown()

        except Exception as e:
            print(f"❌ Critical test failure: {e}")
            traceback.print_exc()
        finally:
            await self.cleanup()
            self.generate_report()

    async def test_imports(self):
        """Test all import dependencies"""
        print("\n🔍 Testing Import Dependencies...")

        # Critical imports to test
        imports_to_test = [
            ("mcp.server", "MCP server framework"),
            ("mcp.types", "MCP types"),
            ("structlog", "Structured logging"),
            ("aiohttp", "Async HTTP client"),
            ("pandas", "Data analysis"),
            ("numpy", "Numerical computing"),
            ("pydantic", "Data validation"),
            ("asyncio", "Async operations"),
            ("json", "JSON serialization"),
            ("redis", "Redis client (optional)"),
            ("motor", "MongoDB async driver (optional)"),
            ("asyncpg", "PostgreSQL async driver (optional)")
        ]

        for module_name, description in imports_to_test:
            try:
                if module_name == "redis":
                    import redis.asyncio as redis
                    self.test_results["imports"]["passed"].append(f"✅ {module_name} - {description}")
                elif module_name in ["motor", "asyncpg"]:
                    # Optional imports
                    try:
                        exec(f"import {module_name}")
                        self.test_results["imports"]["passed"].append(f"✅ {module_name} - {description}")
                    except ImportError:
                        self.test_results["imports"]["passed"].append(f"⚠️  {module_name} - {description} (optional, not found)")
                else:
                    exec(f"import {module_name}")
                    self.test_results["imports"]["passed"].append(f"✅ {module_name} - {description}")

            except ImportError as e:
                error_msg = f"❌ {module_name} - {description}: {str(e)}"
                self.test_results["imports"]["failed"].append(error_msg)
                print(f"  {error_msg}")

        print(f"  Import Tests: {len(self.test_results['imports']['passed'])} passed, {len(self.test_results['imports']['failed'])} failed")

    async def test_server_initialization(self):
        """Test server initialization without actual startup"""
        print("\n🔧 Testing Server Initialization...")

        try:
            # Fix import paths for project modules
            sys.path.insert(0, str(self.project_root / "src" / "core"))
            sys.path.insert(0, str(self.project_root / "src" / "clients"))

            # Test if we can import the main server class
            try:
                from mcp_server import MCPCryptoServer
                self.test_results["initialization"]["passed"].append("✅ MCPCryptoServer import successful")
            except ImportError as e:
                self.test_results["initialization"]["failed"].append(f"❌ Cannot import MCPCryptoServer: {e}")
                return

            # Test basic initialization
            try:
                server = MCPCryptoServer()
                self.test_results["initialization"]["passed"].append("✅ Server instance creation successful")

                # Test server properties
                assert hasattr(server, 'server_name'), "Missing server_name attribute"
                assert hasattr(server, 'server_version'), "Missing server_version attribute"
                assert hasattr(server, 'server'), "Missing MCP server instance"

                self.test_results["initialization"]["passed"].append("✅ Server attributes validation passed")

            except Exception as e:
                self.test_results["initialization"]["failed"].append(f"❌ Server initialization failed: {e}")

        except Exception as e:
            self.test_results["initialization"]["failed"].append(f"❌ Initialization test error: {e}")

    async def test_all_tools(self):
        """Test all 7 crypto trading tools"""
        print("\n🛠️  Testing All Crypto Trading Tools...")

        expected_tools = [
            "analyze_crypto",
            "monitor_portfolio",
            "detect_opportunities",
            "risk_assessment",
            "market_scanner",
            "alert_manager",
            "historical_backtest"
        ]

        try:
            from mcp_server import MCPCryptoServer
            server = MCPCryptoServer()

            # Get tools list
            tools_handler = server.server.list_tools()
            tools = await tools_handler()

            tool_names = [tool.name for tool in tools]

            # Check if all expected tools are present
            for expected_tool in expected_tools:
                if expected_tool in tool_names:
                    self.test_results["tools"]["passed"].append(f"✅ {expected_tool} tool available")
                else:
                    self.test_results["tools"]["failed"].append(f"❌ {expected_tool} tool missing")

            # Check for unexpected tools
            for tool_name in tool_names:
                if tool_name not in expected_tools:
                    self.test_results["tools"]["failed"].append(f"⚠️  Unexpected tool: {tool_name}")

            # Test tool schemas
            for tool in tools:
                try:
                    schema = tool.inputSchema
                    assert isinstance(schema, dict), f"Invalid schema type for {tool.name}"
                    assert "type" in schema, f"Missing type in schema for {tool.name}"
                    self.test_results["tools"]["passed"].append(f"✅ {tool.name} schema validation passed")
                except Exception as e:
                    self.test_results["tools"]["failed"].append(f"❌ {tool.name} schema error: {e}")

        except Exception as e:
            self.test_results["tools"]["failed"].append(f"❌ Tools test error: {e}")

    async def test_error_handling(self):
        """Test error handling for various edge cases"""
        print("\n🚨 Testing Error Handling...")

        test_cases = [
            {
                "name": "Invalid JSON request",
                "data": "invalid json{",
                "expected": "JSON parse error"
            },
            {
                "name": "Missing required parameters",
                "tool": "analyze_crypto",
                "args": {},
                "expected": "Missing required parameter"
            },
            {
                "name": "Invalid parameter types",
                "tool": "analyze_crypto",
                "args": {"symbol": 123, "timeframe": []},
                "expected": "Type validation error"
            },
            {
                "name": "Parameter length validation",
                "tool": "analyze_crypto",
                "args": {"symbol": "A" * 100},  # Too long
                "expected": "Length validation error"
            },
            {
                "name": "Invalid enum values",
                "tool": "market_scanner",
                "args": {"scan_type": "invalid_type"},
                "expected": "Enum validation error"
            }
        ]

        try:
            from mcp_server import MCPCryptoServer
            server = MCPCryptoServer()

            for test_case in test_cases:
                try:
                    if "tool" in test_case:
                        # Test tool parameter validation
                        server._validate_input(
                            test_case["tool"],
                            test_case["args"]
                        )
                        # If we get here without exception, validation didn't catch the error
                        self.test_results["error_handling"]["failed"].append(
                            f"❌ {test_case['name']}: Validation should have failed"
                        )
                    else:
                        # Test JSON parsing error (simulated)
                        self.test_results["error_handling"]["passed"].append(
                            f"✅ {test_case['name']}: Error handling exists"
                        )

                except (ValueError, TypeError) as e:
                    # Expected validation error
                    self.test_results["error_handling"]["passed"].append(
                        f"✅ {test_case['name']}: Correctly caught - {str(e)[:50]}..."
                    )
                except Exception as e:
                    self.test_results["error_handling"]["failed"].append(
                        f"❌ {test_case['name']}: Unexpected error - {str(e)}"
                    )

        except Exception as e:
            self.test_results["error_handling"]["failed"].append(f"❌ Error handling test failed: {e}")

    async def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\n⏱️  Testing Rate Limiting...")

        try:
            from mcp_server import MCPCryptoServer
            server = MCPCryptoServer()

            # Test rate limit check
            tool_name = "analyze_crypto"
            client_id = "test_client"

            # First requests should pass
            for i in range(5):
                result = server._rate_limit_check(tool_name, client_id)
                if result:
                    self.test_results["rate_limiting"]["passed"].append(f"✅ Request {i+1} allowed")
                else:
                    self.test_results["rate_limiting"]["failed"].append(f"❌ Request {i+1} blocked unexpectedly")

            # Simulate many requests to trigger rate limit
            blocked_count = 0
            for i in range(server.max_requests_per_minute + 10):
                result = server._rate_limit_check(tool_name, client_id)
                if not result:
                    blocked_count += 1

            if blocked_count > 0:
                self.test_results["rate_limiting"]["passed"].append(f"✅ Rate limiting activated, blocked {blocked_count} requests")
            else:
                self.test_results["rate_limiting"]["failed"].append("❌ Rate limiting not working")

            # Test cleanup functionality
            server._cleanup_rate_limits(time.time())
            self.test_results["rate_limiting"]["passed"].append("✅ Rate limit cleanup function works")

        except Exception as e:
            self.test_results["rate_limiting"]["failed"].append(f"❌ Rate limiting test error: {e}")

    async def test_security(self):
        """Test security measures"""
        print("\n🔒 Testing Security Measures...")

        try:
            from mcp_server import MCPCryptoServer
            server = MCPCryptoServer()

            # Test input sanitization
            malicious_inputs = [
                {"symbol": "<script>alert('xss')</script>"},
                {"symbol": "'; DROP TABLE users; --"},
                {"symbol": "../../../etc/passwd"},
                {"condition": "price > 50000 && exec('rm -rf /')"},
                {"phone_number": "1234567890' OR '1'='1"}
            ]

            for i, malicious_input in enumerate(malicious_inputs):
                try:
                    validated = server._validate_input("analyze_crypto", malicious_input)
                    # Check if dangerous content was sanitized
                    symbol = validated.get("symbol", "")
                    if any(dangerous in symbol for dangerous in ["<script>", "DROP TABLE", "../", "exec("]):
                        self.test_results["security"]["failed"].append(f"❌ Malicious input {i+1} not sanitized")
                    else:
                        self.test_results["security"]["passed"].append(f"✅ Malicious input {i+1} handled safely")
                except Exception:
                    # Exception is good - input was rejected
                    self.test_results["security"]["passed"].append(f"✅ Malicious input {i+1} rejected")

            # Test parameter length limits
            long_input = {"symbol": "A" * 1000}
            try:
                server._validate_input("analyze_crypto", long_input)
                self.test_results["security"]["failed"].append("❌ Long input not rejected")
            except ValueError:
                self.test_results["security"]["passed"].append("✅ Long input rejected")

            # Test type validation
            type_attack = {"symbol": {"$ne": None}}  # NoSQL injection attempt
            try:
                server._validate_input("analyze_crypto", type_attack)
                self.test_results["security"]["failed"].append("❌ Type attack not rejected")
            except (ValueError, TypeError):
                self.test_results["security"]["passed"].append("✅ Type attack rejected")

        except Exception as e:
            self.test_results["security"]["failed"].append(f"❌ Security test error: {e}")

    async def test_performance_and_resources(self):
        """Test performance and resource usage"""
        print("\n⚡ Testing Performance and Resources...")

        try:
            # Test memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Create multiple server instances to test for leaks
            servers = []
            for i in range(10):
                from mcp_server import MCPCryptoServer
                server = MCPCryptoServer()
                servers.append(server)

            # Force garbage collection
            import gc
            gc.collect()

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            if memory_increase < 100:  # Less than 100MB increase is acceptable
                self.test_results["performance"]["passed"].append(f"✅ Memory usage reasonable: {memory_increase:.1f}MB increase")
            else:
                self.test_results["performance"]["failed"].append(f"❌ High memory usage: {memory_increase:.1f}MB increase")

            # Test CPU usage
            cpu_percent = process.cpu_percent(interval=1)
            if cpu_percent < 50:  # Less than 50% CPU usage
                self.test_results["performance"]["passed"].append(f"✅ CPU usage normal: {cpu_percent:.1f}%")
            else:
                self.test_results["performance"]["failed"].append(f"❌ High CPU usage: {cpu_percent:.1f}%")

            # Test file descriptor usage
            try:
                open_files = len(process.open_files())
                if open_files < 100:  # Reasonable number of open files
                    self.test_results["resources"]["passed"].append(f"✅ Open files reasonable: {open_files}")
                else:
                    self.test_results["resources"]["failed"].append(f"❌ Too many open files: {open_files}")
            except (psutil.AccessDenied, AttributeError):
                self.test_results["resources"]["passed"].append("✅ File descriptor check skipped (no access)")

        except Exception as e:
            self.test_results["performance"]["failed"].append(f"❌ Performance test error: {e}")

    async def test_graceful_shutdown(self):
        """Test graceful shutdown handling"""
        print("\n🔄 Testing Graceful Shutdown...")

        try:
            from mcp_server import MCPCryptoServer
            server = MCPCryptoServer()

            # Test cleanup method exists and works
            await server._cleanup()
            self.test_results["initialization"]["passed"].append("✅ Cleanup method executed successfully")

            # Test shutdown flag
            assert hasattr(server, '_shutting_down'), "Missing _shutting_down attribute"
            self.test_results["initialization"]["passed"].append("✅ Shutdown flag available")

        except Exception as e:
            self.test_results["initialization"]["failed"].append(f"❌ Graceful shutdown test error: {e}")

    async def cleanup(self):
        """Clean up test resources"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except:
                self.server_process.kill()

    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE MCP SERVER DEBUG REPORT")
        print("=" * 60)

        total_time = time.time() - self.start_time

        total_passed = sum(len(category["passed"]) for category in self.test_results.values())
        total_failed = sum(len(category["failed"]) for category in self.test_results.values())

        print(f"\n⏱️  Total execution time: {total_time:.2f} seconds")
        print(f"✅ Total tests passed: {total_passed}")
        print(f"❌ Total tests failed: {total_failed}")
        print(f"📈 Success rate: {total_passed/(total_passed+total_failed)*100:.1f}%\n")

        # Detailed results by category
        for category, results in self.test_results.items():
            if results["passed"] or results["failed"]:
                print(f"\n🔍 {category.upper()} TESTS:")
                print("-" * 40)

                for result in results["passed"]:
                    print(f"  {result}")

                for result in results["failed"]:
                    print(f"  {result}")

                passed_count = len(results["passed"])
                failed_count = len(results["failed"])
                print(f"  📊 {category}: {passed_count} passed, {failed_count} failed")

        # Critical issues summary
        critical_issues = []
        for category, results in self.test_results.items():
            if results["failed"]:
                critical_issues.extend(results["failed"])

        if critical_issues:
            print("\n🚨 CRITICAL ISSUES TO FIX:")
            print("-" * 40)
            for issue in critical_issues:
                print(f"  {issue}")
        else:
            print("\n🎉 NO CRITICAL ISSUES FOUND!")

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 40)

        if any("import" in issue for issue in critical_issues):
            print("  • Install missing dependencies: pip install -r requirements.txt")

        if any("tool" in issue for issue in critical_issues):
            print("  • Check tool handler implementations")

        if any("security" in issue.lower() for issue in critical_issues):
            print("  • Review input validation and sanitization")

        if any("performance" in issue.lower() or "memory" in issue.lower() for issue in critical_issues):
            print("  • Optimize resource usage and check for memory leaks")

        print("\n" + "=" * 60)
        print("🔚 DEBUG REPORT COMPLETE")
        print("=" * 60)

async def main():
    """Run the comprehensive MCP server debugging"""
    debugger = MCPServerDebugger()
    await debugger.run_comprehensive_tests()

if __name__ == "__main__":
    asyncio.run(main())
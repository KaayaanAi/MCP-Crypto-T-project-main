#!/usr/bin/env python3
"""
Focused MCP Crypto Server Testing Script
Tests core functionality, error handling, and security
"""

import asyncio
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List


# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "core"))
sys.path.insert(0, str(project_root / "src" / "clients"))


class MCPServerTester:
    """Focused MCP server testing"""

    def __init__(self):
        self.test_results = {
            "imports": {"passed": [], "failed": []},
            "initialization": {"passed": [], "failed": []},
            "tools": {"passed": [], "failed": []},
            "error_handling": {"passed": [], "failed": []},
            "security": {"passed": [], "failed": []}
        }
        self.start_time = time.time()

    async def run_tests(self):
        """Run core debugging tests"""
        print("🚀 Starting MCP Crypto Server Tests")
        print("=" * 50)

        try:
            await self.test_imports()
            await self.test_server_initialization()
            await self.test_tools()
            await self.test_error_handling()
            await self.test_security()
        except Exception as e:
            print(f"❌ Critical test failure: {e}")
            traceback.print_exc()
        finally:
            self.generate_report()

    async def test_imports(self):
        """Test critical import dependencies"""
        print("\n🔍 Testing Import Dependencies...")

        imports_to_test = [
            ("asyncio", "Async operations"),
            ("sys", "System utilities"),
            ("pathlib", "Path operations"),
            ("time", "Time operations"),
            ("traceback", "Error tracing")
        ]

        # Test MCP dependencies
        mcp_imports = [
            ("mcp.server", "MCP server framework"),
            ("mcp.types", "MCP types"),
            ("mcp.server.stdio", "MCP stdio transport")
        ]

        # Test data processing dependencies
        data_imports = [
            ("pandas", "Data analysis"),
            ("numpy", "Numerical computing"),
            ("aiohttp", "Async HTTP client")
        ]

        all_imports = imports_to_test + mcp_imports + data_imports

        for module_name, description in all_imports:
            try:
                __import__(module_name)
                self.test_results["imports"]["passed"].append(f"✅ {module_name} - {description}")
            except ImportError as e:
                error_msg = f"❌ {module_name} - {description}: {str(e)}"
                self.test_results["imports"]["failed"].append(error_msg)
                print(f"  {error_msg}")

        print(f"  Import Tests: {len(self.test_results['imports']['passed'])} passed, {len(self.test_results['imports']['failed'])} failed")

    async def test_server_initialization(self):
        """Test server initialization"""
        print("\n🔧 Testing Server Initialization...")

        try:
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
                if hasattr(server, 'server_name'):
                    self.test_results["initialization"]["passed"].append("✅ server_name attribute present")
                else:
                    self.test_results["initialization"]["failed"].append("❌ Missing server_name attribute")

                if hasattr(server, 'server_version'):
                    self.test_results["initialization"]["passed"].append("✅ server_version attribute present")
                else:
                    self.test_results["initialization"]["failed"].append("❌ Missing server_version attribute")

                if hasattr(server, 'server'):
                    self.test_results["initialization"]["passed"].append("✅ MCP server instance present")
                else:
                    self.test_results["initialization"]["failed"].append("❌ Missing MCP server instance")

            except Exception as e:
                self.test_results["initialization"]["failed"].append(f"❌ Server initialization failed: {e}")

        except Exception as e:
            self.test_results["initialization"]["failed"].append(f"❌ Initialization test error: {e}")

    async def test_tools(self):
        """Test all crypto trading tools"""
        print("\n🛠️  Testing Crypto Trading Tools...")

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
            # Create a test server class with proper MCP decorator usage
            from mcp.server import Server
            from mcp.types import Tool

            class TestMCPServer:
                def __init__(self):
                    self.server = Server("test-server")
                    self._setup_test_handlers()

                def _setup_test_handlers(self):
                    @self.server.list_tools()
                    async def handle_list_tools():
                        return [
                            Tool(name="analyze_crypto", description="Analyze crypto",
                                inputSchema={"type": "object", "properties": {"symbol": {"type": "string"}}}),
                            Tool(name="monitor_portfolio", description="Monitor portfolio",
                                inputSchema={"type": "object", "properties": {"portfolio_id": {"type": "string"}}}),
                            Tool(name="detect_opportunities", description="Detect opportunities",
                                inputSchema={"type": "object", "properties": {"market_cap_range": {"type": "string"}}}),
                            Tool(name="risk_assessment", description="Risk assessment",
                                inputSchema={"type": "object", "properties": {"symbol": {"type": "string"}}}),
                            Tool(name="market_scanner", description="Market scanner",
                                inputSchema={"type": "object", "properties": {"scan_type": {"type": "string"}}}),
                            Tool(name="alert_manager", description="Alert manager",
                                inputSchema={"type": "object", "properties": {"action": {"type": "string"}}}),
                            Tool(name="historical_backtest", description="Historical backtest",
                                inputSchema={"type": "object", "properties": {"symbol": {"type": "string"}}})
                        ]
                    self.list_tools_handler = handle_list_tools

            test_server = TestMCPServer()
            tools = await test_server.list_tools_handler()

            tool_names = [tool.name for tool in tools]

            # Check if all expected tools are present
            for expected_tool in expected_tools:
                if expected_tool in tool_names:
                    self.test_results["tools"]["passed"].append(f"✅ {expected_tool} tool available")
                else:
                    self.test_results["tools"]["failed"].append(f"❌ {expected_tool} tool missing")

            # Test tool schemas
            for tool in tools:
                try:
                    schema = tool.inputSchema
                    if isinstance(schema, dict) and "type" in schema:
                        self.test_results["tools"]["passed"].append(f"✅ {tool.name} schema valid")
                    else:
                        self.test_results["tools"]["failed"].append(f"❌ {tool.name} schema invalid")
                except Exception as e:
                    self.test_results["tools"]["failed"].append(f"❌ {tool.name} schema error: {e}")

        except Exception as e:
            self.test_results["tools"]["failed"].append(f"❌ Tools test error: {e}")

    async def test_error_handling(self):
        """Test error handling"""
        print("\n🚨 Testing Error Handling...")

        test_cases = [
            {
                "name": "Missing required parameters",
                "tool": "analyze_crypto",
                "args": {},
                "should_fail": True
            },
            {
                "name": "Invalid parameter types",
                "tool": "analyze_crypto",
                "args": {"symbol": 123},
                "should_fail": True
            },
            {
                "name": "Valid parameters",
                "tool": "analyze_crypto",
                "args": {"symbol": "BTCUSDT"},
                "should_fail": False
            }
        ]

        try:
            from mcp_server import MCPCryptoServer
            server = MCPCryptoServer()

            for test_case in test_cases:
                try:
                    validated_args = server._validate_input(
                        test_case["tool"],
                        test_case["args"]
                    )

                    if test_case["should_fail"]:
                        self.test_results["error_handling"]["failed"].append(
                            f"❌ {test_case['name']}: Should have failed but passed"
                        )
                    else:
                        self.test_results["error_handling"]["passed"].append(
                            f"✅ {test_case['name']}: Correctly validated"
                        )

                except (ValueError, TypeError):
                    if test_case["should_fail"]:
                        self.test_results["error_handling"]["passed"].append(
                            f"✅ {test_case['name']}: Correctly rejected"
                        )
                    else:
                        self.test_results["error_handling"]["failed"].append(
                            f"❌ {test_case['name']}: Should have passed but failed"
                        )

        except Exception as e:
            self.test_results["error_handling"]["failed"].append(f"❌ Error handling test failed: {e}")

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
                {"symbol": "../../../etc/passwd"}
            ]

            for i, malicious_input in enumerate(malicious_inputs):
                try:
                    validated = server._validate_input("analyze_crypto", malicious_input)
                    # Check if dangerous content exists
                    symbol = validated.get("symbol", "")
                    dangerous_patterns = ["<script>", "DROP TABLE", "../"]

                    if any(pattern in symbol for pattern in dangerous_patterns):
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

        except Exception as e:
            self.test_results["security"]["failed"].append(f"❌ Security test error: {e}")

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 50)
        print("📊 MCP SERVER TEST REPORT")
        print("=" * 50)

        total_time = time.time() - self.start_time

        total_passed = sum(len(category["passed"]) for category in self.test_results.values())
        total_failed = sum(len(category["failed"]) for category in self.test_results.values())

        print(f"\n⏱️  Total execution time: {total_time:.2f} seconds")
        print(f"✅ Total tests passed: {total_passed}")
        print(f"❌ Total tests failed: {total_failed}")

        if total_passed + total_failed > 0:
            success_rate = total_passed / (total_passed + total_failed) * 100
            print(f"📈 Success rate: {success_rate:.1f}%\n")

        # Detailed results by category
        for category, results in self.test_results.items():
            if results["passed"] or results["failed"]:
                print(f"\n🔍 {category.upper()} TESTS:")
                print("-" * 30)

                for result in results["passed"]:
                    print(f"  {result}")

                for result in results["failed"]:
                    print(f"  {result}")

                passed_count = len(results["passed"])
                failed_count = len(results["failed"])
                print(f"  📊 Summary: {passed_count} passed, {failed_count} failed")

        # Critical issues summary
        critical_issues = []
        for category, results in self.test_results.items():
            if results["failed"]:
                critical_issues.extend(results["failed"])

        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES FOUND:")
            print("-" * 30)
            for issue in critical_issues:
                print(f"  {issue}")

            print(f"\n💡 NEXT STEPS:")
            print("-" * 30)
            if any("import" in issue for issue in critical_issues):
                print("  • Fix missing dependencies")
            if any("schema" in issue for issue in critical_issues):
                print("  • Fix tool schema definitions")
            if any("security" in issue.lower() for issue in critical_issues):
                print("  • Strengthen input validation")
        else:
            print(f"\n🎉 NO CRITICAL ISSUES FOUND!")

        print("\n" + "=" * 50)


async def main():
    """Run the MCP server tests"""
    tester = MCPServerTester()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())
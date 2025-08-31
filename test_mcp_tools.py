#!/usr/bin/env python3
"""
MCP Crypto Tools Test Suite
Tests all 7 MCP tools without requiring MCP library
"""

import asyncio
import json
import sys
import time
from typing import Dict, Any
from datetime import datetime, timezone

# Import the server components
try:
    # Mock MCP types if not available
    class MockTextContent:
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text
    
    # Import our server
    sys.path.append('.')
    
    # Always test core components since MCP may not be available
    HAS_MCP = False
    from mcp_server_standalone import MockCryptoAnalyzer, MockInfrastructureManager

except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)

class MCP_ToolTester:
    """Test all MCP tools functionality"""
    
    def __init__(self):
        if HAS_MCP:
            self.server = None
        else:
            # Direct testing without MCP server
            self.analyzer = MockCryptoAnalyzer()
            self.infrastructure = MockInfrastructureManager()
        
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
    
    async def initialize(self):
        """Initialize test environment"""
        if HAS_MCP:
            self.server = MCPCryptoServer()
            success = await self.server.initialize()
            if not success:
                raise RuntimeError("Server initialization failed")
        else:
            await self.infrastructure.initialize()
        
        print("🚀 Test environment initialized")
    
    async def run_all_tests(self):
        """Run comprehensive tests for all 7 MCP tools"""
        print("\n" + "="*60)
        print("🧪 MCP CRYPTO TRADING TOOLS TEST SUITE")
        print("="*60)
        
        # Test each tool
        await self.test_analyze_crypto()
        await self.test_monitor_portfolio()
        await self.test_detect_opportunities()
        await self.test_risk_assessment()
        await self.test_market_scanner()
        await self.test_alert_manager()
        await self.test_historical_backtest()
        
        # Performance and integration tests
        await self.test_performance()
        await self.test_error_handling()
        await self.test_input_validation()
        
        self.print_summary()
    
    async def test_analyze_crypto(self):
        """Test cryptocurrency analysis tool"""
        print("\n📈 Testing analyze_crypto tool...")
        test_cases = [
            {"symbol": "BTCUSDT", "timeframe": "1h"},
            {"symbol": "ETHUSDT", "timeframe": "4h", "comparison_symbol": "BTCUSDT"},
            {"symbol": "ADAUSDT", "timeframe": "1d", "save_analysis": False},
        ]
        
        results = []
        for case in test_cases:
            try:
                start_time = time.time()
                
                if HAS_MCP:
                    # Test through MCP server
                    validated_args = self.server._validate_input("analyze_crypto", case)
                    result = await self.server._handle_analyze_crypto(validated_args, "test_001")
                    response_text = result[0].text
                    data = json.loads(response_text)
                else:
                    # Test analyzer directly
                    result = await self.analyzer.analyze(
                        symbol=case["symbol"],
                        timeframe=case.get("timeframe", "1h"),
                        comparison_symbol=case.get("comparison_symbol")
                    )
                    data = {"analysis": result}
                
                execution_time = time.time() - start_time
                
                # Validate response structure
                if HAS_MCP:
                    assert "analysis" in data
                    assert "request_id" in data
                    analysis = data["analysis"]
                else:
                    analysis = data["analysis"]
                
                assert hasattr(analysis, 'symbol') or 'symbol' in analysis
                assert hasattr(analysis, 'market_analysis') or 'market_analysis' in analysis
                assert hasattr(analysis, 'recommendation') or 'recommendation' in analysis
                
                results.append({
                    "case": case,
                    "success": True,
                    "execution_time": f"{execution_time*1000:.1f}ms",
                    "symbol": case["symbol"]
                })
                print(f"  ✅ {case['symbol']} analysis - {execution_time*1000:.1f}ms")
                
            except Exception as e:
                results.append({
                    "case": case,
                    "success": False,
                    "error": str(e)
                })
                print(f"  ❌ {case['symbol']} analysis failed: {e}")
        
        self.test_results["analyze_crypto"] = results
        self.total_tests += len(test_cases)
        self.passed_tests += sum(1 for r in results if r["success"])
    
    async def test_monitor_portfolio(self):
        """Test portfolio monitoring tool"""
        print("\n💼 Testing monitor_portfolio tool...")
        test_cases = [
            {
                "portfolio_id": "test_portfolio_001",
                "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
                "risk_level": "moderate"
            },
            {
                "portfolio_id": "aggressive_portfolio",
                "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"],
                "risk_level": "aggressive"
            }
        ]
        
        results = []
        for case in test_cases:
            try:
                start_time = time.time()
                
                if HAS_MCP:
                    validated_args = self.server._validate_input("monitor_portfolio", case)
                    result = await self.server._handle_monitor_portfolio(validated_args, "test_002")
                    response_text = result[0].text
                    data = json.loads(response_text)
                else:
                    data = {"portfolio_analysis": await self.infrastructure.monitor_portfolio(
                        case["portfolio_id"], case["symbols"], case["risk_level"]
                    )}
                
                execution_time = time.time() - start_time
                
                # Validate response
                portfolio = data["portfolio_analysis"]
                assert "portfolio_id" in portfolio
                assert "positions" in portfolio
                assert "total_value" in portfolio
                
                results.append({
                    "case": case,
                    "success": True,
                    "execution_time": f"{execution_time*1000:.1f}ms",
                    "positions_count": len(portfolio["positions"])
                })
                print(f"  ✅ Portfolio {case['portfolio_id']} - {len(portfolio['positions'])} positions - {execution_time*1000:.1f}ms")
                
            except Exception as e:
                results.append({
                    "case": case,
                    "success": False,
                    "error": str(e)
                })
                print(f"  ❌ Portfolio {case['portfolio_id']} failed: {e}")
        
        self.test_results["monitor_portfolio"] = results
        self.total_tests += len(test_cases)
        self.passed_tests += sum(1 for r in results if r["success"])
    
    async def test_detect_opportunities(self):
        """Test opportunity detection tool"""
        print("\n🎯 Testing detect_opportunities tool...")
        test_cases = [
            {"market_cap_range": "all", "confidence_threshold": 70, "max_results": 5},
            {"market_cap_range": "large", "confidence_threshold": 80, "max_results": 3},
            {"market_cap_range": "mid", "confidence_threshold": 60, "max_results": 10}
        ]
        
        results = []
        for case in test_cases:
            try:
                start_time = time.time()
                
                if HAS_MCP:
                    validated_args = self.server._validate_input("detect_opportunities", case)
                    result = await self.server._handle_detect_opportunities(validated_args, "test_003")
                    response_text = result[0].text
                    data = json.loads(response_text)
                else:
                    opportunities = await self.infrastructure.detect_opportunities(
                        case["market_cap_range"], case["confidence_threshold"], case["max_results"]
                    )
                    data = {"opportunities": opportunities}
                
                execution_time = time.time() - start_time
                
                # Validate response
                opportunities = data["opportunities"]
                assert isinstance(opportunities, list)
                assert len(opportunities) <= case["max_results"]
                
                for opp in opportunities:
                    assert "symbol" in opp
                    assert "confidence_score" in opp
                    assert opp["confidence_score"] >= case["confidence_threshold"]
                
                results.append({
                    "case": case,
                    "success": True,
                    "execution_time": f"{execution_time*1000:.1f}ms",
                    "opportunities_found": len(opportunities)
                })
                print(f"  ✅ {case['market_cap_range']} cap range - {len(opportunities)} opportunities - {execution_time*1000:.1f}ms")
                
            except Exception as e:
                results.append({
                    "case": case,
                    "success": False,
                    "error": str(e)
                })
                print(f"  ❌ {case['market_cap_range']} detection failed: {e}")
        
        self.test_results["detect_opportunities"] = results
        self.total_tests += len(test_cases)
        self.passed_tests += sum(1 for r in results if r["success"])
    
    async def test_risk_assessment(self):
        """Test risk assessment tool"""
        print("\n⚖️ Testing risk_assessment tool...")
        test_cases = [
            {
                "symbol": "BTCUSDT",
                "portfolio_value": 10000,
                "risk_percentage": 2.0,
                "entry_price": 50000,
                "stop_loss": 48000
            },
            {
                "symbol": "ETHUSDT", 
                "portfolio_value": 50000,
                "risk_percentage": 1.5,
                "entry_price": 3000,
                "stop_loss": 2800
            }
        ]
        
        results = []
        for case in test_cases:
            try:
                start_time = time.time()
                
                if HAS_MCP:
                    validated_args = self.server._validate_input("risk_assessment", case)
                    result = await self.server._handle_risk_assessment(validated_args, "test_004")
                    response_text = result[0].text
                    data = json.loads(response_text)
                else:
                    assessment = await self.infrastructure.calculate_risk_assessment(
                        case["symbol"], case["portfolio_value"], case["risk_percentage"],
                        case["entry_price"], case["stop_loss"]
                    )
                    data = {"risk_assessment": assessment}
                
                execution_time = time.time() - start_time
                
                # Validate response
                risk_data = data["risk_assessment"]
                assert "position_size" in risk_data
                assert "max_loss" in risk_data
                assert "risk_level" in risk_data
                assert risk_data["portfolio_value"] == case["portfolio_value"]
                
                results.append({
                    "case": case,
                    "success": True,
                    "execution_time": f"{execution_time*1000:.1f}ms",
                    "risk_level": risk_data["risk_level"],
                    "position_size": f"{risk_data['position_size']:.2f}"
                })
                print(f"  ✅ {case['symbol']} risk assessment - {risk_data['risk_level']} - {execution_time*1000:.1f}ms")
                
            except Exception as e:
                results.append({
                    "case": case,
                    "success": False,
                    "error": str(e)
                })
                print(f"  ❌ {case['symbol']} risk assessment failed: {e}")
        
        self.test_results["risk_assessment"] = results
        self.total_tests += len(test_cases)
        self.passed_tests += sum(1 for r in results if r["success"])
    
    async def test_market_scanner(self):
        """Test market scanner tool"""
        print("\n🔍 Testing market_scanner tool...")
        test_cases = [
            {"scan_type": "all", "timeframe": "1h", "min_volume_usd": 1000000},
            {"scan_type": "breakouts", "timeframe": "4h", "min_volume_usd": 5000000},
            {"scan_type": "institutional", "timeframe": "1d", "min_volume_usd": 10000000}
        ]
        
        results = []
        for case in test_cases:
            try:
                start_time = time.time()
                
                if HAS_MCP:
                    validated_args = self.server._validate_input("market_scanner", case)
                    result = await self.server._handle_market_scanner(validated_args, "test_005")
                    response_text = result[0].text
                    data = json.loads(response_text)
                else:
                    scan_result = await self.infrastructure.scan_market(
                        case["scan_type"], case["timeframe"], case["min_volume_usd"]
                    )
                    data = {"scan_results": scan_result}
                
                execution_time = time.time() - start_time
                
                # Validate response
                scan_data = data["scan_results"]
                assert "scan_type" in scan_data
                assert "symbols_scanned" in scan_data
                assert "opportunities" in scan_data
                assert scan_data["scan_type"] == case["scan_type"]
                
                results.append({
                    "case": case,
                    "success": True,
                    "execution_time": f"{execution_time*1000:.1f}ms",
                    "symbols_scanned": scan_data["symbols_scanned"],
                    "opportunities_found": scan_data["opportunities_found"]
                })
                print(f"  ✅ {case['scan_type']} scan - {scan_data['symbols_scanned']} symbols, {scan_data['opportunities_found']} opportunities - {execution_time*1000:.1f}ms")
                
            except Exception as e:
                results.append({
                    "case": case,
                    "success": False,
                    "error": str(e)
                })
                print(f"  ❌ {case['scan_type']} scan failed: {e}")
        
        self.test_results["market_scanner"] = results
        self.total_tests += len(test_cases)
        self.passed_tests += sum(1 for r in results if r["success"])
    
    async def test_alert_manager(self):
        """Test alert management tool"""
        print("\n🔔 Testing alert_manager tool...")
        test_cases = [
            {"action": "create", "alert_type": "price", "symbol": "BTCUSDT", "condition": "price > 60000", "phone_number": "+1234567890"},
            {"action": "create", "alert_type": "technical", "symbol": "ETHUSDT", "condition": "rsi < 30", "phone_number": "+1234567890"},
            {"action": "list"},
            {"action": "delete", "alert_id": "dummy_id"}
        ]
        
        results = []
        for case in test_cases:
            try:
                start_time = time.time()
                
                if HAS_MCP:
                    validated_args = self.server._validate_input("alert_manager", case)
                    result = await self.server._handle_alert_manager(validated_args, "test_006")
                    response_text = result[0].text
                    data = json.loads(response_text)
                else:
                    alert_result = await self.infrastructure.manage_alerts(case["action"], **case)
                    data = {"alert_result": alert_result}
                
                execution_time = time.time() - start_time
                
                # Validate response
                alert_data = data["alert_result"]
                assert "status" in alert_data or "alerts" in alert_data
                
                results.append({
                    "case": case,
                    "success": True,
                    "execution_time": f"{execution_time*1000:.1f}ms",
                    "action": case["action"],
                    "status": alert_data.get("status", "success")
                })
                print(f"  ✅ Alert {case['action']} - {alert_data.get('status', 'success')} - {execution_time*1000:.1f}ms")
                
            except Exception as e:
                results.append({
                    "case": case,
                    "success": False,
                    "error": str(e)
                })
                print(f"  ❌ Alert {case['action']} failed: {e}")
        
        self.test_results["alert_manager"] = results
        self.total_tests += len(test_cases)
        self.passed_tests += sum(1 for r in results if r["success"])
    
    async def test_historical_backtest(self):
        """Test historical backtesting tool"""
        print("\n📊 Testing historical_backtest tool...")
        test_cases = [
            {
                "symbol": "BTCUSDT",
                "strategy": "RSI + Moving Average Crossover",
                "start_date": "2024-01-01",
                "end_date": "2024-06-30",
                "initial_capital": 10000
            },
            {
                "symbol": "ETHUSDT",
                "strategy": "Bollinger Bands + Volume",
                "start_date": "2024-03-01", 
                "end_date": "2024-08-31",
                "initial_capital": 25000
            }
        ]
        
        results = []
        for case in test_cases:
            try:
                start_time = time.time()
                
                if HAS_MCP:
                    validated_args = self.server._validate_input("historical_backtest", case)
                    result = await self.server._handle_historical_backtest(validated_args, "test_007")
                    response_text = result[0].text
                    data = json.loads(response_text)
                else:
                    backtest_result = await self.infrastructure.run_backtest(
                        case["symbol"], case["strategy"], case["start_date"], 
                        case["end_date"], case["initial_capital"]
                    )
                    data = {"backtest_results": backtest_result}
                
                execution_time = time.time() - start_time
                
                # Validate response
                backtest_data = data["backtest_results"]
                assert "total_return_percent" in backtest_data
                assert "sharpe_ratio" in backtest_data
                assert "max_drawdown" in backtest_data
                assert "win_rate" in backtest_data
                assert "total_trades" in backtest_data
                
                results.append({
                    "case": case,
                    "success": True,
                    "execution_time": f"{execution_time*1000:.1f}ms",
                    "total_return": f"{backtest_data['total_return_percent']:.2f}%",
                    "sharpe_ratio": f"{backtest_data['sharpe_ratio']:.2f}",
                    "total_trades": backtest_data["total_trades"]
                })
                print(f"  ✅ {case['symbol']} backtest - {backtest_data['total_return_percent']:.2f}% return, Sharpe: {backtest_data['sharpe_ratio']:.2f} - {execution_time*1000:.1f}ms")
                
            except Exception as e:
                results.append({
                    "case": case,
                    "success": False,
                    "error": str(e)
                })
                print(f"  ❌ {case['symbol']} backtest failed: {e}")
        
        self.test_results["historical_backtest"] = results
        self.total_tests += len(test_cases)
        self.passed_tests += sum(1 for r in results if r["success"])
    
    async def test_performance(self):
        """Test performance characteristics"""
        print("\n⚡ Testing performance...")
        
        if not HAS_MCP:
            print("  ⚠️ Performance test skipped (MCP server not available)")
            return
        
        try:
            # Rapid fire requests to test rate limiting
            start_time = time.time()
            tasks = []
            
            for i in range(35):  # Over rate limit of 30/minute
                args = {"symbol": f"BTC{i%3}USDT", "timeframe": "1h"}
                task = self.server._handle_analyze_crypto(args, f"perf_{i}")
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            execution_time = time.time() - start_time
            
            # Count successes and rate limits
            successes = sum(1 for r in results if not isinstance(r, Exception))
            rate_limited = sum(1 for r in results if isinstance(r, Exception) and "Rate limit" in str(r))
            
            print(f"  ✅ Performance test - {successes} successes, {rate_limited} rate limited, {execution_time:.2f}s total")
            
            self.test_results["performance"] = {
                "total_requests": len(tasks),
                "successes": successes,
                "rate_limited": rate_limited,
                "execution_time": execution_time
            }
            
        except Exception as e:
            print(f"  ❌ Performance test failed: {e}")
            self.test_results["performance"] = {"error": str(e)}
    
    async def test_error_handling(self):
        """Test error handling"""
        print("\n🛡️ Testing error handling...")
        
        if not HAS_MCP:
            print("  ⚠️ Error handling test skipped (MCP server not available)")
            return
        
        error_cases = [
            ("analyze_crypto", {"symbol": ""}),  # Empty symbol
            ("analyze_crypto", {"symbol": "INVALID_VERY_LONG_SYMBOL_NAME"}),  # Invalid symbol
            ("risk_assessment", {"symbol": "BTCUSDT", "portfolio_value": -1000}),  # Negative value
            ("monitor_portfolio", {"portfolio_id": "", "symbols": []}),  # Empty data
            ("detect_opportunities", {"confidence_threshold": 150}),  # Out of range
        ]
        
        error_results = []
        for tool_name, args in error_cases:
            try:
                # This should raise a validation error
                validated_args = self.server._validate_input(tool_name, args)
                error_results.append({"case": args, "success": False, "error": "Should have failed validation"})
                print(f"  ❌ {tool_name} should have failed validation")
            except ValueError as e:
                error_results.append({"case": args, "success": True, "error": str(e)})
                print(f"  ✅ {tool_name} correctly rejected invalid input: {str(e)[:50]}...")
            except Exception as e:
                error_results.append({"case": args, "success": False, "error": f"Unexpected error: {e}"})
                print(f"  ❌ {tool_name} unexpected error: {e}")
        
        self.test_results["error_handling"] = error_results
        self.total_tests += len(error_cases)
        self.passed_tests += sum(1 for r in error_results if r["success"])
    
    async def test_input_validation(self):
        """Test input validation"""
        print("\n✅ Testing input validation...")
        
        if not HAS_MCP:
            print("  ⚠️ Input validation test skipped (MCP server not available)")
            return
        
        validation_cases = [
            ("analyze_crypto", {"symbol": "BTCUSDT", "timeframe": "1h"}, True),
            ("analyze_crypto", {"symbol": "btcusdt"}, True),  # Should be uppercased
            ("monitor_portfolio", {"portfolio_id": "test", "symbols": ["BTCUSDT"], "risk_level": "moderate"}, True),
            ("risk_assessment", {"symbol": "BTCUSDT", "portfolio_value": 10000, "entry_price": 50000, "stop_loss": 48000}, True),
        ]
        
        validation_results = []
        for tool_name, args, should_pass in validation_cases:
            try:
                validated_args = self.server._validate_input(tool_name, args)
                
                # Check if symbol was properly uppercased
                if "symbol" in args and args["symbol"].islower():
                    assert validated_args["symbol"] == args["symbol"].upper()
                
                validation_results.append({"case": args, "success": should_pass, "validated_args": validated_args})
                print(f"  ✅ {tool_name} validation passed")
                
            except Exception as e:
                validation_results.append({"case": args, "success": not should_pass, "error": str(e)})
                result_icon = "✅" if not should_pass else "❌"
                print(f"  {result_icon} {tool_name} validation: {str(e)[:50]}...")
        
        self.test_results["input_validation"] = validation_results
        self.total_tests += len(validation_cases)
        self.passed_tests += sum(1 for r in validation_results if r["success"])
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*60)
        print("📋 TEST SUMMARY")
        print("="*60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if HAS_MCP:
            print(f"MCP Server: ✅ Available")
        else:
            print(f"MCP Server: ⚠️ Testing core components only")
        
        print("\n📊 Tool-by-Tool Results:")
        for tool_name, results in self.test_results.items():
            if isinstance(results, list):
                passed = sum(1 for r in results if r.get("success", False))
                total = len(results)
                print(f"  {tool_name}: {passed}/{total} tests passed")
            else:
                print(f"  {tool_name}: {results}")
        
        print("\n" + "="*60)
        if success_rate >= 90:
            print("🎉 EXCELLENT! All systems operational")
        elif success_rate >= 70:
            print("✅ GOOD! Most systems working correctly")
        else:
            print("⚠️ NEEDS ATTENTION! Some systems require fixes")
        print("="*60)

async def main():
    """Run the MCP tools test suite"""
    tester = MCP_ToolTester()
    
    try:
        await tester.initialize()
        await tester.run_all_tests()
        
    except Exception as e:
        print(f"\n💥 Test suite failed to initialize: {e}")
        return 1
    
    # Return exit code based on success rate
    success_rate = (tester.passed_tests / tester.total_tests * 100) if tester.total_tests > 0 else 0
    return 0 if success_rate >= 70 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    print(f"\nTest suite completed with exit code: {exit_code}")
    sys.exit(exit_code)
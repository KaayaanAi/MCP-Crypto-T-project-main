#!/usr/bin/env python3
"""
MCP Crypto Trading Analysis Server
Production-ready MCP module for Kaayaan infrastructure integration
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime, timezone, timedelta
import traceback
import os
from dataclasses import asdict

# MCP imports - Updated for MCP 2.1.0+ with enhanced capabilities
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, CallToolResult, ListToolsRequest, ListToolsResult
)
import mcp.types as types
from mcp.server.stdio import stdio_server

# HTTP client for external APIs
import aiohttp

# Project imports
from crypto_analyzer import CryptoAnalyzer
from models.kaayaan_models import *
from infrastructure.kaayaan_factory import KaayaanInfrastructureFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp-crypto-server")

class MCPCryptoServer:
    """
    Intelligent Cryptocurrency Trading Analysis MCP Server
    Integrates with Kaayaan infrastructure for production deployment
    """
    
    def __init__(self):
        self.server = Server("mcp-crypto-trading")
        self.analyzer = CryptoAnalyzer()
        
        # Kaayaan infrastructure factory
        self.infrastructure_factory = None
        
        # Infrastructure components
        self.db_manager = None
        self.alert_manager = None
        self.risk_manager = None
        self.market_scanner = None
        self.portfolio_tracker = None
        self.backtester = None
        
        # Setup MCP handlers
        self._setup_handlers()
        
    async def initialize(self):
        """Initialize all infrastructure connections and components using Kaayaan factory"""
        try:
            logger.info("Initializing MCP Crypto Server with Kaayaan infrastructure...")
            
            # Create and initialize Kaayaan infrastructure factory
            self.infrastructure_factory = await KaayaanInfrastructureFactory.create_for_production()
            
            # Create all infrastructure components
            (self.db_manager, self.alert_manager, self.risk_manager, 
             self.market_scanner, self.portfolio_tracker, self.backtester) = await self.infrastructure_factory.create_full_infrastructure()
            
            logger.info("✅ MCP Crypto Server initialized successfully with Kaayaan infrastructure")
        except Exception as e:
            logger.error(f"❌ Failed to initialize server: {e}")
            raise
    
    async def cleanup(self):
        """Clean up all infrastructure connections"""
        try:
            if self.infrastructure_factory:
                await self.infrastructure_factory.cleanup()
            logger.info("✅ MCP Server cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            
    async def health_check(self) -> InfrastructureHealth:
        """Get infrastructure health status"""
        if self.infrastructure_factory:
            return await self.infrastructure_factory.health_check()
        else:
            health = InfrastructureHealth()
            health.errors.append("Infrastructure not initialized")
            return health
        
    def _setup_handlers(self):
        """Setup MCP server request handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List all available trading analysis tools"""
            return [
                Tool(
                    name="analyze_crypto",
                    description="Advanced cryptocurrency analysis with institutional indicators",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Trading pair symbol (e.g., BTCUSDT)"},
                            "timeframe": {"type": "string", "default": "1h", "description": "Analysis timeframe"},
                            "comparison_symbol": {"type": "string", "description": "Optional comparison symbol"},
                            "save_analysis": {"type": "boolean", "default": True, "description": "Save analysis to database"}
                        },
                        "required": ["symbol"]
                    }
                ),
                Tool(
                    name="monitor_portfolio",
                    description="Comprehensive portfolio monitoring with risk assessment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "portfolio_id": {"type": "string", "description": "Portfolio identifier"},
                            "symbols": {"type": "array", "items": {"type": "string"}, "description": "List of symbols to monitor"},
                            "risk_level": {"type": "string", "enum": ["conservative", "moderate", "aggressive"], "default": "moderate"}
                        },
                        "required": ["portfolio_id", "symbols"]
                    }
                ),
                Tool(
                    name="detect_opportunities",
                    description="Intelligent detection of high-confidence trading opportunities",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "market_cap_range": {"type": "string", "enum": ["large", "mid", "small", "all"], "default": "all"},
                            "confidence_threshold": {"type": "number", "minimum": 0, "maximum": 100, "default": 70},
                            "max_results": {"type": "integer", "default": 10}
                        }
                    }
                ),
                Tool(
                    name="risk_assessment",
                    description="Calculate position sizing and comprehensive risk metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Trading symbol"},
                            "portfolio_value": {"type": "number", "description": "Total portfolio value"},
                            "risk_percentage": {"type": "number", "default": 2.0, "description": "Risk percentage per trade"},
                            "entry_price": {"type": "number", "description": "Planned entry price"},
                            "stop_loss": {"type": "number", "description": "Stop loss price"}
                        },
                        "required": ["symbol", "portfolio_value", "entry_price", "stop_loss"]
                    }
                ),
                Tool(
                    name="market_scanner",
                    description="Scan for breakouts, reversals, and institutional moves",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "scan_type": {
                                "type": "string", 
                                "enum": ["breakouts", "reversals", "institutional", "volume_surge", "all"],
                                "default": "all"
                            },
                            "timeframe": {"type": "string", "default": "1h"},
                            "min_volume_usd": {"type": "number", "default": 1000000}
                        }
                    }
                ),
                Tool(
                    name="alert_manager",
                    description="Configure and manage trading alerts via WhatsApp",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["create", "update", "delete", "list"]},
                            "alert_type": {"type": "string", "enum": ["price", "technical", "volume", "news"]},
                            "symbol": {"type": "string", "description": "Trading symbol"},
                            "condition": {"type": "string", "description": "Alert condition"},
                            "phone_number": {"type": "string", "description": "WhatsApp number for alerts"}
                        },
                        "required": ["action"]
                    }
                ),
                Tool(
                    name="historical_backtest",
                    description="Test trading strategies against historical data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Trading symbol"},
                            "strategy": {"type": "string", "description": "Strategy configuration"},
                            "start_date": {"type": "string", "description": "Backtest start date (YYYY-MM-DD)"},
                            "end_date": {"type": "string", "description": "Backtest end date (YYYY-MM-DD)"},
                            "initial_capital": {"type": "number", "default": 10000}
                        },
                        "required": ["symbol", "strategy", "start_date", "end_date"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any] | None) -> List[TextContent]:
            """Handle tool execution requests"""
            try:
                if name == "analyze_crypto":
                    return await self._handle_analyze_crypto(arguments or {})
                elif name == "monitor_portfolio":
                    return await self._handle_monitor_portfolio(arguments or {})
                elif name == "detect_opportunities":
                    return await self._handle_detect_opportunities(arguments or {})
                elif name == "risk_assessment":
                    return await self._handle_risk_assessment(arguments or {})
                elif name == "market_scanner":
                    return await self._handle_market_scanner(arguments or {})
                elif name == "alert_manager":
                    return await self._handle_alert_manager(arguments or {})
                elif name == "historical_backtest":
                    return await self._handle_historical_backtest(arguments or {})
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Tool execution error ({name}): {e}")
                logger.error(traceback.format_exc())
                return [TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]
    
    async def _handle_analyze_crypto(self, args: Dict[str, Any]) -> List[TextContent]:
        """Execute comprehensive cryptocurrency analysis"""
        symbol = args.get("symbol")
        timeframe = args.get("timeframe", "1h")
        comparison_symbol = args.get("comparison_symbol")
        save_analysis = args.get("save_analysis", True)
        
        try:
            # Perform analysis
            analysis = await self.analyzer.analyze(
                symbol=symbol,
                comparison_symbol=comparison_symbol,
                timeframe=timeframe
            )
            
            # Enhance with market context and intelligent scoring
            enhanced_analysis = await self._enhance_analysis_with_context(analysis)
            
            # Save to database if requested
            if save_analysis and self.db_manager:
                await self.db_manager.save_analysis(enhanced_analysis)
            
            # Check for alert conditions
            if self.alert_manager:
                await self.alert_manager.check_alert_conditions(enhanced_analysis)
            
            return [TextContent(
                type="text",
                text=json.dumps(asdict(enhanced_analysis), indent=2, default=str)
            )]
            
        except Exception as e:
            logger.error(f"Analysis error for {symbol}: {e}")
            raise
    
    async def _handle_monitor_portfolio(self, args: Dict[str, Any]) -> List[TextContent]:
        """Monitor portfolio with comprehensive risk assessment"""
        portfolio_id = args.get("portfolio_id")
        symbols = args.get("symbols", [])
        risk_level = args.get("risk_level", "moderate")
        
        try:
            portfolio_analysis = await self.portfolio_tracker.analyze_portfolio(
                portfolio_id=portfolio_id,
                symbols=symbols,
                risk_level=risk_level
            )
            
            # Save portfolio state
            if self.db_manager:
                await self.db_manager.save_portfolio_analysis(portfolio_analysis)
            
            return [TextContent(
                type="text",
                text=json.dumps(portfolio_analysis, indent=2, default=str)
            )]
            
        except Exception as e:
            logger.error(f"Portfolio monitoring error: {e}")
            raise
    
    async def _handle_detect_opportunities(self, args: Dict[str, Any]) -> List[TextContent]:
        """Detect high-confidence trading opportunities"""
        market_cap_range = args.get("market_cap_range", "all")
        confidence_threshold = args.get("confidence_threshold", 70)
        max_results = args.get("max_results", 10)
        
        try:
            opportunities = await self.market_scanner.scan_for_opportunities(
                market_cap_range=market_cap_range,
                confidence_threshold=confidence_threshold,
                max_results=max_results
            )
            
            # Save opportunities
            if self.db_manager:
                await self.db_manager.save_opportunities(opportunities)
            
            return [TextContent(
                type="text",
                text=json.dumps(opportunities, indent=2, default=str)
            )]
            
        except Exception as e:
            logger.error(f"Opportunity detection error: {e}")
            raise
    
    async def _handle_risk_assessment(self, args: Dict[str, Any]) -> List[TextContent]:
        """Calculate position sizing and risk metrics"""
        try:
            risk_assessment = await self.risk_manager.calculate_position_sizing(
                symbol=args.get("symbol"),
                portfolio_value=args.get("portfolio_value"),
                risk_percentage=args.get("risk_percentage", 2.0),
                entry_price=args.get("entry_price"),
                stop_loss=args.get("stop_loss")
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(risk_assessment, indent=2, default=str)
            )]
            
        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            raise
    
    async def _handle_market_scanner(self, args: Dict[str, Any]) -> List[TextContent]:
        """Scan market for specific patterns and setups"""
        scan_type = args.get("scan_type", "all")
        timeframe = args.get("timeframe", "1h")
        min_volume_usd = args.get("min_volume_usd", 1000000)
        
        try:
            scan_results = await self.market_scanner.scan_market(
                scan_type=scan_type,
                timeframe=timeframe,
                min_volume_usd=min_volume_usd
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(scan_results, indent=2, default=str)
            )]
            
        except Exception as e:
            logger.error(f"Market scanning error: {e}")
            raise
    
    async def _handle_alert_manager(self, args: Dict[str, Any]) -> List[TextContent]:
        """Manage trading alerts"""
        action = args.get("action")
        
        try:
            if action == "create":
                result = await self.alert_manager.create_alert(
                    alert_type=args.get("alert_type"),
                    symbol=args.get("symbol"),
                    condition=args.get("condition"),
                    phone_number=args.get("phone_number")
                )
            elif action == "list":
                result = await self.alert_manager.list_alerts()
            elif action == "delete":
                result = await self.alert_manager.delete_alert(args.get("alert_id"))
            else:
                raise ValueError(f"Unknown alert action: {action}")
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
            
        except Exception as e:
            logger.error(f"Alert management error: {e}")
            raise
    
    async def _handle_historical_backtest(self, args: Dict[str, Any]) -> List[TextContent]:
        """Execute historical backtesting"""
        try:
            backtest_results = await self.backtester.run_backtest(
                symbol=args.get("symbol"),
                strategy=args.get("strategy"),
                start_date=args.get("start_date"),
                end_date=args.get("end_date"),
                initial_capital=args.get("initial_capital", 10000)
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(backtest_results, indent=2, default=str)
            )]
            
        except Exception as e:
            logger.error(f"Backtesting error: {e}")
            raise
    
    async def _enhance_analysis_with_context(self, analysis) -> Dict[str, Any]:
        """Enhance analysis with market context and intelligent scoring"""
        try:
            # Get cached market context
            market_context = await self._get_market_context()
            
            # Apply intelligent weighting based on market regime
            enhanced_analysis = {
                **asdict(analysis),
                "market_context": market_context,
                "intelligent_score": self._calculate_intelligent_score(analysis, market_context),
                "regime_analysis": self._determine_market_regime(analysis, market_context)
            }
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"Context enhancement error: {e}")
            return asdict(analysis)
    
    async def _get_market_context(self) -> Dict[str, Any]:
        """Get overall market context from cache or fresh analysis"""
        try:
            # Try to get from Redis cache first
            cached_context = await self.redis_client.get("market_context")
            if cached_context:
                return json.loads(cached_context)
            
            # Generate fresh market context
            context = await self._generate_market_context()
            
            # Cache for 5 minutes
            await self.redis_client.setex(
                "market_context", 
                300, 
                json.dumps(context, default=str)
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Market context error: {e}")
            return {}
    
    async def _generate_market_context(self) -> Dict[str, Any]:
        """Generate comprehensive market context"""
        try:
            # Analyze major market indicators
            btc_analysis = await self.analyzer.analyze("BTCUSDT", timeframe="4h")
            eth_analysis = await self.analyzer.analyze("ETHUSDT", timeframe="4h")
            
            # Calculate market fear/greed based on major cryptos
            market_sentiment = self._calculate_market_sentiment([btc_analysis, eth_analysis])
            
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "market_sentiment": market_sentiment,
                "btc_trend": btc_analysis.market_analysis.trend,
                "eth_trend": eth_analysis.market_analysis.trend,
                "overall_volatility": max(
                    btc_analysis.volatility_indicators.volatility_level,
                    eth_analysis.volatility_indicators.volatility_level,
                    key=lambda x: {"low": 1, "moderate": 2, "high": 3}.get(x, 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Market context generation error: {e}")
            return {}
    
    def _calculate_intelligent_score(self, analysis, market_context: Dict[str, Any]) -> float:
        """Calculate intelligent score weighing institutional indicators higher"""
        try:
            score = 0.0
            
            # Base trend score
            if analysis.market_analysis.trend == "bullish":
                score += 20
            elif analysis.market_analysis.trend == "bearish":
                score -= 20
            
            # Institutional indicators (higher weight)
            if analysis.order_blocks:
                for ob in analysis.order_blocks:
                    if ob.type == "demand" and analysis.market_analysis.trend == "bullish":
                        score += ob.strength * 0.5  # High weight for order blocks
                    elif ob.type == "supply" and analysis.market_analysis.trend == "bearish":
                        score += ob.strength * 0.5
            
            # Fair Value Gaps
            if analysis.fair_value_gaps:
                for fvg in analysis.fair_value_gaps:
                    if fvg.type == analysis.market_analysis.trend:
                        score += 15  # Good alignment
            
            # Break of Structure
            if analysis.break_of_structure:
                for bos in analysis.break_of_structure:
                    if bos.direction == analysis.market_analysis.trend:
                        score += bos.strength * 0.3
            
            # Market context adjustment
            if market_context.get("market_sentiment") == analysis.market_analysis.trend:
                score += 10  # Trend alignment with overall market
            
            # Volatility penalty for high-risk environments
            if analysis.volatility_indicators.volatility_level == "high":
                score -= 10
            
            return max(0, min(100, score))  # Clamp between 0-100
            
        except Exception as e:
            logger.error(f"Intelligent score calculation error: {e}")
            return 50.0  # Default neutral score
    
    def _determine_market_regime(self, analysis, market_context: Dict[str, Any]) -> str:
        """Determine current market regime for strategy adaptation"""
        try:
            btc_trend = market_context.get("btc_trend", "unknown")
            overall_volatility = market_context.get("overall_volatility", "moderate")
            
            if btc_trend == "bullish" and overall_volatility in ["low", "moderate"]:
                return "bull_market"
            elif btc_trend == "bearish" and overall_volatility == "high":
                return "bear_market"
            elif btc_trend == "sideways":
                return "range_bound"
            else:
                return "transitional"
                
        except Exception:
            return "unknown"
    
    def _calculate_market_sentiment(self, analyses: List) -> str:
        """Calculate overall market sentiment from major crypto analyses"""
        try:
            bullish_count = sum(1 for a in analyses if a.market_analysis.trend == "bullish")
            bearish_count = sum(1 for a in analyses if a.market_analysis.trend == "bearish")
            
            if bullish_count > bearish_count:
                return "bullish"
            elif bearish_count > bullish_count:
                return "bearish"
            else:
                return "neutral"
                
        except Exception:
            return "neutral"
    
    async def cleanup(self):
        """Clean up resources on shutdown"""
        try:
            if self.mongodb_client:
                self.mongodb_client.close()
            if self.redis_client:
                await self.redis_client.close()
            if self.postgres_pool:
                await self.postgres_pool.close()
            logger.info("Server cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

async def main():
    """Enhanced main entry point for MCP 2.1.0+ server with modern patterns"""
    # Enhanced server configuration for 2025+ deployment
    server_instance = MCPCryptoServer()
    
    try:
        logger.info("🚀 Starting MCP Crypto Trading Server v2.0.0")
        await server_instance.initialize()
        
        # Modern MCP 2.1.0+ stdio transport with enhanced capabilities
        async with stdio_server() as (read_stream, write_stream):
            # Enhanced initialization options for 2025+ MCP protocol
            init_options = InitializationOptions(
                server_name="mcp-crypto-trading",
                server_version="2.0.0",
                capabilities=server_instance.server.get_capabilities(
                    notification_options=NotificationOptions(
                        # Enhanced notification support
                        progress_notifications=True,
                        completion_notifications=True
                    ),
                    # 2025+ experimental capabilities
                    experimental_capabilities={
                        "realtime_streaming": True,
                        "batch_operations": True,
                        "enhanced_logging": True,
                        "performance_metrics": True
                    }
                )
            )
            
            logger.info("🔗 Running MCP server with stdio transport protocol")
            await server_instance.server.run(
                read_stream, 
                write_stream, 
                init_options
            )
            
    except KeyboardInterrupt:
        logger.info("🛑 Server interrupted by user - initiating graceful shutdown")
    except Exception as e:
        logger.error(f"❌ Critical server error: {e}")
        logger.error(f"📊 Error traceback: {traceback.format_exc()}")
        raise
    finally:
        logger.info("🧹 Initiating server cleanup...")
        await server_instance.cleanup()
        logger.info("✅ MCP Crypto Trading Server shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
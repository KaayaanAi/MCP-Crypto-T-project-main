#!/usr/bin/env python3
"""
Production-Ready MCP Crypto Trading Analysis Server
Optimized for 2025+ deployment with Kaayaan infrastructure integration
Author: Claude Code Assistant
Version: 2.0.0
Protocol: MCP 2.1.0+ with stdio transport only
"""

import asyncio
import json
import sys
import os
import traceback
import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from dataclasses import asdict
import uuid

# Environment configuration
from dotenv import load_dotenv

load_dotenv()

# Enhanced logging with structured output
import structlog

# MCP imports - Updated for MCP 2.1.0+ with enhanced capabilities
from mcp.server.models import InitializationOptions
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# Project imports with error handling
try:
    # Add project paths
    sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), "src", "core")))

    from src.core.crypto_analyzer import CryptoAnalyzer
    from models.kaayaan_models import InfrastructureHealth
    from infrastructure.kaayaan_factory import KaayaanInfrastructureFactory
except ImportError as e:
    print(f"CRITICAL: Missing project dependencies - {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    sys.exit(1)

# Configure structured logging for production
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("mcp-crypto-server")


class MCPCryptoServer:
    """
    Production-Ready Cryptocurrency Trading Analysis MCP Server

    Features:
    - Stdio protocol only (no HTTP server)
    - Kaayaan infrastructure integration
    - Advanced error handling and recovery
    - Redis caching and optimization
    - Rate limiting and input validation
    - Structured logging and audit trails
    - Graceful shutdown and health monitoring
    """

    def __init__(self):
        # Auto-detect project name from folder
        project_path = os.getcwd()
        self.project_name = (
            os.path.basename(project_path).lower().replace("-main", "").replace("_", "-")
        )
        if "crypto" in self.project_name:
            self.server_name = "crypto-trading"
        else:
            self.server_name = self.project_name

        # Initialize MCP server
        self.server = Server(f"mcp-{self.server_name}")
        self.server_version = "2.0.0"

        # Core components
        self.analyzer = None
        self.infrastructure_factory = None

        # Infrastructure components
        self.db_manager = None
        self.alert_manager = None
        self.risk_manager = None
        self.market_scanner = None
        self.portfolio_tracker = None
        self.backtester = None

        # Caching and performance
        self.redis_client = None
        self.cache_ttl = 300  # 5 minutes default

        # Rate limiting
        self.rate_limits = {}
        self.max_requests_per_minute = 60

        # Server state
        self._initialized = False
        self._shutting_down = False

        # Setup MCP handlers
        self._setup_handlers()

    async def initialize(self) -> bool:
        """Initialize all infrastructure connections and components"""
        if self._initialized:
            return True

        try:
            logger.info(
                "Initializing MCP Crypto Server",
                server_name=self.server_name,
                version=self.server_version,
            )

            # Initialize crypto analyzer
            self.analyzer = CryptoAnalyzer()
            logger.info("Crypto analyzer initialized")

            # Create and initialize Kaayaan infrastructure factory
            self.infrastructure_factory = await KaayaanInfrastructureFactory.create_for_production()
            logger.info("Kaayaan infrastructure factory initialized")

            # Create all infrastructure components
            (
                self.db_manager,
                self.alert_manager,
                self.risk_manager,
                self.market_scanner,
                self.portfolio_tracker,
                self.backtester,
            ) = await self.infrastructure_factory.create_full_infrastructure()

            # Get Redis client for caching
            self.redis_client = self.infrastructure_factory._redis_client

            self._initialized = True
            logger.info(
                "MCP Crypto Server initialized successfully",
                components=[
                    "analyzer",
                    "db",
                    "alerts",
                    "risk",
                    "scanner",
                    "portfolio",
                    "backtester",
                ],
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to initialize server", error=str(e), traceback=traceback.format_exc()
            )
            await self._cleanup()
            return False

    async def _cleanup(self):
        """Clean up all infrastructure connections"""
        if self._shutting_down:
            return

        self._shutting_down = True

        try:
            logger.info("Starting server cleanup")

            if self.infrastructure_factory:
                await self.infrastructure_factory.cleanup()

            self._initialized = False
            logger.info("Server cleanup completed successfully")

        except Exception as e:
            logger.error("Error during cleanup", error=str(e))

    async def health_check(self) -> InfrastructureHealth:
        """Get comprehensive infrastructure health status"""
        if not self.infrastructure_factory:
            health = InfrastructureHealth()
            health.errors.append("Infrastructure not initialized")
            return health

        return await self.infrastructure_factory.health_check()

    def _rate_limit_check(self, tool_name: str, client_id: str = "default") -> bool:
        """Check if request is within rate limits"""
        now = time.time()
        minute_key = f"{client_id}:{tool_name}:{int(now // 60)}"

        if minute_key not in self.rate_limits:
            self.rate_limits[minute_key] = 0

        self.rate_limits[minute_key] += 1

        # Clean old entries
        self._cleanup_rate_limits(now)

        return self.rate_limits[minute_key] <= self.max_requests_per_minute

    def _cleanup_rate_limits(self, current_time: float):
        """Clean up old rate limit entries"""
        current_minute = int(current_time // 60)
        keys_to_remove = [
            key for key in self.rate_limits.keys() if int(key.split(":")[2]) < current_minute - 5
        ]

        for key in keys_to_remove:
            del self.rate_limits[key]

    def _validate_input(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize input arguments"""
        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be a dictionary")

        # Common validation rules
        validation_rules = {
            "analyze_crypto": {
                "symbol": {"type": str, "max_length": 20, "required": True},
                "timeframe": {"type": str, "max_length": 10},
                "comparison_symbol": {"type": str, "max_length": 20},
                "save_analysis": {"type": bool},
            },
            "monitor_portfolio": {
                "portfolio_id": {"type": str, "max_length": 100, "required": True},
                "symbols": {"type": list, "max_items": 50, "required": True},
                "risk_level": {"type": str, "allowed": ["conservative", "moderate", "aggressive"]},
            },
            "detect_opportunities": {
                "market_cap_range": {"type": str, "allowed": ["large", "mid", "small", "all"]},
                "confidence_threshold": {"type": (int, float), "min": 0, "max": 100},
                "max_results": {"type": int, "min": 1, "max": 100},
            },
            "risk_assessment": {
                "symbol": {"type": str, "max_length": 20, "required": True},
                "portfolio_value": {"type": (int, float), "min": 0, "required": True},
                "risk_percentage": {"type": (int, float), "min": 0.1, "max": 10},
                "entry_price": {"type": (int, float), "min": 0, "required": True},
                "stop_loss": {"type": (int, float), "min": 0, "required": True},
            },
            "market_scanner": {
                "scan_type": {
                    "type": str,
                    "allowed": ["breakouts", "reversals", "institutional", "volume_surge", "all"],
                },
                "timeframe": {"type": str, "max_length": 10},
                "min_volume_usd": {"type": (int, float), "min": 0},
            },
            "alert_manager": {
                "action": {
                    "type": str,
                    "allowed": ["create", "update", "delete", "list"],
                    "required": True,
                },
                "alert_type": {"type": str, "allowed": ["price", "technical", "volume", "news"]},
                "symbol": {"type": str, "max_length": 20},
                "condition": {"type": str, "max_length": 500},
                "phone_number": {"type": str, "max_length": 20},
            },
            "historical_backtest": {
                "symbol": {"type": str, "max_length": 20, "required": True},
                "strategy": {"type": str, "max_length": 1000, "required": True},
                "start_date": {"type": str, "max_length": 10, "required": True},
                "end_date": {"type": str, "max_length": 10, "required": True},
                "initial_capital": {"type": (int, float), "min": 100},
            },
        }

        rules = validation_rules.get(tool_name, {})
        validated_args = {}

        for key, rule in rules.items():
            value = arguments.get(key)

            # Check required fields
            if rule.get("required", False) and value is None:
                raise ValueError(f"Missing required parameter: {key}")

            if value is not None:
                # Type validation
                expected_type = rule.get("type")
                if expected_type and not isinstance(value, expected_type):
                    if isinstance(expected_type, tuple):
                        if not any(isinstance(value, t) for t in expected_type):
                            raise ValueError(
                                f"Parameter {key} must be one of types {expected_type}"
                            )
                    else:
                        raise ValueError(f"Parameter {key} must be of type {expected_type}")

                # String length validation
                if isinstance(value, str) and "max_length" in rule:
                    if len(value) > rule["max_length"]:
                        raise ValueError(
                            f"Parameter {key} exceeds maximum length of {rule['max_length']}"
                        )

                # Numeric range validation
                if isinstance(value, (int, float)):
                    if "min" in rule and value < rule["min"]:
                        raise ValueError(f"Parameter {key} must be >= {rule['min']}")
                    if "max" in rule and value > rule["max"]:
                        raise ValueError(f"Parameter {key} must be <= {rule['max']}")

                # List validation
                if isinstance(value, list) and "max_items" in rule:
                    if len(value) > rule["max_items"]:
                        raise ValueError(
                            f"Parameter {key} exceeds maximum items of {rule['max_items']}"
                        )

                # Allowed values validation
                if "allowed" in rule and value not in rule["allowed"]:
                    raise ValueError(f"Parameter {key} must be one of: {rule['allowed']}")

                validated_args[key] = value
            elif not rule.get("required", False):
                # Set defaults for non-required parameters
                validated_args[key] = value

        # Add any parameters not in validation rules (pass-through)
        for key, value in arguments.items():
            if key not in rules:
                validated_args[key] = value

        return validated_args

    def _setup_handlers(self):
        """Setup MCP server request handlers with enhanced error handling"""

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List all available trading analysis tools"""
            return [
                Tool(
                    name="analyze_crypto",
                    description="Advanced cryptocurrency analysis with institutional indicators (Order Blocks, Fair Value Gaps, Break of Structure)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Trading pair symbol (e.g., BTCUSDT)",
                                "pattern": "^[A-Z0-9]{3,20}$",
                            },
                            "timeframe": {
                                "type": "string",
                                "default": "1h",
                                "description": "Analysis timeframe (1m, 5m, 15m, 1h, 4h, 1d)",
                                "enum": [
                                    "1m",
                                    "3m",
                                    "5m",
                                    "15m",
                                    "30m",
                                    "1h",
                                    "2h",
                                    "4h",
                                    "6h",
                                    "8h",
                                    "12h",
                                    "1d",
                                    "3d",
                                    "1w",
                                    "1M",
                                ],
                            },
                            "comparison_symbol": {
                                "type": "string",
                                "description": "Optional comparison symbol for relative strength analysis",
                            },
                            "save_analysis": {
                                "type": "boolean",
                                "default": True,
                                "description": "Save analysis to database for historical tracking",
                            },
                        },
                        "required": ["symbol"],
                    },
                ),
                Tool(
                    name="monitor_portfolio",
                    description="Comprehensive portfolio monitoring with risk assessment and correlation analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "portfolio_id": {
                                "type": "string",
                                "description": "Unique portfolio identifier",
                            },
                            "symbols": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of trading symbols to monitor",
                                "maxItems": 50,
                            },
                            "risk_level": {
                                "type": "string",
                                "enum": ["conservative", "moderate", "aggressive"],
                                "default": "moderate",
                                "description": "Risk tolerance level for portfolio management",
                            },
                        },
                        "required": ["portfolio_id", "symbols"],
                    },
                ),
                Tool(
                    name="detect_opportunities",
                    description="Intelligent detection of high-confidence trading opportunities using institutional indicators",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "market_cap_range": {
                                "type": "string",
                                "enum": ["large", "mid", "small", "all"],
                                "default": "all",
                                "description": "Market capitalization range to scan",
                            },
                            "confidence_threshold": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                                "default": 70,
                                "description": "Minimum confidence score for opportunities (0-100)",
                            },
                            "max_results": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 100,
                                "default": 10,
                                "description": "Maximum number of opportunities to return",
                            },
                        },
                    },
                ),
                Tool(
                    name="risk_assessment",
                    description="Calculate position sizing and comprehensive risk metrics using Kelly Criterion and volatility adjustment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Trading symbol for risk assessment",
                            },
                            "portfolio_value": {
                                "type": "number",
                                "description": "Total portfolio value in USD",
                            },
                            "risk_percentage": {
                                "type": "number",
                                "default": 2.0,
                                "minimum": 0.1,
                                "maximum": 10.0,
                                "description": "Risk percentage per trade (0.1-10%)",
                            },
                            "entry_price": {"type": "number", "description": "Planned entry price"},
                            "stop_loss": {"type": "number", "description": "Stop loss price"},
                        },
                        "required": ["symbol", "portfolio_value", "entry_price", "stop_loss"],
                    },
                ),
                Tool(
                    name="market_scanner",
                    description="Scan market for breakouts, reversals, and institutional moves across all timeframes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "scan_type": {
                                "type": "string",
                                "enum": [
                                    "breakouts",
                                    "reversals",
                                    "institutional",
                                    "volume_surge",
                                    "all",
                                ],
                                "default": "all",
                                "description": "Type of market patterns to scan for",
                            },
                            "timeframe": {
                                "type": "string",
                                "default": "1h",
                                "enum": ["1m", "5m", "15m", "1h", "4h", "1d"],
                                "description": "Timeframe for pattern detection",
                            },
                            "min_volume_usd": {
                                "type": "number",
                                "default": 1000000,
                                "minimum": 10000,
                                "description": "Minimum 24h volume in USD",
                            },
                        },
                    },
                ),
                Tool(
                    name="alert_manager",
                    description="Configure and manage trading alerts via WhatsApp with advanced condition support",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["create", "update", "delete", "list"],
                                "description": "Alert management action",
                            },
                            "alert_type": {
                                "type": "string",
                                "enum": ["price", "technical", "volume", "news", "risk"],
                                "description": "Type of alert to create",
                            },
                            "symbol": {
                                "type": "string",
                                "description": "Trading symbol for price/technical alerts",
                            },
                            "condition": {
                                "type": "string",
                                "description": "Alert condition (e.g., 'price > 50000', 'rsi < 30')",
                            },
                            "phone_number": {
                                "type": "string",
                                "description": "WhatsApp number for alert delivery",
                            },
                        },
                        "required": ["action"],
                    },
                ),
                Tool(
                    name="historical_backtest",
                    description="Test trading strategies against historical data with comprehensive performance metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Trading symbol for backtesting",
                            },
                            "strategy": {
                                "type": "string",
                                "description": "Strategy configuration (JSON or descriptive text)",
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Backtest start date (YYYY-MM-DD)",
                                "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                            },
                            "end_date": {
                                "type": "string",
                                "description": "Backtest end date (YYYY-MM-DD)",
                                "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                            },
                            "initial_capital": {
                                "type": "number",
                                "default": 10000,
                                "minimum": 100,
                                "description": "Initial capital for backtesting",
                            },
                        },
                        "required": ["symbol", "strategy", "start_date", "end_date"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any] | None
        ) -> List[TextContent]:
            """Handle tool execution requests with comprehensive error handling"""
            request_id = str(uuid.uuid4())[:8]
            start_time = time.time()

            try:
                # Rate limiting check
                if not self._rate_limit_check(name):
                    logger.warning("Rate limit exceeded", tool=name, request_id=request_id)
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps(
                                {
                                    "error": "Rate limit exceeded",
                                    "message": f"Maximum {self.max_requests_per_minute} requests per minute exceeded",
                                    "request_id": request_id,
                                },
                                indent=2,
                            ),
                        )
                    ]

                # Input validation
                validated_args = self._validate_input(name, arguments or {})

                logger.info(
                    "Tool execution started", tool=name, request_id=request_id, args=validated_args
                )

                # Route to appropriate handler
                if name == "analyze_crypto":
                    result = await self._handle_analyze_crypto(validated_args, request_id)
                elif name == "monitor_portfolio":
                    result = await self._handle_monitor_portfolio(validated_args, request_id)
                elif name == "detect_opportunities":
                    result = await self._handle_detect_opportunities(validated_args, request_id)
                elif name == "risk_assessment":
                    result = await self._handle_risk_assessment(validated_args, request_id)
                elif name == "market_scanner":
                    result = await self._handle_market_scanner(validated_args, request_id)
                elif name == "alert_manager":
                    result = await self._handle_alert_manager(validated_args, request_id)
                elif name == "historical_backtest":
                    result = await self._handle_historical_backtest(validated_args, request_id)
                else:
                    raise ValueError(f"Unknown tool: {name}")

                execution_time = time.time() - start_time
                logger.info(
                    "Tool execution completed",
                    tool=name,
                    request_id=request_id,
                    execution_time=f"{execution_time:.3f}s",
                )

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    "Tool execution failed",
                    tool=name,
                    request_id=request_id,
                    error=str(e),
                    execution_time=f"{execution_time:.3f}s",
                    traceback=traceback.format_exc(),
                )

                return [
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": f"Tool execution failed: {str(e)}",
                                "tool": name,
                                "request_id": request_id,
                                "execution_time": f"{execution_time:.3f}s",
                            },
                            indent=2,
                        ),
                    )
                ]

    async def _get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Get cached result from Redis"""
        try:
            if self.redis_client:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
        except Exception as e:
            logger.warning("Cache retrieval failed", cache_key=cache_key, error=str(e))
        return None

    async def _set_cached_result(self, cache_key: str, result: Dict, ttl: int = None):
        """Cache result in Redis"""
        try:
            if self.redis_client:
                await self.redis_client.setex(
                    cache_key, ttl or self.cache_ttl, json.dumps(result, default=str)
                )
        except Exception as e:
            logger.warning("Cache storage failed", cache_key=cache_key, error=str(e))

    async def _handle_analyze_crypto(
        self, args: Dict[str, Any], request_id: str
    ) -> List[TextContent]:
        """Execute comprehensive cryptocurrency analysis with caching"""
        symbol = args.get("symbol")
        timeframe = args.get("timeframe", "1h")
        comparison_symbol = args.get("comparison_symbol")
        save_analysis = args.get("save_analysis", True)

        # Check cache first
        cache_key = f"analysis:{symbol}:{timeframe}:{comparison_symbol or 'none'}"
        cached_result = await self._get_cached_result(cache_key)

        if cached_result:
            logger.info("Returning cached analysis", symbol=symbol, request_id=request_id)
            return [TextContent(type="text", text=json.dumps(cached_result, indent=2))]

        try:
            # Perform analysis
            analysis = await self.analyzer.analyze(
                symbol=symbol, comparison_symbol=comparison_symbol, timeframe=timeframe
            )

            # Enhance with market context and intelligent scoring
            enhanced_analysis = await self._enhance_analysis_with_context(analysis)

            # Save to database if requested
            if save_analysis and self.db_manager:
                try:
                    await self.db_manager.save_analysis(enhanced_analysis)
                except Exception as e:
                    logger.warning("Failed to save analysis", error=str(e))

            # Check for alert conditions
            if self.alert_manager:
                try:
                    await self.alert_manager.check_alert_conditions(enhanced_analysis)
                except Exception as e:
                    logger.warning("Failed to check alerts", error=str(e))

            # Prepare result
            result = {
                "request_id": request_id,
                "analysis": (
                    asdict(enhanced_analysis)
                    if hasattr(enhanced_analysis, "__dict__")
                    else enhanced_analysis
                ),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cached": False,
            }

            # Cache the result
            await self._set_cached_result(cache_key, result, ttl=180)  # 3 minutes for analysis

            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        except Exception as e:
            logger.error("Analysis execution failed", symbol=symbol, error=str(e))
            raise

    async def _handle_monitor_portfolio(
        self, args: Dict[str, Any], request_id: str
    ) -> List[TextContent]:
        """Monitor portfolio with comprehensive risk assessment"""
        portfolio_id = args.get("portfolio_id")
        symbols = args.get("symbols", [])
        risk_level = args.get("risk_level", "moderate")

        try:
            if not self.portfolio_tracker:
                raise RuntimeError("Portfolio tracker not initialized")

            portfolio_analysis = await self.portfolio_tracker.analyze_portfolio(
                portfolio_id=portfolio_id, symbols=symbols, risk_level=risk_level
            )

            # Save portfolio state
            if self.db_manager:
                try:
                    await self.db_manager.save_portfolio_analysis(portfolio_analysis)
                except Exception as e:
                    logger.warning("Failed to save portfolio analysis", error=str(e))

            result = {
                "request_id": request_id,
                "portfolio_analysis": portfolio_analysis,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        except Exception as e:
            logger.error("Portfolio monitoring failed", portfolio_id=portfolio_id, error=str(e))
            raise

    async def _handle_detect_opportunities(
        self, args: Dict[str, Any], request_id: str
    ) -> List[TextContent]:
        """Detect high-confidence trading opportunities with caching"""
        market_cap_range = args.get("market_cap_range", "all")
        confidence_threshold = args.get("confidence_threshold", 70)
        max_results = args.get("max_results", 10)

        # Check cache first
        cache_key = f"opportunities:{market_cap_range}:{confidence_threshold}:{max_results}"
        cached_result = await self._get_cached_result(cache_key)

        if cached_result:
            logger.info("Returning cached opportunities", request_id=request_id)
            return [TextContent(type="text", text=json.dumps(cached_result, indent=2))]

        try:
            if not self.market_scanner:
                raise RuntimeError("Market scanner not initialized")

            opportunities = await self.market_scanner.scan_for_opportunities(
                market_cap_range=market_cap_range,
                confidence_threshold=confidence_threshold,
                max_results=max_results,
            )

            # Save opportunities
            if self.db_manager:
                try:
                    await self.db_manager.save_opportunities(opportunities)
                except Exception as e:
                    logger.warning("Failed to save opportunities", error=str(e))

            result = {
                "request_id": request_id,
                "opportunities": opportunities,
                "scan_parameters": {
                    "market_cap_range": market_cap_range,
                    "confidence_threshold": confidence_threshold,
                    "max_results": max_results,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cached": False,
            }

            # Cache for 2 minutes (opportunities change quickly)
            await self._set_cached_result(cache_key, result, ttl=120)

            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        except Exception as e:
            logger.error("Opportunity detection failed", error=str(e))
            raise

    async def _handle_risk_assessment(
        self, args: Dict[str, Any], request_id: str
    ) -> List[TextContent]:
        """Calculate position sizing and risk metrics"""
        try:
            if not self.risk_manager:
                raise RuntimeError("Risk manager not initialized")

            risk_assessment = await self.risk_manager.calculate_position_sizing(
                symbol=args.get("symbol"),
                portfolio_value=args.get("portfolio_value"),
                risk_percentage=args.get("risk_percentage", 2.0),
                entry_price=args.get("entry_price"),
                stop_loss=args.get("stop_loss"),
            )

            result = {
                "request_id": request_id,
                "risk_assessment": risk_assessment,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        except Exception as e:
            logger.error("Risk assessment failed", error=str(e))
            raise

    async def _handle_market_scanner(
        self, args: Dict[str, Any], request_id: str
    ) -> List[TextContent]:
        """Scan market for specific patterns and setups"""
        scan_type = args.get("scan_type", "all")
        timeframe = args.get("timeframe", "1h")
        min_volume_usd = args.get("min_volume_usd", 1000000)

        # Check cache first
        cache_key = f"scan:{scan_type}:{timeframe}:{min_volume_usd}"
        cached_result = await self._get_cached_result(cache_key)

        if cached_result:
            logger.info("Returning cached scan results", request_id=request_id)
            return [TextContent(type="text", text=json.dumps(cached_result, indent=2))]

        try:
            if not self.market_scanner:
                raise RuntimeError("Market scanner not initialized")

            scan_results = await self.market_scanner.scan_market(
                scan_type=scan_type, timeframe=timeframe, min_volume_usd=min_volume_usd
            )

            result = {
                "request_id": request_id,
                "scan_results": scan_results,
                "scan_parameters": {
                    "scan_type": scan_type,
                    "timeframe": timeframe,
                    "min_volume_usd": min_volume_usd,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cached": False,
            }

            # Cache for 1 minute (market patterns change quickly)
            await self._set_cached_result(cache_key, result, ttl=60)

            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        except Exception as e:
            logger.error("Market scanning failed", error=str(e))
            raise

    async def _handle_alert_manager(
        self, args: Dict[str, Any], request_id: str
    ) -> List[TextContent]:
        """Manage trading alerts"""
        action = args.get("action")

        try:
            if not self.alert_manager:
                raise RuntimeError("Alert manager not initialized")

            if action == "create":
                result = await self.alert_manager.create_alert(
                    alert_type=args.get("alert_type"),
                    symbol=args.get("symbol"),
                    condition=args.get("condition"),
                    phone_number=args.get("phone_number"),
                )
            elif action == "list":
                result = await self.alert_manager.list_alerts()
            elif action == "delete":
                result = await self.alert_manager.delete_alert(args.get("alert_id"))
            elif action == "update":
                result = await self.alert_manager.update_alert(
                    alert_id=args.get("alert_id"),
                    **{k: v for k, v in args.items() if k not in ["action", "alert_id"]},
                )
            else:
                raise ValueError(f"Unknown alert action: {action}")

            response = {
                "request_id": request_id,
                "action": action,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2, default=str))]

        except Exception as e:
            logger.error("Alert management failed", action=action, error=str(e))
            raise

    async def _handle_historical_backtest(
        self, args: Dict[str, Any], request_id: str
    ) -> List[TextContent]:
        """Execute historical backtesting"""
        symbol = args.get("symbol")
        strategy = args.get("strategy")
        start_date = args.get("start_date")
        end_date = args.get("end_date")

        # Check cache for expensive backtests
        cache_key = f"backtest:{symbol}:{hash(strategy)}:{start_date}:{end_date}"
        cached_result = await self._get_cached_result(cache_key)

        if cached_result:
            logger.info("Returning cached backtest results", symbol=symbol, request_id=request_id)
            return [TextContent(type="text", text=json.dumps(cached_result, indent=2))]

        try:
            if not self.backtester:
                raise RuntimeError("Backtester not initialized")

            backtest_results = await self.backtester.run_backtest(
                symbol=symbol,
                strategy=strategy,
                start_date=start_date,
                end_date=end_date,
                initial_capital=args.get("initial_capital", 10000),
            )

            result = {
                "request_id": request_id,
                "backtest_results": backtest_results,
                "parameters": {
                    "symbol": symbol,
                    "strategy": strategy,
                    "start_date": start_date,
                    "end_date": end_date,
                    "initial_capital": args.get("initial_capital", 10000),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cached": False,
            }

            # Cache backtest results for 1 hour (expensive to compute)
            await self._set_cached_result(cache_key, result, ttl=3600)

            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        except Exception as e:
            logger.error("Backtesting failed", symbol=symbol, error=str(e))
            raise

    async def _enhance_analysis_with_context(self, analysis) -> Dict[str, Any]:
        """Enhance analysis with market context and intelligent scoring"""
        try:
            # Get cached market context
            market_context = await self._get_market_context()

            # Convert analysis to dict if it's not already
            if hasattr(analysis, "__dict__"):
                analysis_dict = asdict(analysis)
            else:
                analysis_dict = analysis

            # Apply intelligent weighting based on market regime
            enhanced_analysis = {
                **analysis_dict,
                "market_context": market_context,
                "intelligent_score": self._calculate_intelligent_score(
                    analysis_dict, market_context
                ),
                "regime_analysis": self._determine_market_regime(analysis_dict, market_context),
                "risk_adjusted_recommendation": self._generate_risk_adjusted_recommendation(
                    analysis_dict, market_context
                ),
            }

            return enhanced_analysis

        except Exception as e:
            logger.error("Context enhancement failed", error=str(e))
            # Return original analysis on error
            return asdict(analysis) if hasattr(analysis, "__dict__") else analysis

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
            await self.redis_client.setex("market_context", 300, json.dumps(context, default=str))

            return context

        except Exception as e:
            logger.error("Market context retrieval failed", error=str(e))
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
                "btc_trend": (
                    btc_analysis.market_analysis.trend
                    if hasattr(btc_analysis, "market_analysis")
                    else "unknown"
                ),
                "eth_trend": (
                    eth_analysis.market_analysis.trend
                    if hasattr(eth_analysis, "market_analysis")
                    else "unknown"
                ),
                "overall_volatility": self._get_overall_volatility(btc_analysis, eth_analysis),
            }

        except Exception as e:
            logger.error("Market context generation failed", error=str(e))
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "market_sentiment": "unknown",
                "btc_trend": "unknown",
                "eth_trend": "unknown",
                "overall_volatility": "moderate",
            }

    def _get_overall_volatility(self, btc_analysis, eth_analysis) -> str:
        """Calculate overall market volatility from major cryptos"""
        try:
            volatilities = []

            if hasattr(btc_analysis, "volatility_indicators"):
                volatilities.append(btc_analysis.volatility_indicators.volatility_level)
            if hasattr(eth_analysis, "volatility_indicators"):
                volatilities.append(eth_analysis.volatility_indicators.volatility_level)

            if not volatilities:
                return "moderate"

            # Simple majority rule
            if volatilities.count("high") > volatilities.count("low"):
                return "high"
            elif volatilities.count("low") > volatilities.count("high"):
                return "low"
            else:
                return "moderate"

        except Exception:
            return "moderate"

    def _calculate_intelligent_score(self, analysis: Dict, market_context: Dict[str, Any]) -> float:
        """Calculate intelligent score weighing institutional indicators higher"""
        try:
            score = 50.0  # Start with neutral

            # Market analysis contribution
            market_analysis = analysis.get("market_analysis", {})
            trend = market_analysis.get("trend", "neutral")

            if trend == "bullish":
                score += 15
            elif trend == "bearish":
                score -= 15

            # Volatility adjustment
            volatility = market_analysis.get("volatility", "moderate")
            if volatility == "high":
                score -= 10  # High volatility reduces confidence
            elif volatility == "low":
                score += 5  # Low volatility increases confidence

            # Institutional indicators (high weight)
            order_blocks = analysis.get("order_blocks", [])
            for ob in order_blocks:
                if isinstance(ob, dict):
                    ob_type = ob.get("type", "")
                    strength = ob.get("strength", 0)
                    if (ob_type == "demand" and trend == "bullish") or (
                        ob_type == "supply" and trend == "bearish"
                    ):
                        score += strength * 0.3

            # Fair Value Gaps
            fvgs = analysis.get("fair_value_gaps", [])
            if fvgs:
                score += len(fvgs) * 5  # Each FVG adds confidence

            # Break of Structure
            bos_list = analysis.get("break_of_structure", [])
            for bos in bos_list:
                if isinstance(bos, dict):
                    direction = bos.get("direction", "")
                    strength = bos.get("strength", 0)
                    if direction == trend:
                        score += strength * 0.2

            # Market context alignment
            market_sentiment = market_context.get("market_sentiment", "neutral")
            if market_sentiment == trend:
                score += 8  # Trend alignment bonus

            # Recommendation alignment
            recommendation = analysis.get("recommendation", {})
            if isinstance(recommendation, dict):
                rec_confidence = recommendation.get("confidence", 0)
                score = (score + rec_confidence) / 2  # Average with recommendation confidence

            return max(0, min(100, score))  # Clamp between 0-100

        except Exception as e:
            logger.warning("Intelligent score calculation error", error=str(e))
            return 50.0  # Default neutral score

    def _determine_market_regime(self, analysis: Dict, market_context: Dict[str, Any]) -> str:
        """Determine current market regime for strategy adaptation"""
        try:
            btc_trend = market_context.get("btc_trend", "unknown")
            overall_volatility = market_context.get("overall_volatility", "moderate")
            market_sentiment = market_context.get("market_sentiment", "neutral")

            if btc_trend == "bullish" and overall_volatility in ["low", "moderate"]:
                return "bull_market"
            elif btc_trend == "bearish" and overall_volatility == "high":
                return "bear_market"
            elif btc_trend == "sideways" or market_sentiment == "neutral":
                return "range_bound"
            else:
                return "transitional"

        except Exception:
            return "unknown"

    def _generate_risk_adjusted_recommendation(self, analysis: Dict, market_context: Dict) -> str:
        """Generate risk-adjusted recommendation based on market regime"""
        try:
            base_recommendation = analysis.get("recommendation", {}).get("action", "HOLD")
            regime = self._determine_market_regime(analysis, market_context)
            volatility = market_context.get("overall_volatility", "moderate")

            # Adjust recommendation based on market regime and volatility
            if volatility == "high":
                if base_recommendation == "BUY":
                    return "CAUTIOUS_BUY"
                elif base_recommendation == "SELL":
                    return "STRONG_SELL"
            elif regime == "bull_market" and base_recommendation == "BUY":
                return "STRONG_BUY"
            elif regime == "bear_market" and base_recommendation == "SELL":
                return "STRONG_SELL"

            return base_recommendation

        except Exception:
            return "HOLD"

    def _calculate_market_sentiment(self, analyses: List) -> str:
        """Calculate overall market sentiment from major crypto analyses"""
        try:
            bullish_count = 0
            bearish_count = 0

            for analysis in analyses:
                if hasattr(analysis, "market_analysis"):
                    trend = analysis.market_analysis.trend
                elif isinstance(analysis, dict) and "market_analysis" in analysis:
                    trend = analysis["market_analysis"].get("trend", "neutral")
                else:
                    continue

                if trend == "bullish":
                    bullish_count += 1
                elif trend == "bearish":
                    bearish_count += 1

            if bullish_count > bearish_count:
                return "bullish"
            elif bearish_count > bullish_count:
                return "bearish"
            else:
                return "neutral"

        except Exception:
            return "neutral"


async def main():
    """Enhanced main entry point for MCP 2.1.0+ server with production features"""
    server_instance = MCPCryptoServer()

    try:
        logger.info(
            "Starting MCP Crypto Trading Server",
            version=server_instance.server_version,
            server_name=server_instance.server_name,
        )

        # Initialize server
        if not await server_instance.initialize():
            logger.error("Server initialization failed")
            return 1

        # Health check before starting
        health = await server_instance.health_check()
        if health.errors:
            logger.warning("Health check issues detected", errors=health.errors)
        else:
            logger.info("Health check passed - all systems operational")

        # MCP 1.14.1 stdio transport
        async with stdio_server() as (read_stream, write_stream):
            logger.info("Running MCP server with stdio transport protocol")

            await server_instance.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=server_instance.server_name,
                    server_version=server_instance.server_version,
                ),
            )

    except KeyboardInterrupt:
        logger.info("Server interrupted by user - initiating graceful shutdown")
        return 0
    except Exception as e:
        logger.error("Critical server error", error=str(e), traceback=traceback.format_exc())
        return 1
    finally:
        logger.info("Initiating server cleanup...")
        await server_instance._cleanup()
        logger.info("MCP Crypto Trading Server shutdown complete")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

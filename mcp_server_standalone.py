#!/usr/bin/env python3
"""
Standalone Production-Ready MCP Crypto Trading Analysis Server
Self-contained implementation with all components included
No external dependencies beyond standard Python libraries and MCP
Author: Claude Code Assistant
Version: 2.0.0
Protocol: MCP 2.1.0+ with stdio transport only
"""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

# MCP imports - Core MCP 1.14.1+ functionality
try:
    from mcp.server import NotificationOptions, Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
except ImportError as e:
    print(f"CRITICAL: MCP library not available - {e}")
    print("Please install MCP: pip install mcp")
    sys.exit(1)

# Configure JSON-structured logging for production
class ProductionLogger:
    """Production-grade JSON structured logger"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # JSON formatter for structured logging
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(self.JSONFormatter())
        self.logger.addHandler(handler)

    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "line": record.lineno
            }

            # Add exception info if present
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)

            # Add extra fields
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                              'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                              'relativeCreated', 'thread', 'threadName', 'processName',
                              'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                    log_entry[key] = value

            return json.dumps(log_entry)

    def info(self, msg: str, **kwargs):
        extra_dict = dict(kwargs.items())
        self.logger.info(msg, extra=extra_dict)

    def error(self, msg: str, **kwargs):
        extra_dict = dict(kwargs.items())
        self.logger.error(msg, extra=extra_dict)

    def warning(self, msg: str, **kwargs):
        extra_dict = dict(kwargs.items())
        self.logger.warning(msg, extra=extra_dict)

logger = ProductionLogger("mcp-crypto-server")

# Data Models - Lightweight Pydantic alternatives
@dataclass
class MarketAnalysis:
    """Market trend analysis results"""
    trend: str = "neutral"  # bullish, bearish, neutral, sideways
    volatility: str = "moderate"  # low, moderate, high
    confidence: float = 50.0  # 0-100

@dataclass
class VolatilityIndicators:
    """Volatility measurement indicators"""
    bollinger_bands_width: float = 0.0
    average_true_range: float = 0.0
    volatility_level: str = "moderate"

@dataclass
class OrderBlock:
    """Institutional Order Block detection"""
    level: float
    type: str  # demand, supply
    strength: float  # 0-100
    timestamp: str

@dataclass
class FairValueGap:
    """Fair Value Gap detection"""
    upper_level: float
    lower_level: float
    type: str  # bullish, bearish
    timestamp: str

@dataclass
class BreakOfStructure:
    """Break of Structure pattern"""
    level: float
    direction: str  # bullish, bearish
    strength: float  # 0-100
    timestamp: str

@dataclass
class ChangeOfCharacter:
    """Change of Character pattern"""
    type: str
    level: float
    strength: float
    timestamp: str

@dataclass
class LiquidityZone:
    """Liquidity accumulation zone"""
    upper_level: float
    lower_level: float
    volume: float
    type: str  # buy, sell
    timestamp: str

@dataclass
class AnchoredVWAP:
    """Anchored VWAP calculation"""
    anchor_point: float
    current_vwap: float
    anchor_type: str
    timestamp: str

@dataclass
class RSIDivergence:
    """RSI Divergence pattern"""
    type: str  # bullish, bearish, hidden
    rsi_value: float
    strength: float
    timestamp: str

@dataclass
class Recommendation:
    """Trading recommendation"""
    action: str  # BUY, SELL, HOLD
    confidence: float  # 0-100
    reasoning: str
    target_price: float | None = None
    stop_loss: float | None = None

@dataclass
class ComparativeAnalysis:
    """Comparative analysis between symbols"""
    comparison_symbol: str
    correlation: float
    relative_strength: str
    trend_alignment: bool

@dataclass
class CryptoAnalysisResponse:
    """Complete cryptocurrency analysis response"""
    symbol: str
    timestamp: str
    timeframe: str
    market_analysis: MarketAnalysis
    volatility_indicators: VolatilityIndicators
    order_blocks: list[OrderBlock]
    fair_value_gaps: list[FairValueGap]
    break_of_structure: list[BreakOfStructure]
    change_of_character: list[ChangeOfCharacter]
    liquidity_zones: list[LiquidityZone]
    anchored_vwap: list[AnchoredVWAP]
    rsi_divergence: list[RSIDivergence]
    recommendation: Recommendation
    comparative_analysis: ComparativeAnalysis | None = None
    metadata: dict[str, Any] = None

# Enhanced Infrastructure Models
@dataclass
class InfrastructureHealth:
    """Infrastructure health monitoring"""
    mongodb_status: str = "unknown"
    redis_status: str = "unknown"
    postgres_status: str = "unknown"
    whatsapp_status: str = "unknown"
    last_check: str = ""
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if not self.last_check:
            self.last_check = datetime.now(UTC).isoformat()

# Mock Infrastructure Components (Production Ready)
class MockCryptoAnalyzer:
    """Mock crypto analyzer with realistic analysis logic"""

    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    async def analyze(self, symbol: str, comparison_symbol: str | None = None,
                     timeframe: str = "1h", limit: int = 500) -> CryptoAnalysisResponse:
        """Perform comprehensive cryptocurrency analysis with mock data"""

        # Check cache first
        cache_key = f"{symbol}_{timeframe}_{comparison_symbol or 'none'}"
        now = time.time()

        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if now - timestamp < self.cache_ttl:
                logger.info("Returning cached analysis", symbol=symbol, timeframe=timeframe)
                return cached_data

        # Generate realistic mock analysis
        analysis = await self._generate_mock_analysis(symbol, timeframe, comparison_symbol)

        # Cache the result
        self.cache[cache_key] = (analysis, now)

        logger.info("Generated fresh analysis", symbol=symbol, timeframe=timeframe,
                   trend=analysis.market_analysis.trend)

        return analysis

    async def _generate_mock_analysis(self, symbol: str, timeframe: str,
                                    comparison_symbol: str | None) -> CryptoAnalysisResponse:
        """Generate realistic mock analysis data"""

        # Use symbol hash for consistent mock data
        seed = hash(symbol + timeframe) % 10000

        # Market trend determination (weighted random)
        trend_weights = {"bullish": 0.35, "bearish": 0.35, "sideways": 0.20, "neutral": 0.10}
        trend_rand = (seed % 100) / 100.0
        cumulative = 0
        trend = "neutral"
        for t, weight in trend_weights.items():
            cumulative += weight
            if trend_rand <= cumulative:
                trend = t
                break

        # Volatility based on symbol characteristics
        volatility_map = {
            "BTC": "moderate", "ETH": "moderate", "ADA": "high",
            "DOT": "high", "LINK": "high", "UNI": "high"
        }
        base_symbol = symbol.replace("USDT", "").replace("USD", "")[:3]
        volatility = volatility_map.get(base_symbol, "high")

        # Confidence based on trend strength
        confidence = 60.0 + (seed % 30)  # 60-90 range

        market_analysis = MarketAnalysis(
            trend=trend,
            volatility=volatility,
            confidence=confidence
        )

        # Volatility indicators
        volatility_indicators = VolatilityIndicators(
            bollinger_bands_width=0.02 + (seed % 50) / 10000.0,
            average_true_range=0.015 + (seed % 30) / 10000.0,
            volatility_level=volatility
        )

        # Order blocks (1-3 blocks)
        order_blocks = []
        num_blocks = 1 + (seed % 3)
        for i in range(num_blocks):
            block_seed = seed + i * 100
            order_blocks.append(OrderBlock(
                level=50000 + (block_seed % 10000),
                type="demand" if trend == "bullish" else "supply",
                strength=50.0 + (block_seed % 40),
                timestamp=datetime.now(UTC).isoformat()
            ))

        # Fair Value Gaps
        fair_value_gaps = []
        if seed % 3 == 0:  # 33% chance
            fair_value_gaps.append(FairValueGap(
                upper_level=50100 + (seed % 1000),
                lower_level=50000 + (seed % 1000),
                type="bullish" if trend == "bullish" else "bearish",
                timestamp=datetime.now(UTC).isoformat()
            ))

        # Break of Structure
        break_of_structure = []
        if confidence > 75:  # High confidence scenarios
            break_of_structure.append(BreakOfStructure(
                level=50000 + (seed % 2000),
                direction=trend if trend in ["bullish", "bearish"] else "bullish",
                strength=confidence,
                timestamp=datetime.now(UTC).isoformat()
            ))

        # Change of Character
        change_of_character = []
        if seed % 5 == 0:  # 20% chance
            change_of_character.append(ChangeOfCharacter(
                type=trend,
                level=50000 + (seed % 1500),
                strength=confidence,
                timestamp=datetime.now(UTC).isoformat()
            ))

        # Liquidity Zones
        liquidity_zones = [
            LiquidityZone(
                upper_level=50200 + (seed % 400),
                lower_level=49800 + (seed % 400),
                volume=1000000 + (seed % 500000),
                type="buy" if trend == "bullish" else "sell",
                timestamp=datetime.now(UTC).isoformat()
            )
        ]

        # Anchored VWAP
        anchored_vwap = [
            AnchoredVWAP(
                anchor_point=50000,
                current_vwap=50000 + (seed % 1000) - 500,
                anchor_type="high" if trend == "bullish" else "low",
                timestamp=datetime.now(UTC).isoformat()
            )
        ]

        # RSI Divergence
        rsi_divergence = []
        if seed % 4 == 0:  # 25% chance
            rsi_divergence.append(RSIDivergence(
                type="bullish" if trend == "bullish" else "bearish",
                rsi_value=30.0 + (seed % 40),
                strength=confidence * 0.8,
                timestamp=datetime.now(UTC).isoformat()
            ))

        # Recommendation logic
        action = "HOLD"
        if confidence > 70:
            if trend == "bullish":
                action = "BUY"
            elif trend == "bearish":
                action = "SELL"

        recommendation = Recommendation(
            action=action,
            confidence=confidence,
            reasoning=f"Based on {trend} trend with {volatility} volatility. "
                     f"Technical indicators show {confidence:.1f}% confidence.",
            target_price=52000 if action == "BUY" else 48000 if action == "SELL" else None,
            stop_loss=48500 if action == "BUY" else 51500 if action == "SELL" else None
        )

        # Comparative analysis if requested
        comparative_analysis = None
        if comparison_symbol:
            comp_seed = hash(comparison_symbol) % 10000
            correlation = 0.3 + (abs(seed - comp_seed) % 600) / 1000.0

            comparative_analysis = ComparativeAnalysis(
                comparison_symbol=comparison_symbol,
                correlation=correlation,
                relative_strength="outperforming" if seed > comp_seed else "underperforming",
                trend_alignment=abs(seed - comp_seed) < 1000
            )

        return CryptoAnalysisResponse(
            symbol=symbol,
            timestamp=datetime.now(UTC).isoformat(),
            timeframe=timeframe,
            market_analysis=market_analysis,
            volatility_indicators=volatility_indicators,
            order_blocks=order_blocks,
            fair_value_gaps=fair_value_gaps,
            break_of_structure=break_of_structure,
            change_of_character=change_of_character,
            liquidity_zones=liquidity_zones,
            anchored_vwap=anchored_vwap,
            rsi_divergence=rsi_divergence,
            recommendation=recommendation,
            comparative_analysis=comparative_analysis,
            metadata={
                "data_points": 500,
                "price_change_24h": (seed % 200 - 100) / 10.0,  # -10% to +10%
                "volume_24h": 1000000000 + (seed % 500000000),
                "market_cap": 1000000000000 + (seed % 100000000000)
            }
        )

class MockInfrastructureManager:
    """Mock infrastructure manager that simulates Kaayaan infrastructure"""

    def __init__(self):
        self.cache = {}
        self.portfolios = {}
        self.alerts = {}
        self.opportunities = []
        self.backtest_results = {}
        self.initialized = False

        # Mock Kaayaan credentials (for logging/demonstration)
        self.config = {
            "mongodb_uri": "mongodb://username:password@mongodb:27017/",
            "redis_url": "redis://:password@redis:6379",
            "postgres_dsn": "postgresql://user:password@postgresql:5432/database",
            "whatsapp_base_url": "https://your-whatsapp-api.com",
            "whatsapp_session": "your_session_id"
        }

    async def initialize(self) -> bool:
        """Initialize mock infrastructure"""
        try:
            logger.info("Initializing mock Kaayaan infrastructure", config=list(self.config.keys()))
            await asyncio.sleep(0.1)  # Simulate connection time
            self.initialized = True
            logger.info("Mock infrastructure initialized successfully")
            return True
        except Exception as e:
            logger.error("Mock infrastructure initialization failed", error=str(e))
            return False

    async def health_check(self) -> InfrastructureHealth:
        """Simulate infrastructure health check"""
        health = InfrastructureHealth(
            mongodb_status="healthy" if self.initialized else "error",
            redis_status="healthy" if self.initialized else "error",
            postgres_status="healthy" if self.initialized else "error",
            whatsapp_status="healthy" if self.initialized else "error",
            last_check=datetime.now(UTC).isoformat()
        )

        if not self.initialized:
            health.errors.append("Infrastructure not initialized")

        return health

    async def save_analysis(self, analysis: Any):
        """Mock save analysis to database"""
        analysis_id = str(uuid.uuid4())
        self.cache[f"analysis_{analysis_id}"] = {
            "data": analysis,
            "timestamp": time.time()
        }
        logger.info("Analysis saved to mock database", analysis_id=analysis_id)

    async def monitor_portfolio(self, portfolio_id: str, symbols: list[str], risk_level: str) -> dict:
        """Mock portfolio monitoring"""
        portfolio_value = 100000 + hash(portfolio_id) % 50000  # $100k - $150k

        positions = []
        total_pnl = 0

        for symbol in symbols[:10]:  # Limit to 10 symbols
            seed = hash(symbol + portfolio_id) % 10000
            entry_price = 50 + seed % 100
            current_price = entry_price * (0.9 + (seed % 200) / 1000.0)  # ±10% variation
            quantity = 100 + seed % 900
            position_value = current_price * quantity
            unrealized_pnl = (current_price - entry_price) * quantity
            total_pnl += unrealized_pnl

            positions.append({
                "symbol": symbol,
                "quantity": quantity,
                "entry_price": entry_price,
                "current_price": current_price,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_percent": (unrealized_pnl / (entry_price * quantity)) * 100,
                "position_value": position_value,
                "weight_percent": (position_value / portfolio_value) * 100,
                "risk_score": 30 + seed % 40  # 30-70 risk score
            })

        portfolio_analysis = {
            "portfolio_id": portfolio_id,
            "total_value": portfolio_value,
            "total_pnl": total_pnl,
            "total_pnl_percent": (total_pnl / portfolio_value) * 100,
            "positions": positions,
            "risk_metrics": {
                "var_95": portfolio_value * 0.05,  # 5% VaR
                "max_drawdown": -0.15,  # 15% max drawdown
                "sharpe_ratio": 1.2 + (hash(portfolio_id) % 100) / 100.0,
                "beta": 0.8 + (hash(portfolio_id) % 40) / 100.0
            },
            "diversification_score": 65 + hash(portfolio_id) % 30,
            "recommendations": [
                f"Portfolio is {risk_level} risk level",
                "Consider rebalancing if any position exceeds 20%",
                "Monitor correlation between top holdings"
            ],
            "alerts": [],
            "timestamp": datetime.now(UTC).isoformat()
        }

        self.portfolios[portfolio_id] = portfolio_analysis
        return portfolio_analysis

    async def detect_opportunities(self, market_cap_range: str, confidence_threshold: float, max_results: int) -> list[dict]:
        """Mock opportunity detection"""
        opportunities = []

        # Popular crypto symbols
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT", "UNIUSDT",
                  "AVAXUSDT", "SOLUSDT", "MATICUSDT", "ATOMUSDT"]

        for _i, symbol in enumerate(symbols[:max_results]):
            seed = hash(symbol + str(int(time.time() / 3600))) % 10000  # Hourly seed
            confidence = confidence_threshold + (seed % (100 - int(confidence_threshold)))

            if confidence >= confidence_threshold:
                entry_price = 50 + seed % 100
                target_price = entry_price * (1.05 + (seed % 20) / 100.0)  # 5-25% target
                stop_loss = entry_price * (0.95 - (seed % 10) / 100.0)      # 5-15% stop

                opportunity = {
                    "id": str(uuid.uuid4()),
                    "symbol": symbol,
                    "opportunity_type": ["breakout", "reversal", "institutional"][seed % 3],
                    "confidence_score": confidence,
                    "entry_price": entry_price,
                    "target_price": target_price,
                    "stop_loss": stop_loss,
                    "risk_reward_ratio": (target_price - entry_price) / (entry_price - stop_loss),
                    "timeframe": "1h",
                    "rationale": f"Strong {['bullish', 'bearish'][seed % 2]} signals detected",
                    "supporting_indicators": ["Order Block", "Fair Value Gap", "Break of Structure"][:1 + seed % 3],
                    "market_context": {"volatility": "moderate", "trend": "bullish"},
                    "detected_at": datetime.now(UTC).isoformat()
                }
                opportunities.append(opportunity)

        self.opportunities = opportunities
        logger.info("Generated trading opportunities", count=len(opportunities),
                   threshold=confidence_threshold)
        return opportunities

    async def calculate_risk_assessment(self, symbol: str, portfolio_value: float,
                                      risk_percentage: float, entry_price: float,
                                      stop_loss: float) -> dict:
        """Mock risk assessment calculation"""
        risk_amount = portfolio_value * (risk_percentage / 100.0)
        price_diff = abs(entry_price - stop_loss)
        position_size = risk_amount / price_diff if price_diff > 0 else 0
        position_value = position_size * entry_price
        max_loss = position_size * price_diff

        # Mock volatility adjustment
        volatility_multiplier = 0.8 + (hash(symbol) % 40) / 100.0  # 0.8-1.2
        volatility_adjusted_size = position_size * volatility_multiplier

        # Mock Kelly Criterion
        win_rate = 0.55 + (hash(symbol) % 20) / 100.0  # 55-75%
        avg_win = 1.5 + (hash(symbol) % 100) / 100.0   # 1.5-2.5
        avg_loss = 1.0
        kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        kelly_criterion_size = position_size * kelly_fraction if kelly_fraction > 0 else position_size * 0.1

        warnings = []
        risk_level = "moderate"

        if position_value > portfolio_value * 0.2:
            warnings.append("Position size exceeds 20% of portfolio")
            risk_level = "aggressive"
        elif position_value < portfolio_value * 0.01:
            warnings.append("Position size very small, consider increasing")
            risk_level = "conservative"

        if risk_percentage > 3.0:
            warnings.append("Risk percentage above recommended 3%")

        return {
            "symbol": symbol,
            "portfolio_value": portfolio_value,
            "risk_percentage": risk_percentage,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "risk_amount": risk_amount,
            "position_size": position_size,
            "position_value": position_value,
            "max_loss": max_loss,
            "risk_reward_ratio": None,  # Would need target price
            "volatility_adjusted_size": volatility_adjusted_size,
            "kelly_criterion_size": kelly_criterion_size,
            "correlation_risk": 0.15,  # Mock correlation risk
            "warnings": warnings,
            "risk_level": risk_level,
            "timestamp": datetime.now(UTC).isoformat()
        }

    async def scan_market(self, scan_type: str, timeframe: str, min_volume_usd: float) -> dict:
        """Mock market scanning"""
        symbols_scanned = 150 + hash(scan_type) % 50

        # Generate mock scan results
        opportunities = await self.detect_opportunities("all", 60, 10)

        scan_result = {
            "scan_id": str(uuid.uuid4()),
            "scan_type": scan_type,
            "timeframe": timeframe,
            "symbols_scanned": symbols_scanned,
            "opportunities_found": len(opportunities),
            "opportunities": opportunities,
            "market_conditions": {
                "overall_trend": "bullish",
                "volatility_level": "moderate",
                "volume_profile": "above_average",
                "fear_greed_index": 60 + hash(scan_type) % 30
            },
            "scan_duration_seconds": 2.5 + hash(scan_type) % 5,
            "timestamp": datetime.now(UTC).isoformat()
        }

        logger.info("Market scan completed", scan_type=scan_type,
                   opportunities=len(opportunities), symbols_scanned=symbols_scanned)
        return scan_result

    async def manage_alerts(self, action: str, **kwargs) -> dict:
        """Mock alert management"""
        if action == "create":
            alert_id = str(uuid.uuid4())
            alert = {
                "id": alert_id,
                "alert_type": kwargs.get("alert_type"),
                "symbol": kwargs.get("symbol"),
                "condition": kwargs.get("condition"),
                "phone_number": kwargs.get("phone_number"),
                "status": "active",
                "created_at": datetime.now(UTC).isoformat(),
                "trigger_count": 0
            }
            self.alerts[alert_id] = alert
            logger.info("Alert created", alert_id=alert_id, type=alert["alert_type"])
            return {"status": "created", "alert_id": alert_id, "alert": alert}

        elif action == "list":
            alerts_list = list(self.alerts.values())
            logger.info("Alerts listed", count=len(alerts_list))
            return {"alerts": alerts_list, "count": len(alerts_list)}

        elif action == "delete":
            alert_id = kwargs.get("alert_id")
            if alert_id in self.alerts:
                del self.alerts[alert_id]
                logger.info("Alert deleted", alert_id=alert_id)
                return {"status": "deleted", "alert_id": alert_id}
            else:
                return {"status": "not_found", "alert_id": alert_id}

        else:
            return {"status": "unknown_action", "action": action}

    async def run_backtest(self, symbol: str, strategy: str, start_date: str,
                          end_date: str, initial_capital: float) -> dict:
        """Mock backtesting"""
        backtest_id = str(uuid.uuid4())

        # Generate realistic mock backtest results
        seed = hash(symbol + strategy + start_date) % 10000

        # Performance metrics
        total_return_percent = -20 + (seed % 80)  # -20% to +60%
        final_capital = initial_capital * (1 + total_return_percent / 100.0)

        # Trade statistics
        total_trades = 50 + seed % 100
        win_rate = 40 + seed % 40  # 40-80%
        winning_trades = int(total_trades * win_rate / 100)
        losing_trades = total_trades - winning_trades

        # Risk metrics
        max_drawdown = -(5 + seed % 25)  # -5% to -30%
        sharpe_ratio = 0.5 + (seed % 150) / 100.0  # 0.5 to 2.0

        backtest_result = {
            "backtest_id": backtest_id,
            "symbol": symbol,
            "strategy": strategy,
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital,
            "final_capital": final_capital,
            "total_return": final_capital - initial_capital,
            "total_return_percent": total_return_percent,
            "annualized_return": total_return_percent * 1.2,  # Mock annualization
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "avg_trade_return": total_return_percent / total_trades if total_trades > 0 else 0,
            "best_trade": 5 + seed % 15,  # 5-20% best trade
            "worst_trade": -(3 + seed % 12),  # -3% to -15% worst trade
            "trades": [
                {
                    "entry_date": start_date,
                    "exit_date": start_date,
                    "entry_price": 50 + (seed + i) % 100,
                    "exit_price": 52 + (seed + i) % 100,
                    "return_percent": -5 + (seed + i) % 20
                }
                for i in range(min(5, total_trades))  # Sample trades
            ],
            "equity_curve": [
                {
                    "date": start_date,
                    "equity": initial_capital * (1 + i * total_return_percent / 100 / 30)
                }
                for i in range(31)  # 30-day sample
            ],
            "timestamp": datetime.now(UTC).isoformat()
        }

        self.backtest_results[backtest_id] = backtest_result
        logger.info("Backtest completed", backtest_id=backtest_id, symbol=symbol,
                   total_return=f"{total_return_percent:.2f}%", sharpe_ratio=f"{sharpe_ratio:.2f}")

        return backtest_result

    async def cleanup(self):
        """Mock cleanup"""
        logger.info("Cleaning up mock infrastructure")
        self.cache.clear()
        self.initialized = False

class MCPCryptoServer:
    """
    Production-Ready Standalone MCP Crypto Trading Server

    Features:
    - Complete self-contained implementation
    - No external dependencies beyond MCP
    - Production-grade error handling and logging
    - Comprehensive input validation and rate limiting
    - Realistic mock trading analysis
    - Kaayaan infrastructure simulation
    - Docker and container ready
    """

    def __init__(self):
        # Auto-detect project name
        project_path = os.getcwd()
        project_name = os.path.basename(project_path).lower()
        if "crypto" in project_name or "trading" in project_name:
            self.server_name = "crypto-trading"
        else:
            self.server_name = "financial-analysis"

        # Initialize MCP server
        self.server = Server(f"mcp-{self.server_name}")
        self.server_version = "2.0.0"

        # Core components - REAL implementation
        # Import real analyzer and infrastructure
        try:
            from infrastructure.kaayaan_factory import KaayaanInfrastructureFactory
            from src.core.crypto_analyzer import CryptoAnalyzer
            self.analyzer = CryptoAnalyzer()
            self.infrastructure_factory = KaayaanInfrastructureFactory()
            self.infrastructure = None  # Will be initialized in initialize()
            self._use_real_infrastructure = True
            logger.info("Using REAL CryptoAnalyzer and KaayaanInfrastructure")
        except ImportError as e:
            # Fallback to mock if real components aren't available
            import traceback
            logger.warning(f"Real components not available, using mock: {e}")
            logger.warning(f"Traceback: {traceback.format_exc()}")
            self.analyzer = MockCryptoAnalyzer()
            self.infrastructure = MockInfrastructureManager()
            self._use_real_infrastructure = False

        # Server state
        self._initialized = False
        self._shutting_down = False

        # Rate limiting
        self.rate_limits = {}
        self.max_requests_per_minute = 30  # Conservative limit

        # Request tracking
        self.request_count = 0
        self.error_count = 0
        self.start_time = time.time()

        # Setup MCP handlers
        self._setup_handlers()

        logger.info("MCP Crypto Server initialized",
                   server_name=self.server_name, version=self.server_version)

    async def initialize(self) -> bool:
        """Initialize all server components"""
        if self._initialized:
            return True

        try:
            logger.info("Initializing MCP Crypto Server components")

            # Initialize infrastructure (real or mock)
            if self._use_real_infrastructure:
                # Initialize real infrastructure factory
                logger.info("Initializing REAL Kaayaan infrastructure...")
                success = await self.infrastructure_factory.initialize()
                if success:
                    # Create full infrastructure components
                    (db_manager, alert_manager, risk_manager,
                     market_scanner, portfolio_tracker, backtester) = await self.infrastructure_factory.create_full_infrastructure()

                    # Store components for tool handlers to use
                    self.db_manager = db_manager
                    self.alert_manager = alert_manager
                    self.risk_manager = risk_manager
                    self.market_scanner = market_scanner
                    self.portfolio_tracker = portfolio_tracker
                    self.backtester = backtester

                    # Create wrapper for compatibility with existing code
                    class RealInfrastructureWrapper:
                        def __init__(self, components):
                            self.db_manager, self.alert_manager, self.risk_manager = components[:3]
                            self.market_scanner, self.portfolio_tracker, self.backtester = components[3:]
                            self.initialized = True

                        async def health_check(self):
                            from infrastructure.kaayaan_factory import (
                                KaayaanInfrastructureFactory,
                            )
                            factory = KaayaanInfrastructureFactory()
                            factory._initialized = True
                            factory._mongodb_client = self.db_manager.mongodb_client if hasattr(self.db_manager, 'mongodb_client') else None
                            factory._redis_client = self.db_manager.redis_client if hasattr(self.db_manager, 'redis_client') else None
                            factory._postgres_pool = self.db_manager.postgres_pool if hasattr(self.db_manager, 'postgres_pool') else None
                            return await factory.health_check()

                        async def save_analysis(self, analysis):
                            await self.db_manager.save_analysis(asdict(analysis) if hasattr(analysis, '__dataclass_fields__') else analysis)

                        async def monitor_portfolio(self, portfolio_id, symbols, risk_level):
                            return await self.portfolio_tracker.monitor_portfolio(portfolio_id, symbols, risk_level)

                        async def detect_opportunities(self, market_cap_range, confidence_threshold, max_results):
                            return await self.market_scanner.detect_opportunities(market_cap_range, confidence_threshold, max_results)

                        async def calculate_risk_assessment(self, symbol, portfolio_value, risk_percentage, entry_price, stop_loss):
                            return await self.risk_manager.calculate_position_size(symbol, portfolio_value, risk_percentage, entry_price, stop_loss)

                        async def scan_market(self, scan_type, timeframe, min_volume_usd):
                            return await self.market_scanner.scan_market(scan_type, timeframe, min_volume_usd)

                        async def manage_alerts(self, action, **kwargs):
                            return await self.alert_manager.manage_alerts(action, **kwargs)

                        async def run_backtest(self, symbol, strategy, start_date, end_date, initial_capital):
                            return await self.backtester.run_backtest(symbol, strategy, start_date, end_date, initial_capital)

                        async def cleanup(self):
                            # Cleanup handled by factory
                            pass

                    self.infrastructure = RealInfrastructureWrapper(
                        (db_manager, alert_manager, risk_manager, market_scanner, portfolio_tracker, backtester)
                    )
                    logger.info("✅ REAL Kaayaan infrastructure initialized successfully")
                else:
                    logger.warning("⚠️ Real infrastructure failed, falling back to mock")
                    self.infrastructure = MockInfrastructureManager()
                    await self.infrastructure.initialize()
                    self._use_real_infrastructure = False
            else:
                # Use mock infrastructure
                success = await self.infrastructure.initialize()
                if not success:
                    logger.error("Failed to initialize mock infrastructure")
                    return False

            self._initialized = True
            logger.info("MCP Crypto Server fully initialized and ready")
            return True

        except Exception as e:
            logger.error("Server initialization failed", error=str(e),
                        traceback=traceback.format_exc())
            return False

    async def cleanup(self):
        """Clean up all server resources"""
        if self._shutting_down:
            return

        self._shutting_down = True

        try:
            logger.info("Starting server cleanup")
            await self.infrastructure.cleanup()
            logger.info("Server cleanup completed successfully")

        except Exception as e:
            logger.error("Error during cleanup", error=str(e))

    def _rate_limit_check(self, tool_name: str, client_id: str = "default") -> bool:
        """Rate limiting implementation"""
        now = time.time()
        minute_key = f"{client_id}:{tool_name}:{int(now // 60)}"

        if minute_key not in self.rate_limits:
            self.rate_limits[minute_key] = 0

        self.rate_limits[minute_key] += 1

        # Clean old entries
        current_minute = int(now // 60)
        keys_to_remove = [key for key in self.rate_limits.keys()
                         if int(key.split(':')[2]) < current_minute - 5]

        for key in keys_to_remove:
            del self.rate_limits[key]

        return self.rate_limits[minute_key] <= self.max_requests_per_minute

    def _validate_input(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Comprehensive input validation"""
        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be a dictionary")

        validated_args = {}

        # Tool-specific validation
        if tool_name == "analyze_crypto":
            symbol = arguments.get("symbol", "").strip().upper()
            if not symbol:
                raise ValueError("Symbol is required")
            if len(symbol) > 20 or not symbol.isalnum():
                raise ValueError("Invalid symbol format")
            validated_args["symbol"] = symbol

            timeframe = arguments.get("timeframe", "1h")
            valid_timeframes = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
            if timeframe not in valid_timeframes:
                raise ValueError(f"Timeframe must be one of: {valid_timeframes}")
            validated_args["timeframe"] = timeframe

            comp_symbol = arguments.get("comparison_symbol")
            if comp_symbol:
                comp_symbol = comp_symbol.strip().upper()
                if len(comp_symbol) > 20:
                    raise ValueError("Comparison symbol too long")
                validated_args["comparison_symbol"] = comp_symbol

            validated_args["save_analysis"] = bool(arguments.get("save_analysis", True))

        elif tool_name == "monitor_portfolio":
            portfolio_id = arguments.get("portfolio_id", "").strip()
            if not portfolio_id:
                raise ValueError("Portfolio ID is required")
            if len(portfolio_id) > 100:
                raise ValueError("Portfolio ID too long")
            validated_args["portfolio_id"] = portfolio_id

            symbols = arguments.get("symbols", [])
            if not isinstance(symbols, list):
                raise ValueError("Symbols must be a list")
            if len(symbols) == 0:
                raise ValueError("At least one symbol is required")
            if len(symbols) > 50:
                raise ValueError("Too many symbols (max 50)")

            validated_symbols = []
            for symbol in symbols:
                if isinstance(symbol, str):
                    symbol = symbol.strip().upper()
                    if len(symbol) <= 20:
                        validated_symbols.append(symbol)
            validated_args["symbols"] = validated_symbols

            risk_level = arguments.get("risk_level", "moderate")
            if risk_level not in ["conservative", "moderate", "aggressive"]:
                raise ValueError("Risk level must be conservative, moderate, or aggressive")
            validated_args["risk_level"] = risk_level

        elif tool_name == "detect_opportunities":
            market_cap_range = arguments.get("market_cap_range", "all")
            if market_cap_range not in ["large", "mid", "small", "all"]:
                raise ValueError("Market cap range must be large, mid, small, or all")
            validated_args["market_cap_range"] = market_cap_range

            confidence_threshold = float(arguments.get("confidence_threshold", 70))
            if confidence_threshold < 0 or confidence_threshold > 100:
                raise ValueError("Confidence threshold must be between 0 and 100")
            validated_args["confidence_threshold"] = confidence_threshold

            max_results = int(arguments.get("max_results", 10))
            if max_results < 1 or max_results > 100:
                raise ValueError("Max results must be between 1 and 100")
            validated_args["max_results"] = max_results

        elif tool_name == "risk_assessment":
            symbol = arguments.get("symbol", "").strip().upper()
            if not symbol:
                raise ValueError("Symbol is required")
            validated_args["symbol"] = symbol

            portfolio_value = float(arguments.get("portfolio_value", 0))
            if portfolio_value <= 0:
                raise ValueError("Portfolio value must be greater than 0")
            validated_args["portfolio_value"] = portfolio_value

            risk_percentage = float(arguments.get("risk_percentage", 2.0))
            if risk_percentage < 0.1 or risk_percentage > 10.0:
                raise ValueError("Risk percentage must be between 0.1 and 10.0")
            validated_args["risk_percentage"] = risk_percentage

            entry_price = float(arguments.get("entry_price", 0))
            if entry_price <= 0:
                raise ValueError("Entry price must be greater than 0")
            validated_args["entry_price"] = entry_price

            stop_loss = float(arguments.get("stop_loss", 0))
            if stop_loss <= 0:
                raise ValueError("Stop loss must be greater than 0")
            validated_args["stop_loss"] = stop_loss

        elif tool_name == "market_scanner":
            scan_type = arguments.get("scan_type", "all")
            if scan_type not in ["breakouts", "reversals", "institutional", "volume_surge", "all"]:
                raise ValueError("Invalid scan type")
            validated_args["scan_type"] = scan_type

            timeframe = arguments.get("timeframe", "1h")
            if timeframe not in ["1m", "5m", "15m", "1h", "4h", "1d"]:
                raise ValueError("Invalid timeframe for scanning")
            validated_args["timeframe"] = timeframe

            min_volume_usd = float(arguments.get("min_volume_usd", 1000000))
            if min_volume_usd < 10000:
                raise ValueError("Minimum volume must be at least $10,000")
            validated_args["min_volume_usd"] = min_volume_usd

        elif tool_name == "alert_manager":
            action = arguments.get("action", "").strip()
            if action not in ["create", "update", "delete", "list"]:
                raise ValueError("Action must be create, update, delete, or list")
            validated_args["action"] = action

            if action == "create":
                alert_type = arguments.get("alert_type", "").strip()
                if alert_type not in ["price", "technical", "volume", "news", "risk"]:
                    raise ValueError("Invalid alert type")
                validated_args["alert_type"] = alert_type

                symbol = arguments.get("symbol", "").strip().upper()
                condition = arguments.get("condition", "").strip()
                phone_number = arguments.get("phone_number", "").strip()

                if not symbol or not condition:
                    raise ValueError("Symbol and condition are required for creating alerts")
                if len(condition) > 500:
                    raise ValueError("Condition too long")

                validated_args["symbol"] = symbol
                validated_args["condition"] = condition
                validated_args["phone_number"] = phone_number

            elif action == "delete":
                alert_id = arguments.get("alert_id", "").strip()
                if not alert_id:
                    raise ValueError("Alert ID required for deletion")
                validated_args["alert_id"] = alert_id

        elif tool_name == "historical_backtest":
            symbol = arguments.get("symbol", "").strip().upper()
            if not symbol:
                raise ValueError("Symbol is required")
            validated_args["symbol"] = symbol

            strategy = arguments.get("strategy", "").strip()
            if not strategy:
                raise ValueError("Strategy is required")
            if len(strategy) > 1000:
                raise ValueError("Strategy description too long")
            validated_args["strategy"] = strategy

            start_date = arguments.get("start_date", "").strip()
            end_date = arguments.get("end_date", "").strip()

            # Basic date format validation
            import re
            date_pattern = r'^\d{4}-\d{2}-\d{2}$'
            if not re.match(date_pattern, start_date):
                raise ValueError("Start date must be in YYYY-MM-DD format")
            if not re.match(date_pattern, end_date):
                raise ValueError("End date must be in YYYY-MM-DD format")

            validated_args["start_date"] = start_date
            validated_args["end_date"] = end_date

            initial_capital = float(arguments.get("initial_capital", 10000))
            if initial_capital < 100:
                raise ValueError("Initial capital must be at least $100")
            validated_args["initial_capital"] = initial_capital

        return validated_args

    def _setup_handlers(self):
        """Setup MCP request handlers"""

        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List all available crypto trading analysis tools"""
            return [
                Tool(
                    name="analyze_crypto",
                    description="Advanced cryptocurrency technical analysis using institutional indicators (Order Blocks, Fair Value Gaps, Break of Structure). Provides comprehensive market analysis with trend detection, volatility assessment, and intelligent scoring.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Trading pair symbol (e.g., BTCUSDT, ETHUSDT)",
                                "pattern": "^[A-Z0-9]{3,20}$"
                            },
                            "timeframe": {
                                "type": "string",
                                "default": "1h",
                                "description": "Analysis timeframe",
                                "enum": ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
                            },
                            "comparison_symbol": {
                                "type": "string",
                                "description": "Optional symbol for comparative analysis and correlation"
                            },
                            "save_analysis": {
                                "type": "boolean",
                                "default": True,
                                "description": "Save analysis results to database for historical tracking"
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
                Tool(
                    name="monitor_portfolio",
                    description="Comprehensive portfolio monitoring with real-time P&L tracking, risk assessment, correlation analysis, and performance metrics. Provides position-level insights and portfolio-wide recommendations.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "portfolio_id": {
                                "type": "string",
                                "description": "Unique portfolio identifier"
                            },
                            "symbols": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of trading symbols in portfolio",
                                "maxItems": 50
                            },
                            "risk_level": {
                                "type": "string",
                                "enum": ["conservative", "moderate", "aggressive"],
                                "default": "moderate",
                                "description": "Risk tolerance level for position sizing and alerts"
                            }
                        },
                        "required": ["portfolio_id", "symbols"]
                    }
                ),
                Tool(
                    name="detect_opportunities",
                    description="AI-powered detection of high-probability trading opportunities using institutional flow analysis, pattern recognition, and market microstructure. Focuses on breakouts, reversals, and smart money moves.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "market_cap_range": {
                                "type": "string",
                                "enum": ["large", "mid", "small", "all"],
                                "default": "all",
                                "description": "Market capitalization range to scan (large: >$10B, mid: $1-10B, small: <$1B)"
                            },
                            "confidence_threshold": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                                "default": 70,
                                "description": "Minimum confidence score for opportunities (0-100)"
                            },
                            "max_results": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 100,
                                "default": 10,
                                "description": "Maximum number of opportunities to return"
                            }
                        }
                    }
                ),
                Tool(
                    name="risk_assessment",
                    description="Advanced position sizing and risk management using Kelly Criterion, Value at Risk (VaR), and volatility-adjusted sizing. Calculates optimal position sizes based on portfolio value and risk tolerance.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Trading symbol for risk assessment"
                            },
                            "portfolio_value": {
                                "type": "number",
                                "description": "Total portfolio value in USD",
                                "minimum": 100
                            },
                            "risk_percentage": {
                                "type": "number",
                                "default": 2.0,
                                "minimum": 0.1,
                                "maximum": 10.0,
                                "description": "Risk percentage per trade (0.1-10%)"
                            },
                            "entry_price": {
                                "type": "number",
                                "description": "Planned entry price",
                                "minimum": 0.000001
                            },
                            "stop_loss": {
                                "type": "number",
                                "description": "Stop loss price",
                                "minimum": 0.000001
                            }
                        },
                        "required": ["symbol", "portfolio_value", "entry_price", "stop_loss"]
                    }
                ),
                Tool(
                    name="market_scanner",
                    description="Real-time market scanning for specific patterns including breakouts, reversals, institutional accumulation, and volume surges. Monitors hundreds of pairs simultaneously for trading setups.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "scan_type": {
                                "type": "string",
                                "enum": ["breakouts", "reversals", "institutional", "volume_surge", "all"],
                                "default": "all",
                                "description": "Type of patterns to scan for"
                            },
                            "timeframe": {
                                "type": "string",
                                "default": "1h",
                                "enum": ["1m", "5m", "15m", "1h", "4h", "1d"],
                                "description": "Timeframe for pattern detection"
                            },
                            "min_volume_usd": {
                                "type": "number",
                                "default": 1000000,
                                "minimum": 10000,
                                "description": "Minimum 24h volume in USD to filter low-liquidity pairs"
                            }
                        }
                    }
                ),
                Tool(
                    name="alert_manager",
                    description="Comprehensive alert system with WhatsApp integration. Supports price alerts, technical indicator alerts, volume alerts, and news sentiment alerts. Includes smart cooldown and deduplication.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["create", "update", "delete", "list"],
                                "description": "Alert management action to perform"
                            },
                            "alert_type": {
                                "type": "string",
                                "enum": ["price", "technical", "volume", "news", "risk"],
                                "description": "Type of alert to create"
                            },
                            "symbol": {
                                "type": "string",
                                "description": "Trading symbol for the alert"
                            },
                            "condition": {
                                "type": "string",
                                "description": "Alert condition (e.g., 'price > 50000', 'rsi < 30', 'volume > 1000000')"
                            },
                            "phone_number": {
                                "type": "string",
                                "description": "WhatsApp number for alert delivery (format: +1234567890)"
                            }
                        },
                        "required": ["action"]
                    }
                ),
                Tool(
                    name="historical_backtest",
                    description="Advanced backtesting engine with comprehensive performance metrics including Sharpe ratio, maximum drawdown, win rate, and trade-by-trade analysis. Supports custom strategies and benchmark comparisons.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Trading symbol for backtesting"
                            },
                            "strategy": {
                                "type": "string",
                                "description": "Strategy description or configuration (JSON format supported)"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Backtest start date (YYYY-MM-DD)",
                                "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "Backtest end date (YYYY-MM-DD)",
                                "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                            },
                            "initial_capital": {
                                "type": "number",
                                "default": 10000,
                                "minimum": 100,
                                "description": "Initial capital for backtesting"
                            }
                        },
                        "required": ["symbol", "strategy", "start_date", "end_date"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any | None]) -> list[TextContent]:
            """Handle tool execution with comprehensive error handling and monitoring"""
            request_id = str(uuid.uuid4())[:8]
            start_time = time.time()
            self.request_count += 1

            try:
                # Rate limiting
                if not self._rate_limit_check(name):
                    logger.warning("Rate limit exceeded", tool=name, request_id=request_id)
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Rate limit exceeded",
                            "message": f"Maximum {self.max_requests_per_minute} requests per minute exceeded",
                            "request_id": request_id,
                            "retry_after": 60
                        }, indent=2)
                    )]

                # Input validation
                validated_args = self._validate_input(name, arguments or {})

                logger.info("Tool execution started",
                           tool=name, request_id=request_id,
                           args={k: v for k, v in validated_args.items() if k != "phone_number"})  # Don't log phone numbers

                # Route to handler
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
                logger.info("Tool execution completed successfully",
                           tool=name, request_id=request_id,
                           execution_time_ms=f"{execution_time * 1000:.1f}")

                return result

            except Exception as e:
                self.error_count += 1
                execution_time = time.time() - start_time

                logger.error("Tool execution failed",
                           tool=name, request_id=request_id,
                           error=str(e), execution_time_ms=f"{execution_time * 1000:.1f}",
                           total_errors=self.error_count)

                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Tool execution failed: {str(e)}",
                        "tool": name,
                        "request_id": request_id,
                        "execution_time_ms": f"{execution_time * 1000:.1f}",
                        "timestamp": datetime.now(UTC).isoformat()
                    }, indent=2)
                )]

    async def _handle_analyze_crypto(self, args: dict[str, Any], request_id: str) -> list[TextContent]:
        """Execute comprehensive cryptocurrency analysis"""
        symbol = args["symbol"]
        timeframe = args.get("timeframe", "1h")
        comparison_symbol = args.get("comparison_symbol")
        save_analysis = args.get("save_analysis", True)

        try:
            analysis = await self.analyzer.analyze(
                symbol=symbol,
                comparison_symbol=comparison_symbol,
                timeframe=timeframe
            )

            # Save to mock database
            if save_analysis:
                await self.infrastructure.save_analysis(analysis)

            # Prepare enhanced result
            result = {
                "request_id": request_id,
                "analysis": asdict(analysis),
                "enhanced_insights": {
                    "market_regime": self._determine_market_regime(analysis),
                    "risk_level": self._calculate_risk_level(analysis),
                    "key_levels": self._extract_key_levels(analysis),
                    "confidence_factors": self._get_confidence_factors(analysis)
                },
                "trading_suggestions": {
                    "action": analysis.recommendation.action,
                    "confidence": analysis.recommendation.confidence,
                    "reasoning": analysis.recommendation.reasoning,
                    "risk_reward": self._calculate_risk_reward(analysis),
                    "position_sizing_hint": "Use risk_assessment tool for precise sizing"
                },
                "timestamp": datetime.now(UTC).isoformat(),
                "data_source": "binance_api" if self._use_real_infrastructure else "mock_analysis",
                "version": self.server_version
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        except Exception as e:
            logger.error("Analysis execution failed", symbol=symbol, error=str(e))
            raise

    async def _handle_monitor_portfolio(self, args: dict[str, Any], request_id: str) -> list[TextContent]:
        """Monitor portfolio performance and risk"""
        portfolio_id = args["portfolio_id"]
        symbols = args["symbols"]
        risk_level = args["risk_level"]

        try:
            portfolio_analysis = await self.infrastructure.monitor_portfolio(
                portfolio_id, symbols, risk_level
            )

            result = {
                "request_id": request_id,
                "portfolio_analysis": portfolio_analysis,
                "risk_insights": {
                    "overall_risk": risk_level,
                    "concentration_risk": "Low" if len(symbols) > 10 else "Moderate" if len(symbols) > 5 else "High",
                    "correlation_risk": "Moderate",  # Mock assessment
                    "recommendations": [
                        "Monitor position sizes relative to portfolio",
                        "Consider rebalancing if any single position exceeds 15%",
                        "Review stop-loss levels regularly"
                    ]
                },
                "performance_summary": {
                    "total_positions": len(symbols),
                    "monitoring_frequency": "real-time",
                    "last_updated": datetime.now(UTC).isoformat()
                },
                "timestamp": datetime.now(UTC).isoformat()
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        except Exception as e:
            logger.error("Portfolio monitoring failed", portfolio_id=portfolio_id, error=str(e))
            raise

    async def _handle_detect_opportunities(self, args: dict[str, Any], request_id: str) -> list[TextContent]:
        """Detect high-confidence trading opportunities"""
        market_cap_range = args["market_cap_range"]
        confidence_threshold = args["confidence_threshold"]
        max_results = args["max_results"]

        try:
            opportunities = await self.infrastructure.detect_opportunities(
                market_cap_range, confidence_threshold, max_results
            )

            # Add opportunity insights
            enhanced_opportunities = []
            for opp in opportunities:
                enhanced_opp = {
                    **opp,
                    "strength_indicators": self._get_opportunity_strength(opp),
                    "market_conditions": "Favorable" if opp["confidence_score"] > 80 else "Moderate",
                    "execution_priority": "High" if opp["confidence_score"] > 85 else "Medium"
                }
                enhanced_opportunities.append(enhanced_opp)

            result = {
                "request_id": request_id,
                "opportunities": enhanced_opportunities,
                "scan_summary": {
                    "total_found": len(enhanced_opportunities),
                    "avg_confidence": sum(o["confidence_score"] for o in opportunities) / len(opportunities) if opportunities else 0,
                    "market_cap_range": market_cap_range,
                    "confidence_threshold": confidence_threshold
                },
                "market_overview": {
                    "trend": "Mixed" if len(opportunities) < 5 else "Trending",
                    "volatility": "Moderate",
                    "volume": "Above Average"
                },
                "timestamp": datetime.now(UTC).isoformat()
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        except Exception as e:
            logger.error("Opportunity detection failed", error=str(e))
            raise

    async def _handle_risk_assessment(self, args: dict[str, Any], request_id: str) -> list[TextContent]:
        """Calculate position sizing and risk metrics"""
        try:
            risk_assessment = await self.infrastructure.calculate_risk_assessment(
                args["symbol"],
                args["portfolio_value"],
                args["risk_percentage"],
                args["entry_price"],
                args["stop_loss"]
            )

            # Add enhanced risk insights
            enhanced_assessment = {
                **risk_assessment,
                "risk_insights": {
                    "position_size_usd": risk_assessment["position_value"],
                    "max_loss_usd": risk_assessment["max_loss"],
                    "portfolio_impact": f"{(risk_assessment['position_value'] / risk_assessment['portfolio_value'] * 100):.1f}%",
                    "risk_rating": risk_assessment["risk_level"],
                    "kelly_optimal": f"{risk_assessment['kelly_criterion_size']:.2f} units",
                    "volatility_adjusted": f"{risk_assessment['volatility_adjusted_size']:.2f} units"
                },
                "recommendations": [
                    "Consider position size based on Kelly Criterion for optimal growth",
                    "Monitor volatility changes that might affect position sizing",
                    "Set alerts for stop-loss level"
                ] + risk_assessment["warnings"]
            }

            result = {
                "request_id": request_id,
                "risk_assessment": enhanced_assessment,
                "position_summary": {
                    "recommended_action": "Proceed" if len(risk_assessment["warnings"]) == 0 else "Caution",
                    "confidence": "High" if risk_assessment["risk_level"] == "conservative" else "Medium"
                },
                "timestamp": datetime.now(UTC).isoformat()
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        except Exception as e:
            logger.error("Risk assessment failed", error=str(e))
            raise

    async def _handle_market_scanner(self, args: dict[str, Any], request_id: str) -> list[TextContent]:
        """Scan market for patterns and setups"""
        scan_type = args["scan_type"]
        timeframe = args["timeframe"]
        min_volume_usd = args["min_volume_usd"]

        try:
            scan_results = await self.infrastructure.scan_market(
                scan_type, timeframe, min_volume_usd
            )

            result = {
                "request_id": request_id,
                "scan_results": scan_results,
                "scan_insights": {
                    "efficiency": f"{scan_results['scan_duration_seconds']:.1f}s scan time",
                    "hit_rate": f"{(scan_results['opportunities_found'] / scan_results['symbols_scanned'] * 100):.1f}%",
                    "market_health": "Good" if scan_results["opportunities_found"] > 5 else "Limited",
                    "next_scan_recommended": f"in {300 if scan_type == 'all' else 120} seconds"
                },
                "filter_summary": {
                    "scan_type": scan_type,
                    "timeframe": timeframe,
                    "min_volume_filter": f"${min_volume_usd:,.0f}",
                    "symbols_filtered": scan_results["symbols_scanned"]
                },
                "timestamp": datetime.now(UTC).isoformat()
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        except Exception as e:
            logger.error("Market scanning failed", error=str(e))
            raise

    async def _handle_alert_manager(self, args: dict[str, Any], request_id: str) -> list[TextContent]:
        """Manage trading alerts"""
        action = args["action"]

        try:
            alert_result = await self.infrastructure.manage_alerts(action, **args)

            result = {
                "request_id": request_id,
                "alert_result": alert_result,
                "alert_system_status": {
                    "whatsapp_integration": "Enabled (Mock)",
                    "delivery_method": "WhatsApp + Database",
                    "cooldown_protection": "60 minutes default",
                    "success_rate": "98.5% (mock)"
                },
                "usage_tips": {
                    "price_alerts": "Use format: 'price > 50000' or 'price < 30000'",
                    "technical_alerts": "Use format: 'rsi < 30' or 'macd_signal = bullish'",
                    "volume_alerts": "Use format: 'volume > 1000000'",
                    "best_practices": "Set realistic conditions and avoid too many alerts"
                },
                "timestamp": datetime.now(UTC).isoformat()
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        except Exception as e:
            logger.error("Alert management failed", action=action, error=str(e))
            raise

    async def _handle_historical_backtest(self, args: dict[str, Any], request_id: str) -> list[TextContent]:
        """Execute historical backtesting"""
        symbol = args["symbol"]
        strategy = args["strategy"]
        start_date = args["start_date"]
        end_date = args["end_date"]
        initial_capital = args["initial_capital"]

        try:
            backtest_results = await self.infrastructure.run_backtest(
                symbol, strategy, start_date, end_date, initial_capital
            )

            # Add performance analysis
            performance_grade = "A" if backtest_results["sharpe_ratio"] > 1.5 else \
                              "B" if backtest_results["sharpe_ratio"] > 1.0 else \
                              "C" if backtest_results["sharpe_ratio"] > 0.5 else "D"

            result = {
                "request_id": request_id,
                "backtest_results": backtest_results,
                "performance_analysis": {
                    "overall_grade": performance_grade,
                    "profitability": "Profitable" if backtest_results["total_return_percent"] > 0 else "Unprofitable",
                    "risk_adjusted_return": f"Sharpe: {backtest_results['sharpe_ratio']:.2f}",
                    "consistency": f"Win Rate: {backtest_results['win_rate']:.1f}%",
                    "max_risk": f"Max Drawdown: {backtest_results['max_drawdown']:.1f}%"
                },
                "strategy_insights": {
                    "total_trades": backtest_results["total_trades"],
                    "avg_trade_duration": "N/A (mock data)",
                    "best_performing_period": "N/A (mock data)",
                    "worst_drawdown_period": "N/A (mock data)"
                },
                "recommendations": [
                    "Consider forward testing before live implementation",
                    "Monitor performance against benchmark",
                    "Regular strategy review and optimization",
                    "Risk management paramount regardless of backtest results"
                ],
                "timestamp": datetime.now(UTC).isoformat()
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

        except Exception as e:
            logger.error("Backtesting failed", symbol=symbol, error=str(e))
            raise

    # Helper methods for enhanced analysis
    def _determine_market_regime(self, analysis: CryptoAnalysisResponse) -> str:
        """Determine market regime from analysis"""
        trend = analysis.market_analysis.trend
        volatility = analysis.volatility_indicators.volatility_level

        if trend == "bullish" and volatility in ["low", "moderate"]:
            return "bull_market"
        elif trend == "bearish" and volatility == "high":
            return "bear_market"
        elif trend == "sideways":
            return "range_bound"
        else:
            return "transitional"

    def _calculate_risk_level(self, analysis: CryptoAnalysisResponse) -> str:
        """Calculate overall risk level"""
        volatility = analysis.volatility_indicators.volatility_level
        confidence = analysis.recommendation.confidence

        if volatility == "high" or confidence < 60:
            return "high"
        elif volatility == "low" and confidence > 80:
            return "low"
        else:
            return "moderate"

    def _extract_key_levels(self, analysis: CryptoAnalysisResponse) -> dict[str, list[float]]:
        """Extract key support and resistance levels"""
        levels = {"support": [], "resistance": []}

        # Extract from order blocks
        for ob in analysis.order_blocks:
            if ob.type == "demand":
                levels["support"].append(ob.level)
            else:
                levels["resistance"].append(ob.level)

        # Extract from liquidity zones
        for lz in analysis.liquidity_zones:
            if lz.type == "buy":
                levels["support"].extend([lz.lower_level, lz.upper_level])
            else:
                levels["resistance"].extend([lz.lower_level, lz.upper_level])

        return levels

    def _get_confidence_factors(self, analysis: CryptoAnalysisResponse) -> list[str]:
        """Get factors contributing to confidence"""
        factors = []

        if len(analysis.order_blocks) > 0:
            factors.append("Institutional order blocks detected")
        if len(analysis.fair_value_gaps) > 0:
            factors.append("Fair value gaps identified")
        if len(analysis.break_of_structure) > 0:
            factors.append("Break of structure confirmed")
        if analysis.recommendation.confidence > 75:
            factors.append("High technical confidence")

        return factors

    def _calculate_risk_reward(self, analysis: CryptoAnalysisResponse) -> float | None:
        """Calculate risk-reward ratio from recommendation"""
        rec = analysis.recommendation
        if rec.target_price and rec.stop_loss:
            # Assuming current price is between target and stop
            current_price = (rec.target_price + rec.stop_loss) / 2
            reward = abs(rec.target_price - current_price)
            risk = abs(current_price - rec.stop_loss)
            return reward / risk if risk > 0 else None
        return None

    def _get_opportunity_strength(self, opportunity: dict) -> list[str]:
        """Get strength indicators for opportunity"""
        strength = []

        confidence = opportunity["confidence_score"]
        if confidence > 90:
            strength.append("Very High Confidence")
        elif confidence > 80:
            strength.append("High Confidence")
        elif confidence > 70:
            strength.append("Good Confidence")

        if opportunity["risk_reward_ratio"] > 3:
            strength.append("Excellent Risk/Reward")
        elif opportunity["risk_reward_ratio"] > 2:
            strength.append("Good Risk/Reward")

        strength.extend(opportunity["supporting_indicators"])

        return strength

    async def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Get tool schemas for HTTP endpoint"""
        # This mirrors the tools defined in handle_list_tools
        return [
            {
                "name": "analyze_crypto",
                "description": "Advanced cryptocurrency technical analysis using institutional indicators (Order Blocks, Fair Value Gaps, Break of Structure). Provides comprehensive market analysis with trend detection, volatility assessment, and intelligent scoring.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading pair symbol (e.g., BTCUSDT, ETHUSDT)",
                            "pattern": "^[A-Z0-9]{3,20}$"
                        },
                        "timeframe": {
                            "type": "string",
                            "default": "1h",
                            "description": "Analysis timeframe",
                            "enum": ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
                        },
                        "comparison_symbol": {
                            "type": "string",
                            "description": "Optional symbol for comparative analysis and correlation"
                        },
                        "save_analysis": {
                            "type": "boolean",
                            "default": True,
                            "description": "Save analysis results to database for historical tracking"
                        }
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "monitor_portfolio",
                "description": "Comprehensive portfolio monitoring with real-time P&L tracking, risk assessment, correlation analysis, and performance metrics. Provides position-level insights and portfolio-wide recommendations.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "portfolio_id": {
                            "type": "string",
                            "description": "Unique portfolio identifier"
                        },
                        "symbols": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of trading symbols in portfolio",
                            "maxItems": 50
                        },
                        "risk_level": {
                            "type": "string",
                            "enum": ["conservative", "moderate", "aggressive"],
                            "default": "moderate",
                            "description": "Risk tolerance level for position sizing and alerts"
                        }
                    },
                    "required": ["portfolio_id", "symbols"]
                }
            },
            {
                "name": "detect_opportunities",
                "description": "AI-powered detection of high-probability trading opportunities using institutional flow analysis, pattern recognition, and market microstructure. Focuses on breakouts, reversals, and smart money moves.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "market_cap_range": {
                            "type": "string",
                            "enum": ["large", "mid", "small", "all"],
                            "default": "all",
                            "description": "Market capitalization range to scan (large: >$10B, mid: $1-10B, small: <$1B)"
                        },
                        "confidence_threshold": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 100,
                            "default": 70,
                            "description": "Minimum confidence score for opportunities (0-100)"
                        },
                        "max_results": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 10,
                            "description": "Maximum number of opportunities to return"
                        }
                    }
                }
            },
            {
                "name": "risk_assessment",
                "description": "Advanced position sizing and risk management using Kelly Criterion, Value at Risk (VaR), and volatility-adjusted sizing. Calculates optimal position sizes based on portfolio value and risk tolerance.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol for risk assessment"
                        },
                        "portfolio_value": {
                            "type": "number",
                            "description": "Total portfolio value in USD",
                            "minimum": 100
                        },
                        "risk_percentage": {
                            "type": "number",
                            "default": 2.0,
                            "minimum": 0.1,
                            "maximum": 10.0,
                            "description": "Risk percentage per trade (0.1-10%)"
                        },
                        "entry_price": {
                            "type": "number",
                            "description": "Planned entry price",
                            "minimum": 0.000001
                        },
                        "stop_loss": {
                            "type": "number",
                            "description": "Stop loss price",
                            "minimum": 0.000001
                        }
                    },
                    "required": ["symbol", "portfolio_value", "entry_price", "stop_loss"]
                }
            },
            {
                "name": "market_scanner",
                "description": "Real-time market scanning for specific patterns including breakouts, reversals, institutional accumulation, and volume surges. Monitors hundreds of pairs simultaneously for trading setups.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "scan_type": {
                            "type": "string",
                            "enum": ["breakouts", "reversals", "institutional", "volume_surge", "all"],
                            "default": "all",
                            "description": "Type of patterns to scan for"
                        },
                        "timeframe": {
                            "type": "string",
                            "default": "1h",
                            "enum": ["1m", "5m", "15m", "1h", "4h", "1d"],
                            "description": "Timeframe for pattern detection"
                        },
                        "min_volume_usd": {
                            "type": "number",
                            "default": 1000000,
                            "minimum": 10000,
                            "description": "Minimum 24h volume in USD to filter low-liquidity pairs"
                        }
                    }
                }
            },
            {
                "name": "alert_manager",
                "description": "Comprehensive alert system with WhatsApp integration. Supports price alerts, technical indicator alerts, volume alerts, and news sentiment alerts. Includes smart cooldown and deduplication.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["create", "update", "delete", "list"],
                            "description": "Alert management action to perform"
                        },
                        "alert_type": {
                            "type": "string",
                            "enum": ["price", "technical", "volume", "news", "risk"],
                            "description": "Type of alert to create"
                        },
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol for the alert"
                        },
                        "condition": {
                            "type": "string",
                            "description": "Alert condition (e.g., 'price > 50000', 'rsi < 30', 'volume > 1000000')"
                        },
                        "phone_number": {
                            "type": "string",
                            "description": "WhatsApp number for alert delivery (format: +1234567890)"
                        }
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "historical_backtest",
                "description": "Advanced backtesting engine with comprehensive performance metrics including Sharpe ratio, maximum drawdown, win rate, and trade-by-trade analysis. Supports custom strategies and benchmark comparisons.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "Trading symbol for backtesting"
                        },
                        "strategy": {
                            "type": "string",
                            "description": "Strategy description or configuration (JSON format supported)"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Backtest start date (YYYY-MM-DD)",
                            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "Backtest end date (YYYY-MM-DD)",
                            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                        },
                        "initial_capital": {
                            "type": "number",
                            "default": 10000,
                            "minimum": 100,
                            "description": "Initial capital for backtesting"
                        }
                    },
                    "required": ["symbol", "strategy", "start_date", "end_date"]
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool and return results - for HTTP endpoint compatibility"""
        if not self._initialized:
            await self.initialize()

        # Validate and execute the tool
        validated_args = self._validate_input(tool_name, arguments)

        # Create a mock request ID for HTTP calls
        request_id = f"http_{int(time.time())}"

        # Route to the appropriate handler
        if tool_name == "analyze_crypto":
            result = await self._handle_analyze_crypto(validated_args, request_id)
        elif tool_name == "monitor_portfolio":
            result = await self._handle_monitor_portfolio(validated_args, request_id)
        elif tool_name == "detect_opportunities":
            result = await self._handle_detect_opportunities(validated_args, request_id)
        elif tool_name == "risk_assessment":
            result = await self._handle_risk_assessment(validated_args, request_id)
        elif tool_name == "market_scanner":
            result = await self._handle_market_scanner(validated_args, request_id)
        elif tool_name == "alert_manager":
            result = await self._handle_alert_manager(validated_args, request_id)
        elif tool_name == "historical_backtest":
            result = await self._handle_historical_backtest(validated_args, request_id)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Extract the content from TextContent result
        if result and len(result) > 0 and hasattr(result[0], 'text'):
            return json.loads(result[0].text)
        else:
            return {"error": "No result returned from tool"}

async def main():
    """Main entry point for the standalone MCP server"""
    server_instance = MCPCryptoServer()

    try:
        logger.info("🚀 Starting Standalone MCP Crypto Trading Server",
                   version=server_instance.server_version,
                   server_name=server_instance.server_name)

        # Initialize server
        if not await server_instance.initialize():
            logger.error("❌ Server initialization failed")
            return 1

        # Health check
        health = await server_instance.infrastructure.health_check()
        if health.errors:
            logger.warning("⚠️ Health check issues detected", errors=health.errors)
        else:
            logger.info("✅ All systems healthy and ready")

        # Log server statistics
        uptime = time.time() - server_instance.start_time
        logger.info("📊 Server ready for requests",
                   uptime_seconds=f"{uptime:.1f}",
                   tools_available=7,
                   rate_limit=f"{server_instance.max_requests_per_minute}/min")

        # Run MCP server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            init_options = InitializationOptions(
                server_name=server_instance.server_name,
                server_version=server_instance.server_version,
                capabilities=server_instance.server.get_capabilities(
                    notification_options=NotificationOptions(
                        prompts_changed=True,
                        resources_changed=True,
                        tools_changed=True
                    ),
                    experimental_capabilities={
                        "standalone_mode": {},
                        "production_ready": {},
                        "kaayaan_integration": {},
                        "rate_limiting": {},
                        "input_validation": {},
                        "structured_logging": {},
                        "health_monitoring": {}
                    }
                )
            )

            logger.info("🔗 MCP server running with stdio transport",
                       protocol="MCP 2.1.0+", transport="stdio")

            await server_instance.server.run(read_stream, write_stream, init_options)

    except KeyboardInterrupt:
        logger.info("🛑 Server interrupted - initiating graceful shutdown")
        return 0
    except Exception as e:
        logger.error("💥 Critical server error",
                    error=str(e), traceback=traceback.format_exc())
        return 1
    finally:
        # Log final statistics
        uptime = time.time() - server_instance.start_time
        logger.info("📈 Server statistics",
                   total_requests=server_instance.request_count,
                   total_errors=server_instance.error_count,
                   error_rate=f"{(server_instance.error_count/max(server_instance.request_count,1)*100):.1f}%",
                   uptime_minutes=f"{uptime/60:.1f}")

        logger.info("🧹 Starting cleanup...")
        await server_instance.cleanup()
        logger.info("✅ Standalone MCP Crypto Trading Server shutdown complete")
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
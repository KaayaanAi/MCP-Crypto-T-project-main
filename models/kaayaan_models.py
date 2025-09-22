"""
Kaayaan Infrastructure Models
Enhanced data models for production MCP deployment
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timezone
from enum import Enum
import uuid

# Import existing models from legacy folder
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'legacy'))
from response_models import (
    MarketAnalysis, VolatilityIndicators, OrderBlock, FairValueGap,
    BreakOfStructure, ChangeOfCharacter, LiquidityZone, AnchoredVWAP,
    RSIDivergence, Recommendation, ComparativeAnalysis, CryptoAnalysisResponse
)

class AlertType(str, Enum):
    PRICE = "price"
    TECHNICAL = "technical"
    VOLUME = "volume"
    NEWS = "news"
    RISK = "risk"

class AlertStatus(str, Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    DISABLED = "disabled"

class MarketRegime(str, Enum):
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    RANGE_BOUND = "range_bound"
    TRANSITIONAL = "transitional"
    UNKNOWN = "unknown"

class RiskLevel(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class ScanType(str, Enum):
    BREAKOUTS = "breakouts"
    REVERSALS = "reversals"
    INSTITUTIONAL = "institutional"
    VOLUME_SURGE = "volume_surge"
    ALL = "all"

class EnhancedAnalysisResult(BaseModel):
    """Enhanced analysis with market context and intelligent scoring"""
    # Original analysis data
    symbol: str
    timestamp: str
    timeframe: str
    market_analysis: MarketAnalysis
    volatility_indicators: VolatilityIndicators
    order_blocks: List[OrderBlock]
    fair_value_gaps: List[FairValueGap]
    break_of_structure: List[BreakOfStructure]
    change_of_character: List[ChangeOfCharacter]
    liquidity_zones: List[LiquidityZone]
    anchored_vwap: List[AnchoredVWAP]
    rsi_divergence: List[RSIDivergence]
    recommendation: Recommendation
    comparative_analysis: Optional[ComparativeAnalysis] = None
    metadata: Dict[str, Any]
    
    # Enhanced features
    market_context: Dict[str, Any] = Field(default_factory=dict)
    intelligent_score: float = Field(ge=0, le=100, description="Intelligent confidence score 0-100")
    regime_analysis: MarketRegime = MarketRegime.UNKNOWN
    risk_adjusted_recommendation: Optional[str] = None
    position_sizing_suggestion: Optional[Dict[str, Any]] = None
    
    @validator('intelligent_score')
    def validate_score(cls, v: float) -> float:
        return max(0, min(100, v))

class PortfolioPosition(BaseModel):
    """Individual position in a portfolio"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_percent: float = 0.0
    position_value: float = 0.0
    weight_percent: float = 0.0
    risk_score: float = Field(ge=0, le=100)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PortfolioAnalysis(BaseModel):
    """Comprehensive portfolio analysis"""
    portfolio_id: str
    total_value: float
    total_pnl: float
    total_pnl_percent: float
    positions: List[PortfolioPosition]
    risk_metrics: Dict[str, Any]
    diversification_score: float = Field(ge=0, le=100)
    correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None
    recommendations: List[str] = Field(default_factory=list)
    alerts: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TradingOpportunity(BaseModel):
    """High-confidence trading opportunity"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    opportunity_type: str  # "breakout", "reversal", "institutional", etc.
    confidence_score: float = Field(ge=0, le=100)
    entry_price: float
    target_price: float
    stop_loss: float
    risk_reward_ratio: float
    timeframe: str
    rationale: str
    supporting_indicators: List[str]
    market_context: Dict[str, Any] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('risk_reward_ratio')
    def validate_risk_reward(cls, v: float) -> float:
        return max(0.1, v)  # Minimum 1:10 risk-reward

class RiskAssessment(BaseModel):
    """Comprehensive risk assessment for position sizing"""
    symbol: str
    portfolio_value: float
    risk_percentage: float
    entry_price: float
    stop_loss: float
    
    # Calculated fields
    risk_amount: float = 0.0
    position_size: float = 0.0
    position_value: float = 0.0
    max_loss: float = 0.0
    risk_reward_ratio: Optional[float] = None
    
    # Advanced risk metrics
    volatility_adjusted_size: float = 0.0
    kelly_criterion_size: float = 0.0
    correlation_risk: float = 0.0
    
    # Risk warnings
    warnings: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MODERATE
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MarketScanResult(BaseModel):
    """Market scan results"""
    scan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scan_type: ScanType
    timeframe: str
    symbols_scanned: int
    opportunities_found: int
    opportunities: List[TradingOpportunity]
    market_conditions: Dict[str, Any] = Field(default_factory=dict)
    scan_duration_seconds: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Alert(BaseModel):
    """Trading alert configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: AlertType
    symbol: str
    condition: str  # "price > 50000", "rsi < 30", etc.
    phone_number: str
    status: AlertStatus = AlertStatus.ACTIVE
    message_template: Optional[str] = None
    cooldown_minutes: int = 60  # Prevent spam
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    expires_at: Optional[datetime] = None

class BacktestResult(BaseModel):
    """Historical backtesting results"""
    backtest_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    strategy: str
    start_date: str
    end_date: str
    initial_capital: float
    
    # Performance metrics
    final_capital: float = 0.0
    total_return: float = 0.0
    total_return_percent: float = 0.0
    annualized_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    
    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_trade_return: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    
    # Detailed results
    trades: List[Dict[str, Any]] = Field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = Field(default_factory=list)
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DatabaseConfig(BaseModel):
    """Database configuration model"""
    mongodb_uri: str
    redis_url: str
    postgres_dsn: str

class WhatsAppConfig(BaseModel):
    """WhatsApp API configuration"""
    base_url: str
    session: str
    timeout_seconds: int = 30

class InfrastructureHealth(BaseModel):
    """Infrastructure health status"""
    mongodb_status: str = "unknown"
    redis_status: str = "unknown"
    postgres_status: str = "unknown"
    whatsapp_status: str = "unknown"
    last_check: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    errors: List[str] = Field(default_factory=list)

class MarketContext(BaseModel):
    """Overall market context for intelligent decision making"""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    market_sentiment: str  # bullish, bearish, neutral
    btc_trend: str
    eth_trend: str
    overall_volatility: str
    vix_equivalent: Optional[float] = None
    fear_greed_index: Optional[int] = None
    market_regime: MarketRegime = MarketRegime.UNKNOWN
    
    # Cache control
    ttl_seconds: int = 300  # 5 minutes default TTL

class TradingSignal(BaseModel):
    """Standardized trading signal"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    signal_type: str  # "buy", "sell", "hold"
    strength: float = Field(ge=0, le=100)
    timeframe: str
    entry_price: float
    target_prices: List[float] = Field(default_factory=list)
    stop_loss: float
    rationale: str
    indicators_used: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MODERATE
    
    # Metadata
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    confidence_score: float = Field(ge=0, le=100)

class AuditLog(BaseModel):
    """Audit logging for all trading decisions"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str
    symbol: Optional[str] = None
    user_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Export all models for easy imports
__all__ = [
    'AlertType', 'AlertStatus', 'MarketRegime', 'RiskLevel', 'ScanType',
    'EnhancedAnalysisResult', 'PortfolioPosition', 'PortfolioAnalysis',
    'TradingOpportunity', 'RiskAssessment', 'MarketScanResult', 'Alert',
    'BacktestResult', 'DatabaseConfig', 'WhatsAppConfig', 'InfrastructureHealth',
    'MarketContext', 'TradingSignal', 'AuditLog'
]
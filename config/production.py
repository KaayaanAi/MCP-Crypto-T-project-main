"""
Production Configuration for MCP Crypto Trading Module
Environment variables, security settings, and infrastructure configuration
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import timedelta

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    # MongoDB settings
    mongodb_uri: str = field(default_factory=lambda: os.getenv(
        "MONGODB_URI", 
        "mongodb://username:password@mongodb:27017/"
    ))
    mongodb_database: str = field(default_factory=lambda: os.getenv(
        "MONGODB_DATABASE", 
        "crypto_trading"
    ))
    mongodb_timeout_ms: int = field(default_factory=lambda: int(os.getenv(
        "MONGODB_TIMEOUT_MS", 
        "10000"
    )))
    
    # Redis settings
    redis_url: str = field(default_factory=lambda: os.getenv(
        "REDIS_URL", 
        "redis://:password@redis:6379"
    ))
    redis_timeout: int = field(default_factory=lambda: int(os.getenv(
        "REDIS_TIMEOUT", 
        "5"
    )))
    redis_retry_attempts: int = field(default_factory=lambda: int(os.getenv(
        "REDIS_RETRY_ATTEMPTS", 
        "3"
    )))
    
    # PostgreSQL settings
    postgres_dsn: str = field(default_factory=lambda: os.getenv(
        "POSTGRES_DSN", 
        "postgresql://user:password@postgresql:5432/database"
    ))
    postgres_pool_min: int = field(default_factory=lambda: int(os.getenv(
        "POSTGRES_POOL_MIN", 
        "1"
    )))
    postgres_pool_max: int = field(default_factory=lambda: int(os.getenv(
        "POSTGRES_POOL_MAX", 
        "10"
    )))

@dataclass
class WhatsAppConfig:
    """WhatsApp API configuration"""
    base_url: str = field(default_factory=lambda: os.getenv(
        "WHATSAPP_API", 
        "https://your-whatsapp-api.com"
    ))
    session: str = field(default_factory=lambda: os.getenv(
        "WHATSAPP_SESSION", 
        "your_session_id"
    ))
    timeout_seconds: int = field(default_factory=lambda: int(os.getenv(
        "WHATSAPP_TIMEOUT", 
        "30"
    )))
    max_retries: int = field(default_factory=lambda: int(os.getenv(
        "WHATSAPP_MAX_RETRIES", 
        "3"
    )))
    rate_limit_per_minute: int = field(default_factory=lambda: int(os.getenv(
        "WHATSAPP_RATE_LIMIT", 
        "20"
    )))

@dataclass
class ExchangeConfig:
    """Cryptocurrency exchange API configuration"""
    # Binance API
    binance_api_key: Optional[str] = field(default_factory=lambda: os.getenv("BINANCE_API_KEY"))
    binance_api_secret: Optional[str] = field(default_factory=lambda: os.getenv("BINANCE_API_SECRET"))
    binance_testnet: bool = field(default_factory=lambda: os.getenv("BINANCE_TESTNET", "false").lower() == "true")
    
    # CoinGecko API
    coingecko_api_key: Optional[str] = field(default_factory=lambda: os.getenv("COINGECKO_API_KEY"))
    
    # CoinMarketCap API
    coinmarketcap_api_key: Optional[str] = field(default_factory=lambda: os.getenv("COINMARKETCAP_API_KEY"))
    
    # Rate limiting
    api_request_timeout: int = field(default_factory=lambda: int(os.getenv("API_REQUEST_TIMEOUT", "10")))
    max_requests_per_minute: int = field(default_factory=lambda: int(os.getenv("MAX_REQUESTS_PER_MINUTE", "100")))

@dataclass
class SecurityConfig:
    """Security and encryption configuration"""
    # JWT settings
    jwt_secret_key: str = field(default_factory=lambda: os.getenv(
        "JWT_SECRET_KEY", 
        "your-super-secret-jwt-key-change-in-production"
    ))
    jwt_algorithm: str = field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    jwt_expiration_hours: int = field(default_factory=lambda: int(os.getenv("JWT_EXPIRATION_HOURS", "24")))
    
    # Encryption
    encryption_key: Optional[str] = field(default_factory=lambda: os.getenv("ENCRYPTION_KEY"))
    
    # API security
    api_key_length: int = 32
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_format: str = field(default_factory=lambda: os.getenv(
        "LOG_FORMAT", 
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    log_file: Optional[str] = field(default_factory=lambda: os.getenv("LOG_FILE"))
    
    # Metrics
    enable_metrics: bool = field(default_factory=lambda: os.getenv("ENABLE_METRICS", "true").lower() == "true")
    metrics_port: int = field(default_factory=lambda: int(os.getenv("METRICS_PORT", "8080")))
    
    # Error tracking
    sentry_dsn: Optional[str] = field(default_factory=lambda: os.getenv("SENTRY_DSN"))
    enable_sentry: bool = field(default_factory=lambda: bool(os.getenv("SENTRY_DSN")))
    
    # Health checks
    health_check_interval: int = field(default_factory=lambda: int(os.getenv("HEALTH_CHECK_INTERVAL", "300")))
    enable_deep_health_checks: bool = field(default_factory=lambda: os.getenv("ENABLE_DEEP_HEALTH_CHECKS", "true").lower() == "true")

@dataclass
class PerformanceConfig:
    """Performance and optimization configuration"""
    # Caching
    cache_ttl_seconds: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL_SECONDS", "300")))
    max_cache_size: int = field(default_factory=lambda: int(os.getenv("MAX_CACHE_SIZE", "1000")))
    
    # Async settings
    max_concurrent_requests: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_REQUESTS", "100")))
    request_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")))
    
    # Memory management
    max_memory_usage_mb: int = field(default_factory=lambda: int(os.getenv("MAX_MEMORY_USAGE_MB", "512")))
    gc_threshold: int = field(default_factory=lambda: int(os.getenv("GC_THRESHOLD", "700")))

@dataclass
class TradingConfig:
    """Trading and analysis configuration"""
    # Default risk parameters
    default_risk_percentage: float = field(default_factory=lambda: float(os.getenv("DEFAULT_RISK_PERCENTAGE", "2.0")))
    max_position_size_percentage: float = field(default_factory=lambda: float(os.getenv("MAX_POSITION_SIZE_PERCENTAGE", "10.0")))
    
    # Analysis parameters
    default_timeframe: str = field(default_factory=lambda: os.getenv("DEFAULT_TIMEFRAME", "1h"))
    max_analysis_history_days: int = field(default_factory=lambda: int(os.getenv("MAX_ANALYSIS_HISTORY_DAYS", "30")))
    
    # Portfolio settings
    max_positions_per_portfolio: int = field(default_factory=lambda: int(os.getenv("MAX_POSITIONS_PER_PORTFOLIO", "20")))
    rebalance_threshold_percentage: float = field(default_factory=lambda: float(os.getenv("REBALANCE_THRESHOLD_PERCENTAGE", "5.0")))
    
    # Alert settings
    max_alerts_per_user: int = field(default_factory=lambda: int(os.getenv("MAX_ALERTS_PER_USER", "50")))
    alert_cooldown_minutes: int = field(default_factory=lambda: int(os.getenv("ALERT_COOLDOWN_MINUTES", "15")))

class ProductionConfig:
    """Main production configuration class"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.version = os.getenv("APP_VERSION", "1.0.0")
        
        # Load all configurations
        self.database = DatabaseConfig()
        self.whatsapp = WhatsAppConfig()
        self.exchanges = ExchangeConfig()
        self.security = SecurityConfig()
        self.monitoring = MonitoringConfig()
        self.performance = PerformanceConfig()
        self.trading = TradingConfig()
        
        # Validate critical settings
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate critical configuration settings"""
        errors = []
        
        # Database validation
        if not self.database.mongodb_uri:
            errors.append("MONGODB_URI is required")
        
        if not self.database.redis_url:
            errors.append("REDIS_URL is required")
        
        if not self.database.postgres_dsn:
            errors.append("POSTGRES_DSN is required")
        
        # WhatsApp validation
        if not self.whatsapp.base_url:
            errors.append("WHATSAPP_API base URL is required")
        
        # Security validation
        if self.security.jwt_secret_key == "your-super-secret-jwt-key-change-in-production":
            errors.append("JWT_SECRET_KEY must be changed in production")
        
        # Exchange API validation (warnings, not errors)
        warnings = []
        if not self.exchanges.binance_api_key:
            warnings.append("BINANCE_API_KEY not set - limited functionality")
        
        if not self.exchanges.coingecko_api_key:
            warnings.append("COINGECKO_API_KEY not set - rate limiting may apply")
        
        # Log warnings
        if warnings:
            logger = logging.getLogger(__name__)
            for warning in warnings:
                logger.warning(warning)
        
        # Raise errors
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration as dictionary"""
        return {
            'mongodb_uri': self.database.mongodb_uri,
            'redis_url': self.database.redis_url,
            'postgres_dsn': self.database.postgres_dsn,
            'mongodb_timeout_ms': self.database.mongodb_timeout_ms,
            'redis_timeout': self.database.redis_timeout,
            'postgres_pool_min': self.database.postgres_pool_min,
            'postgres_pool_max': self.database.postgres_pool_max
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': self.monitoring.log_format
                },
                'json': {
                    'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': self.monitoring.log_level,
                    'formatter': 'json' if self.environment == 'production' else 'standard',
                    'stream': 'ext://sys.stdout'
                }
            },
            'loggers': {
                'mcp-crypto-server': {
                    'handlers': ['console'],
                    'level': self.monitoring.log_level,
                    'propagate': False
                },
                'root': {
                    'handlers': ['console'],
                    'level': 'WARNING'
                }
            }
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment in ["development", "dev"]
    
    def is_testing(self) -> bool:
        """Check if running in testing environment"""
        return self.environment in ["testing", "test"]

# Global configuration instance
config = ProductionConfig()

# Environment-specific configurations
def get_config_for_environment(env: str = None) -> ProductionConfig:
    """Get configuration for specific environment"""
    if env:
        os.environ["ENVIRONMENT"] = env
    
    return ProductionConfig()

# Configuration validation utility
def validate_environment_variables() -> Dict[str, Any]:
    """Validate all required environment variables"""
    required_vars = [
        "MONGODB_URI",
        "REDIS_URL", 
        "POSTGRES_DSN",
        "WHATSAPP_API",
        "WHATSAPP_SESSION"
    ]
    
    optional_vars = [
        "BINANCE_API_KEY",
        "COINGECKO_API_KEY",
        "COINMARKETCAP_API_KEY",
        "SENTRY_DSN",
        "JWT_SECRET_KEY"
    ]
    
    result = {
        "required": {},
        "optional": {},
        "missing_required": [],
        "missing_optional": []
    }
    
    # Check required variables
    for var in required_vars:
        value = os.getenv(var)
        if value:
            result["required"][var] = "✓ Set"
        else:
            result["missing_required"].append(var)
    
    # Check optional variables
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            result["optional"][var] = "✓ Set"
        else:
            result["missing_optional"].append(var)
    
    return result

# Export main config instance
__all__ = ["config", "ProductionConfig", "get_config_for_environment", "validate_environment_variables"]
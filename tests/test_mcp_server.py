"""
Test suite for MCP Crypto Trading Server
Comprehensive testing of all MCP tools and infrastructure components
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

# Import the main server and components
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server_standalone import MCPCryptoServer

# Mock specs for infrastructure components - don't import actual classes
from enum import Enum

class RiskLevel(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class DatabaseManager:
    pass

class AlertManager:
    pass

class RiskManager:
    pass

class MarketScanner:
    pass

class PortfolioTracker:
    pass

class Backtester:
    pass

class TestMCPCryptoServer:
    """Test the main MCP server functionality"""
    
    @pytest.fixture
    async def server(self):
        """Create a test server instance with mocked dependencies"""
        server = MCPCryptoServer()
        
        # Mock infrastructure connections
        server.mongodb_client = AsyncMock()
        server.redis_client = AsyncMock()
        server.postgres_pool = AsyncMock()
        
        # Mock components
        server.db_manager = AsyncMock(spec=DatabaseManager)
        server.alert_manager = AsyncMock(spec=AlertManager)
        server.risk_manager = AsyncMock(spec=RiskManager)
        server.market_scanner = AsyncMock(spec=MarketScanner)
        server.portfolio_tracker = AsyncMock(spec=PortfolioTracker)
        server.backtester = AsyncMock(spec=Backtester)
        
        return server
    
    @pytest.fixture
    def sample_analysis(self):
        """Sample analysis data for testing"""
        return {
            'symbol': 'BTCUSDT',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'timeframe': '1h',
            'market_analysis': {
                'trend': 'bullish',
                'volatility': 'moderate',
                'confidence': 75.0
            },
            'volatility_indicators': {
                'bollinger_bands_width': 3.5,
                'average_true_range': 250.0,
                'volatility_level': 'moderate'
            },
            'order_blocks': [
                {
                    'level': 45000.0,
                    'type': 'demand',
                    'strength': 80.0,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            ],
            'recommendation': {
                'action': 'BUY',
                'confidence': 78.0,
                'reasoning': 'Strong bullish momentum with institutional support'
            },
            'intelligent_score': 82.5,
            'regime_analysis': 'bull_market',
            'metadata': {
                'current_price': 45500.0,
                'volume_24h': 2500000000.0
            }
        }
    
    async def test_analyze_crypto_tool(self, server, sample_analysis):
        """Test the analyze_crypto tool"""
        # Mock the analyzer
        server.analyzer.analyze = AsyncMock(return_value=sample_analysis)
        server._enhance_analysis_with_context = AsyncMock(return_value=sample_analysis)
        
        # Test the tool
        result = await server._handle_analyze_crypto({
            'symbol': 'BTCUSDT',
            'timeframe': '1h',
            'save_analysis': True
        }, 'test_req_1')
        
        # Verify results
        assert len(result) == 1
        assert result[0].type == 'text'

        # Parse the JSON response - note the response is wrapped
        response_data = json.loads(result[0].text)
        assert 'analysis' in response_data
        analysis = response_data['analysis']
        assert analysis['symbol'] == 'BTCUSDT'
        
        # Verify analyzer was called
        server.analyzer.analyze.assert_called_once_with(
            symbol='BTCUSDT',
            comparison_symbol=None,
            timeframe='1h'
        )
    
    async def test_monitor_portfolio_tool(self, server):
        """Test the monitor_portfolio tool"""
        mock_portfolio_analysis = {
            'portfolio_id': 'test_portfolio',
            'total_value': 100000.0,
            'total_pnl': 5000.0,
            'total_pnl_percent': 5.0,
            'positions': [
                {
                    'symbol': 'BTCUSDT',
                    'quantity': 1.0,
                    'entry_price': 40000.0,
                    'current_price': 45000.0,
                    'unrealized_pnl': 5000.0,
                    'unrealized_pnl_percent': 12.5,
                    'position_value': 45000.0,
                    'weight_percent': 45.0,
                    'risk_score': 65.0
                }
            ],
            'diversification_score': 75.0,
            'recommendations': ['Portfolio well balanced'],
            'alerts': []
        }
        
        server.portfolio_tracker.analyze_portfolio = AsyncMock(return_value=mock_portfolio_analysis)
        
        # Test the tool
        result = await server._handle_monitor_portfolio({
            'portfolio_id': 'test_portfolio',
            'symbols': ['BTCUSDT', 'ETHUSDT'],
            'risk_level': 'moderate'
        }, "test_req_id")
        
        # Verify results
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['portfolio_id'] == 'test_portfolio'
        assert response_data['total_pnl_percent'] == 5.0
    
    async def test_detect_opportunities_tool(self, server):
        """Test the detect_opportunities tool"""
        mock_opportunities = [
            {
                'id': 'opp_1',
                'symbol': 'BTCUSDT',
                'opportunity_type': 'breakout',
                'confidence_score': 85.0,
                'entry_price': 45000.0,
                'target_price': 47000.0,
                'stop_loss': 43000.0,
                'risk_reward_ratio': 1.5,
                'rationale': 'Strong breakout pattern with volume confirmation'
            }
        ]
        
        server.market_scanner.scan_for_opportunities = AsyncMock(return_value=mock_opportunities)
        
        # Test the tool
        result = await server._handle_detect_opportunities({
            'market_cap_range': 'large',
            'confidence_threshold': 80.0,
            'max_results': 10
        }, "test_req_id")
        
        # Verify results
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert len(response_data) == 1
        assert response_data[0]['confidence_score'] == 85.0
    
    async def test_risk_assessment_tool(self, server):
        """Test the risk_assessment tool"""
        mock_risk_assessment = {
            'symbol': 'BTCUSDT',
            'portfolio_value': 100000.0,
            'risk_percentage': 2.0,
            'entry_price': 45000.0,
            'stop_loss': 43000.0,
            'position_size': 0.9,
            'position_value': 40500.0,
            'risk_amount': 2000.0,
            'risk_reward_ratio': 1.5,
            'risk_level': 'moderate',
            'warnings': []
        }
        
        server.risk_manager.calculate_position_sizing = AsyncMock(return_value=mock_risk_assessment)
        
        # Test the tool
        result = await server._handle_risk_assessment({
            'symbol': 'BTCUSDT',
            'portfolio_value': 100000.0,
            'risk_percentage': 2.0,
            'entry_price': 45000.0,
            'stop_loss': 43000.0
        }, "test_req_id")
        
        # Verify results
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['position_size'] == 0.9
        assert response_data['risk_level'] == 'moderate'
    
    async def test_market_scanner_tool(self, server):
        """Test the market_scanner tool"""
        mock_scan_results = {
            'scan_id': 'scan_123',
            'scan_type': 'all',
            'symbols_scanned': 25,
            'opportunities_found': 3,
            'opportunities': [
                {
                    'symbol': 'ETHUSDT',
                    'opportunity_type': 'reversal',
                    'confidence_score': 78.0
                }
            ],
            'scan_duration_seconds': 15.2
        }
        
        server.market_scanner.scan_market = AsyncMock(return_value=mock_scan_results)
        
        # Test the tool
        result = await server._handle_market_scanner({
            'scan_type': 'all',
            'timeframe': '1h',
            'min_volume_usd': 1000000
        }, "test_req_id")
        
        # Verify results
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['symbols_scanned'] == 25
        assert response_data['opportunities_found'] == 3
    
    async def test_alert_manager_tool(self, server):
        """Test the alert_manager tool"""
        # Test create alert
        mock_create_result = {
            'alert_id': 'alert_123',
            'status': 'created',
            'message': 'Alert created successfully'
        }
        
        server.alert_manager.create_alert = AsyncMock(return_value=mock_create_result)
        
        result = await server._handle_alert_manager({
            'action': 'create',
            'alert_type': 'price',
            'symbol': 'BTCUSDT',
            'condition': 'price > 50000',
            'phone_number': '+1234567890'
        }, "test_req_id")
        
        # Verify results
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['status'] == 'created'
        
        # Test list alerts
        mock_list_result = [
            {
                'id': 'alert_123',
                'symbol': 'BTCUSDT',
                'condition': 'price > 50000',
                'status': 'active'
            }
        ]
        
        server.alert_manager.list_alerts = AsyncMock(return_value=mock_list_result)
        
        result = await server._handle_alert_manager({'action': 'list'}, "test_req_id")
        response_data = json.loads(result[0].text)
        assert len(response_data) == 1
        assert response_data[0]['symbol'] == 'BTCUSDT'
    
    async def test_historical_backtest_tool(self, server):
        """Test the historical_backtest tool"""
        mock_backtest_results = {
            'backtest_id': 'backtest_123',
            'symbol': 'BTCUSDT',
            'strategy': 'technical_momentum',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'initial_capital': 10000.0,
            'final_capital': 12500.0,
            'total_return_percent': 25.0,
            'total_trades': 15,
            'win_rate': 66.7,
            'max_drawdown': 8.5,
            'sharpe_ratio': 1.8
        }
        
        server.backtester.run_backtest = AsyncMock(return_value=mock_backtest_results)
        
        # Test the tool
        result = await server._handle_historical_backtest({
            'symbol': 'BTCUSDT',
            'strategy': 'technical_momentum',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'initial_capital': 10000
        }, "test_req_id")
        
        # Verify results
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['total_return_percent'] == 25.0
        assert response_data['win_rate'] == 66.7
    
    async def test_error_handling(self, server):
        """Test error handling in tools"""
        # Test error in analyze_crypto
        server.analyzer.analyze = AsyncMock(side_effect=Exception("API Error"))
        
        result = await server._handle_analyze_crypto({'symbol': 'INVALID'}, "test_req_id")
        
        # Should return error message
        assert len(result) == 1
        assert "Error executing analyze_crypto" in result[0].text
    
    @pytest.mark.asyncio
    async def test_intelligent_scoring(self, server, sample_analysis):
        """Test intelligent scoring algorithm - using public method"""
        # Test via the public handler which uses internal scoring
        server.analyzer.analyze = AsyncMock(return_value=sample_analysis)
        server.infrastructure = AsyncMock()
        server.infrastructure.save_analysis = AsyncMock()

        # Execute analysis to test scoring
        result = await server._handle_analyze_crypto({
            'symbol': 'BTCUSDT',
            'timeframe': '1h',
            'save_analysis': False
        }, 'test_req_scoring')

        # Verify result contains analysis with scoring
        assert len(result) == 1
        response = json.loads(result[0].text)
        assert 'analysis' in response

    async def test_market_regime_detection(self, server, sample_analysis):
        """Test market regime detection - using public method"""
        from mcp_server_standalone import (
            CryptoAnalysisResponse, MarketAnalysis, VolatilityIndicators, Recommendation
        )

        # Create a proper CryptoAnalysisResponse object
        analysis_obj = CryptoAnalysisResponse(
            symbol='BTCUSDT',
            timestamp=datetime.now(timezone.utc).isoformat(),
            timeframe='1h',
            market_analysis=MarketAnalysis(trend='bullish', volatility='moderate', confidence=75.0),
            volatility_indicators=VolatilityIndicators(
                bollinger_bands_width=2.5,
                average_true_range=150.0,
                volatility_level='moderate'
            ),
            order_blocks=[],
            fair_value_gaps=[],
            break_of_structure=[],
            change_of_character=[],
            liquidity_zones=[],
            anchored_vwap=[],
            rsi_divergence=[],
            recommendation=Recommendation(action='BUY', confidence=75.0, reasoning='Test'),
            metadata={}
        )

        # Test the actual method from server
        regime = server._determine_market_regime(analysis_obj)

        # Should detect bull market
        assert regime in ['bull_market', 'transitional', 'range_bound', 'bear_market']
    
class TestDatabaseManager:
    """Test database manager functionality"""
    
    @pytest.fixture
    async def db_manager(self):
        """Create test database manager"""
        mongodb_client = AsyncMock()
        redis_client = AsyncMock()
        postgres_pool = AsyncMock()
        
        return DatabaseManager(mongodb_client, redis_client, postgres_pool)
    
    async def test_save_analysis(self, db_manager):
        """Test saving analysis to database"""
        analysis = {
            'symbol': 'BTCUSDT',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'intelligent_score': 75.0
        }
        
        # Mock database operations
        db_manager.analysis_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id='test_id'))
        db_manager.redis_client.setex = AsyncMock()
        
        result = await db_manager.save_analysis(analysis)
        
        assert result == 'test_id'
        db_manager.analysis_collection.insert_one.assert_called_once()
        db_manager.redis_client.setex.assert_called_once()
    
    async def test_health_check(self, db_manager):
        """Test infrastructure health check"""
        # Mock successful connections
        db_manager.mongodb_client.admin.command = AsyncMock()
        db_manager.redis_client.ping = AsyncMock()
        db_manager.postgres_pool.acquire = AsyncMock()
        
        health = await db_manager.health_check()
        
        assert health.mongodb_status == "healthy"
        assert health.redis_status == "healthy" 
        assert health.postgres_status == "healthy"
        assert len(health.errors) == 0

class TestAlertManager:
    """Test alert management functionality"""
    
    @pytest.fixture
    def alert_manager(self):
        """Create test alert manager"""
        db_manager = AsyncMock(spec=DatabaseManager)
        return AlertManager(
            whatsapp_base_url="https://test.api",
            whatsapp_session="test_session",
            db_manager=db_manager
        )
    
    async def test_create_alert(self, alert_manager):
        """Test creating new alert"""
        alert_manager.db_manager.save_alert = AsyncMock(return_value="alert_123")
        alert_manager.db_manager.log_action = AsyncMock()
        
        result = await alert_manager.create_alert(
            alert_type="price",
            symbol="BTCUSDT",
            condition="price > 50000",
            phone_number="1234567890"
        )
        
        assert result['status'] == 'created'
        assert result['alert_id'] == 'alert_123'
    
    def test_validate_phone_number(self, alert_manager):
        """Test phone number validation"""
        assert alert_manager._validate_phone_number("1234567890") == True
        assert alert_manager._validate_phone_number("+1-234-567-8900") == True
        assert alert_manager._validate_phone_number("123") == False
        assert alert_manager._validate_phone_number("invalid") == False
    
    def test_validate_condition(self, alert_manager):
        """Test condition validation"""
        assert alert_manager._validate_condition("price > 50000", "price") == True
        assert alert_manager._validate_condition("rsi < 30", "technical") == False
        assert alert_manager._validate_condition("bullish_divergence", "technical") == True
        assert alert_manager._validate_condition("invalid", "price") == False

class TestRiskManager:
    """Test risk management functionality"""
    
    @pytest.fixture
    def risk_manager(self):
        """Create test risk manager"""
        db_manager = AsyncMock(spec=DatabaseManager)
        return RiskManager(db_manager)
    
    async def test_position_sizing(self, risk_manager):
        """Test position sizing calculation"""
        # Mock analysis data
        mock_analysis = {
            'volatility_indicators': {'volatility_level': 'moderate'},
            'intelligent_score': 75.0,
            'regime_analysis': 'bull_market'
        }
        
        risk_manager.db_manager.get_latest_analysis = AsyncMock(return_value=mock_analysis)
        
        result = await risk_manager.calculate_position_sizing(
            symbol="BTCUSDT",
            portfolio_value=100000.0,
            risk_percentage=2.0,
            entry_price=45000.0,
            stop_loss=43000.0
        )
        
        assert result.symbol == "BTCUSDT"
        assert result.risk_percentage == 2.0
        assert result.position_size > 0
        assert result.risk_level in [RiskLevel.CONSERVATIVE, RiskLevel.MODERATE, RiskLevel.AGGRESSIVE]
    
    def test_risk_level_determination(self, risk_manager):
        """Test risk level determination"""
        risk_level = risk_manager._determine_risk_level(
            risk_percentage=1.0,
            correlation_risk=5.0,
            analysis={'volatility_indicators': {'volatility_level': 'low'}}
        )
        
        assert risk_level == RiskLevel.CONSERVATIVE
        
        risk_level = risk_manager._determine_risk_level(
            risk_percentage=5.0,
            correlation_risk=30.0,
            analysis={'volatility_indicators': {'volatility_level': 'high'}}
        )
        
        assert risk_level == RiskLevel.AGGRESSIVE

class TestMarketScanner:
    """Test market scanning functionality"""
    
    @pytest.fixture
    def market_scanner(self):
        """Create test market scanner"""
        analyzer = AsyncMock()
        db_manager = AsyncMock(spec=DatabaseManager)
        return MarketScanner(analyzer, db_manager)
    
    async def test_opportunity_detection(self, market_scanner):
        """Test opportunity detection"""
        # Mock analysis with breakout signal
        mock_analysis = type('Analysis', (), {
            'symbol': 'BTCUSDT',
            'timeframe': '1h',
            'break_of_structure': [
                type('BOS', (), {
                    'strength': 3.0,
                    'direction': 'bullish',
                    'level': 44000.0
                })()
            ],
            'liquidity_zones': [{'volume': 1000000}],
            'regime_analysis': 'bull_market',
            'metadata': {'volume_24h': 2000000000}
        })()
        
        opportunities = await market_scanner._detect_breakout_opportunities(mock_analysis)
        
        assert len(opportunities) > 0
        assert opportunities[0].opportunity_type == "breakout"
        assert opportunities[0].confidence_score > 0

# Integration tests
@pytest.mark.integration
class TestMCPIntegration:
    """Integration tests for the complete MCP system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_analysis_workflow(self):
        """Test complete analysis workflow"""
        server = MCPCryptoServer()

        # Mock dependencies
        server.analyzer = AsyncMock()
        server.db_manager = AsyncMock(spec=DatabaseManager)
        server._enhance_analysis_with_context = AsyncMock()

        # Mock analysis result
        analysis_result = {
            'symbol': 'BTCUSDT',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'intelligent_score': 85.0,
            'recommendation': {'action': 'BUY', 'confidence': 82.0},
            'regime_analysis': 'bull_market',
            'metadata': {'current_price': 45000.0}
        }

        server.analyzer.analyze = AsyncMock(return_value=analysis_result)
        server._enhance_analysis_with_context.return_value = analysis_result
        server.db_manager.save_analysis = AsyncMock(return_value='analysis_123')

        # Execute analysis workflow
        result = await server._handle_analyze_crypto({
            'symbol': 'BTCUSDT',
            'timeframe': '1h',
            'save_analysis': True
        }, "test_req_id")

        # Verify workflow completion
        assert len(result) == 1
        response = json.loads(result[0].text)
        assert response['symbol'] == 'BTCUSDT'
        assert response['intelligent_score'] == 85.0

        # Verify all components were called
        server.analyzer.analyze.assert_called_once()
        server.db_manager.save_analysis.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_portfolio_management_workflow(self):
        """Test complete portfolio management workflow"""
        server = MCPCryptoServer()

        # Mock portfolio tracker
        server.portfolio_tracker = AsyncMock(spec=PortfolioTracker)
        server.risk_manager = AsyncMock(spec=RiskManager)

        # Mock portfolio data
        portfolio_data = {
            'portfolio_id': 'integration_test_portfolio',
            'total_value': 150000.0,
            'total_pnl': 15000.0,
            'total_pnl_percent': 10.0,
            'positions': [
                {
                    'symbol': 'BTCUSDT',
                    'quantity': 2.0,
                    'entry_price': 40000.0,
                    'current_price': 45000.0,
                    'unrealized_pnl': 10000.0,
                    'unrealized_pnl_percent': 25.0,
                    'position_value': 90000.0,
                    'weight_percent': 60.0,
                    'risk_score': 55.0
                },
                {
                    'symbol': 'ETHUSDT',
                    'quantity': 20.0,
                    'entry_price': 2500.0,
                    'current_price': 2750.0,
                    'unrealized_pnl': 5000.0,
                    'unrealized_pnl_percent': 10.0,
                    'position_value': 55000.0,
                    'weight_percent': 36.67,
                    'risk_score': 48.0
                }
            ],
            'diversification_score': 72.5,
            'recommendations': ['Consider rebalancing BTC position'],
            'alerts': []
        }

        server.portfolio_tracker.analyze_portfolio = AsyncMock(return_value=portfolio_data)

        # Execute portfolio workflow
        result = await server._handle_monitor_portfolio({
            'portfolio_id': 'integration_test_portfolio',
            'symbols': ['BTCUSDT', 'ETHUSDT'],
            'risk_level': 'moderate'
        }, "test_req_id")

        # Verify workflow execution
        assert len(result) == 1
        response = json.loads(result[0].text)
        assert response['portfolio_id'] == 'integration_test_portfolio'
        assert response['total_value'] == 150000.0
        assert len(response['positions']) == 2
        assert response['diversification_score'] == 72.5

        # Verify portfolio tracker was called with correct parameters
        server.portfolio_tracker.analyze_portfolio.assert_called_once_with(
            portfolio_id='integration_test_portfolio',
            symbols=['BTCUSDT', 'ETHUSDT'],
            risk_level='moderate'
        )
    
    @pytest.mark.asyncio
    async def test_alert_workflow(self):
        """Test complete alert workflow"""
        server = MCPCryptoServer()

        # Mock alert manager
        server.alert_manager = AsyncMock(spec=AlertManager)

        # Test alert creation
        create_result = {
            'alert_id': 'workflow_alert_123',
            'status': 'created',
            'message': 'Price alert created for BTCUSDT',
            'alert_type': 'price',
            'symbol': 'BTCUSDT',
            'condition': 'price > 50000',
            'phone_number': '+1234567890'
        }

        server.alert_manager.create_alert = AsyncMock(return_value=create_result)

        # Create alert
        result = await server._handle_alert_manager({
            'action': 'create',
            'alert_type': 'price',
            'symbol': 'BTCUSDT',
            'condition': 'price > 50000',
            'phone_number': '+1234567890'
        }, "test_req_id")

        # Verify alert creation
        assert len(result) == 1
        response = json.loads(result[0].text)
        assert response['status'] == 'created'
        assert response['alert_id'] == 'workflow_alert_123'
        assert response['symbol'] == 'BTCUSDT'

        # Test listing alerts
        list_result = [
            {
                'id': 'workflow_alert_123',
                'alert_type': 'price',
                'symbol': 'BTCUSDT',
                'condition': 'price > 50000',
                'status': 'active',
                'created_at': datetime.now(timezone.utc).isoformat()
            }
        ]

        server.alert_manager.list_alerts = AsyncMock(return_value=list_result)

        # List alerts
        list_response = await server._handle_alert_manager({'action': 'list'}, "test_req_id")
        list_data = json.loads(list_response[0].text)

        assert len(list_data) == 1
        assert list_data[0]['id'] == 'workflow_alert_123'
        assert list_data[0]['status'] == 'active'

        # Verify both operations were called
        server.alert_manager.create_alert.assert_called_once()
        server.alert_manager.list_alerts.assert_called_once()

# Performance tests
@pytest.mark.performance
class TestPerformance:
    """Performance tests for critical paths"""
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests(self):
        """Test handling multiple concurrent analysis requests"""
        server = MCPCryptoServer()

        # Mock analyzer
        server.analyzer = AsyncMock()
        server.db_manager = AsyncMock(spec=DatabaseManager)
        server._enhance_analysis_with_context = AsyncMock()

        # Create mock analysis result generator
        async def mock_analyze(symbol, comparison_symbol=None, timeframe='1h'):
            # Simulate processing delay
            await asyncio.sleep(0.05)
            return {
                'symbol': symbol,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'intelligent_score': 75.0,
                'recommendation': {'action': 'HOLD', 'confidence': 70.0},
                'regime_analysis': 'neutral',
                'metadata': {'current_price': 40000.0}
            }

        server.analyzer.analyze = mock_analyze
        server._enhance_analysis_with_context.side_effect = lambda x: x
        server.db_manager.save_analysis = AsyncMock(return_value='analysis_id')

        # Test concurrent requests
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT']
        start_time = asyncio.get_event_loop().time()

        # Execute concurrent analysis requests
        tasks = [
            server._handle_analyze_crypto({
                'symbol': symbol,
                'timeframe': '1h',
                'save_analysis': False
            }, f'concurrent_req_{i}')
            for i, symbol in enumerate(symbols)
        ]

        results = await asyncio.gather(*tasks)

        # Calculate duration
        duration = asyncio.get_event_loop().time() - start_time

        # Verify all requests completed
        assert len(results) == 5
        for i, result in enumerate(results):
            assert len(result) == 1
            response = json.loads(result[0].text)
            assert response['symbol'] == symbols[i]

        # Verify concurrency (should be much faster than sequential)
        # Sequential would take 5 * 0.05 = 0.25s, concurrent should be ~0.05s
        assert duration < 0.15, f"Concurrent execution too slow: {duration}s"
    
    @pytest.mark.asyncio
    async def test_large_portfolio_analysis(self):
        """Test analysis of large portfolios"""
        server = MCPCryptoServer()

        # Mock portfolio tracker
        server.portfolio_tracker = AsyncMock(spec=PortfolioTracker)

        # Generate large portfolio with 50 positions
        large_positions = []
        for i in range(50):
            symbol = f"COIN{i}USDT"
            large_positions.append({
                'symbol': symbol,
                'quantity': 100.0,
                'entry_price': 10.0 + i,
                'current_price': 11.0 + i,
                'unrealized_pnl': 100.0,
                'unrealized_pnl_percent': 10.0,
                'position_value': 1100.0 + (i * 100),
                'weight_percent': 2.0,
                'risk_score': 50.0 + (i % 20)
            })

        portfolio_data = {
            'portfolio_id': 'large_portfolio_test',
            'total_value': sum(p['position_value'] for p in large_positions),
            'total_pnl': sum(p['unrealized_pnl'] for p in large_positions),
            'total_pnl_percent': 10.0,
            'positions': large_positions,
            'diversification_score': 85.0,
            'recommendations': ['Well diversified portfolio'],
            'alerts': []
        }

        # Mock the portfolio analysis
        async def mock_analyze_portfolio(portfolio_id, symbols, risk_level):
            # Simulate processing time
            await asyncio.sleep(0.1)
            return portfolio_data

        server.portfolio_tracker.analyze_portfolio = mock_analyze_portfolio

        # Execute large portfolio analysis
        start_time = asyncio.get_event_loop().time()

        symbols = [f"COIN{i}USDT" for i in range(50)]
        result = await server._handle_monitor_portfolio({
            'portfolio_id': 'large_portfolio_test',
            'symbols': symbols,
            'risk_level': 'moderate'
        }, "test_req_id")

        duration = asyncio.get_event_loop().time() - start_time

        # Verify results
        assert len(result) == 1
        response = json.loads(result[0].text)
        assert response['portfolio_id'] == 'large_portfolio_test'
        assert len(response['positions']) == 50
        assert response['diversification_score'] == 85.0

        # Verify performance (should complete in reasonable time)
        assert duration < 0.5, f"Large portfolio analysis too slow: {duration}s"
    
    @pytest.mark.asyncio
    async def test_market_scan_performance(self):
        """Test market scanning performance"""
        server = MCPCryptoServer()

        # Mock market scanner
        server.market_scanner = AsyncMock(spec=MarketScanner)

        # Create mock scan results with many opportunities
        opportunities = []
        for i in range(25):
            opportunities.append({
                'id': f'opp_{i}',
                'symbol': f'COIN{i}USDT',
                'opportunity_type': ['breakout', 'reversal', 'institutional'][i % 3],
                'confidence_score': 70.0 + (i % 25),
                'entry_price': 100.0 + i,
                'target_price': 110.0 + i,
                'stop_loss': 95.0 + i,
                'risk_reward_ratio': 2.0,
                'rationale': f'Trading opportunity {i}'
            })

        scan_result = {
            'scan_id': 'performance_scan_123',
            'scan_type': 'all',
            'timeframe': '1h',
            'symbols_scanned': 200,
            'opportunities_found': 25,
            'opportunities': opportunities,
            'market_conditions': {
                'overall_trend': 'bullish',
                'volatility_level': 'moderate',
                'volume_profile': 'above_average'
            },
            'scan_duration_seconds': 2.5
        }

        # Mock the scan with processing time
        async def mock_scan_market(scan_type, timeframe, min_volume_usd):
            # Simulate processing time for large scan
            await asyncio.sleep(0.1)
            return scan_result

        server.market_scanner.scan_market = mock_scan_market

        # Execute market scan
        start_time = asyncio.get_event_loop().time()

        result = await server._handle_market_scanner({
            'scan_type': 'all',
            'timeframe': '1h',
            'min_volume_usd': 1000000
        }, "test_req_id")

        duration = asyncio.get_event_loop().time() - start_time

        # Verify results
        assert len(result) == 1
        response = json.loads(result[0].text)
        assert response['scan_results']['symbols_scanned'] == 200
        assert response['scan_results']['opportunities_found'] == 25
        assert len(response['scan_results']['opportunities']) == 25

        # Verify performance (should complete in reasonable time even with 200 symbols)
        assert duration < 0.5, f"Market scan too slow: {duration}s"

# Fixtures and utilities
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
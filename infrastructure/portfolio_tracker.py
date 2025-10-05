"""
Portfolio Tracker for Multi-Asset Risk Management
Comprehensive portfolio monitoring with correlation analysis and risk assessment
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Any
import numpy as np
import pandas as pd
from dataclasses import asdict

from models.kaayaan_models import *
from infrastructure.database_manager import DatabaseManager
from src.core.crypto_analyzer import CryptoAnalyzer

logger = logging.getLogger(__name__)

class PortfolioTracker:
    """
    Intelligent portfolio tracking and management system
    Features:
    - Real-time position monitoring
    - Correlation analysis between holdings
    - Risk-adjusted performance metrics
    - Automated rebalancing suggestions
    - Portfolio optimization recommendations
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.analyzer = CryptoAnalyzer()  # Create analyzer instance
        # Note: risk_manager will be injected later via method parameter or created as needed
        
        # Portfolio parameters
        self.max_position_weight = 25.0    # Max % per position
        self.target_diversification = 80.0  # Target diversification score
        self.rebalance_threshold = 5.0     # % drift before rebalance
        self.correlation_warning_threshold = 0.75
        
        # Performance tracking
        self.benchmark_symbol = "BTCUSDT"  # Default benchmark
        
    async def analyze_portfolio(self, portfolio_id: str, symbols: list[str],
                              risk_level: str = "moderate") -> dict[str, Any]:
        """
        Comprehensive portfolio analysis and monitoring
        """
        try:
            logger.info(f"Starting portfolio analysis for {portfolio_id}")
            
            # Get current portfolio state or create new
            existing_portfolio = await self.db_manager.get_latest_portfolio(portfolio_id)
            
            if existing_portfolio:
                # Update existing portfolio
                portfolio_analysis = await self._update_existing_portfolio(
                    existing_portfolio, symbols, risk_level
                )
            else:
                # Create new portfolio analysis
                portfolio_analysis = await self._create_new_portfolio_analysis(
                    portfolio_id, symbols, risk_level
                )
            
            # Enhanced analysis
            enhanced_analysis = await self._enhance_portfolio_analysis(portfolio_analysis)
            
            logger.info(f"Portfolio analysis completed for {portfolio_id}")
            
            return enhanced_analysis
            
        except Exception as e:
            logger.error(f"Portfolio analysis failed for {portfolio_id}: {e}")
            raise
    
    async def _create_new_portfolio_analysis(self, portfolio_id: str, 
                                           symbols: list[str], 
                                           risk_level: str) -> dict[str, Any]:
        """Create analysis for a new portfolio"""
        try:
            # Initialize equal weights for new portfolio
            num_symbols = len(symbols)
            equal_weight = 100.0 / num_symbols if num_symbols > 0 else 0
            
            positions = []
            total_value = 100000  # Default $100k portfolio for analysis
            
            # Analyze each symbol
            for symbol in symbols:
                try:
                    # Get current analysis
                    analysis = await self.analyzer.analyze(symbol)
                    current_price = self._extract_current_price(analysis)
                    
                    if current_price <= 0:
                        logger.warning(f"Invalid price for {symbol}, skipping")
                        continue
                    
                    # Calculate position metrics
                    position_value = total_value * (equal_weight / 100)
                    quantity = position_value / current_price
                    
                    # Calculate risk score based on analysis
                    risk_score = self._calculate_position_risk_score(analysis, risk_level)
                    
                    position = PortfolioPosition(
                        symbol=symbol,
                        quantity=quantity,
                        entry_price=current_price,
                        current_price=current_price,
                        unrealized_pnl=0.0,
                        unrealized_pnl_percent=0.0,
                        position_value=position_value,
                        weight_percent=equal_weight,
                        risk_score=risk_score
                    )
                    
                    positions.append(position)
                    
                except Exception as e:
                    logger.error(f"Failed to analyze {symbol}: {e}")
                    continue
            
            # Calculate portfolio metrics
            portfolio_analysis = await self._calculate_portfolio_metrics(
                portfolio_id, positions, total_value, risk_level
            )
            
            return portfolio_analysis
            
        except Exception as e:
            logger.error(f"Failed to create new portfolio analysis: {e}")
            raise
    
    async def _update_existing_portfolio(self, existing_portfolio: dict[str, Any],
                                       symbols: list[str], risk_level: str) -> dict[str, Any]:
        """Update analysis for existing portfolio"""
        try:
            portfolio_id = existing_portfolio.get('portfolio_id', '')
            existing_positions = existing_portfolio.get('positions', [])
            
            # Create position lookup
            existing_lookup = {pos['symbol']: pos for pos in existing_positions}
            
            updated_positions = []
            total_value = 0
            
            # Update existing positions and add new ones
            for symbol in symbols:
                try:
                    # Get current analysis
                    analysis = await self.analyzer.analyze(symbol)
                    current_price = self._extract_current_price(analysis)
                    
                    if current_price <= 0:
                        continue
                    
                    if symbol in existing_lookup:
                        # Update existing position
                        existing_pos = existing_lookup[symbol]
                        
                        quantity = existing_pos['quantity']
                        entry_price = existing_pos['entry_price']
                        position_value = quantity * current_price
                        
                        # Calculate PnL
                        unrealized_pnl = (current_price - entry_price) * quantity
                        unrealized_pnl_percent = ((current_price - entry_price) / entry_price) * 100
                        
                        # Update risk score
                        risk_score = self._calculate_position_risk_score(analysis, risk_level)
                        
                        position = PortfolioPosition(
                            symbol=symbol,
                            quantity=quantity,
                            entry_price=entry_price,
                            current_price=current_price,
                            unrealized_pnl=unrealized_pnl,
                            unrealized_pnl_percent=unrealized_pnl_percent,
                            position_value=position_value,
                            weight_percent=0,  # Will be calculated later
                            risk_score=risk_score
                        )
                        
                    else:
                        # New position - use small initial allocation
                        total_existing_value = sum(pos['position_value'] for pos in existing_positions)
                        new_position_value = total_existing_value * 0.05  # 5% allocation
                        
                        quantity = new_position_value / current_price
                        
                        position = PortfolioPosition(
                            symbol=symbol,
                            quantity=quantity,
                            entry_price=current_price,
                            current_price=current_price,
                            unrealized_pnl=0.0,
                            unrealized_pnl_percent=0.0,
                            position_value=new_position_value,
                            weight_percent=0,  # Will be calculated later
                            risk_score=self._calculate_position_risk_score(analysis, risk_level)
                        )
                    
                    updated_positions.append(position)
                    total_value += position.position_value
                    
                except Exception as e:
                    logger.error(f"Failed to update position for {symbol}: {e}")
                    continue
            
            # Update position weights
            for position in updated_positions:
                position.weight_percent = (position.position_value / total_value) * 100 if total_value > 0 else 0
            
            # Calculate updated portfolio metrics
            portfolio_analysis = await self._calculate_portfolio_metrics(
                portfolio_id, updated_positions, total_value, risk_level
            )
            
            return portfolio_analysis
            
        except Exception as e:
            logger.error(f"Failed to update existing portfolio: {e}")
            raise
    
    async def _calculate_portfolio_metrics(self, portfolio_id: str, 
                                         positions: list[PortfolioPosition],
                                         total_value: float, 
                                         risk_level: str) -> dict[str, Any]:
        """Calculate comprehensive portfolio metrics"""
        try:
            # Basic portfolio metrics
            total_pnl = sum(pos.unrealized_pnl for pos in positions)
            total_pnl_percent = (total_pnl / total_value) * 100 if total_value > 0 else 0
            
            # Calculate correlation matrix
            correlation_matrix = await self._calculate_correlation_matrix(positions)
            
            # Calculate diversification score
            diversification_score = await self._calculate_diversification_score(positions)
            
            # Calculate risk metrics
            risk_metrics = await self._calculate_risk_metrics(positions, risk_level)
            
            # Generate recommendations
            recommendations = await self._generate_portfolio_recommendations(
                positions, diversification_score, risk_metrics, correlation_matrix
            )
            
            # Generate alerts
            alerts = self._generate_portfolio_alerts(positions, risk_metrics, total_pnl_percent)
            
            # Create portfolio analysis
            portfolio_analysis = PortfolioAnalysis(
                portfolio_id=portfolio_id,
                total_value=total_value,
                total_pnl=total_pnl,
                total_pnl_percent=total_pnl_percent,
                positions=positions,
                risk_metrics=risk_metrics,
                diversification_score=diversification_score,
                correlation_matrix=correlation_matrix,
                recommendations=recommendations,
                alerts=alerts
            )
            
            return portfolio_analysis.dict()
            
        except Exception as e:
            logger.error(f"Failed to calculate portfolio metrics: {e}")
            raise
    
    async def _calculate_correlation_matrix(self, positions: list[PortfolioPosition]) -> dict[str, dict[str, float | None]]:
        """Calculate correlation matrix between positions"""
        try:
            if len(positions) < 2:
                return None
            
            symbols = [pos.symbol for pos in positions]
            correlation_matrix = {}
            
            # Initialize matrix
            for symbol in symbols:
                correlation_matrix[symbol] = {}
            
            # Calculate pairwise correlations
            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols):
                    if i == j:
                        correlation_matrix[symbol1][symbol2] = 1.0
                    elif symbol2 not in correlation_matrix[symbol1]:
                        # Get correlation (simplified implementation)
                        correlation = await self._get_symbol_correlation(symbol1, symbol2)
                        correlation_matrix[symbol1][symbol2] = correlation
                        correlation_matrix[symbol2][symbol1] = correlation
            
            return correlation_matrix
            
        except Exception as e:
            logger.error(f"Correlation matrix calculation failed: {e}")
            return None
    
    async def _get_symbol_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation between two symbols (simplified)"""
        try:
            # This is a simplified implementation
            # In production, calculate from actual price history
            
            crypto_categories = {
                'major': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
                'defi': ['UNIUSDT', 'AAVEUSDT', 'COMPUSDT', 'SUSHIUSDT'],
                'layer1': ['ADAUSDT', 'SOLUSDT', 'DOTUSDT', 'AVAXUSDT'],
                'layer2': ['MATICUSDT', 'ARBUSDT', 'OPUSDT'],
                'meme': ['DOGEUSDT', 'SHIBUSDT', 'PEPEUSDT']
            }
            
            def get_category(symbol):
                for category, symbols in crypto_categories.items():
                    if symbol in symbols:
                        return category
                return 'other'
            
            cat1, cat2 = get_category(symbol1), get_category(symbol2)
            
            # Correlation based on categories
            if cat1 == cat2:
                return 0.75  # High correlation within category
            elif 'major' in [cat1, cat2]:
                return 0.6   # Moderate correlation with majors
            else:
                return 0.4   # Lower correlation between different categories
                
        except Exception:
            return 0.5  # Default correlation
    
    async def _calculate_diversification_score(self, positions: list[PortfolioPosition]) -> float:
        """Calculate portfolio diversification score"""
        try:
            if len(positions) <= 1:
                return 0.0
            
            # Calculate using Herfindahl Index
            weights = [pos.weight_percent / 100 for pos in positions]
            herfindahl_index = sum(w**2 for w in weights)
            
            # Convert to diversification score (0-100)
            num_positions = len(positions)
            max_herfindahl = 1.0  # All in one position
            min_herfindahl = 1.0 / num_positions  # Equal weights
            
            if max_herfindahl == min_herfindahl:
                return 100.0
            
            # Normalized diversification score
            diversification = (1 - (herfindahl_index - min_herfindahl) / (max_herfindahl - min_herfindahl)) * 100
            
            return max(0, min(100, diversification))
            
        except Exception:
            return 50.0  # Default moderate diversification
    
    async def _calculate_risk_metrics(self, positions: list[PortfolioPosition], 
                                    risk_level: str) -> dict[str, Any]:
        """Calculate portfolio risk metrics"""
        try:
            total_value = sum(pos.position_value for pos in positions)
            
            # Weighted average risk score
            weighted_risk = sum(
                pos.risk_score * (pos.position_value / total_value)
                for pos in positions
            ) if total_value > 0 else 0
            
            # Value at Risk calculation (simplified)
            position_risks = [pos.risk_score / 100 * pos.position_value for pos in positions]
            portfolio_var_95 = sum(position_risks) * 1.65  # 95% confidence
            var_percent = (portfolio_var_95 / total_value) * 100 if total_value > 0 else 0
            
            # Maximum drawdown estimation
            max_individual_risk = max(pos.risk_score for pos in positions) if positions else 0
            estimated_max_drawdown = max_individual_risk * 0.7  # Conservative estimate
            
            # Risk concentration
            risk_contributions = [
                pos.risk_score * (pos.position_value / total_value)
                for pos in positions
            ] if total_value > 0 else []
            
            max_risk_contribution = max(risk_contributions) if risk_contributions else 0
            
            risk_metrics = {
                'weighted_risk_score': weighted_risk,
                'value_at_risk_95': portfolio_var_95,
                'var_percent': var_percent,
                'estimated_max_drawdown': estimated_max_drawdown,
                'max_risk_contribution': max_risk_contribution,
                'total_positions': len(positions),
                'risk_level': risk_level
            }
            
            return risk_metrics
            
        except Exception as e:
            logger.error(f"Risk metrics calculation failed: {e}")
            return {'error': str(e)}
    
    async def _generate_portfolio_recommendations(self, positions: list[PortfolioPosition],
                                                diversification_score: float,
                                                risk_metrics: dict[str, Any],
                                                correlation_matrix: dict[str, dict[str, float | None]]) -> list[str]:
        """Generate portfolio optimization recommendations"""
        recommendations = []
        
        try:
            total_value = sum(pos.position_value for pos in positions)
            
            # Position size recommendations
            for pos in positions:
                if pos.weight_percent > self.max_position_weight:
                    recommendations.append(
                        f"Reduce {pos.symbol} position: Currently {pos.weight_percent:.1f}% "
                        f"(max recommended: {self.max_position_weight}%)"
                    )
                elif pos.weight_percent < 2 and total_value > 10000:  # Min 2% for meaningful positions
                    recommendations.append(f"Consider increasing {pos.symbol} position size")
            
            # Diversification recommendations
            if diversification_score < 50:
                recommendations.append(
                    f"Low diversification ({diversification_score:.1f}/100): "
                    "Consider adding more uncorrelated assets"
                )
            elif diversification_score < self.target_diversification:
                recommendations.append(
                    f"Moderate diversification ({diversification_score:.1f}/100): "
                    "Consider rebalancing position sizes"
                )
            
            # Risk recommendations
            weighted_risk = risk_metrics.get('weighted_risk_score', 0)
            if weighted_risk > 80:
                recommendations.append("High portfolio risk: Consider reducing position sizes or adding defensive assets")
            elif weighted_risk < 30:
                recommendations.append("Conservative portfolio: Consider adding moderate-risk growth positions")
            
            # Correlation recommendations
            if correlation_matrix:
                high_correlation_pairs = []
                for symbol1, correlations in correlation_matrix.items():
                    for symbol2, correlation in correlations.items():
                        if symbol1 < symbol2 and correlation > self.correlation_warning_threshold:
                            high_correlation_pairs.append((symbol1, symbol2, correlation))
                
                if high_correlation_pairs:
                    for symbol1, symbol2, correlation in high_correlation_pairs[:3]:  # Limit to top 3
                        recommendations.append(
                            f"High correlation between {symbol1} and {symbol2} ({correlation:.2f}): "
                            "Consider diversifying"
                        )
            
            # Performance recommendations
            losing_positions = [pos for pos in positions if pos.unrealized_pnl_percent < -10]
            if losing_positions:
                recommendations.append(
                    f"{len(losing_positions)} positions down >10%: "
                    "Review stop-losses and position management"
                )
            
            # Rebalancing recommendations
            target_weight = 100 / len(positions) if positions else 0
            positions_to_rebalance = [
                pos for pos in positions 
                if abs(pos.weight_percent - target_weight) > self.rebalance_threshold
            ]
            
            if len(positions_to_rebalance) > len(positions) * 0.5:  # More than half need rebalancing
                recommendations.append("Consider rebalancing: Many positions have drifted from target weights")
            
            # Add default recommendation if none generated
            if not recommendations:
                recommendations.append("Portfolio appears well-balanced. Continue monitoring performance.")
            
            return recommendations[:10]  # Limit to top 10 recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return ["Error generating recommendations. Please review manually."]
    
    def _generate_portfolio_alerts(self, positions: list[PortfolioPosition],
                                  risk_metrics: dict[str, Any],
                                  total_pnl_percent: float) -> list[str]:
        """Generate portfolio alerts"""
        alerts = []
        
        try:
            # Performance alerts
            if total_pnl_percent < -15:
                alerts.append(f"ALERT: Portfolio down {abs(total_pnl_percent):.1f}% - Review risk management")
            elif total_pnl_percent > 20:
                alerts.append(f"SUCCESS: Portfolio up {total_pnl_percent:.1f}% - Consider profit taking")
            
            # Individual position alerts
            for pos in positions:
                if pos.unrealized_pnl_percent < -20:
                    alerts.append(f"ALERT: {pos.symbol} down {abs(pos.unrealized_pnl_percent):.1f}%")
                elif pos.unrealized_pnl_percent > 50:
                    alerts.append(f"PROFIT: {pos.symbol} up {pos.unrealized_pnl_percent:.1f}%")
                
                # Risk alerts
                if pos.risk_score > 90:
                    alerts.append(f"HIGH RISK: {pos.symbol} risk score {pos.risk_score}/100")
                
                # Position size alerts
                if pos.weight_percent > 30:
                    alerts.append(f"CONCENTRATION: {pos.symbol} is {pos.weight_percent:.1f}% of portfolio")
            
            # Risk metric alerts
            var_percent = risk_metrics.get('var_percent', 0)
            if var_percent > 25:
                alerts.append(f"RISK: High Value-at-Risk ({var_percent:.1f}%)")
            
            return alerts[:8]  # Limit to top 8 alerts
            
        except Exception as e:
            logger.error(f"Failed to generate alerts: {e}")
            return ["Error generating alerts"]
    
    async def _enhance_portfolio_analysis(self, portfolio_analysis: dict[str, Any]) -> dict[str, Any]:
        """Add enhanced analysis features"""
        try:
            # Add benchmark comparison
            benchmark_analysis = await self._compare_to_benchmark(portfolio_analysis)
            
            # Add sector analysis
            sector_analysis = await self._analyze_sector_allocation(portfolio_analysis)
            
            # Add performance attribution
            performance_attribution = await self._calculate_performance_attribution(portfolio_analysis)
            
            # Enhanced analysis
            enhanced = {
                **portfolio_analysis,
                'benchmark_comparison': benchmark_analysis,
                'sector_analysis': sector_analysis,
                'performance_attribution': performance_attribution,
                'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                'next_review_date': (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
            }
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Portfolio enhancement failed: {e}")
            return portfolio_analysis
    
    async def _compare_to_benchmark(self, portfolio_analysis: dict[str, Any]) -> dict[str, Any]:
        """Compare portfolio performance to benchmark"""
        try:
            portfolio_return = portfolio_analysis.get('total_pnl_percent', 0)
            
            # Get benchmark analysis (simplified)
            benchmark_analysis = await self.db_manager.get_latest_analysis(self.benchmark_symbol)
            
            if benchmark_analysis:
                # Extract benchmark return (simplified)
                benchmark_metadata = benchmark_analysis.get('metadata', {})
                benchmark_return = benchmark_metadata.get('price_change_24h', 0)
                
                alpha = portfolio_return - benchmark_return
                
                return {
                    'benchmark_symbol': self.benchmark_symbol,
                    'benchmark_return': benchmark_return,
                    'portfolio_return': portfolio_return,
                    'alpha': alpha,
                    'outperforming': alpha > 0
                }
            
            return {'error': 'Benchmark data unavailable'}
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _analyze_sector_allocation(self, portfolio_analysis: dict[str, Any]) -> dict[str, Any]:
        """Analyze portfolio allocation by sectors"""
        try:
            positions = portfolio_analysis.get('positions', [])
            
            # Simple sector classification
            sectors = {
                'major_crypto': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
                'defi': ['UNIUSDT', 'AAVEUSDT', 'COMPUSDT', 'SUSHIUSDT'],
                'layer1': ['ADAUSDT', 'SOLUSDT', 'DOTUSDT', 'AVAXUSDT'],
                'layer2': ['MATICUSDT', 'ARBUSDT', 'OPUSDT'],
                'other': []
            }
            
            sector_allocation = {}
            total_value = sum(pos['position_value'] for pos in positions)
            
            for sector, symbols in sectors.items():
                sector_value = sum(
                    pos['position_value'] for pos in positions
                    if pos['symbol'] in symbols
                )
                if sector_value > 0:
                    sector_allocation[sector] = {
                        'value': sector_value,
                        'percentage': (sector_value / total_value) * 100 if total_value > 0 else 0
                    }
            
            # Add "other" category for unclassified symbols
            classified_symbols = set()
            for symbols in sectors.values():
                classified_symbols.update(symbols)
            
            other_value = sum(
                pos['position_value'] for pos in positions
                if pos['symbol'] not in classified_symbols
            )
            
            if other_value > 0:
                sector_allocation['other'] = {
                    'value': other_value,
                    'percentage': (other_value / total_value) * 100 if total_value > 0 else 0
                }
            
            return sector_allocation
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _calculate_performance_attribution(self, portfolio_analysis: dict[str, Any]) -> dict[str, Any]:
        """Calculate performance attribution by position"""
        try:
            positions = portfolio_analysis.get('positions', [])
            total_return = portfolio_analysis.get('total_pnl_percent', 0)
            
            attribution = []
            for pos in positions:
                weight = pos['weight_percent'] / 100
                position_return = pos['unrealized_pnl_percent']
                contribution = weight * position_return
                
                attribution.append({
                    'symbol': pos['symbol'],
                    'weight_percent': pos['weight_percent'],
                    'return_percent': position_return,
                    'contribution_to_return': contribution
                })
            
            # Sort by contribution
            attribution.sort(key=lambda x: abs(x['contribution_to_return']), reverse=True)
            
            return {
                'position_contributions': attribution,
                'total_return': total_return
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_position_risk_score(self, analysis, risk_level: str) -> float:
        """Calculate risk score for individual position"""
        try:
            base_risk = 50.0  # Default moderate risk
            
            # Volatility adjustment
            volatility_level = analysis.volatility_indicators.volatility_level
            if volatility_level == "high":
                base_risk += 25
            elif volatility_level == "low":
                base_risk -= 15
            
            # Market trend adjustment
            trend = analysis.market_analysis.trend
            if trend == "bearish":
                base_risk += 20
            elif trend == "bullish":
                base_risk -= 10
            
            # Confidence adjustment
            confidence = analysis.market_analysis.confidence
            base_risk += (100 - confidence) * 0.2
            
            # Risk level adjustment
            risk_multipliers = {
                "conservative": 0.7,
                "moderate": 1.0,
                "aggressive": 1.3
            }
            
            multiplier = risk_multipliers.get(risk_level, 1.0)
            final_risk = base_risk * multiplier
            
            return max(0, min(100, final_risk))
            
        except Exception:
            return 60.0  # Default moderate-high risk
    
    def _extract_current_price(self, analysis) -> float:
        """Extract current price from analysis"""
        try:
            # Try multiple sources for current price
            # 1. From market_analysis close price (most recent)
            if hasattr(analysis, 'market_analysis') and analysis.market_analysis:
                market_data = analysis.market_analysis
                if hasattr(market_data, 'current_price'):
                    return float(market_data.current_price)
            
            # 2. From metadata if available
            if hasattr(analysis, 'metadata') and analysis.metadata:
                metadata = analysis.metadata
                if 'current_price' in metadata:
                    return float(metadata['current_price'])
                if 'close' in metadata:
                    return float(metadata['close'])
            
            # 3. From analysis dict format
            if isinstance(analysis, dict):
                if 'market_analysis' in analysis and 'current_price' in analysis['market_analysis']:
                    return float(analysis['market_analysis']['current_price'])
                if 'metadata' in analysis:
                    metadata = analysis['metadata']
                    if 'current_price' in metadata:
                        return float(metadata['current_price'])
                    if 'close' in metadata:
                        return float(metadata['close'])
            
            # 4. Fallback: Use a reasonable default for crypto (this should rarely trigger)
            logger.warning(f"Could not extract current price from analysis, using default: 50000.0")
            return 50000.0
            
        except Exception as e:
            logger.error(f"Error extracting current price: {e}")
            return 0.0
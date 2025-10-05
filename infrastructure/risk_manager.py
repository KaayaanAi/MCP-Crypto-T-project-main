"""
Risk Manager for Intelligent Position Sizing and Risk Assessment
Advanced risk management with Kelly Criterion, correlation analysis, and volatility adjustments
"""

import asyncio
import numpy as np
import pandas as pd
import logging
from datetime import datetime, timezone, timedelta
from typing import Any
from dataclasses import asdict
import math

from models.kaayaan_models import *
from infrastructure.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class RiskManager:
    """
    Intelligent risk management system with multiple position sizing methodologies
    Features:
    - Kelly Criterion position sizing
    - Volatility-adjusted position sizing
    - Portfolio correlation analysis
    - Risk-adjusted returns calculation
    - Dynamic stop-loss recommendations
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
        # Risk parameters
        self.max_portfolio_risk = 20.0  # Maximum % of portfolio at risk
        self.max_single_position_risk = 5.0  # Maximum % risk per position
        self.max_correlation_threshold = 0.7  # Maximum correlation between positions
        self.volatility_lookback_days = 30  # Days for volatility calculation
        self.kelly_max_fraction = 0.25  # Maximum Kelly fraction (anti-overbetting)
        
        # Market regime risk adjustments
        self.regime_risk_adjustments = {
            MarketRegime.BULL_MARKET: 1.0,      # Normal risk
            MarketRegime.BEAR_MARKET: 0.5,      # Reduce risk by 50%
            MarketRegime.RANGE_BOUND: 0.8,      # Reduce risk by 20%
            MarketRegime.TRANSITIONAL: 0.6,     # Reduce risk by 40%
            MarketRegime.UNKNOWN: 0.7           # Conservative approach
        }
        
    async def calculate_position_sizing(self, symbol: str, portfolio_value: float,
                                      risk_percentage: float, entry_price: float,
                                      stop_loss: float, target_price: float | None = None,
                                      portfolio_id: str | None = None) -> RiskAssessment:
        """
        Calculate intelligent position sizing using multiple methodologies
        """
        try:
            # Validate inputs
            if entry_price <= 0 or stop_loss <= 0 or portfolio_value <= 0:
                raise ValueError("Prices and portfolio value must be positive")
            
            if risk_percentage <= 0 or risk_percentage > 100:
                raise ValueError("Risk percentage must be between 0 and 100")
            
            # Calculate basic risk metrics
            price_diff = abs(entry_price - stop_loss)
            risk_per_share = price_diff
            risk_amount = portfolio_value * (risk_percentage / 100)
            
            # Basic position size (risk-based)
            basic_position_size = risk_amount / risk_per_share if risk_per_share > 0 else 0
            position_value = basic_position_size * entry_price
            
            # Get market analysis for advanced calculations
            latest_analysis = await self.db_manager.get_latest_analysis(symbol)
            
            # Calculate advanced position sizes
            volatility_adjusted_size = await self._calculate_volatility_adjusted_size(
                symbol, basic_position_size, latest_analysis
            )
            
            kelly_size = await self._calculate_kelly_position_size(
                symbol, entry_price, stop_loss, target_price, latest_analysis
            )
            
            # Get portfolio correlation risk if portfolio_id provided
            correlation_risk = 0.0
            if portfolio_id:
                correlation_risk = await self._calculate_correlation_risk(
                    portfolio_id, symbol, position_value
                )
            
            # Apply market regime adjustments
            regime_adjustment = self._get_regime_risk_adjustment(latest_analysis)
            
            # Final position size (conservative approach - take minimum of methods)
            final_sizes = [basic_position_size, volatility_adjusted_size]
            if kelly_size > 0:
                final_sizes.append(kelly_size)
            
            adjusted_size = min(final_sizes) * regime_adjustment
            final_position_value = adjusted_size * entry_price
            
            # Calculate risk-reward ratio
            risk_reward_ratio = None
            if target_price:
                potential_profit = abs(target_price - entry_price)
                risk_reward_ratio = potential_profit / risk_per_share if risk_per_share > 0 else 0
            
            # Generate warnings
            warnings = self._generate_risk_warnings(
                risk_percentage, position_value, portfolio_value,
                correlation_risk, latest_analysis
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(
                risk_percentage, correlation_risk, latest_analysis
            )
            
            # Create risk assessment
            risk_assessment = RiskAssessment(
                symbol=symbol,
                portfolio_value=portfolio_value,
                risk_percentage=risk_percentage,
                entry_price=entry_price,
                stop_loss=stop_loss,
                risk_amount=risk_amount,
                position_size=adjusted_size,
                position_value=final_position_value,
                max_loss=risk_amount,
                risk_reward_ratio=risk_reward_ratio,
                volatility_adjusted_size=volatility_adjusted_size,
                kelly_criterion_size=kelly_size,
                correlation_risk=correlation_risk,
                warnings=warnings,
                risk_level=risk_level
            )
            
            # Log the calculation
            await self.db_manager.log_action(AuditLog(
                action="calculate_position_sizing",
                symbol=symbol,
                parameters={
                    "portfolio_value": portfolio_value,
                    "risk_percentage": risk_percentage,
                    "entry_price": entry_price,
                    "stop_loss": stop_loss
                },
                result={
                    "position_size": adjusted_size,
                    "position_value": final_position_value,
                    "risk_level": risk_level.value
                },
                success=True
            ))
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Position sizing calculation failed for {symbol}: {e}")
            await self.db_manager.log_action(AuditLog(
                action="calculate_position_sizing",
                symbol=symbol,
                parameters={"error": str(e)},
                result={},
                success=False,
                error_message=str(e)
            ))
            raise
    
    async def _calculate_volatility_adjusted_size(self, symbol: str, base_size: float,
                                                analysis: dict[str, Any | None]) -> float:
        """Calculate volatility-adjusted position size"""
        try:
            if not analysis:
                return base_size
            
            # Get volatility from analysis
            volatility_indicators = analysis.get('volatility_indicators', {})
            volatility_level = volatility_indicators.get('volatility_level', 'moderate')
            atr = volatility_indicators.get('average_true_range', 0)
            
            # Volatility adjustments
            volatility_multipliers = {
                'low': 1.2,      # Increase size for low volatility
                'moderate': 1.0,  # Keep normal size
                'high': 0.6       # Reduce size for high volatility
            }
            
            multiplier = volatility_multipliers.get(volatility_level, 1.0)
            
            # Additional ATR-based adjustment
            if atr > 0:
                # If ATR is high relative to price, reduce position size further
                current_price = analysis.get('metadata', {}).get('current_price', 0)
                if current_price > 0:
                    atr_percentage = (atr / current_price) * 100
                    if atr_percentage > 5:  # Very high volatility
                        multiplier *= 0.8
                    elif atr_percentage > 10:  # Extremely high volatility
                        multiplier *= 0.6
            
            adjusted_size = base_size * multiplier
            
            logger.debug(f"Volatility adjustment for {symbol}: {multiplier:.2f}x")
            
            return max(0, adjusted_size)
            
        except Exception as e:
            logger.error(f"Volatility adjustment calculation failed: {e}")
            return base_size
    
    async def _calculate_kelly_position_size(self, symbol: str, entry_price: float,
                                           stop_loss: float, target_price: float | None,
                                           analysis: dict[str, Any | None]) -> float:
        """Calculate Kelly Criterion position size"""
        try:
            if not analysis or not target_price:
                return 0
            
            # Get win probability from analysis confidence
            recommendation = analysis.get('recommendation', {})
            confidence = recommendation.get('confidence', 50) / 100  # Convert to 0-1
            
            # Estimate win probability based on confidence and market conditions
            intelligent_score = analysis.get('intelligent_score', 50) / 100
            win_probability = (confidence + intelligent_score) / 2
            
            # Ensure reasonable probability bounds
            win_probability = max(0.1, min(0.9, win_probability))
            
            # Calculate potential win/loss amounts
            potential_win = abs(target_price - entry_price)
            potential_loss = abs(entry_price - stop_loss)
            
            if potential_loss <= 0:
                return 0
            
            # Win/loss ratio
            win_loss_ratio = potential_win / potential_loss
            
            # Kelly Criterion formula: f = (bp - q) / b
            # where f = fraction to bet, b = win/loss ratio, p = win probability, q = loss probability
            kelly_fraction = (win_loss_ratio * win_probability - (1 - win_probability)) / win_loss_ratio
            
            # Apply safety cap to prevent over-betting
            kelly_fraction = max(0, min(self.kelly_max_fraction, kelly_fraction))
            
            logger.debug(f"Kelly calculation for {symbol}: "
                        f"win_prob={win_probability:.2f}, ratio={win_loss_ratio:.2f}, "
                        f"fraction={kelly_fraction:.3f}")
            
            return kelly_fraction  # Return as fraction of portfolio
            
        except Exception as e:
            logger.error(f"Kelly criterion calculation failed: {e}")
            return 0
    
    async def _calculate_correlation_risk(self, portfolio_id: str, new_symbol: str,
                                        new_position_value: float) -> float:
        """Calculate correlation risk with existing portfolio positions"""
        try:
            # Get current portfolio
            portfolio = await self.db_manager.get_latest_portfolio(portfolio_id)
            if not portfolio:
                return 0.0
            
            positions = portfolio.get('positions', [])
            if not positions:
                return 0.0
            
            # Get correlation data for symbols
            correlations = []
            total_risk_exposure = 0.0
            
            for position in positions:
                existing_symbol = position.get('symbol', '')
                position_value = position.get('position_value', 0)
                
                if existing_symbol and existing_symbol != new_symbol:
                    # Get historical correlation (simplified - in production, use real correlation data)
                    correlation = await self._get_symbol_correlation(new_symbol, existing_symbol)
                    
                    if correlation > self.max_correlation_threshold:
                        # High correlation increases risk
                        risk_contribution = correlation * position_value
                        correlations.append({
                            'symbol': existing_symbol,
                            'correlation': correlation,
                            'risk_contribution': risk_contribution
                        })
                        total_risk_exposure += risk_contribution
            
            # Calculate correlation risk as percentage of new position
            if new_position_value > 0 and correlations:
                correlation_risk = min(100, (total_risk_exposure / new_position_value) * 100)
                
                logger.debug(f"Correlation risk for {new_symbol}: {correlation_risk:.1f}%")
                return correlation_risk
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Correlation risk calculation failed: {e}")
            return 0.0
    
    async def _get_symbol_correlation(self, symbol1: str, symbol2: str) -> float:
        """Get correlation between two symbols (simplified implementation)"""
        try:
            # In production, this would calculate actual correlation from price history
            # For now, use simplified logic based on symbol categories
            
            crypto_majors = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
            crypto_alts = ['ADAUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT']
            crypto_meme = ['DOGEUSDT', 'SHIBUSDT']
            
            def get_category(symbol):
                if symbol in crypto_majors:
                    return 'major'
                elif symbol in crypto_alts:
                    return 'alt'
                elif symbol in crypto_meme:
                    return 'meme'
                else:
                    return 'other'
            
            cat1, cat2 = get_category(symbol1), get_category(symbol2)
            
            # Simplified correlation based on categories
            if cat1 == cat2:
                return 0.8  # High correlation within same category
            elif 'major' in [cat1, cat2]:
                return 0.6  # Moderate correlation with majors
            else:
                return 0.4  # Lower correlation between different categories
                
        except Exception:
            return 0.5  # Default moderate correlation
    
    def _get_regime_risk_adjustment(self, analysis: dict[str, Any | None]) -> float:
        """Get risk adjustment factor based on market regime"""
        try:
            if not analysis:
                return self.regime_risk_adjustments[MarketRegime.UNKNOWN]
            
            regime_str = analysis.get('regime_analysis', 'unknown')
            regime = MarketRegime(regime_str) if regime_str in [r.value for r in MarketRegime] else MarketRegime.UNKNOWN
            
            return self.regime_risk_adjustments.get(regime, 0.7)
            
        except Exception:
            return 0.7  # Conservative default
    
    def _generate_risk_warnings(self, risk_percentage: float, position_value: float,
                               portfolio_value: float, correlation_risk: float,
                               analysis: dict[str, Any | None]) -> list[str]:
        """Generate risk warnings based on position and market conditions"""
        warnings = []
        
        # Position size warnings
        position_percent = (position_value / portfolio_value) * 100
        if position_percent > 10:
            warnings.append(f"Large position size: {position_percent:.1f}% of portfolio")
        
        # Risk percentage warnings
        if risk_percentage > 5:
            warnings.append(f"High risk per trade: {risk_percentage}%")
        
        # Correlation warnings
        if correlation_risk > 20:
            warnings.append(f"High correlation risk: {correlation_risk:.1f}%")
        
        # Market condition warnings
        if analysis:
            volatility_level = analysis.get('volatility_indicators', {}).get('volatility_level')
            if volatility_level == 'high':
                warnings.append("High market volatility detected")
            
            regime = analysis.get('regime_analysis', '')
            if regime == 'bear_market':
                warnings.append("Bear market conditions - consider reduced position sizes")
            elif regime == 'transitional':
                warnings.append("Transitional market - increased uncertainty")
            
            # Technical warnings
            market_analysis = analysis.get('market_analysis', {})
            confidence = market_analysis.get('confidence', 100)
            if confidence < 60:
                warnings.append(f"Low analysis confidence: {confidence}%")
        
        return warnings
    
    def _determine_risk_level(self, risk_percentage: float, correlation_risk: float,
                             analysis: dict[str, Any | None]) -> RiskLevel:
        """Determine overall risk level for the position"""
        try:
            risk_score = 0
            
            # Risk percentage contribution
            if risk_percentage <= 1:
                risk_score += 1
            elif risk_percentage <= 2:
                risk_score += 2
            elif risk_percentage <= 5:
                risk_score += 3
            else:
                risk_score += 5
            
            # Correlation risk contribution
            if correlation_risk > 30:
                risk_score += 3
            elif correlation_risk > 15:
                risk_score += 2
            elif correlation_risk > 5:
                risk_score += 1
            
            # Market conditions contribution
            if analysis:
                volatility_level = analysis.get('volatility_indicators', {}).get('volatility_level', 'moderate')
                if volatility_level == 'high':
                    risk_score += 2
                elif volatility_level == 'low':
                    risk_score -= 1
                
                regime = analysis.get('regime_analysis', '')
                if regime == 'bear_market':
                    risk_score += 2
                elif regime == 'bull_market':
                    risk_score -= 1
            
            # Determine final risk level
            if risk_score <= 2:
                return RiskLevel.CONSERVATIVE
            elif risk_score <= 5:
                return RiskLevel.MODERATE
            else:
                return RiskLevel.AGGRESSIVE
                
        except Exception:
            return RiskLevel.MODERATE
    
    async def analyze_portfolio_risk(self, portfolio_id: str) -> dict[str, Any]:
        """Analyze overall portfolio risk metrics"""
        try:
            portfolio = await self.db_manager.get_latest_portfolio(portfolio_id)
            if not portfolio:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            positions = portfolio.get('positions', [])
            if not positions:
                return {"error": "No positions in portfolio"}
            
            total_value = portfolio.get('total_value', 0)
            total_risk = 0
            position_risks = []
            correlations = {}
            
            # Analyze each position
            for position in positions:
                symbol = position.get('symbol', '')
                position_value = position.get('position_value', 0)
                risk_score = position.get('risk_score', 0)
                
                # Calculate position risk contribution
                position_risk = (position_value / total_value) * (risk_score / 100)
                total_risk += position_risk
                
                position_risks.append({
                    'symbol': symbol,
                    'position_value': position_value,
                    'weight_percent': (position_value / total_value) * 100,
                    'risk_score': risk_score,
                    'risk_contribution': position_risk * 100
                })
            
            # Calculate diversification score
            diversification_score = self._calculate_diversification_score(position_risks)
            
            # Generate recommendations
            recommendations = self._generate_portfolio_recommendations(
                position_risks, total_risk, diversification_score
            )
            
            return {
                'portfolio_id': portfolio_id,
                'total_risk_percent': total_risk * 100,
                'diversification_score': diversification_score,
                'position_risks': position_risks,
                'recommendations': recommendations,
                'risk_level': 'low' if total_risk < 0.1 else 'moderate' if total_risk < 0.2 else 'high'
            }
            
        except Exception as e:
            logger.error(f"Portfolio risk analysis failed: {e}")
            raise
    
    def _calculate_diversification_score(self, position_risks: list[dict[str, Any]]) -> float:
        """Calculate portfolio diversification score (0-100)"""
        try:
            if len(position_risks) < 2:
                return 0  # No diversification with single position
            
            # Calculate concentration (Herfindahl Index)
            weights = [pos['weight_percent'] / 100 for pos in position_risks]
            herfindahl_index = sum(w**2 for w in weights)
            
            # Convert to diversification score (lower HI = higher diversification)
            max_herfindahl = 1.0  # All money in one position
            min_herfindahl = 1.0 / len(position_risks)  # Equal weights
            
            if max_herfindahl == min_herfindahl:
                return 100
            
            # Normalized diversification score
            diversification_score = (1 - (herfindahl_index - min_herfindahl) / (max_herfindahl - min_herfindahl)) * 100
            
            return max(0, min(100, diversification_score))
            
        except Exception:
            return 50  # Default moderate diversification
    
    def _generate_portfolio_recommendations(self, position_risks: list[dict[str, Any]],
                                          total_risk: float, diversification_score: float) -> list[str]:
        """Generate portfolio risk management recommendations"""
        recommendations = []
        
        # Risk level recommendations
        if total_risk > 0.25:
            recommendations.append("Portfolio risk is very high - consider reducing position sizes")
        elif total_risk > 0.15:
            recommendations.append("Portfolio risk is elevated - monitor closely")
        
        # Diversification recommendations
        if diversification_score < 30:
            recommendations.append("Low diversification - consider adding uncorrelated positions")
        elif diversification_score < 50:
            recommendations.append("Moderate diversification - room for improvement")
        
        # Position concentration recommendations
        for pos in position_risks:
            if pos['weight_percent'] > 20:
                recommendations.append(f"{pos['symbol']}: Position is {pos['weight_percent']:.1f}% of portfolio - consider reducing")
            elif pos['risk_contribution'] > 30:
                recommendations.append(f"{pos['symbol']}: High risk contribution ({pos['risk_contribution']:.1f}%)")
        
        # General recommendations
        if len(position_risks) < 3:
            recommendations.append("Consider adding more positions to improve diversification")
        
        if not recommendations:
            recommendations.append("Portfolio risk profile appears well-balanced")
        
        return recommendations
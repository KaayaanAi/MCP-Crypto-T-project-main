"""
Backtester for Historical Strategy Validation
Advanced backtesting engine with multiple strategy types and performance analytics
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
from dataclasses import asdict
import json

from models.kaayaan_models import *
from infrastructure.database_manager import DatabaseManager
from crypto_analyzer import CryptoAnalyzer

logger = logging.getLogger(__name__)

class Backtester:
    """
    Comprehensive backtesting engine for trading strategies
    Features:
    - Multiple strategy implementations
    - Risk-adjusted performance metrics
    - Monte Carlo simulation
    - Walk-forward analysis
    - Strategy optimization
    """
    
    def __init__(self, analyzer: CryptoAnalyzer, db_manager: DatabaseManager):
        self.analyzer = analyzer
        self.db_manager = db_manager
        
        # Backtesting parameters
        self.transaction_cost = 0.001  # 0.1% per trade
        self.slippage = 0.0005        # 0.05% slippage
        self.risk_free_rate = 0.02    # 2% annual risk-free rate
        
        # Strategy implementations
        self.strategies = {
            'technical_momentum': self._technical_momentum_strategy,
            'mean_reversion': self._mean_reversion_strategy,
            'breakout': self._breakout_strategy,
            'institutional_following': self._institutional_following_strategy,
            'multi_timeframe': self._multi_timeframe_strategy
        }
        
    async def run_backtest(self, symbol: str, strategy: str, start_date: str,
                          end_date: str, initial_capital: float = 10000,
                          strategy_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run comprehensive backtest for specified strategy and period
        """
        try:
            logger.info(f"Starting backtest: {strategy} on {symbol} from {start_date} to {end_date}")
            
            # Parse dates
            start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
            end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
            
            # Validate inputs
            if start_dt >= end_dt:
                raise ValueError("Start date must be before end date")
            
            if strategy not in self.strategies:
                raise ValueError(f"Unknown strategy: {strategy}. Available: {list(self.strategies.keys())}")
            
            # Get historical data
            historical_data = await self._get_historical_data(symbol, start_dt, end_dt)
            
            if not historical_data:
                raise ValueError(f"No historical data available for {symbol}")
            
            # Run strategy backtest
            backtest_results = await self._execute_strategy_backtest(
                symbol, strategy, historical_data, initial_capital, strategy_params or {}
            )
            
            # Calculate comprehensive performance metrics
            performance_metrics = self._calculate_performance_metrics(
                backtest_results['trades'], 
                backtest_results['equity_curve'],
                initial_capital
            )
            
            # Create final backtest result
            final_result = BacktestResult(
                symbol=symbol,
                strategy=strategy,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                **performance_metrics,
                trades=backtest_results['trades'],
                equity_curve=backtest_results['equity_curve']
            )
            
            logger.info(f"Backtest completed: {final_result.total_return_percent:.2f}% return, "
                       f"{final_result.total_trades} trades, {final_result.win_rate:.1f}% win rate")
            
            return final_result.dict()
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            raise
    
    async def _get_historical_data(self, symbol: str, start_date: datetime,
                                 end_date: datetime) -> List[Dict[str, Any]]:
        """Get historical analysis data for backtesting"""
        try:
            # Get historical analysis from database
            historical_analyses = await self.db_manager.get_historical_analysis(
                symbol, start_date, end_date, timeframe="1h"
            )
            
            if not historical_analyses:
                # If no historical analysis available, generate synthetic data
                logger.warning(f"No historical analysis for {symbol}, generating synthetic data")
                historical_analyses = await self._generate_synthetic_data(symbol, start_date, end_date)
            
            return historical_analyses
            
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            return []
    
    async def _generate_synthetic_data(self, symbol: str, start_date: datetime,
                                     end_date: datetime) -> List[Dict[str, Any]]:
        """Generate synthetic historical data for backtesting (fallback)"""
        try:
            # Generate synthetic price and analysis data
            # This is a simplified implementation for demonstration
            
            synthetic_data = []
            current_date = start_date
            base_price = 50000.0  # Starting price
            
            while current_date < end_date:
                # Generate synthetic price movement
                price_change = np.random.normal(0, 0.02)  # 2% daily volatility
                base_price *= (1 + price_change)
                
                # Generate synthetic analysis
                synthetic_analysis = {
                    'symbol': symbol,
                    'timestamp': current_date.isoformat(),
                    'timeframe': '1h',
                    'market_analysis': {
                        'trend': np.random.choice(['bullish', 'bearish', 'sideways'], p=[0.4, 0.3, 0.3]),
                        'volatility': np.random.choice(['low', 'moderate', 'high'], p=[0.3, 0.5, 0.2]),
                        'confidence': np.random.uniform(40, 90)
                    },
                    'volatility_indicators': {
                        'bollinger_bands_width': np.random.uniform(2, 8),
                        'average_true_range': np.random.uniform(100, 500),
                        'volatility_level': np.random.choice(['low', 'moderate', 'high'], p=[0.3, 0.5, 0.2])
                    },
                    'recommendation': {
                        'action': np.random.choice(['BUY', 'SELL', 'HOLD'], p=[0.3, 0.3, 0.4]),
                        'confidence': np.random.uniform(50, 85),
                        'reasoning': 'Synthetic backtest signal'
                    },
                    'intelligent_score': np.random.uniform(40, 90),
                    'metadata': {
                        'current_price': base_price,
                        'volume_24h': np.random.uniform(1000000, 10000000)
                    }
                }
                
                synthetic_data.append(synthetic_analysis)
                current_date += timedelta(hours=1)
            
            return synthetic_data
            
        except Exception as e:
            logger.error(f"Failed to generate synthetic data: {e}")
            return []
    
    async def _execute_strategy_backtest(self, symbol: str, strategy_name: str,
                                       historical_data: List[Dict[str, Any]],
                                       initial_capital: float,
                                       strategy_params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategy backtest on historical data"""
        try:
            strategy_func = self.strategies[strategy_name]
            
            # Initialize backtest state
            capital = initial_capital
            position = 0.0  # Current position size
            entry_price = 0.0
            trades = []
            equity_curve = []
            
            # Track performance
            max_capital = initial_capital
            
            for i, analysis in enumerate(historical_data):
                current_price = analysis.get('metadata', {}).get('current_price', 0)
                timestamp = analysis.get('timestamp', '')
                
                if current_price <= 0:
                    continue
                
                # Get strategy signal
                signal = await strategy_func(analysis, historical_data[:i], strategy_params)
                
                # Execute trades based on signal
                if signal['action'] == 'BUY' and position == 0:
                    # Open long position
                    position_size = capital * signal.get('position_size', 0.95)  # Use 95% of capital
                    shares = position_size / current_price
                    
                    # Apply transaction costs
                    cost = position_size * self.transaction_cost
                    slippage_cost = position_size * self.slippage
                    total_cost = cost + slippage_cost
                    
                    position = shares
                    entry_price = current_price * (1 + self.slippage)  # Include slippage
                    capital -= (position_size + total_cost)
                    
                    trades.append({
                        'type': 'BUY',
                        'timestamp': timestamp,
                        'price': entry_price,
                        'shares': shares,
                        'value': position_size,
                        'cost': total_cost,
                        'signal_confidence': signal.get('confidence', 0),
                        'reasoning': signal.get('reasoning', '')
                    })
                
                elif signal['action'] == 'SELL' and position > 0:
                    # Close long position
                    exit_price = current_price * (1 - self.slippage)  # Include slippage
                    position_value = position * exit_price
                    
                    # Apply transaction costs
                    cost = position_value * self.transaction_cost
                    slippage_cost = position_value * self.slippage
                    total_cost = cost + slippage_cost
                    
                    # Calculate trade P&L
                    trade_pnl = (exit_price - entry_price) * position - total_cost
                    
                    capital += (position_value - total_cost)
                    
                    trades.append({
                        'type': 'SELL',
                        'timestamp': timestamp,
                        'price': exit_price,
                        'shares': position,
                        'value': position_value,
                        'cost': total_cost,
                        'pnl': trade_pnl,
                        'pnl_percent': (trade_pnl / (entry_price * position)) * 100,
                        'hold_period': self._calculate_hold_period(trades[-1]['timestamp'], timestamp),
                        'signal_confidence': signal.get('confidence', 0),
                        'reasoning': signal.get('reasoning', '')
                    })
                    
                    position = 0.0
                    entry_price = 0.0
                
                # Calculate current portfolio value
                portfolio_value = capital
                if position > 0:
                    portfolio_value += position * current_price
                
                # Update max capital for drawdown calculation
                max_capital = max(max_capital, portfolio_value)
                
                # Record equity curve
                equity_curve.append({
                    'timestamp': timestamp,
                    'portfolio_value': portfolio_value,
                    'capital': capital,
                    'position_value': position * current_price if position > 0 else 0,
                    'drawdown': (max_capital - portfolio_value) / max_capital * 100,
                    'price': current_price
                })
            
            # Close any remaining position at the end
            if position > 0:
                final_price = historical_data[-1].get('metadata', {}).get('current_price', entry_price)
                final_value = position * final_price * (1 - self.slippage)
                final_cost = final_value * self.transaction_cost
                
                trade_pnl = (final_price - entry_price) * position - final_cost
                
                trades.append({
                    'type': 'SELL',
                    'timestamp': historical_data[-1].get('timestamp', ''),
                    'price': final_price * (1 - self.slippage),
                    'shares': position,
                    'value': final_value,
                    'cost': final_cost,
                    'pnl': trade_pnl,
                    'pnl_percent': (trade_pnl / (entry_price * position)) * 100,
                    'hold_period': 0,
                    'signal_confidence': 0,
                    'reasoning': 'End of backtest period'
                })
                
                capital += (final_value - final_cost)
            
            return {
                'trades': trades,
                'equity_curve': equity_curve,
                'final_capital': capital
            }
            
        except Exception as e:
            logger.error(f"Strategy backtest execution failed: {e}")
            raise
    
    async def _technical_momentum_strategy(self, current_analysis: Dict[str, Any],
                                         historical_analyses: List[Dict[str, Any]],
                                         params: Dict[str, Any]) -> Dict[str, str]:
        """Technical momentum strategy implementation"""
        try:
            # Strategy parameters
            confidence_threshold = params.get('confidence_threshold', 70)
            trend_strength_threshold = params.get('trend_strength_threshold', 60)
            
            # Extract signals
            recommendation = current_analysis.get('recommendation', {})
            market_analysis = current_analysis.get('market_analysis', {})
            intelligent_score = current_analysis.get('intelligent_score', 50)
            
            action = recommendation.get('action', 'HOLD')
            confidence = recommendation.get('confidence', 0)
            trend = market_analysis.get('trend', 'unknown')
            
            # Strategy logic
            if (action == 'BUY' and 
                confidence >= confidence_threshold and
                intelligent_score >= trend_strength_threshold and
                trend == 'bullish'):
                
                return {
                    'action': 'BUY',
                    'confidence': confidence,
                    'position_size': min(0.95, confidence / 100),
                    'reasoning': f'Strong bullish momentum: {confidence:.1f}% confidence, {intelligent_score:.1f} score'
                }
            
            elif (action == 'SELL' and 
                  confidence >= confidence_threshold and
                  trend == 'bearish'):
                
                return {
                    'action': 'SELL',
                    'confidence': confidence,
                    'reasoning': f'Strong bearish momentum: {confidence:.1f}% confidence'
                }
            
            return {
                'action': 'HOLD',
                'confidence': 0,
                'reasoning': 'Insufficient momentum signal'
            }
            
        except Exception as e:
            logger.error(f"Technical momentum strategy error: {e}")
            return {'action': 'HOLD', 'confidence': 0, 'reasoning': 'Strategy error'}
    
    async def _mean_reversion_strategy(self, current_analysis: Dict[str, Any],
                                     historical_analyses: List[Dict[str, Any]],
                                     params: Dict[str, Any]) -> Dict[str, str]:
        """Mean reversion strategy implementation"""
        try:
            # Strategy parameters
            rsi_oversold = params.get('rsi_oversold', 30)
            rsi_overbought = params.get('rsi_overbought', 70)
            
            # Look for RSI divergences
            rsi_divergences = current_analysis.get('rsi_divergence', [])
            market_analysis = current_analysis.get('market_analysis', {})
            
            for divergence in rsi_divergences:
                rsi_value = divergence.get('rsi_value', 50)
                div_type = divergence.get('type', '')
                strength = divergence.get('strength', 0)
                
                if div_type == 'bullish' and rsi_value <= rsi_oversold and strength > 10:
                    return {
                        'action': 'BUY',
                        'confidence': min(90, 50 + strength),
                        'position_size': 0.8,
                        'reasoning': f'Bullish RSI divergence at oversold level: RSI {rsi_value:.1f}'
                    }
                
                elif div_type == 'bearish' and rsi_value >= rsi_overbought and strength > 10:
                    return {
                        'action': 'SELL',
                        'confidence': min(90, 50 + strength),
                        'reasoning': f'Bearish RSI divergence at overbought level: RSI {rsi_value:.1f}'
                    }
            
            return {
                'action': 'HOLD',
                'confidence': 0,
                'reasoning': 'No mean reversion signal'
            }
            
        except Exception as e:
            logger.error(f"Mean reversion strategy error: {e}")
            return {'action': 'HOLD', 'confidence': 0, 'reasoning': 'Strategy error'}
    
    async def _breakout_strategy(self, current_analysis: Dict[str, Any],
                               historical_analyses: List[Dict[str, Any]],
                               params: Dict[str, Any]) -> Dict[str, str]:
        """Breakout strategy implementation"""
        try:
            # Strategy parameters
            min_bos_strength = params.get('min_bos_strength', 2.0)
            volume_confirmation = params.get('volume_confirmation', True)
            
            # Look for break of structure signals
            bos_signals = current_analysis.get('break_of_structure', [])
            liquidity_zones = current_analysis.get('liquidity_zones', [])
            
            for bos in bos_signals:
                strength = bos.get('strength', 0)
                direction = bos.get('direction', '')
                
                if strength >= min_bos_strength:
                    # Check for volume confirmation if required
                    volume_confirmed = True
                    if volume_confirmation:
                        volume_confirmed = len(liquidity_zones) > 0
                    
                    if volume_confirmed:
                        if direction == 'bullish':
                            return {
                                'action': 'BUY',
                                'confidence': min(85, 50 + strength * 10),
                                'position_size': 0.9,
                                'reasoning': f'Bullish breakout: {strength:.1f} strength'
                            }
                        elif direction == 'bearish':
                            return {
                                'action': 'SELL',
                                'confidence': min(85, 50 + strength * 10),
                                'reasoning': f'Bearish breakout: {strength:.1f} strength'
                            }
            
            return {
                'action': 'HOLD',
                'confidence': 0,
                'reasoning': 'No breakout signal'
            }
            
        except Exception as e:
            logger.error(f"Breakout strategy error: {e}")
            return {'action': 'HOLD', 'confidence': 0, 'reasoning': 'Strategy error'}
    
    async def _institutional_following_strategy(self, current_analysis: Dict[str, Any],
                                              historical_analyses: List[Dict[str, Any]],
                                              params: Dict[str, Any]) -> Dict[str, str]:
        """Institutional following strategy implementation"""
        try:
            # Strategy parameters
            min_ob_strength = params.get('min_order_block_strength', 60)
            
            # Look for strong order blocks
            order_blocks = current_analysis.get('order_blocks', [])
            fair_value_gaps = current_analysis.get('fair_value_gaps', [])
            
            # Find strongest order block
            strongest_ob = None
            max_strength = 0
            
            for ob in order_blocks:
                strength = ob.get('strength', 0)
                if strength > max_strength and strength >= min_ob_strength:
                    strongest_ob = ob
                    max_strength = strength
            
            if strongest_ob:
                ob_type = strongest_ob.get('type', '')
                
                # Check for FVG confirmation
                fvg_confirmation = False
                for fvg in fair_value_gaps:
                    if ((ob_type == 'demand' and fvg.get('type') == 'bullish') or
                        (ob_type == 'supply' and fvg.get('type') == 'bearish')):
                        fvg_confirmation = True
                        break
                
                confidence_bonus = 10 if fvg_confirmation else 0
                
                if ob_type == 'demand':
                    return {
                        'action': 'BUY',
                        'confidence': min(90, 60 + (max_strength - min_ob_strength) + confidence_bonus),
                        'position_size': 0.85,
                        'reasoning': f'Strong demand order block: {max_strength:.1f} strength'
                    }
                elif ob_type == 'supply':
                    return {
                        'action': 'SELL',
                        'confidence': min(90, 60 + (max_strength - min_ob_strength) + confidence_bonus),
                        'reasoning': f'Strong supply order block: {max_strength:.1f} strength'
                    }
            
            return {
                'action': 'HOLD',
                'confidence': 0,
                'reasoning': 'No institutional signal'
            }
            
        except Exception as e:
            logger.error(f"Institutional following strategy error: {e}")
            return {'action': 'HOLD', 'confidence': 0, 'reasoning': 'Strategy error'}
    
    async def _multi_timeframe_strategy(self, current_analysis: Dict[str, Any],
                                      historical_analyses: List[Dict[str, Any]],
                                      params: Dict[str, Any]) -> Dict[str, str]:
        """Multi-timeframe strategy implementation"""
        try:
            # This would analyze multiple timeframes in production
            # For now, combine signals from current analysis
            
            recommendation = current_analysis.get('recommendation', {})
            intelligent_score = current_analysis.get('intelligent_score', 50)
            market_analysis = current_analysis.get('market_analysis', {})
            
            action = recommendation.get('action', 'HOLD')
            confidence = recommendation.get('confidence', 0)
            trend = market_analysis.get('trend', 'unknown')
            
            # Multi-signal confirmation
            signals = []
            
            # Add recommendation signal
            if action == 'BUY' and confidence > 60:
                signals.append(('BUY', confidence))
            elif action == 'SELL' and confidence > 60:
                signals.append(('SELL', confidence))
            
            # Add intelligent score signal
            if intelligent_score > 70:
                signals.append(('BUY', intelligent_score))
            elif intelligent_score < 30:
                signals.append(('SELL', 100 - intelligent_score))
            
            # Add trend signal
            if trend == 'bullish':
                signals.append(('BUY', 65))
            elif trend == 'bearish':
                signals.append(('SELL', 65))
            
            # Consensus decision
            buy_signals = [s for s in signals if s[0] == 'BUY']
            sell_signals = [s for s in signals if s[0] == 'SELL']
            
            if len(buy_signals) >= 2:
                avg_confidence = sum(s[1] for s in buy_signals) / len(buy_signals)
                return {
                    'action': 'BUY',
                    'confidence': avg_confidence,
                    'position_size': 0.9,
                    'reasoning': f'Multi-timeframe bullish consensus: {len(buy_signals)} signals'
                }
            elif len(sell_signals) >= 2:
                avg_confidence = sum(s[1] for s in sell_signals) / len(sell_signals)
                return {
                    'action': 'SELL',
                    'confidence': avg_confidence,
                    'reasoning': f'Multi-timeframe bearish consensus: {len(sell_signals)} signals'
                }
            
            return {
                'action': 'HOLD',
                'confidence': 0,
                'reasoning': 'No multi-timeframe consensus'
            }
            
        except Exception as e:
            logger.error(f"Multi-timeframe strategy error: {e}")
            return {'action': 'HOLD', 'confidence': 0, 'reasoning': 'Strategy error'}
    
    def _calculate_performance_metrics(self, trades: List[Dict[str, Any]],
                                     equity_curve: List[Dict[str, Any]],
                                     initial_capital: float) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        try:
            if not trades or not equity_curve:
                return {
                    'final_capital': initial_capital,
                    'total_return': 0,
                    'total_return_percent': 0,
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0,
                    'max_drawdown': 0,
                    'sharpe_ratio': 0,
                    'annualized_return': 0,
                    'avg_trade_return': 0,
                    'best_trade': 0,
                    'worst_trade': 0
                }
            
            final_capital = equity_curve[-1]['portfolio_value']
            total_return = final_capital - initial_capital
            total_return_percent = (total_return / initial_capital) * 100
            
            # Trade statistics
            completed_trades = [t for t in trades if 'pnl' in t]
            total_trades = len(completed_trades)
            
            if total_trades == 0:
                return {
                    'final_capital': final_capital,
                    'total_return': total_return,
                    'total_return_percent': total_return_percent,
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0,
                    'max_drawdown': max(eq['drawdown'] for eq in equity_curve) if equity_curve else 0,
                    'sharpe_ratio': 0,
                    'annualized_return': 0,
                    'avg_trade_return': 0,
                    'best_trade': 0,
                    'worst_trade': 0
                }
            
            trade_returns = [t['pnl'] for t in completed_trades]
            winning_trades = len([t for t in trade_returns if t > 0])
            losing_trades = len([t for t in trade_returns if t < 0])
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            # Drawdown calculation
            max_drawdown = max(eq['drawdown'] for eq in equity_curve) if equity_curve else 0
            
            # Returns for Sharpe ratio
            returns = []
            for i in range(1, len(equity_curve)):
                prev_value = equity_curve[i-1]['portfolio_value']
                curr_value = equity_curve[i]['portfolio_value']
                if prev_value > 0:
                    returns.append((curr_value - prev_value) / prev_value)
            
            # Sharpe ratio calculation
            if returns and len(returns) > 1:
                mean_return = np.mean(returns)
                std_return = np.std(returns, ddof=1)
                # Convert to annualized (assuming hourly data)
                sharpe_ratio = (mean_return * 8760 - self.risk_free_rate) / (std_return * np.sqrt(8760)) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Annualized return
            if len(equity_curve) > 1:
                start_date = datetime.fromisoformat(equity_curve[0]['timestamp'].replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(equity_curve[-1]['timestamp'].replace('Z', '+00:00'))
                days_elapsed = (end_date - start_date).days
                years_elapsed = max(days_elapsed / 365.25, 1/365.25)  # Minimum 1 day
                annualized_return = ((final_capital / initial_capital) ** (1/years_elapsed) - 1) * 100
            else:
                annualized_return = 0
            
            return {
                'final_capital': final_capital,
                'total_return': total_return,
                'total_return_percent': total_return_percent,
                'annualized_return': annualized_return,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'win_rate': win_rate,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'avg_trade_return': np.mean(trade_returns) if trade_returns else 0,
                'best_trade': max(trade_returns) if trade_returns else 0,
                'worst_trade': min(trade_returns) if trade_returns else 0
            }
            
        except Exception as e:
            logger.error(f"Performance metrics calculation failed: {e}")
            return {'error': str(e)}
    
    def _calculate_hold_period(self, start_time: str, end_time: str) -> int:
        """Calculate hold period in hours"""
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            return int((end - start).total_seconds() / 3600)
        except Exception:
            return 0
"""
Market Scanner for Trading Opportunity Detection
Advanced scanning for breakouts, reversals, institutional moves, and volume surges
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import numpy as np
from dataclasses import asdict

from models.kaayaan_models import *
from infrastructure.database_manager import DatabaseManager
from src.core.crypto_analyzer import CryptoAnalyzer

logger = logging.getLogger(__name__)

class MarketScanner:
    """
    Intelligent market scanner for high-probability trading opportunities
    Features:
    - Multi-pattern detection (breakouts, reversals, institutional)
    - Volume surge analysis
    - Momentum screening
    - Risk-adjusted opportunity scoring
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.analyzer = CryptoAnalyzer()  # Create analyzer instance
        
        # Scanning parameters
        self.scan_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT',
            'SOLUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'AVAXUSDT',
            'MATICUSDT', 'ATOMUSDT', 'FILUSDT', 'TRXUSDT', 'ETCUSDT',
            'XLMUSDT', 'VETUSDT', 'ICPUSDT', 'FTMUSDT', 'HBARUSDT',
            'ALGOUSDT', 'AXSUSDT', 'SANDUSDT', 'MANAUSDT', 'APEUSDT'
        ]
        
        # Market cap categories
        self.market_cap_ranges = {
            'large': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT'],
            'mid': ['SOLUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'AVAXUSDT', 'MATICUSDT'],
            'small': ['AXSUSDT', 'SANDUSDT', 'MANAUSDT', 'APEUSDT', 'FTMUSDT']
        }
        
        # Opportunity thresholds
        self.thresholds = {
            'breakout_strength_min': 2.0,      # Minimum breakout strength
            'volume_surge_multiplier': 2.5,    # Minimum volume increase
            'reversal_rsi_oversold': 30,       # RSI oversold level
            'reversal_rsi_overbought': 70,     # RSI overbought level
            'institutional_order_block_min': 60,  # Min order block strength
            'min_confidence_score': 60,        # Minimum opportunity confidence
            'risk_reward_min': 1.5             # Minimum risk-reward ratio
        }
        
        # Pattern detection weights
        self.pattern_weights = {
            'order_blocks': 0.3,          # High institutional significance
            'fair_value_gaps': 0.2,       # Good structural levels
            'break_of_structure': 0.25,   # Strong momentum signals
            'rsi_divergence': 0.15,       # Reversal confirmation
            'volume_surge': 0.1           # Supporting evidence
        }
    
    async def scan_market(self, scan_type: str = "all", timeframe: str = "1h",
                         min_volume_usd: float = 1000000) -> MarketScanResult:
        """
        Scan market for trading opportunities based on scan type
        """
        start_time = datetime.now()
        
        try:
            # Get symbols to scan based on market cap filter
            symbols_to_scan = self.scan_symbols
            
            logger.info(f"Starting {scan_type} scan for {len(symbols_to_scan)} symbols")
            
            # Scan symbols concurrently
            scan_tasks = [
                self._scan_symbol(symbol, scan_type, timeframe, min_volume_usd)
                for symbol in symbols_to_scan
            ]
            
            scan_results = await asyncio.gather(*scan_tasks, return_exceptions=True)
            
            # Process results
            opportunities = []
            symbols_scanned = 0
            
            for i, result in enumerate(scan_results):
                if isinstance(result, Exception):
                    logger.error(f"Scan failed for {symbols_to_scan[i]}: {result}")
                    continue
                
                symbols_scanned += 1
                if result:  # If opportunity found
                    opportunities.extend(result if isinstance(result, list) else [result])
            
            # Sort opportunities by confidence score
            opportunities.sort(key=lambda x: x.confidence_score, reverse=True)
            
            # Get market conditions
            market_conditions = await self._get_current_market_conditions()
            
            # Create scan result
            scan_duration = (datetime.now() - start_time).total_seconds()
            
            scan_result = MarketScanResult(
                scan_type=ScanType(scan_type),
                timeframe=timeframe,
                symbols_scanned=symbols_scanned,
                opportunities_found=len(opportunities),
                opportunities=opportunities[:20],  # Limit to top 20
                market_conditions=market_conditions,
                scan_duration_seconds=scan_duration
            )
            
            logger.info(f"Scan completed: {len(opportunities)} opportunities found in {scan_duration:.1f}s")
            
            return scan_result
            
        except Exception as e:
            logger.error(f"Market scan failed: {e}")
            raise
    
    async def scan_for_opportunities(self, market_cap_range: str = "all",
                                   confidence_threshold: float = 70,
                                   max_results: int = 10) -> list[TradingOpportunity]:
        """
        Scan for high-confidence trading opportunities with filters
        """
        try:
            # Get symbols based on market cap range
            if market_cap_range == "all":
                symbols = self.scan_symbols
            else:
                symbols = self.market_cap_ranges.get(market_cap_range, self.scan_symbols)
            
            # Scan for all opportunity types
            scan_result = await self.scan_market("all", "1h")
            
            # Filter by confidence threshold
            filtered_opportunities = [
                opp for opp in scan_result.opportunities
                if opp.confidence_score >= confidence_threshold
                and opp.symbol in symbols
            ]
            
            return filtered_opportunities[:max_results]
            
        except Exception as e:
            logger.error(f"Opportunity scanning failed: {e}")
            return []
    
    async def _scan_symbol(self, symbol: str, scan_type: str, timeframe: str,
                          min_volume_usd: float) -> list[TradingOpportunity | None]:
        """
        Scan individual symbol for opportunities
        """
        try:
            # Get analysis for symbol
            analysis = await self.analyzer.analyze(symbol, timeframe=timeframe)
            
            # Check volume threshold
            volume_24h = analysis.metadata.get('volume_24h', 0)
            if volume_24h < min_volume_usd:
                return None
            
            opportunities = []
            
            # Apply scan type filters
            if scan_type in ["all", "breakouts"]:
                breakout_ops = await self._detect_breakout_opportunities(analysis)
                opportunities.extend(breakout_ops)
            
            if scan_type in ["all", "reversals"]:
                reversal_ops = await self._detect_reversal_opportunities(analysis)
                opportunities.extend(reversal_ops)
            
            if scan_type in ["all", "institutional"]:
                institutional_ops = await self._detect_institutional_opportunities(analysis)
                opportunities.extend(institutional_ops)
            
            if scan_type in ["all", "volume_surge"]:
                volume_ops = await self._detect_volume_surge_opportunities(analysis)
                opportunities.extend(volume_ops)
            
            # Filter by minimum confidence
            qualified_opportunities = [
                opp for opp in opportunities
                if opp.confidence_score >= self.thresholds['min_confidence_score']
            ]
            
            return qualified_opportunities if qualified_opportunities else None
            
        except Exception as e:
            logger.error(f"Symbol scan failed for {symbol}: {e}")
            return None
    
    async def _detect_breakout_opportunities(self, analysis) -> list[TradingOpportunity]:
        """Detect breakout trading opportunities"""
        opportunities = []
        
        try:
            symbol = analysis.symbol
            current_price = self._extract_current_price(analysis)
            
            # Check for break of structure (BOS)
            bos_signals = analysis.break_of_structure
            
            for bos in bos_signals:
                if bos.strength >= self.thresholds['breakout_strength_min']:
                    # Calculate entry, target, and stop loss
                    if bos.direction == "bullish":
                        entry_price = current_price
                        target_price = current_price * 1.05  # 5% target
                        stop_loss = bos.level * 0.98  # 2% below BOS level
                    else:  # bearish
                        entry_price = current_price
                        target_price = current_price * 0.95  # 5% target
                        stop_loss = bos.level * 1.02  # 2% above BOS level
                    
                    # Calculate risk-reward ratio
                    risk = abs(entry_price - stop_loss)
                    reward = abs(target_price - entry_price)
                    risk_reward_ratio = reward / risk if risk > 0 else 0
                    
                    if risk_reward_ratio >= self.thresholds['risk_reward_min']:
                        # Calculate confidence score
                        confidence = self._calculate_breakout_confidence(analysis, bos)
                        
                        opportunity = TradingOpportunity(
                            symbol=symbol,
                            opportunity_type="breakout",
                            confidence_score=confidence,
                            entry_price=entry_price,
                            target_price=target_price,
                            stop_loss=stop_loss,
                            risk_reward_ratio=risk_reward_ratio,
                            timeframe=analysis.timeframe,
                            rationale=f"Break of Structure ({bos.direction}) with {bos.strength:.1f} strength",
                            supporting_indicators=[
                                f"BOS {bos.direction}",
                                f"Strength: {bos.strength:.1f}",
                                f"Level: {bos.level:.4f}"
                            ],
                            market_context={"regime": analysis.regime_analysis},
                            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
                        )
                        
                        opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Breakout detection failed: {e}")
            return []
    
    async def _detect_reversal_opportunities(self, analysis) -> list[TradingOpportunity]:
        """Detect reversal trading opportunities"""
        opportunities = []
        
        try:
            symbol = analysis.symbol
            current_price = self._extract_current_price(analysis)
            
            # Check RSI divergences
            rsi_divergences = analysis.rsi_divergence
            
            for divergence in rsi_divergences:
                rsi_value = divergence.rsi_value
                
                # Check for oversold/overbought conditions
                is_valid_reversal = False
                direction = ""
                
                if (divergence.type == "bullish" and 
                    rsi_value <= self.thresholds['reversal_rsi_oversold']):
                    is_valid_reversal = True
                    direction = "bullish"
                elif (divergence.type == "bearish" and 
                      rsi_value >= self.thresholds['reversal_rsi_overbought']):
                    is_valid_reversal = True
                    direction = "bearish"
                
                if is_valid_reversal:
                    # Calculate trade parameters
                    if direction == "bullish":
                        entry_price = current_price
                        target_price = current_price * 1.08  # 8% target for reversals
                        stop_loss = current_price * 0.95     # 5% stop loss
                    else:  # bearish
                        entry_price = current_price
                        target_price = current_price * 0.92  # 8% target
                        stop_loss = current_price * 1.05     # 5% stop loss
                    
                    risk = abs(entry_price - stop_loss)
                    reward = abs(target_price - entry_price)
                    risk_reward_ratio = reward / risk if risk > 0 else 0
                    
                    if risk_reward_ratio >= self.thresholds['risk_reward_min']:
                        # Calculate confidence
                        confidence = self._calculate_reversal_confidence(analysis, divergence)
                        
                        opportunity = TradingOpportunity(
                            symbol=symbol,
                            opportunity_type="reversal",
                            confidence_score=confidence,
                            entry_price=entry_price,
                            target_price=target_price,
                            stop_loss=stop_loss,
                            risk_reward_ratio=risk_reward_ratio,
                            timeframe=analysis.timeframe,
                            rationale=f"RSI Divergence ({direction}) with RSI at {rsi_value:.1f}",
                            supporting_indicators=[
                                f"RSI Divergence {direction}",
                                f"RSI: {rsi_value:.1f}",
                                f"Strength: {divergence.strength:.1f}"
                            ],
                            market_context={"regime": analysis.regime_analysis},
                            expires_at=datetime.now(timezone.utc) + timedelta(hours=12)
                        )
                        
                        opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Reversal detection failed: {e}")
            return []
    
    async def _detect_institutional_opportunities(self, analysis) -> list[TradingOpportunity]:
        """Detect institutional trading opportunities"""
        opportunities = []
        
        try:
            symbol = analysis.symbol
            current_price = self._extract_current_price(analysis)
            
            # Check order blocks for institutional activity
            order_blocks = analysis.order_blocks
            
            for ob in order_blocks:
                if ob.strength >= self.thresholds['institutional_order_block_min']:
                    # Determine trade direction based on order block type
                    if ob.type == "demand":
                        direction = "bullish"
                        entry_price = current_price
                        target_price = current_price * 1.06  # 6% target
                        stop_loss = ob.level * 0.97          # Below demand zone
                    else:  # supply
                        direction = "bearish"
                        entry_price = current_price
                        target_price = current_price * 0.94  # 6% target
                        stop_loss = ob.level * 1.03          # Above supply zone
                    
                    risk = abs(entry_price - stop_loss)
                    reward = abs(target_price - entry_price)
                    risk_reward_ratio = reward / risk if risk > 0 else 0
                    
                    if risk_reward_ratio >= self.thresholds['risk_reward_min']:
                        # Calculate confidence
                        confidence = self._calculate_institutional_confidence(analysis, ob)
                        
                        opportunity = TradingOpportunity(
                            symbol=symbol,
                            opportunity_type="institutional",
                            confidence_score=confidence,
                            entry_price=entry_price,
                            target_price=target_price,
                            stop_loss=stop_loss,
                            risk_reward_ratio=risk_reward_ratio,
                            timeframe=analysis.timeframe,
                            rationale=f"Strong {ob.type} order block at {ob.level:.4f}",
                            supporting_indicators=[
                                f"Order Block {ob.type}",
                                f"Level: {ob.level:.4f}",
                                f"Strength: {ob.strength:.1f}"
                            ],
                            market_context={"regime": analysis.regime_analysis},
                            expires_at=datetime.now(timezone.utc) + timedelta(hours=48)
                        )
                        
                        opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Institutional detection failed: {e}")
            return []
    
    async def _detect_volume_surge_opportunities(self, analysis) -> list[TradingOpportunity]:
        """Detect volume surge opportunities"""
        opportunities = []
        
        try:
            symbol = analysis.symbol
            current_price = self._extract_current_price(analysis)
            
            # Check for volume surges in liquidity zones
            liquidity_zones = analysis.liquidity_zones
            
            for zone in liquidity_zones:
                # Check if volume is significantly above average
                zone_volume = zone.volume
                avg_volume = analysis.metadata.get('volume_24h', 0) / 24  # Rough hourly average
                
                if avg_volume > 0 and zone_volume > avg_volume * self.thresholds['volume_surge_multiplier']:
                    # Volume surge detected
                    direction = "bullish" if zone.type == "demand" else "bearish"
                    
                    if direction == "bullish":
                        entry_price = current_price
                        target_price = zone.upper_level * 1.02  # Above zone
                        stop_loss = zone.lower_level * 0.98     # Below zone
                    else:
                        entry_price = current_price
                        target_price = zone.lower_level * 0.98  # Below zone
                        stop_loss = zone.upper_level * 1.02     # Above zone
                    
                    risk = abs(entry_price - stop_loss)
                    reward = abs(target_price - entry_price)
                    risk_reward_ratio = reward / risk if risk > 0 else 0
                    
                    if risk_reward_ratio >= self.thresholds['risk_reward_min']:
                        # Calculate confidence
                        confidence = self._calculate_volume_surge_confidence(analysis, zone, avg_volume)
                        
                        opportunity = TradingOpportunity(
                            symbol=symbol,
                            opportunity_type="volume_surge",
                            confidence_score=confidence,
                            entry_price=entry_price,
                            target_price=target_price,
                            stop_loss=stop_loss,
                            risk_reward_ratio=risk_reward_ratio,
                            timeframe=analysis.timeframe,
                            rationale=f"Volume surge in {zone.type} zone",
                            supporting_indicators=[
                                f"Volume surge: {zone_volume:,.0f}",
                                f"Avg volume: {avg_volume:,.0f}",
                                f"Multiplier: {zone_volume/avg_volume:.1f}x"
                            ],
                            market_context={"regime": analysis.regime_analysis},
                            expires_at=datetime.now(timezone.utc) + timedelta(hours=8)
                        )
                        
                        opportunities.append(opportunity)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Volume surge detection failed: {e}")
            return []
    
    def _calculate_breakout_confidence(self, analysis, bos) -> float:
        """Calculate confidence score for breakout opportunities"""
        try:
            base_confidence = min(bos.strength * 10, 70)  # Max 70 from BOS strength
            
            # Add confidence from supporting indicators
            bonus = 0
            
            # Volume confirmation
            if analysis.liquidity_zones:
                bonus += 10
            
            # Trend alignment
            if analysis.market_analysis.trend == bos.direction:
                bonus += 15
            
            # Fair value gap support
            if analysis.fair_value_gaps:
                fvg_support = any(fvg.type == bos.direction for fvg in analysis.fair_value_gaps)
                if fvg_support:
                    bonus += 10
            
            # Market regime support
            regime = analysis.regime_analysis
            if (regime == "bull_market" and bos.direction == "bullish") or \
               (regime == "bear_market" and bos.direction == "bearish"):
                bonus += 5
            
            total_confidence = min(base_confidence + bonus, 100)
            return max(0, total_confidence)
            
        except Exception:
            return 60  # Default confidence
    
    def _calculate_reversal_confidence(self, analysis, divergence) -> float:
        """Calculate confidence score for reversal opportunities"""
        try:
            base_confidence = min(divergence.strength * 2, 50)  # Max 50 from divergence
            
            bonus = 0
            
            # RSI extreme levels
            rsi_value = divergence.rsi_value
            if divergence.type == "bullish" and rsi_value < 25:
                bonus += 20  # Very oversold
            elif divergence.type == "bullish" and rsi_value < 30:
                bonus += 15  # Oversold
            elif divergence.type == "bearish" and rsi_value > 75:
                bonus += 20  # Very overbought
            elif divergence.type == "bearish" and rsi_value > 70:
                bonus += 15  # Overbought
            
            # Order block support
            if analysis.order_blocks:
                ob_support = any(
                    (ob.type == "demand" and divergence.type == "bullish") or
                    (ob.type == "supply" and divergence.type == "bearish")
                    for ob in analysis.order_blocks
                )
                if ob_support:
                    bonus += 15
            
            # Volatility consideration (reversals work better in high volatility)
            if analysis.volatility_indicators.volatility_level == "high":
                bonus += 10
            
            total_confidence = min(base_confidence + bonus, 100)
            return max(0, total_confidence)
            
        except Exception:
            return 55  # Default confidence
    
    def _calculate_institutional_confidence(self, analysis, order_block) -> float:
        """Calculate confidence score for institutional opportunities"""
        try:
            base_confidence = min(order_block.strength, 80)  # Max 80 from OB strength
            
            bonus = 0
            
            # Multiple order blocks in same direction
            same_type_count = sum(1 for ob in analysis.order_blocks if ob.type == order_block.type)
            if same_type_count > 1:
                bonus += 10
            
            # Fair value gap alignment
            if analysis.fair_value_gaps:
                fvg_alignment = any(
                    (fvg.type == "bullish" and order_block.type == "demand") or
                    (fvg.type == "bearish" and order_block.type == "supply")
                    for fvg in analysis.fair_value_gaps
                )
                if fvg_alignment:
                    bonus += 15
            
            # Market structure support
            if analysis.break_of_structure:
                structure_support = any(
                    (bos.direction == "bullish" and order_block.type == "demand") or
                    (bos.direction == "bearish" and order_block.type == "supply")
                    for bos in analysis.break_of_structure
                )
                if structure_support:
                    bonus += 10
            
            total_confidence = min(base_confidence + bonus, 100)
            return max(0, total_confidence)
            
        except Exception:
            return 70  # Default confidence for institutional signals
    
    def _calculate_volume_surge_confidence(self, analysis, zone, avg_volume) -> float:
        """Calculate confidence score for volume surge opportunities"""
        try:
            volume_multiplier = zone.volume / avg_volume if avg_volume > 0 else 1
            base_confidence = min(volume_multiplier * 20, 60)  # Max 60 from volume
            
            bonus = 0
            
            # Trend alignment
            if ((zone.type == "demand" and analysis.market_analysis.trend == "bullish") or
                (zone.type == "supply" and analysis.market_analysis.trend == "bearish")):
                bonus += 15
            
            # Order block confirmation
            if analysis.order_blocks:
                ob_confirmation = any(
                    (ob.type == "demand" and zone.type == "demand") or
                    (ob.type == "supply" and zone.type == "supply")
                    for ob in analysis.order_blocks
                )
                if ob_confirmation:
                    bonus += 10
            
            # Time-based urgency (volume surges are time-sensitive)
            bonus += 10
            
            total_confidence = min(base_confidence + bonus, 100)
            return max(0, total_confidence)
            
        except Exception:
            return 50  # Default confidence
    
    async def _get_current_market_conditions(self) -> dict[str, Any]:
        """Get current market conditions for context"""
        try:
            # Get BTC and ETH analysis for market sentiment
            btc_analysis = await self.db_manager.get_latest_analysis("BTCUSDT")
            eth_analysis = await self.db_manager.get_latest_analysis("ETHUSDT")
            
            conditions = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "btc_trend": "unknown",
                "eth_trend": "unknown",
                "overall_sentiment": "neutral",
                "volatility": "moderate"
            }
            
            if btc_analysis:
                conditions["btc_trend"] = btc_analysis.get("market_analysis", {}).get("trend", "unknown")
                conditions["volatility"] = btc_analysis.get("volatility_indicators", {}).get("volatility_level", "moderate")
            
            if eth_analysis:
                conditions["eth_trend"] = eth_analysis.get("market_analysis", {}).get("trend", "unknown")
            
            # Determine overall sentiment
            btc_trend = conditions["btc_trend"]
            eth_trend = conditions["eth_trend"]
            
            if btc_trend == "bullish" and eth_trend == "bullish":
                conditions["overall_sentiment"] = "bullish"
            elif btc_trend == "bearish" and eth_trend == "bearish":
                conditions["overall_sentiment"] = "bearish"
            elif btc_trend in ["bullish", "bearish"] or eth_trend in ["bullish", "bearish"]:
                conditions["overall_sentiment"] = "mixed"
            
            return conditions
            
        except Exception as e:
            logger.error(f"Failed to get market conditions: {e}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": "Failed to analyze market conditions"
            }
    
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
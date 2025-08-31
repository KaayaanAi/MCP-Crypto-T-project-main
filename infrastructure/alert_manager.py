"""
Alert Manager for WhatsApp Notifications
Intelligent alert system with condition evaluation and spam prevention
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
import re
from dataclasses import asdict

from models.kaayaan_models import *
from infrastructure.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class AlertManager:
    """
    Intelligent alert management system with WhatsApp integration
    Features:
    - Condition-based alerts (price, technical indicators, volume)
    - Spam prevention with cooldowns
    - Template-based messaging
    - Alert history and analytics
    """
    
    def __init__(self, whatsapp_base_url: str, whatsapp_session: str, 
                 db_manager: DatabaseManager):
        self.whatsapp_base_url = whatsapp_base_url.rstrip('/')
        self.whatsapp_session = whatsapp_session
        self.db_manager = db_manager
        
        # Alert condition evaluators
        self.condition_evaluators = {
            'price': self._evaluate_price_condition,
            'rsi': self._evaluate_rsi_condition,
            'volume': self._evaluate_volume_condition,
            'technical': self._evaluate_technical_condition
        }
        
        # Message templates
        self.message_templates = {
            'price_alert': "🚨 {symbol} Price Alert\n💰 Current: ${current_price:,.2f}\n📊 Condition: {condition}\n⏰ {timestamp}",
            'technical_alert': "📈 {symbol} Technical Alert\n🔍 Signal: {signal}\n💪 Strength: {strength}/100\n⏰ {timestamp}",
            'volume_alert': "📊 {symbol} Volume Alert\n🔥 Volume: {volume:,.0f}\n📈 Change: {volume_change:+.1f}%\n⏰ {timestamp}",
            'risk_alert': "⚠️ {symbol} Risk Alert\n🛡️ Level: {risk_level}\n📉 Details: {details}\n⏰ {timestamp}"
        }
        
        # Rate limiting
        self.rate_limits = {}
        self.max_alerts_per_hour = 10
        self.global_cooldown_minutes = 5
        
    async def create_alert(self, alert_type: str, symbol: str, 
                          condition: str, phone_number: str,
                          message_template: Optional[str] = None,
                          cooldown_minutes: int = 60,
                          expires_hours: int = 24) -> Dict[str, Any]:
        """Create a new trading alert"""
        try:
            # Validate inputs
            if not self._validate_phone_number(phone_number):
                raise ValueError("Invalid phone number format")
            
            if not self._validate_condition(condition, alert_type):
                raise ValueError("Invalid alert condition")
            
            # Create alert object
            alert = Alert(
                alert_type=AlertType(alert_type),
                symbol=symbol.upper(),
                condition=condition,
                phone_number=phone_number,
                message_template=message_template,
                cooldown_minutes=cooldown_minutes,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_hours)
            )
            
            # Save to database
            alert_id = await self.db_manager.save_alert(alert)
            
            # Log the creation
            await self.db_manager.log_action(AuditLog(
                action="create_alert",
                symbol=symbol,
                parameters={
                    "alert_type": alert_type,
                    "condition": condition,
                    "phone_number": phone_number[-4:]  # Only log last 4 digits for privacy
                },
                result={"alert_id": alert_id},
                success=True
            ))
            
            logger.info(f"Alert created for {symbol}: {condition}")
            
            return {
                "alert_id": alert_id,
                "status": "created",
                "message": f"Alert created for {symbol} with condition: {condition}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            await self.db_manager.log_action(AuditLog(
                action="create_alert",
                symbol=symbol,
                parameters={"alert_type": alert_type, "condition": condition},
                result={"error": str(e)},
                success=False,
                error_message=str(e)
            ))
            raise
    
    async def list_alerts(self, phone_number: Optional[str] = None,
                         symbol: Optional[str] = None,
                         status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List alerts with optional filtering"""
        try:
            # Get alerts from database
            alerts = await self.db_manager.get_active_alerts(symbol)
            
            # Apply filters
            filtered_alerts = []
            for alert in alerts:
                if phone_number and alert.get('phone_number') != phone_number:
                    continue
                if status and alert.get('status') != status:
                    continue
                
                # Remove sensitive information
                safe_alert = {**alert}
                if 'phone_number' in safe_alert:
                    safe_alert['phone_number'] = safe_alert['phone_number'][-4:]
                
                filtered_alerts.append(safe_alert)
            
            return filtered_alerts
            
        except Exception as e:
            logger.error(f"Failed to list alerts: {e}")
            return []
    
    async def delete_alert(self, alert_id: str) -> Dict[str, Any]:
        """Delete/disable an alert"""
        try:
            success = await self.db_manager.update_alert_status(
                alert_id, 
                AlertStatus.DISABLED
            )
            
            if success:
                await self.db_manager.log_action(AuditLog(
                    action="delete_alert",
                    parameters={"alert_id": alert_id},
                    result={"success": True},
                    success=True
                ))
                
                return {
                    "status": "deleted",
                    "message": f"Alert {alert_id} has been disabled"
                }
            else:
                return {
                    "status": "not_found",
                    "message": f"Alert {alert_id} not found"
                }
                
        except Exception as e:
            logger.error(f"Failed to delete alert {alert_id}: {e}")
            raise
    
    async def check_alert_conditions(self, analysis: Union[EnhancedAnalysisResult, Dict[str, Any]]):
        """Check all active alerts against current analysis"""
        try:
            # Convert analysis to dict if needed
            if isinstance(analysis, EnhancedAnalysisResult):
                analysis_dict = asdict(analysis)
            else:
                analysis_dict = analysis
            
            symbol = analysis_dict.get('symbol', '').upper()
            
            # Get active alerts for this symbol
            alerts = await self.db_manager.get_active_alerts(symbol)
            
            triggered_alerts = []
            
            for alert_data in alerts:
                try:
                    alert = Alert(**alert_data)
                    
                    # Check rate limiting
                    if self._is_rate_limited(alert):
                        continue
                    
                    # Evaluate condition
                    should_trigger = await self._evaluate_alert_condition(
                        alert, analysis_dict
                    )
                    
                    if should_trigger:
                        # Send notification
                        await self._send_alert_notification(alert, analysis_dict)
                        
                        # Update alert status
                        await self.db_manager.update_alert_status(
                            alert.id,
                            AlertStatus.TRIGGERED,
                            datetime.now(timezone.utc)
                        )
                        
                        triggered_alerts.append(alert.id)
                        
                        # Update rate limiting
                        self._update_rate_limit(alert)
                        
                except Exception as e:
                    logger.error(f"Failed to process alert {alert_data.get('id', 'unknown')}: {e}")
                    continue
            
            if triggered_alerts:
                logger.info(f"Triggered {len(triggered_alerts)} alerts for {symbol}")
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"Failed to check alert conditions: {e}")
            return []
    
    async def _evaluate_alert_condition(self, alert: Alert, 
                                      analysis: Dict[str, Any]) -> bool:
        """Evaluate if alert condition is met"""
        try:
            alert_type = alert.alert_type.value
            condition = alert.condition
            
            if alert_type in self.condition_evaluators:
                return await self.condition_evaluators[alert_type](
                    condition, analysis
                )
            else:
                logger.warning(f"Unknown alert type: {alert_type}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to evaluate condition '{alert.condition}': {e}")
            return False
    
    async def _evaluate_price_condition(self, condition: str, 
                                      analysis: Dict[str, Any]) -> bool:
        """Evaluate price-based conditions"""
        try:
            # Parse condition like "price > 50000" or "price <= 45000"
            pattern = r'price\s*(>=|<=|>|<|==|!=)\s*(\d+(?:\.\d+)?)'
            match = re.match(pattern, condition.lower())
            
            if not match:
                logger.error(f"Invalid price condition: {condition}")
                return False
            
            operator, threshold_str = match.groups()
            threshold = float(threshold_str)
            
            # Get current price from analysis
            current_price = self._extract_current_price(analysis)
            if current_price is None:
                return False
            
            # Evaluate condition
            if operator == '>':
                return current_price > threshold
            elif operator == '>=':
                return current_price >= threshold
            elif operator == '<':
                return current_price < threshold
            elif operator == '<=':
                return current_price <= threshold
            elif operator == '==':
                return abs(current_price - threshold) < 0.01  # Small tolerance
            elif operator == '!=':
                return abs(current_price - threshold) >= 0.01
            
            return False
            
        except Exception as e:
            logger.error(f"Price condition evaluation error: {e}")
            return False
    
    async def _evaluate_rsi_condition(self, condition: str, 
                                    analysis: Dict[str, Any]) -> bool:
        """Evaluate RSI-based conditions"""
        try:
            # Parse condition like "rsi < 30" or "rsi > 70"
            pattern = r'rsi\s*(>=|<=|>|<)\s*(\d+(?:\.\d+)?)'
            match = re.match(pattern, condition.lower())
            
            if not match:
                return False
            
            operator, threshold_str = match.groups()
            threshold = float(threshold_str)
            
            # Extract RSI from analysis
            rsi_value = self._extract_rsi_value(analysis)
            if rsi_value is None:
                return False
            
            # Evaluate condition
            if operator == '>':
                return rsi_value > threshold
            elif operator == '>=':
                return rsi_value >= threshold
            elif operator == '<':
                return rsi_value < threshold
            elif operator == '<=':
                return rsi_value <= threshold
            
            return False
            
        except Exception as e:
            logger.error(f"RSI condition evaluation error: {e}")
            return False
    
    async def _evaluate_volume_condition(self, condition: str, 
                                       analysis: Dict[str, Any]) -> bool:
        """Evaluate volume-based conditions"""
        try:
            # Parse condition like "volume_spike > 200%" or "volume > 1000000"
            if 'volume_spike' in condition.lower():
                # Volume spike condition
                pattern = r'volume_spike\s*>\s*(\d+(?:\.\d+)?)%?'
                match = re.match(pattern, condition.lower())
                if not match:
                    return False
                
                threshold_percent = float(match.group(1))
                
                # Check for volume spike in analysis
                volume_change = self._extract_volume_change(analysis)
                return volume_change is not None and volume_change > threshold_percent
            
            else:
                # Absolute volume condition
                pattern = r'volume\s*(>=|<=|>|<)\s*(\d+(?:\.\d+)?)'
                match = re.match(pattern, condition.lower())
                if not match:
                    return False
                
                operator, threshold_str = match.groups()
                threshold = float(threshold_str)
                
                current_volume = self._extract_current_volume(analysis)
                if current_volume is None:
                    return False
                
                if operator == '>':
                    return current_volume > threshold
                elif operator == '>=':
                    return current_volume >= threshold
                elif operator == '<':
                    return current_volume < threshold
                elif operator == '<=':
                    return current_volume <= threshold
            
            return False
            
        except Exception as e:
            logger.error(f"Volume condition evaluation error: {e}")
            return False
    
    async def _evaluate_technical_condition(self, condition: str, 
                                          analysis: Dict[str, Any]) -> bool:
        """Evaluate technical indicator conditions"""
        try:
            condition_lower = condition.lower()
            
            # Check for specific technical patterns
            if 'bullish_divergence' in condition_lower:
                divergences = analysis.get('rsi_divergence', [])
                return any(d.get('type') == 'bullish' for d in divergences)
            
            elif 'bearish_divergence' in condition_lower:
                divergences = analysis.get('rsi_divergence', [])
                return any(d.get('type') == 'bearish' for d in divergences)
            
            elif 'order_block' in condition_lower:
                order_blocks = analysis.get('order_blocks', [])
                if 'demand' in condition_lower:
                    return any(ob.get('type') == 'demand' for ob in order_blocks)
                elif 'supply' in condition_lower:
                    return any(ob.get('type') == 'supply' for ob in order_blocks)
                else:
                    return len(order_blocks) > 0
            
            elif 'break_of_structure' in condition_lower or 'bos' in condition_lower:
                bos_signals = analysis.get('break_of_structure', [])
                if 'bullish' in condition_lower:
                    return any(bos.get('direction') == 'bullish' for bos in bos_signals)
                elif 'bearish' in condition_lower:
                    return any(bos.get('direction') == 'bearish' for bos in bos_signals)
                else:
                    return len(bos_signals) > 0
            
            elif 'fair_value_gap' in condition_lower or 'fvg' in condition_lower:
                fvgs = analysis.get('fair_value_gaps', [])
                return len(fvgs) > 0
            
            elif 'trend_change' in condition_lower:
                market_analysis = analysis.get('market_analysis', {})
                trend = market_analysis.get('trend', '')
                
                if 'bullish' in condition_lower:
                    return trend == 'bullish'
                elif 'bearish' in condition_lower:
                    return trend == 'bearish'
                elif 'sideways' in condition_lower:
                    return trend == 'sideways'
            
            return False
            
        except Exception as e:
            logger.error(f"Technical condition evaluation error: {e}")
            return False
    
    async def _send_alert_notification(self, alert: Alert, analysis: Dict[str, Any]):
        """Send WhatsApp notification for triggered alert"""
        try:
            # Generate message
            message = self._generate_alert_message(alert, analysis)
            
            # Send via WhatsApp API
            success = await self._send_whatsapp_message(alert.phone_number, message)
            
            if success:
                logger.info(f"Alert notification sent to {alert.phone_number[-4:]}")
                
                # Log successful notification
                await self.db_manager.log_action(AuditLog(
                    action="send_alert",
                    symbol=alert.symbol,
                    parameters={
                        "alert_type": alert.alert_type.value,
                        "condition": alert.condition,
                        "phone_number": alert.phone_number[-4:]
                    },
                    result={"success": True},
                    success=True
                ))
            else:
                logger.error(f"Failed to send alert to {alert.phone_number[-4:]}")
                
        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")
    
    def _generate_alert_message(self, alert: Alert, analysis: Dict[str, Any]) -> str:
        """Generate formatted alert message"""
        try:
            # Use custom template if provided
            if alert.message_template:
                template = alert.message_template
            else:
                # Use default template based on alert type
                template = self.message_templates.get(
                    f"{alert.alert_type.value}_alert",
                    self.message_templates['technical_alert']
                )
            
            # Prepare template variables
            variables = {
                'symbol': alert.symbol,
                'condition': alert.condition,
                'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
                'current_price': self._extract_current_price(analysis) or 0,
                'volume': self._extract_current_volume(analysis) or 0,
                'volume_change': self._extract_volume_change(analysis) or 0,
                'signal': self._extract_signal_description(analysis),
                'strength': analysis.get('intelligent_score', 50),
                'risk_level': analysis.get('regime_analysis', 'unknown'),
                'details': alert.condition
            }
            
            # Format message
            message = template.format(**variables)
            
            # Add analysis link if available
            message += f"\n\n📱 Full Analysis: {self.whatsapp_base_url}/analysis/{alert.symbol}"
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to generate alert message: {e}")
            return f"🚨 {alert.symbol} Alert: {alert.condition}"
    
    async def _send_whatsapp_message(self, phone_number: str, message: str) -> bool:
        """Send message via WhatsApp API"""
        try:
            url = f"{self.whatsapp_base_url}/api/sendText"
            
            payload = {
                "session": self.whatsapp_session,
                "chatId": f"{phone_number}@c.us",
                "text": message
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('success', False)
                    else:
                        logger.error(f"WhatsApp API error: {response.status}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.error("WhatsApp API timeout")
            return False
        except Exception as e:
            logger.error(f"WhatsApp API error: {e}")
            return False
    
    # ==================== UTILITY METHODS ====================
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone_number)
        # Should be 10-15 digits
        return 10 <= len(digits) <= 15
    
    def _validate_condition(self, condition: str, alert_type: str) -> bool:
        """Validate alert condition format"""
        try:
            condition_lower = condition.lower()
            
            if alert_type == 'price':
                return bool(re.match(r'price\s*(>=|<=|>|<|==|!=)\s*\d+', condition_lower))
            elif alert_type == 'technical':
                technical_terms = [
                    'bullish_divergence', 'bearish_divergence', 'order_block',
                    'break_of_structure', 'fair_value_gap', 'trend_change'
                ]
                return any(term in condition_lower for term in technical_terms)
            elif alert_type == 'volume':
                return 'volume' in condition_lower
            else:
                return len(condition.strip()) > 0
                
        except Exception:
            return False
    
    def _is_rate_limited(self, alert: Alert) -> bool:
        """Check if alert is rate limited"""
        try:
            now = datetime.now(timezone.utc)
            
            # Check individual alert cooldown
            if alert.last_triggered:
                last_triggered = datetime.fromisoformat(alert.last_triggered.replace('Z', '+00:00'))
                cooldown_end = last_triggered + timedelta(minutes=alert.cooldown_minutes)
                if now < cooldown_end:
                    return True
            
            # Check per-phone rate limiting
            phone_key = f"rate_limit:{alert.phone_number}"
            phone_limits = self.rate_limits.get(phone_key, [])
            
            # Remove old timestamps (older than 1 hour)
            hour_ago = now - timedelta(hours=1)
            phone_limits = [ts for ts in phone_limits if ts > hour_ago]
            
            if len(phone_limits) >= self.max_alerts_per_hour:
                return True
            
            # Check global cooldown
            if phone_limits:
                last_alert = max(phone_limits)
                if now - last_alert < timedelta(minutes=self.global_cooldown_minutes):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return False
    
    def _update_rate_limit(self, alert: Alert):
        """Update rate limiting data"""
        try:
            now = datetime.now(timezone.utc)
            phone_key = f"rate_limit:{alert.phone_number}"
            
            if phone_key not in self.rate_limits:
                self.rate_limits[phone_key] = []
            
            self.rate_limits[phone_key].append(now)
            
            # Keep only last hour of data
            hour_ago = now - timedelta(hours=1)
            self.rate_limits[phone_key] = [
                ts for ts in self.rate_limits[phone_key] if ts > hour_ago
            ]
            
        except Exception as e:
            logger.error(f"Rate limit update error: {e}")
    
    def _extract_current_price(self, analysis: Dict[str, Any]) -> Optional[float]:
        """Extract current price from analysis"""
        try:
            # Try multiple sources
            metadata = analysis.get('metadata', {})
            if 'current_price' in metadata:
                return float(metadata['current_price'])
            
            # Try from market analysis
            market_analysis = analysis.get('market_analysis', {})
            if 'current_price' in market_analysis:
                return float(market_analysis['current_price'])
            
            return None
            
        except Exception:
            return None
    
    def _extract_current_volume(self, analysis: Dict[str, Any]) -> Optional[float]:
        """Extract current volume from analysis"""
        try:
            metadata = analysis.get('metadata', {})
            volume_24h = metadata.get('volume_24h')
            return float(volume_24h) if volume_24h else None
        except Exception:
            return None
    
    def _extract_volume_change(self, analysis: Dict[str, Any]) -> Optional[float]:
        """Extract volume change percentage from analysis"""
        try:
            metadata = analysis.get('metadata', {})
            return metadata.get('volume_change_24h')
        except Exception:
            return None
    
    def _extract_rsi_value(self, analysis: Dict[str, Any]) -> Optional[float]:
        """Extract RSI value from analysis"""
        try:
            rsi_divergence = analysis.get('rsi_divergence', [])
            if rsi_divergence:
                return rsi_divergence[-1].get('rsi_value')
            return None
        except Exception:
            return None
    
    def _extract_signal_description(self, analysis: Dict[str, Any]) -> str:
        """Extract signal description from analysis"""
        try:
            recommendation = analysis.get('recommendation', {})
            action = recommendation.get('action', 'HOLD')
            confidence = recommendation.get('confidence', 0)
            
            return f"{action} ({confidence:.0f}% confidence)"
            
        except Exception:
            return "Analysis available"
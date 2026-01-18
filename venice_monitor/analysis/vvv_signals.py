"""VVV token buy signal analysis."""

import logging
from typing import Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class VVVSignalAnalyzer:
    """Analyze VVV token for buy signals."""

    def __init__(
        self,
        rsi_oversold: int = 30,
        price_drop_threshold: float = 15.0,
        volume_spike_multiplier: float = 2.0,
    ):
        """Initialize VVV signal analyzer.

        Args:
            rsi_oversold: RSI threshold for oversold condition
            price_drop_threshold: Percentage drop from recent high to trigger alert
            volume_spike_multiplier: Volume multiplier vs average to trigger alert
        """
        self.rsi_oversold = rsi_oversold
        self.price_drop_threshold = price_drop_threshold
        self.volume_spike_multiplier = volume_spike_multiplier

    def calculate_rsi(self, prices: list[float], period: int = 14) -> Optional[float]:
        """Calculate RSI (Relative Strength Index).

        Args:
            prices: List of historical prices
            period: RSI period (default 14)

        Returns:
            Current RSI value or None if insufficient data
        """
        if len(prices) < period + 1:
            logger.warning(f"Insufficient data for RSI calculation (need {period + 1}, got {len(prices)})")
            return None

        df = pd.DataFrame({"price": prices})
        df["change"] = df["price"].diff()

        gains = df["change"].clip(lower=0)
        losses = -df["change"].clip(upper=0)

        avg_gain = gains.rolling(window=period).mean()
        avg_loss = losses.rolling(window=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        current_rsi = rsi.iloc[-1]
        logger.debug(f"RSI({period}): {current_rsi:.2f}")

        return current_rsi

    def analyze_price_action(
        self, current_price: float, price_history: list[float], lookback_days: int = 7
    ) -> dict:
        """Analyze price action for buy signals.

        Args:
            current_price: Current VVV price
            price_history: Historical prices (most recent first)
            lookback_days: Number of days to look back for high

        Returns:
            Price action analysis dictionary
        """
        if not price_history or len(price_history) < lookback_days:
            logger.warning("Insufficient price history for analysis")
            return {"signals": [], "recommendation": "INSUFFICIENT_DATA"}

        recent_prices = price_history[:lookback_days]
        recent_high = max(recent_prices)
        recent_low = min(recent_prices)

        drop_from_high = ((recent_high - current_price) / recent_high) * 100
        rise_from_low = ((current_price - recent_low) / recent_low) * 100

        signals = []

        # Price drop signal
        if drop_from_high >= self.price_drop_threshold:
            signals.append({
                "type": "PRICE_DROP",
                "severity": "HIGH" if drop_from_high > 20 else "MEDIUM",
                "value": drop_from_high,
                "message": f"Price dropped {drop_from_high:.1f}% from {lookback_days}-day high"
            })

        # Bounce from low
        if rise_from_low > 5 and drop_from_high > 10:
            signals.append({
                "type": "BOUNCE",
                "severity": "MEDIUM",
                "value": rise_from_low,
                "message": f"Potential bounce: {rise_from_low:.1f}% from recent low"
            })

        analysis = {
            "current_price": current_price,
            "recent_high": recent_high,
            "recent_low": recent_low,
            "drop_from_high_percent": drop_from_high,
            "rise_from_low_percent": rise_from_low,
            "signals": signals,
        }

        return analysis

    def generate_buy_signal(
        self,
        current_price: float,
        price_history: list[float],
        volume_current: Optional[float] = None,
        volume_avg: Optional[float] = None,
    ) -> dict:
        """Generate comprehensive buy signal analysis.

        Args:
            current_price: Current VVV price
            price_history: Historical prices
            volume_current: Current 24h volume (optional)
            volume_avg: Average 24h volume (optional)

        Returns:
            Buy signal analysis dictionary
        """
        signals = []
        score = 0  # Buy signal score (higher = stronger buy)

        # RSI analysis
        rsi = self.calculate_rsi(price_history)
        if rsi is not None:
            if rsi < self.rsi_oversold:
                signals.append({
                    "type": "RSI_OVERSOLD",
                    "severity": "HIGH" if rsi < 20 else "MEDIUM",
                    "value": rsi,
                    "message": f"RSI oversold at {rsi:.1f}"
                })
                score += 3 if rsi < 20 else 2

        # Price action
        price_analysis = self.analyze_price_action(current_price, price_history)
        signals.extend(price_analysis.get("signals", []))

        # Add score for price drops
        for signal in price_analysis.get("signals", []):
            if signal["type"] == "PRICE_DROP":
                score += 3 if signal["severity"] == "HIGH" else 2
            elif signal["type"] == "BOUNCE":
                score += 1

        # Volume spike analysis
        if volume_current and volume_avg and volume_avg > 0:
            volume_ratio = volume_current / volume_avg
            if volume_ratio >= self.volume_spike_multiplier:
                signals.append({
                    "type": "VOLUME_SPIKE",
                    "severity": "MEDIUM",
                    "value": volume_ratio,
                    "message": f"Volume spike: {volume_ratio:.1f}x average"
                })
                score += 2

        # Generate recommendation
        if score >= 5:
            recommendation = "STRONG BUY"
            confidence = "HIGH"
        elif score >= 3:
            recommendation = "BUY"
            confidence = "MEDIUM"
        elif score >= 1:
            recommendation = "CONSIDER"
            confidence = "LOW"
        else:
            recommendation = "HOLD"
            confidence = "NEUTRAL"

        analysis = {
            "current_price": current_price,
            "rsi": rsi,
            "signals": signals,
            "signal_count": len(signals),
            "score": score,
            "recommendation": recommendation,
            "confidence": confidence,
            "price_action": price_analysis,
        }

        if score >= 3:
            logger.warning(
                f"💰 VVV BUY SIGNAL: {recommendation} "
                f"(Score: {score}, Signals: {len(signals)}, "
                f"Price: ${current_price:.4f}, RSI: {rsi:.1f if rsi else 'N/A'})"
            )

        return analysis

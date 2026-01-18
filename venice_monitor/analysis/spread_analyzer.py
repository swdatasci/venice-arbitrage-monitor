"""DIEM spread and arbitrage analysis."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SpreadAnalyzer:
    """Analyze DIEM arbitrage spreads and opportunities."""

    def __init__(self, min_profit_percent: float = 5.0):
        """Initialize spread analyzer.

        Args:
            min_profit_percent: Minimum profit percentage to trigger alerts
        """
        self.min_profit_percent = min_profit_percent
        self.last_alert = None

    def analyze_mint_arbitrage(
        self, mint_cost: float, market_price: float, mint_rate: float
    ) -> dict:
        """Analyze mint-and-sell arbitrage opportunity.

        Args:
            mint_cost: Cost to mint 1 DIEM in USD
            market_price: Current DIEM market price in USD
            mint_rate: Current mint rate (sVVV per DIEM)

        Returns:
            Arbitrage analysis dictionary
        """
        spread_usd = market_price - mint_cost
        spread_percent = (spread_usd / mint_cost) * 100 if mint_cost > 0 else 0

        is_profitable = spread_percent >= self.min_profit_percent
        is_negative = spread_percent < 0

        if is_profitable:
            recommendation = "MINT & SELL"
            confidence = "HIGH" if spread_percent > 10 else "MEDIUM"
        elif is_negative:
            recommendation = "HOLD VVV"
            confidence = "HIGH"
        else:
            recommendation = "MONITOR"
            confidence = "LOW"

        analysis = {
            "type": "mint_arbitrage",
            "mint_cost_usd": mint_cost,
            "market_price_usd": market_price,
            "spread_usd": spread_usd,
            "spread_percent": spread_percent,
            "is_profitable": is_profitable,
            "recommendation": recommendation,
            "confidence": confidence,
            "mint_rate": mint_rate,
            "estimated_profit_per_diem": max(0, spread_usd),
        }

        if is_profitable:
            logger.warning(
                f"🎯 MINT ARBITRAGE OPPORTUNITY: "
                f"Mint at ${mint_cost:.2f}, Sell at ${market_price:.2f}, "
                f"Spread: +{spread_percent:.2f}% (+${spread_usd:.2f} per DIEM)"
            )
        elif abs(spread_percent) > 50:
            logger.info(
                f"Large negative spread detected: {spread_percent:.2f}% "
                f"(Mint: ${mint_cost:.2f}, Market: ${market_price:.2f})"
            )

        return analysis

    def should_alert(self, analysis: dict) -> bool:
        """Determine if an alert should be sent.

        Args:
            analysis: Arbitrage analysis dictionary

        Returns:
            True if alert should be sent
        """
        # Alert on profitable opportunities
        if analysis["is_profitable"]:
            return True

        # Alert on extreme negative spreads (might indicate data error)
        if analysis["spread_percent"] < -75:
            return True

        return False

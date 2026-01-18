"""DIEM mint rate and cost calculator."""

import logging
import math
from typing import Optional
import requests

logger = logging.getLogger(__name__)


class MintCalculator:
    """Calculate DIEM mint costs and rates."""

    # Venice AI mint rate parameters
    BASE_MINT_RATE = 90.0  # Starting rate at launch
    TARGET_DIEM_SUPPLY = 38000  # Target supply
    ADJUSTMENT_POWER = 3.0  # Exponential power in formula

    # Venice API endpoint for live mint rate
    MINT_RATE_API = "https://diem-calculator.venice.ai/api/mint-rate"

    def __init__(self):
        """Initialize mint calculator."""
        self.session = requests.Session()

    def get_current_mint_rate(self) -> Optional[float]:
        """Get current mint rate from Venice API.

        Returns:
            Current mint rate (sVVV per DIEM) or None if error
        """
        try:
            response = self.session.get(self.MINT_RATE_API, timeout=10)
            response.raise_for_status()

            data = response.json()
            mint_rate = float(data.get("mint_rate", 0))

            logger.debug(f"Current mint rate: {mint_rate:.2f} sVVV per DIEM")
            return mint_rate

        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch live mint rate from Venice API: {e}")
            # Fall back to estimation
            return self.estimate_mint_rate()
        except (KeyError, ValueError) as e:
            logger.error(f"Mint rate data parsing error: {e}")
            return self.estimate_mint_rate()

    def estimate_mint_rate(self, current_supply: Optional[float] = None) -> float:
        """Estimate mint rate using formula.

        Formula: Mint Rate = Base Rate × e^(power × (current/target)^3)

        Args:
            current_supply: Current DIEM supply (if known)

        Returns:
            Estimated mint rate (sVVV per DIEM)
        """
        # If no current supply, use conservative estimate
        if current_supply is None:
            # As of Jan 2026, supply is around 32000 (estimated)
            current_supply = 32000

        ratio = current_supply / self.TARGET_DIEM_SUPPLY
        exponent = self.ADJUSTMENT_POWER * (ratio**3)
        mint_rate = self.BASE_MINT_RATE * math.exp(exponent)

        logger.debug(f"Estimated mint rate: {mint_rate:.2f} sVVV per DIEM")
        return mint_rate

    def calculate_mint_cost(self, vvv_price: float, mint_rate: Optional[float] = None) -> float:
        """Calculate USD cost to mint 1 DIEM.

        Args:
            vvv_price: Current VVV token price in USD
            mint_rate: Mint rate (sVVV per DIEM), fetches if not provided

        Returns:
            USD cost to mint 1 DIEM
        """
        if mint_rate is None:
            mint_rate = self.get_current_mint_rate()
            if mint_rate is None:
                mint_rate = self.estimate_mint_rate()

        mint_cost = mint_rate * vvv_price
        logger.debug(f"Mint cost: ${mint_cost:.2f} ({mint_rate:.2f} sVVV × ${vvv_price:.2f})")

        return mint_cost

    def calculate_arbitrage_spread(
        self, vvv_price: float, diem_market_price: float, mint_rate: Optional[float] = None
    ) -> dict:
        """Calculate arbitrage spread between minting and market price.

        Args:
            vvv_price: Current VVV token price in USD
            diem_market_price: Current DIEM market price in USD
            mint_rate: Mint rate (sVVV per DIEM), fetches if not provided

        Returns:
            Dictionary with spread analysis
        """
        mint_cost = self.calculate_mint_cost(vvv_price, mint_rate)

        spread_usd = diem_market_price - mint_cost
        spread_percent = (spread_usd / mint_cost) * 100 if mint_cost > 0 else 0

        is_profitable = spread_percent > 0

        result = {
            "mint_cost_usd": mint_cost,
            "market_price_usd": diem_market_price,
            "spread_usd": spread_usd,
            "spread_percent": spread_percent,
            "is_profitable": is_profitable,
            "recommendation": "MINT & SELL" if is_profitable else "HOLD VVV",
            "mint_rate": mint_rate or self.get_current_mint_rate(),
        }

        logger.info(
            f"Arbitrage spread: {spread_percent:+.2f}% "
            f"(Mint: ${mint_cost:.2f}, Market: ${diem_market_price:.2f})"
        )

        return result

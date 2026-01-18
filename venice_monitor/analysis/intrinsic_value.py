"""DIEM intrinsic value calculations."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class IntrinsicValueCalculator:
    """Calculate DIEM intrinsic value using DCF and other models."""

    # DIEM provides $1 per day of API credit
    DAILY_API_CREDIT = 1.0
    ANNUAL_API_CREDIT = 365.0

    def __init__(self, discount_rate: float = 0.25):
        """Initialize intrinsic value calculator.

        Args:
            discount_rate: Annual discount rate for DCF (default 25%)
        """
        self.discount_rate = discount_rate

    def calculate_dcf_value(self, discount_rate: Optional[float] = None) -> float:
        """Calculate DIEM intrinsic value using perpetuity DCF.

        Formula: PV = Annual Cash Flow / Discount Rate

        Args:
            discount_rate: Annual discount rate (uses default if None)

        Returns:
            Intrinsic value in USD
        """
        rate = discount_rate if discount_rate is not None else self.discount_rate

        if rate <= 0:
            logger.warning("Invalid discount rate, using default 25%")
            rate = 0.25

        intrinsic_value = self.ANNUAL_API_CREDIT / rate

        logger.debug(
            f"DCF intrinsic value: ${intrinsic_value:.2f} "
            f"(${self.ANNUAL_API_CREDIT}/year at {rate*100}% discount rate)"
        )

        return intrinsic_value

    def calculate_payback_period(self, market_price: float) -> float:
        """Calculate payback period in days.

        Args:
            market_price: Current DIEM market price

        Returns:
            Number of days to recover investment
        """
        payback_days = market_price / self.DAILY_API_CREDIT
        logger.debug(f"Payback period: {payback_days:.0f} days at ${market_price:.2f}")
        return payback_days

    def analyze_valuation(self, market_price: float, vvv_price: float, mint_rate: float) -> dict:
        """Comprehensive valuation analysis.

        Args:
            market_price: Current DIEM market price
            vvv_price: Current VVV price
            mint_rate: Current mint rate (sVVV per DIEM)

        Returns:
            Valuation analysis dictionary
        """
        # DCF valuations at different discount rates
        dcf_25 = self.calculate_dcf_value(0.25)  # Conservative
        dcf_50 = self.calculate_dcf_value(0.50)  # Aggressive

        # Mint cost
        mint_cost = mint_rate * vvv_price

        # Payback period
        payback_days = self.calculate_payback_period(market_price)

        # Valuation ratios
        price_to_dcf_25 = market_price / dcf_25
        price_to_mint = market_price / mint_cost if mint_cost > 0 else 0

        # Determine if undervalued
        is_undervalued_vs_dcf = market_price < dcf_25
        is_undervalued_vs_mint = market_price < mint_cost

        # Buy recommendation
        if is_undervalued_vs_dcf and price_to_dcf_25 < 0.85:
            buy_signal = "STRONG BUY"
            rationale = f"Trading {((1-price_to_dcf_25)*100):.1f}% below intrinsic value"
        elif is_undervalued_vs_dcf:
            buy_signal = "BUY"
            rationale = "Trading below intrinsic value"
        elif payback_days < 300:
            buy_signal = "HOLD"
            rationale = f"Reasonable {payback_days:.0f}-day payback if using API credits"
        else:
            buy_signal = "AVOID"
            rationale = f"Overvalued with {payback_days:.0f}-day payback"

        analysis = {
            "market_price": market_price,
            "dcf_value_25pct": dcf_25,
            "dcf_value_50pct": dcf_50,
            "mint_cost": mint_cost,
            "payback_days": payback_days,
            "price_to_dcf_ratio": price_to_dcf_25,
            "price_to_mint_ratio": price_to_mint,
            "is_undervalued": is_undervalued_vs_dcf,
            "buy_signal": buy_signal,
            "rationale": rationale,
        }

        if is_undervalued_vs_dcf:
            discount_pct = (1 - price_to_dcf_25) * 100
            logger.warning(
                f"📉 DIEM UNDERVALUED: ${market_price:.2f} vs ${dcf_25:.2f} "
                f"intrinsic ({discount_pct:.1f}% discount)"
            )

        return analysis

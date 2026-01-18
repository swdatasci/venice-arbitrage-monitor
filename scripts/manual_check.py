"""Manual one-time price check and analysis."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from venice_monitor.utils.config import Config
from venice_monitor.utils.logger import setup_logger
from venice_monitor.pricing.vvv_tracker import VVVPriceTracker
from venice_monitor.pricing.diem_tracker import DIEMPriceTracker
from venice_monitor.pricing.mint_calculator import MintCalculator
from venice_monitor.analysis.spread_analyzer import SpreadAnalyzer
from venice_monitor.analysis.intrinsic_value import IntrinsicValueCalculator


def main():
    """Run manual price check."""
    setup_logger(level="INFO")
    config = Config()

    print("\n" + "=" * 60)
    print("Venice AI Manual Price Check")
    print("=" * 60 + "\n")

    # Initialize trackers
    cmc_key = config.get("api_keys.coinmarketcap")
    cg_key = config.get("api_keys.coingecko")

    vvv_tracker = VVVPriceTracker(cmc_key, cg_key)
    diem_tracker = DIEMPriceTracker(cmc_key, cg_key)
    mint_calc = MintCalculator()

    # Get prices
    print("Fetching prices...")
    vvv_price = vvv_tracker.get_price()
    diem_price = diem_tracker.get_price()
    mint_rate = mint_calc.get_current_mint_rate()

    if not vvv_price or not diem_price:
        print("❌ Failed to fetch prices")
        return

    # Display prices
    print(f"\n📊 Current Prices:")
    print(f"   VVV:  ${vvv_price:.4f}")
    print(f"   DIEM: ${diem_price:.2f}")
    print(f"   Mint Rate: {mint_rate:.2f} sVVV per DIEM")

    # Calculate mint cost
    mint_cost = mint_rate * vvv_price
    print(f"   Mint Cost: ${mint_cost:.2f}")

    # Arbitrage analysis
    print(f"\n🎯 Arbitrage Analysis:")
    spread_usd = diem_price - mint_cost
    spread_pct = (spread_usd / mint_cost) * 100

    if spread_pct > 5:
        print(f"   ✅ PROFITABLE: {spread_pct:+.2f}% ({spread_usd:+.2f} USD per DIEM)")
        print(f"   Recommendation: MINT & SELL")
    elif spread_pct > 0:
        print(f"   ⚠️  Small Profit: {spread_pct:+.2f}% ({spread_usd:+.2f} USD per DIEM)")
        print(f"   Recommendation: MONITOR")
    else:
        print(f"   ❌ NEGATIVE: {spread_pct:+.2f}% ({spread_usd:+.2f} USD per DIEM)")
        print(f"   Recommendation: HOLD VVV")

    # Valuation analysis
    print(f"\n💰 Valuation Analysis:")
    intrinsic_calc = IntrinsicValueCalculator(discount_rate=0.25)
    dcf_value = intrinsic_calc.calculate_dcf_value()
    payback_days = intrinsic_calc.calculate_payback_period(diem_price)

    print(f"   DCF Value (25%): ${dcf_value:.2f}")
    print(f"   Market Price: ${diem_price:.2f}")

    if diem_price < dcf_value:
        discount = ((dcf_value - diem_price) / dcf_value) * 100
        print(f"   ✅ UNDERVALUED by {discount:.1f}%")
    else:
        premium = ((diem_price - dcf_value) / dcf_value) * 100
        print(f"   ⚠️  OVERVALUED by {premium:.1f}%")

    print(f"   Payback Period: {payback_days:.0f} days ($1/day API credit)")

    # Cross-exchange check
    print(f"\n🔄 Cross-Exchange Prices:")
    diem_prices = diem_tracker.get_all_prices()
    for source, price in diem_prices.items():
        if price:
            print(f"   {source}: ${price:.2f}")
        else:
            print(f"   {source}: N/A")

    vvv_prices = vvv_tracker.get_all_prices()
    print(f"\n📈 VVV Prices by Source:")
    for source, price in vvv_prices.items():
        if price:
            print(f"   {source}: ${price:.4f}")
        else:
            print(f"   {source}: N/A")

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()

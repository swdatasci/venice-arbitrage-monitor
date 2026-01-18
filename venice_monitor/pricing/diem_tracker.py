"""DIEM token price aggregation."""

import logging
from typing import Optional
from statistics import median

from venice_monitor.pricing.exchanges.coinmarketcap import CoinMarketCapAPI
from venice_monitor.pricing.exchanges.coingecko import CoinGeckoAPI

logger = logging.getLogger(__name__)


class DIEMPriceTracker:
    """Aggregate DIEM prices from multiple sources."""

    def __init__(self, cmc_api_key: Optional[str] = None, cg_api_key: Optional[str] = None):
        """Initialize DIEM price tracker.

        Args:
            cmc_api_key: CoinMarketCap API key
            cg_api_key: CoinGecko API key (optional)
        """
        self.sources = []

        if cmc_api_key:
            self.sources.append(("coinmarketcap", CoinMarketCapAPI(cmc_api_key)))
        if cg_api_key or True:  # CoinGecko works without API key
            self.sources.append(("coingecko", CoinGeckoAPI(cg_api_key)))

        if not self.sources:
            logger.warning("No price sources configured for DIEM")

    def get_price(self) -> Optional[float]:
        """Get aggregated DIEM price from all sources.

        Returns:
            Median DIEM price in USD or None if all sources fail
        """
        prices = []

        for source_name, source in self.sources:
            try:
                price = source.get_diem_price()
                if price and price > 0:
                    prices.append(price)
                    logger.debug(f"DIEM price from {source_name}: ${price:.2f}")
            except Exception as e:
                logger.error(f"Error fetching DIEM price from {source_name}: {e}")

        if not prices:
            logger.error("Failed to fetch DIEM price from any source")
            return None

        # Use median to handle outliers
        median_price = median(prices)
        logger.info(f"DIEM median price: ${median_price:.2f} (from {len(prices)} sources)")

        return median_price

    def get_all_prices(self) -> dict[str, Optional[float]]:
        """Get DIEM prices from all sources individually.

        Returns:
            Dictionary mapping source name to price
        """
        prices = {}

        for source_name, source in self.sources:
            try:
                price = source.get_diem_price()
                prices[source_name] = price
            except Exception as e:
                logger.error(f"Error fetching DIEM price from {source_name}: {e}")
                prices[source_name] = None

        return prices

    def detect_cross_exchange_arbitrage(self, min_spread_percent: float = 5.0) -> Optional[dict]:
        """Detect cross-exchange arbitrage opportunities.

        Args:
            min_spread_percent: Minimum spread percentage to report

        Returns:
            Arbitrage opportunity details or None
        """
        prices = self.get_all_prices()
        valid_prices = {k: v for k, v in prices.items() if v is not None and v > 0}

        if len(valid_prices) < 2:
            return None

        min_source = min(valid_prices, key=valid_prices.get)
        max_source = max(valid_prices, key=valid_prices.get)

        min_price = valid_prices[min_source]
        max_price = valid_prices[max_source]

        spread_usd = max_price - min_price
        spread_percent = (spread_usd / min_price) * 100

        if spread_percent >= min_spread_percent:
            logger.warning(
                f"Cross-exchange arbitrage detected: "
                f"Buy on {min_source} (${min_price:.2f}), "
                f"Sell on {max_source} (${max_price:.2f}), "
                f"Spread: {spread_percent:.2f}%"
            )

            return {
                "buy_exchange": min_source,
                "buy_price": min_price,
                "sell_exchange": max_source,
                "sell_price": max_price,
                "spread_usd": spread_usd,
                "spread_percent": spread_percent,
            }

        return None

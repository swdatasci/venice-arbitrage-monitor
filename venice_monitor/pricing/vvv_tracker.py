"""VVV token price aggregation."""

import logging
from typing import Optional
from statistics import median

from venice_monitor.pricing.exchanges.coinmarketcap import CoinMarketCapAPI
from venice_monitor.pricing.exchanges.coingecko import CoinGeckoAPI

logger = logging.getLogger(__name__)


class VVVPriceTracker:
    """Aggregate VVV prices from multiple sources."""

    def __init__(self, cmc_api_key: Optional[str] = None, cg_api_key: Optional[str] = None):
        """Initialize VVV price tracker.

        Args:
            cmc_api_key: CoinMarketCap API key
            cg_api_key: CoinGecko API key (optional)
        """
        self.sources = []

        if cmc_api_key:
            self.sources.append(("coinmarketcap", CoinMarketCapAPI(cmc_api_key)))
        if cg_api_key or True:  # CoinGecko works without API key (rate limited)
            self.sources.append(("coingecko", CoinGeckoAPI(cg_api_key)))

        if not self.sources:
            logger.warning("No price sources configured for VVV")

    def get_price(self) -> Optional[float]:
        """Get aggregated VVV price from all sources.

        Returns:
            Median VVV price in USD or None if all sources fail
        """
        prices = []

        for source_name, source in self.sources:
            try:
                price = source.get_vvv_price()
                if price and price > 0:
                    prices.append(price)
                    logger.debug(f"VVV price from {source_name}: ${price:.4f}")
            except Exception as e:
                logger.error(f"Error fetching VVV price from {source_name}: {e}")

        if not prices:
            logger.error("Failed to fetch VVV price from any source")
            return None

        # Use median to handle outliers
        median_price = median(prices)
        logger.info(f"VVV median price: ${median_price:.4f} (from {len(prices)} sources)")

        return median_price

    def get_all_prices(self) -> dict[str, Optional[float]]:
        """Get VVV prices from all sources individually.

        Returns:
            Dictionary mapping source name to price
        """
        prices = {}

        for source_name, source in self.sources:
            try:
                price = source.get_vvv_price()
                prices[source_name] = price
            except Exception as e:
                logger.error(f"Error fetching VVV price from {source_name}: {e}")
                prices[source_name] = None

        return prices

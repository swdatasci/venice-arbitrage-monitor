"""CoinGecko API integration."""

import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)


class CoinGeckoAPI:
    """CoinGecko API client."""

    BASE_URL = "https://api.coingecko.com/api/v3"

    # CoinGecko IDs
    VVV_ID = "venice-token"
    DIEM_ID = "venice-ai"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize CoinGecko API client.

        Args:
            api_key: CoinGecko Pro API key (optional for free tier)
        """
        self.api_key = api_key
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"x-cg-pro-api-key": api_key})

    def get_vvv_price(self) -> Optional[float]:
        """Get current VVV token price in USD.

        Returns:
            VVV price in USD or None if error
        """
        return self._get_token_price(self.VVV_ID, "VVV")

    def get_diem_price(self) -> Optional[float]:
        """Get current DIEM token price in USD.

        Returns:
            DIEM price in USD or None if error
        """
        return self._get_token_price(self.DIEM_ID, "DIEM")

    def _get_token_price(self, token_id: str, token_name: str) -> Optional[float]:
        """Get token price by CoinGecko ID.

        Args:
            token_id: CoinGecko token ID
            token_name: Token name for logging

        Returns:
            Token price in USD or None if error
        """
        try:
            url = f"{self.BASE_URL}/simple/price"
            params = {"ids": token_id, "vs_currencies": "usd"}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            price = data[token_id]["usd"]

            logger.debug(f"CoinGecko {token_name} price: ${price:.2f}")
            return float(price)

        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko API error for {token_name}: {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"CoinGecko data parsing error for {token_name}: {e}")
            return None

    def get_market_data(self, token_id: str) -> Optional[dict]:
        """Get comprehensive market data for a token.

        Args:
            token_id: CoinGecko token ID

        Returns:
            Market data dictionary or None if error
        """
        try:
            url = f"{self.BASE_URL}/coins/{token_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "community_data": "false",
                "developer_data": "false",
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"CoinGecko market data error: {e}")
            return None

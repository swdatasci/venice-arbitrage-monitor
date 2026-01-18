"""CoinMarketCap API integration."""

import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)


class CoinMarketCapAPI:
    """CoinMarketCap API client."""

    BASE_URL = "https://pro-api.coinmarketcap.com/v2"

    # CoinMarketCap IDs
    VVV_ID = 31991  # Venice Token
    DIEM_ID = 33947  # Diem (Venice AI)

    def __init__(self, api_key: str):
        """Initialize CoinMarketCap API client.

        Args:
            api_key: CoinMarketCap API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update(
            {"X-CMC_PRO_API_KEY": api_key, "Accept": "application/json"}
        )

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

    def _get_token_price(self, token_id: int, token_name: str) -> Optional[float]:
        """Get token price by CoinMarketCap ID.

        Args:
            token_id: CoinMarketCap token ID
            token_name: Token name for logging

        Returns:
            Token price in USD or None if error
        """
        try:
            url = f"{self.BASE_URL}/cryptocurrency/quotes/latest"
            params = {"id": token_id, "convert": "USD"}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            price = data["data"][str(token_id)]["quote"]["USD"]["price"]

            logger.debug(f"CoinMarketCap {token_name} price: ${price:.2f}")
            return float(price)

        except requests.exceptions.RequestException as e:
            logger.error(f"CoinMarketCap API error for {token_name}: {e}")
            return None
        except (KeyError, ValueError) as e:
            logger.error(f"CoinMarketCap data parsing error for {token_name}: {e}")
            return None

    def get_token_info(self, token_id: int) -> Optional[dict]:
        """Get detailed token information.

        Args:
            token_id: CoinMarketCap token ID

        Returns:
            Token data dictionary or None if error
        """
        try:
            url = f"{self.BASE_URL}/cryptocurrency/quotes/latest"
            params = {"id": token_id, "convert": "USD"}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            return data["data"][str(token_id)]

        except Exception as e:
            logger.error(f"CoinMarketCap token info error: {e}")
            return None

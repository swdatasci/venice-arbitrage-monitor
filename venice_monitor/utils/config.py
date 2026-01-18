"""Configuration management."""

import os
from pathlib import Path
from typing import Any, Dict
import yaml
from dotenv import load_dotenv


class Config:
    """Configuration manager."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_env()
        self._load_yaml()

    def _load_env(self) -> None:
        """Load environment variables from .env file."""
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)

    def _load_yaml(self) -> None:
        """Load YAML configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                "Copy config.example.yaml to config.yaml and configure it."
            )

        with open(self.config_path, "r") as f:
            self._config = yaml.safe_load(f)

        # Override with environment variables where applicable
        self._apply_env_overrides()

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        # API keys
        if api_key := os.getenv("COINMARKETCAP_API_KEY"):
            self._config.setdefault("api_keys", {})["coinmarketcap"] = api_key

        if api_key := os.getenv("COINGECKO_API_KEY"):
            self._config.setdefault("api_keys", {})["coingecko"] = api_key

        # Caelum
        if host := os.getenv("CAELUM_HOST"):
            self._config.setdefault("notifications", {}).setdefault("caelum", {})["host"] = host

        if port := os.getenv("CAELUM_PORT"):
            self._config.setdefault("notifications", {}).setdefault("caelum", {})["port"] = int(
                port
            )

        # Web3
        if rpc_url := os.getenv("BASE_RPC_URL"):
            self._config.setdefault("web3", {})["base_rpc_url"] = rpc_url

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.

        Args:
            key: Dot-notation key (e.g., "monitoring.check_interval_seconds")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    @property
    def check_interval(self) -> int:
        """Get monitoring check interval in seconds."""
        return self.get("monitoring.check_interval_seconds", 300)

    @property
    def vvv_sources(self) -> list[str]:
        """Get list of VVV price sources."""
        return self.get("monitoring.vvv_sources", ["coinmarketcap"])

    @property
    def diem_sources(self) -> list[str]:
        """Get list of DIEM price sources."""
        return self.get("monitoring.diem_sources", ["aerodrome"])

    @property
    def min_profit_percent(self) -> float:
        """Get minimum profit percentage for arbitrage alerts."""
        return self.get("monitoring.diem_arbitrage.min_profit_percent", 5.0)

    @property
    def intrinsic_value_discount(self) -> float:
        """Get intrinsic value discount percentage threshold."""
        return self.get("monitoring.diem_arbitrage.intrinsic_value_discount_percent", 10.0)

    @property
    def dcf_discount_rate(self) -> float:
        """Get DCF discount rate."""
        return self.get("monitoring.diem_arbitrage.dcf_discount_rate", 0.25)

    @property
    def caelum_enabled(self) -> bool:
        """Check if Caelum notifications are enabled."""
        return self.get("notifications.caelum.enabled", False)

    @property
    def caelum_host(self) -> str:
        """Get Caelum host."""
        return self.get("notifications.caelum.host", "10.32.3.27")

    @property
    def caelum_port(self) -> int:
        """Get Caelum port."""
        return self.get("notifications.caelum.port", 8090)

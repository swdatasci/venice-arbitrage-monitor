"""Main monitoring loop."""

import logging
import time
from pathlib import Path

from venice_monitor.utils.config import Config
from venice_monitor.utils.logger import setup_logger
from venice_monitor.pricing.vvv_tracker import VVVPriceTracker
from venice_monitor.pricing.diem_tracker import DIEMPriceTracker
from venice_monitor.pricing.mint_calculator import MintCalculator
from venice_monitor.analysis.spread_analyzer import SpreadAnalyzer
from venice_monitor.analysis.intrinsic_value import IntrinsicValueCalculator
from venice_monitor.analysis.vvv_signals import VVVSignalAnalyzer
from venice_monitor.notifications.caelum_notifier import CaelumNotifier
from venice_monitor.storage.price_history import PriceHistoryDB

logger = logging.getLogger(__name__)


class VeniceMonitor:
    """Main monitoring service."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize Venice monitor.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = Config(config_path)

        # Initialize logger
        log_file = self.config.get("logging.file", "logs/venice_monitor.log")
        log_level = self.config.get("logging.level", "INFO")
        setup_logger(level=log_level, log_file=log_file)

        logger.info("=== Venice AI Arbitrage Monitor Starting ===")

        # Initialize components
        cmc_key = self.config.get("api_keys.coinmarketcap")
        cg_key = self.config.get("api_keys.coingecko")

        self.vvv_tracker = VVVPriceTracker(cmc_key, cg_key)
        self.diem_tracker = DIEMPriceTracker(cmc_key, cg_key)
        self.mint_calculator = MintCalculator()

        # Analysis modules
        self.spread_analyzer = SpreadAnalyzer(self.config.min_profit_percent)
        self.intrinsic_calculator = IntrinsicValueCalculator(self.config.dcf_discount_rate)
        self.vvv_analyzer = VVVSignalAnalyzer(
            rsi_oversold=self.config.get("monitoring.vvv_buy_signals.rsi_oversold", 30),
            price_drop_threshold=self.config.get("monitoring.vvv_buy_signals.price_drop_percent", 15.0),
            volume_spike_multiplier=self.config.get("monitoring.vvv_buy_signals.volume_spike_multiplier", 2.0),
        )

        # Notifications
        self.notifier = None
        if self.config.caelum_enabled:
            self.notifier = CaelumNotifier(self.config.caelum_host, self.config.caelum_port)
            logger.info(f"Caelum notifications enabled ({self.config.caelum_host}:{self.config.caelum_port})")

        # Storage
        db_path = self.config.get("database.path", "data/price_history.db")
        self.db = PriceHistoryDB(db_path)

        # State tracking
        self.last_arbitrage_alert = None
        self.last_vvv_signal = None

    def check_prices(self) -> None:
        """Check prices and analyze opportunities."""
        logger.info("--- Price Check Started ---")

        # Get current prices
        vvv_price = self.vvv_tracker.get_price()
        diem_price = self.diem_tracker.get_price()

        if not vvv_price or not diem_price:
            logger.error("Failed to fetch prices, skipping this check")
            return

        logger.info(f"VVV: ${vvv_price:.4f}, DIEM: ${diem_price:.2f}")

        # Save to database
        self.db.save_vvv_price(vvv_price)
        self.db.save_diem_price(diem_price)

        # Get mint rate
        mint_rate = self.mint_calculator.get_current_mint_rate()
        if mint_rate:
            self.db.save_mint_rate(mint_rate, estimated=False)
        else:
            mint_rate = self.mint_calculator.estimate_mint_rate()
            self.db.save_mint_rate(mint_rate, estimated=True)

        logger.info(f"Mint Rate: {mint_rate:.2f} sVVV per DIEM")

        # Calculate mint cost
        mint_cost = self.mint_calculator.calculate_mint_cost(vvv_price, mint_rate)
        logger.info(f"Mint Cost: ${mint_cost:.2f}")

        # === DIEM ARBITRAGE ANALYSIS ===
        self._analyze_diem_arbitrage(vvv_price, diem_price, mint_rate, mint_cost)

        # === VVV BUY SIGNALS ===
        self._analyze_vvv_signals(vvv_price)

        # === CROSS-EXCHANGE ARBITRAGE ===
        self._check_cross_exchange_arbitrage()

        logger.info("--- Price Check Complete ---\n")

    def _analyze_diem_arbitrage(
        self, vvv_price: float, diem_price: float, mint_rate: float, mint_cost: float
    ) -> None:
        """Analyze DIEM arbitrage opportunities."""
        # Spread analysis
        spread_analysis = self.spread_analyzer.analyze_mint_arbitrage(
            mint_cost, diem_price, mint_rate
        )

        # Valuation analysis
        valuation_analysis = self.intrinsic_calculator.analyze_valuation(
            diem_price, vvv_price, mint_rate
        )

        # Send alerts
        if self.notifier:
            # Arbitrage alert (if profitable or extreme spread)
            if self.spread_analyzer.should_alert(spread_analysis):
                if self.last_arbitrage_alert != spread_analysis["recommendation"]:
                    self.notifier.send_arbitrage_alert(spread_analysis)
                    self.last_arbitrage_alert = spread_analysis["recommendation"]

            # Valuation alert (if strong buy)
            if valuation_analysis["buy_signal"] in ["STRONG BUY", "BUY"]:
                self.notifier.send_valuation_alert(valuation_analysis)

    def _analyze_vvv_signals(self, vvv_price: float) -> None:
        """Analyze VVV buy signals."""
        # Get price history
        price_history = self.db.get_vvv_history(days=30)

        if len(price_history) < 15:
            logger.info("Insufficient VVV price history for technical analysis")
            return

        # Generate buy signal
        signal_analysis = self.vvv_analyzer.generate_buy_signal(vvv_price, price_history)

        # Send alert if buy/strong buy
        if self.notifier and signal_analysis["recommendation"] in ["BUY", "STRONG BUY"]:
            if self.last_vvv_signal != signal_analysis["recommendation"]:
                self.notifier.send_vvv_buy_signal(signal_analysis)
                self.last_vvv_signal = signal_analysis["recommendation"]

    def _check_cross_exchange_arbitrage(self) -> None:
        """Check for cross-exchange arbitrage."""
        arb_opportunity = self.diem_tracker.detect_cross_exchange_arbitrage(min_spread_percent=5.0)

        if arb_opportunity and self.notifier:
            title = "🔄 Cross-Exchange DIEM Arbitrage"
            message = (
                f"Buy: {arb_opportunity['buy_exchange']} @ ${arb_opportunity['buy_price']:.2f}\n"
                f"Sell: {arb_opportunity['sell_exchange']} @ ${arb_opportunity['sell_price']:.2f}\n"
                f"Spread: {arb_opportunity['spread_percent']:.2f}% (${arb_opportunity['spread_usd']:.2f})"
            )
            self.notifier.send_notification(
                title=title, message=message, priority="high", data=arb_opportunity
            )

    def run(self) -> None:
        """Run monitoring loop."""
        check_interval = self.config.check_interval

        logger.info(f"Monitoring started (check interval: {check_interval}s)")
        logger.info("Press Ctrl+C to stop\n")

        try:
            while True:
                try:
                    self.check_prices()
                except Exception as e:
                    logger.error(f"Error during price check: {e}", exc_info=True)

                # Wait for next check
                time.sleep(check_interval)

        except KeyboardInterrupt:
            logger.info("\n=== Venice AI Monitor Stopping ===")


def main():
    """Entry point."""
    monitor = VeniceMonitor()
    monitor.run()


if __name__ == "__main__":
    main()

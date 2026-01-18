"""Caelum MCP notification integration."""

import logging
import socket
import json
from typing import Optional

logger = logging.getLogger(__name__)


class CaelumNotifier:
    """Send notifications through Caelum MCP service."""

    def __init__(self, host: str = "10.32.3.27", port: int = 8090):
        """Initialize Caelum notifier.

        Args:
            host: Caelum daemon host
            port: Caelum daemon port
        """
        self.host = host
        self.port = port

    def send_notification(
        self,
        title: str,
        message: str,
        priority: str = "medium",
        device: str = "all",
        data: Optional[dict] = None,
    ) -> bool:
        """Send notification through Caelum.

        Args:
            title: Notification title
            message: Notification message
            priority: Priority level (low, medium, high, urgent)
            device: Target device (all, mobile, desktop)
            data: Additional data payload

        Returns:
            True if notification sent successfully
        """
        try:
            # Construct notification payload
            payload = {
                "jsonrpc": "2.0",
                "method": "send_notification",
                "params": {
                    "title": title,
                    "message": message,
                    "priority": priority,
                    "device": device,
                    "category": "venice_monitor",
                    "data": data or {},
                },
                "id": 1,
            }

            # Connect to Caelum daemon
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                sock.connect((self.host, self.port))

                # Send JSON-RPC request
                request = json.dumps(payload) + "\n"
                sock.sendall(request.encode("utf-8"))

                # Receive response
                response = sock.recv(4096).decode("utf-8")
                result = json.loads(response)

                if "error" in result:
                    logger.error(f"Caelum notification error: {result['error']}")
                    return False

                logger.info(f"Caelum notification sent: {title}")
                return True

        except socket.timeout:
            logger.error(f"Caelum connection timeout ({self.host}:{self.port})")
            return False
        except ConnectionRefusedError:
            logger.error(f"Caelum connection refused ({self.host}:{self.port})")
            return False
        except Exception as e:
            logger.error(f"Caelum notification failed: {e}")
            return False

    def send_arbitrage_alert(self, analysis: dict) -> bool:
        """Send DIEM arbitrage alert.

        Args:
            analysis: Arbitrage analysis dictionary

        Returns:
            True if sent successfully
        """
        spread_pct = analysis["spread_percent"]
        spread_usd = analysis["spread_usd"]
        mint_cost = analysis["mint_cost_usd"]
        market_price = analysis["market_price_usd"]

        title = "🎯 DIEM Arbitrage Opportunity"
        message = (
            f"Spread: {spread_pct:+.2f}% ({spread_usd:+.2f} USD)\n"
            f"Mint Cost: ${mint_cost:.2f}\n"
            f"Market Price: ${market_price:.2f}\n"
            f"Action: {analysis['recommendation']}"
        )

        priority = "high" if abs(spread_pct) > 10 else "medium"

        return self.send_notification(
            title=title, message=message, priority=priority, device="all", data=analysis
        )

    def send_vvv_buy_signal(self, analysis: dict) -> bool:
        """Send VVV buy signal alert.

        Args:
            analysis: VVV signal analysis dictionary

        Returns:
            True if sent successfully
        """
        price = analysis["current_price"]
        recommendation = analysis["recommendation"]
        score = analysis["score"]
        rsi = analysis.get("rsi")

        signals_summary = ", ".join([s["type"] for s in analysis.get("signals", [])])

        title = f"💰 VVV {recommendation}"
        message = (
            f"Price: ${price:.4f}\n"
            f"RSI: {rsi:.1f if rsi else 'N/A'}\n"
            f"Score: {score}\n"
            f"Signals: {signals_summary or 'None'}"
        )

        priority = "high" if score >= 5 else "medium"

        return self.send_notification(
            title=title, message=message, priority=priority, device="all", data=analysis
        )

    def send_valuation_alert(self, analysis: dict) -> bool:
        """Send DIEM valuation alert.

        Args:
            analysis: Valuation analysis dictionary

        Returns:
            True if sent successfully
        """
        market_price = analysis["market_price"]
        dcf_value = analysis["dcf_value_25pct"]
        buy_signal = analysis["buy_signal"]
        rationale = analysis["rationale"]

        discount = ((dcf_value - market_price) / dcf_value) * 100

        title = f"📊 DIEM Valuation: {buy_signal}"
        message = (
            f"Market: ${market_price:.2f}\n"
            f"Fair Value: ${dcf_value:.2f}\n"
            f"Discount: {discount:.1f}%\n"
            f"{rationale}"
        )

        priority = "high" if "STRONG BUY" in buy_signal else "medium"

        return self.send_notification(
            title=title, message=message, priority=priority, device="all", data=analysis
        )

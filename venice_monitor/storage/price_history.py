"""Price history storage using SQLite."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import sqlite3

logger = logging.getLogger(__name__)


class PriceHistoryDB:
    """SQLite database for price history."""

    def __init__(self, db_path: str = "data/price_history.db"):
        """Initialize price history database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vvv_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    price REAL NOT NULL,
                    source TEXT,
                    volume_24h REAL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS diem_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    price REAL NOT NULL,
                    source TEXT,
                    volume_24h REAL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS mint_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    mint_rate REAL NOT NULL,
                    estimated BOOLEAN DEFAULT 0
                )
            """)

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vvv_timestamp ON vvv_prices(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_diem_timestamp ON diem_prices(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mint_timestamp ON mint_rates(timestamp)")

            conn.commit()

    def save_vvv_price(
        self, price: float, source: str = "aggregated", volume: Optional[float] = None
    ) -> None:
        """Save VVV price to database.

        Args:
            price: VVV price in USD
            source: Price source name
            volume: 24h trading volume
        """
        timestamp = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO vvv_prices (timestamp, price, source, volume_24h) VALUES (?, ?, ?, ?)",
                (timestamp, price, source, volume),
            )
            conn.commit()

        logger.debug(f"Saved VVV price: ${price:.4f} from {source}")

    def save_diem_price(
        self, price: float, source: str = "aggregated", volume: Optional[float] = None
    ) -> None:
        """Save DIEM price to database.

        Args:
            price: DIEM price in USD
            source: Price source name
            volume: 24h trading volume
        """
        timestamp = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO diem_prices (timestamp, price, source, volume_24h) VALUES (?, ?, ?, ?)",
                (timestamp, price, source, volume),
            )
            conn.commit()

        logger.debug(f"Saved DIEM price: ${price:.2f} from {source}")

    def save_mint_rate(self, mint_rate: float, estimated: bool = False) -> None:
        """Save mint rate to database.

        Args:
            mint_rate: Mint rate (sVVV per DIEM)
            estimated: Whether rate is estimated vs actual
        """
        timestamp = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO mint_rates (timestamp, mint_rate, estimated) VALUES (?, ?, ?)",
                (timestamp, mint_rate, estimated),
            )
            conn.commit()

        logger.debug(f"Saved mint rate: {mint_rate:.2f} sVVV per DIEM")

    def get_vvv_history(self, days: int = 30) -> List[float]:
        """Get VVV price history.

        Args:
            days: Number of days of history to retrieve

        Returns:
            List of prices (most recent first)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT price FROM vvv_prices
                WHERE datetime(timestamp) > datetime('now', ? || ' days')
                AND source = 'aggregated'
                ORDER BY timestamp DESC
                """,
                (f"-{days}",),
            )
            prices = [row[0] for row in cursor.fetchall()]

        logger.debug(f"Retrieved {len(prices)} VVV price records from last {days} days")
        return prices

    def get_diem_history(self, days: int = 30) -> List[float]:
        """Get DIEM price history.

        Args:
            days: Number of days of history to retrieve

        Returns:
            List of prices (most recent first)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT price FROM diem_prices
                WHERE datetime(timestamp) > datetime('now', ? || ' days')
                AND source = 'aggregated'
                ORDER BY timestamp DESC
                """,
                (f"-{days}",),
            )
            prices = [row[0] for row in cursor.fetchall()]

        logger.debug(f"Retrieved {len(prices)} DIEM price records from last {days} days")
        return prices

"""
Azure SQL Database connector for the Banking Multi-Agent RAG System.

Provides the DataConnector class that manages connections to Azure SQL Database
and exposes async methods for fetching customer income and transaction records.
"""

import asyncio
import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import pyodbc
from dotenv import load_dotenv

# Resolve project root (one level above src/)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

logger = logging.getLogger(__name__)


class DataConnector:
    """
    Azure SQL Database connectivity for customer and transaction data.

    Uses ``pyodbc`` under the hood.  All public query methods are async-compatible
    (they off-load blocking I/O via ``asyncio.to_thread``).

    Args:
        connection_string: ODBC connection string.  Falls back to the
            ``AZURE_SQL_CONNECTION_STRING`` environment variable when *None*.
    """

    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string: str = (
            connection_string or os.getenv("AZURE_SQL_CONNECTION_STRING", "")
        )
        self._available: bool = False
        if self.connection_string:
            self._test_connection()
        else:
            logger.warning(
                "No SQL connection string provided — "
                "DataConnector will use fallback sample data."
            )

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _test_connection(self) -> None:
        """Test that the database is reachable."""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            self._available = True
            logger.info("Azure SQL Database connection verified successfully.")
        except Exception as exc:
            self._available = False
            logger.warning("Azure SQL Database connection failed: %s", exc)

    @contextmanager
    def get_db_connection(self):
        """
        Context manager that yields a ``pyodbc.Connection``.

        Ensures the connection is closed even when an error occurs.
        """
        conn = None
        try:
            conn = pyodbc.connect(self.connection_string, timeout=30)
            yield conn
        except pyodbc.Error as exc:
            logger.error("Database connection error: %s", exc)
            raise
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    @property
    def is_available(self) -> bool:
        """Return *True* when a live database connection is available."""
        return self._available

    # ------------------------------------------------------------------
    # Async query methods
    # ------------------------------------------------------------------

    async def fetch_income(self, customer_id: str) -> Optional[float]:
        """
        Fetch the latest recorded income for *customer_id*.

        Returns ``None`` when the customer is not found or the database is
        unreachable (callers should fall back to sample data).
        """
        if not self._available:
            return None

        def _query() -> Optional[float]:
            try:
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT TOP 1 income FROM transactions "
                        "WHERE customer_id = ? AND income IS NOT NULL "
                        "ORDER BY ts DESC",
                        customer_id,
                    )
                    row = cursor.fetchone()
                    return float(row[0]) if row else None
            except Exception as exc:
                logger.error(
                    "Error fetching income for customer %s: %s",
                    customer_id,
                    exc,
                )
                return None

        return await asyncio.to_thread(_query)

    async def fetch_transactions(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all transactions for *customer_id* ordered by timestamp descending.

        Returns an empty list when the database is unreachable.
        """
        if not self._available:
            return []

        def _query() -> List[Dict[str, Any]]:
            try:
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT transaction_id, customer_id, income, amount, "
                        "ts, description "
                        "FROM transactions WHERE customer_id = ? ORDER BY ts DESC",
                        customer_id,
                    )
                    columns = [col[0] for col in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
            except Exception as exc:
                logger.error(
                    "Error fetching transactions for customer %s: %s",
                    customer_id,
                    exc,
                )
                return []

        return await asyncio.to_thread(_query)

    async def fetch_all_customer_ids(self) -> List[str]:
        """Return distinct customer IDs present in the transactions table."""
        if not self._available:
            return []

        def _query() -> List[str]:
            try:
                with self.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT DISTINCT customer_id FROM transactions"
                    )
                    return [row[0] for row in cursor.fetchall()]
            except Exception as exc:
                logger.error("Error fetching customer IDs: %s", exc)
                return []

        return await asyncio.to_thread(_query)

    # ------------------------------------------------------------------
    # Fallback sample data
    # ------------------------------------------------------------------

    @staticmethod
    def get_sample_transactions(customer_id: str) -> List[Dict[str, Any]]:
        """
        Return hard-coded sample transactions when the database is unavailable.

        Mirrors the rows from ``insert.sql`` so the system can still
        demonstrate full functionality without Azure SQL.
        """
        samples: Dict[str, List[Dict[str, Any]]] = {
            "12345": [
                {
                    "transaction_id": "TXN12345_1",
                    "customer_id": "12345",
                    "income": 75000.00,
                    "amount": 4500.00,
                    "ts": "2024-03-20 08:30:00",
                    "description": "Salary Deposit",
                },
                {
                    "transaction_id": "TXN12345_2",
                    "customer_id": "12345",
                    "income": 75000.00,
                    "amount": 1500.00,
                    "ts": "2024-03-15 14:20:00",
                    "description": "Mortgage Payment",
                },
                {
                    "transaction_id": "TXN12345_3",
                    "customer_id": "12345",
                    "income": 75000.00,
                    "amount": 300.00,
                    "ts": "2024-03-10 09:15:00",
                    "description": "Investment Contribution",
                },
                {
                    "transaction_id": "TXN12345_4",
                    "customer_id": "12345",
                    "income": 75000.00,
                    "amount": 200.00,
                    "ts": "2024-03-05 16:45:00",
                    "description": "Utility Bills",
                },
            ],
            "67890": [
                {
                    "transaction_id": "TXN67890_1",
                    "customer_id": "67890",
                    "income": 45000.00,
                    "amount": 3200.00,
                    "ts": "2024-03-20 09:00:00",
                    "description": "Salary Deposit",
                },
                {
                    "transaction_id": "TXN67890_2",
                    "customer_id": "67890",
                    "income": 45000.00,
                    "amount": 1200.00,
                    "ts": "2024-03-14 10:30:00",
                    "description": "Rent Payment",
                },
                {
                    "transaction_id": "TXN67890_3",
                    "customer_id": "67890",
                    "income": 45000.00,
                    "amount": 400.00,
                    "ts": "2024-03-08 11:15:00",
                    "description": "Car Payment",
                },
                {
                    "transaction_id": "TXN67890_4",
                    "customer_id": "67890",
                    "income": 45000.00,
                    "amount": 150.00,
                    "ts": "2024-03-02 13:20:00",
                    "description": "Student Loan",
                },
            ],
            "11111": [
                {
                    "transaction_id": "TXN11111_1",
                    "customer_id": "11111",
                    "income": 28000.00,
                    "amount": 2300.00,
                    "ts": "2024-03-20 07:45:00",
                    "description": "Salary Deposit",
                },
                {
                    "transaction_id": "TXN11111_2",
                    "customer_id": "11111",
                    "income": 28000.00,
                    "amount": 800.00,
                    "ts": "2024-03-12 12:10:00",
                    "description": "Rent Payment",
                },
                {
                    "transaction_id": "TXN11111_3",
                    "customer_id": "11111",
                    "income": 28000.00,
                    "amount": 300.00,
                    "ts": "2024-03-07 15:30:00",
                    "description": "Credit Card Payment",
                },
                {
                    "transaction_id": "TXN11111_4",
                    "customer_id": "11111",
                    "income": 28000.00,
                    "amount": 150.00,
                    "ts": "2024-03-01 17:55:00",
                    "description": "Overdraft Fee",
                },
            ],
        }
        return samples.get(customer_id, [])

    @staticmethod
    def get_sample_income(customer_id: str) -> Optional[float]:
        """Return sample income for *customer_id* when the DB is unavailable."""
        incomes: Dict[str, float] = {
            "12345": 75000.00,
            "67890": 45000.00,
            "11111": 28000.00,
        }
        return incomes.get(customer_id)

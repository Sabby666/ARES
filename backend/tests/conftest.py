# backend/tests/conftest.py
"""
Pytest configuration for ARES test suite.
Enforces strict test database isolation so pytest executions NEVER write
test records into the production data/ares.db file.
"""

import os
import sys
from pathlib import Path

# Resolve test database path
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DATA_DIR = _BACKEND_DIR.parent / "data"
_DATA_DIR.mkdir(parents=True, exist_ok=True)
_TEST_DB_PATH = _DATA_DIR / "ares_test.db"

# Force environment variables BEFORE any app imports
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB_PATH}"
os.environ["APP_ENV"] = "test"

import pytest
import pytest_asyncio
from app.database.engine import engine, init_db, AsyncSessionLocal


@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_test_database():
    """Initialize tables in the test database for each test session."""
    await init_db()
    yield

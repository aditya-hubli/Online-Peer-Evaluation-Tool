"""Additional tests for database session to increase coverage."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.db.session import get_db, engine, AsyncSessionLocal, Base
import os


@pytest.mark.asyncio
async def test_get_db_yields_session():
    """Test get_db yields a database session."""
    # get_db should work in test environment
    count = 0
    async for db in get_db():
        assert db is not None
        count += 1
        break  # Only iterate once
    assert count == 1


def test_async_session_local_exists():
    """Test AsyncSessionLocal is available."""
    assert AsyncSessionLocal is not None


def test_engine_exists():
    """Test database engine exists."""
    assert engine is not None


def test_base_class_exists():
    """Test Base class for ORM models exists."""
    assert Base is not None


def test_database_url_configuration():
    """Test DATABASE_URL is configured in environment."""
    # Should have a database URL in test env
    assert "DATABASE_URL" in os.environ or "ASYNC_DATABASE_URL" in os.environ

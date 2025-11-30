"""Tests for config module to improve coverage."""
from app.core.config import settings


def test_settings_env_is_test():
    """Test that ENV is set to test."""
    assert settings.ENV == "test"


def test_settings_has_database_url():
    """Test that database URLs are configured."""
    assert settings.DATABASE_URL is not None
    assert settings.ASYNC_DATABASE_URL is not None


def test_settings_has_supabase_config():
    """Test that Supabase configuration exists."""
    assert settings.SUPABASE_URL is not None
    assert settings.SUPABASE_ANON_KEY is not None
    assert settings.SUPABASE_SERVICE_ROLE_KEY is not None


def test_settings_debug_mode():
    """Test debug mode configuration."""
    # In test environment, debug might be True or False
    assert isinstance(settings.DEBUG, bool)


def test_settings_jwt_config():
    """Test JWT configuration exists."""
    assert hasattr(settings, 'SECRET_KEY') or hasattr(settings, 'JWT_SECRET_KEY')

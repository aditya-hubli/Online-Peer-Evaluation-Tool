"""Tests for supabase connection to improve coverage."""
from app.core.supabase import supabase


def test_supabase_client_exists():
    """Test that Supabase client is initialized."""
    assert supabase is not None


def test_supabase_table_method_exists():
    """Test that Supabase table method exists."""
    assert hasattr(supabase, 'table')


def test_supabase_can_create_query():
    """Test that Supabase can create table queries."""
    # This should not throw an error
    table_query = supabase.table("test_table")
    assert table_query is not None

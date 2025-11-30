"""Supabase client initialization."""
import os
from supabase import create_client, Client
from app.core.config import settings

# For testing, we'll create a mock-friendly client
if os.getenv("ENV") == "test":
    # In test mode, create a minimal client that won't actually connect
    try:
        supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    except Exception:
        # If creation fails in test mode, create a mock placeholder
        from unittest.mock import Mock
        supabase = Mock(spec=Client)
else:
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

__all__ = ["supabase"]

# Core package initialization
from app.core.config import settings
from app.core.supabase import supabase

__all__ = ["settings", "supabase"]

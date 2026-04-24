from supabase import create_client, Client
from app.core.config import settings

def get_supabase() -> Client:
    """Initializes and returns a Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Use this variable throughout the app to access the DB
supabase: Client = get_supabase()
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

_supabase: Client = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")  # service_role para bypass RLS
        if not url or not key:
            raise ValueError("SUPABASE_URL e SUPABASE_SERVICE_KEY são obrigatórios")
        _supabase = create_client(url, key)
    return _supabase
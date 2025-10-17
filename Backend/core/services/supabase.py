from supabase import create_client
import dotenv
import os

# Load .env file from the backend directory
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

# Only create client if both URL and KEY are available
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY) if SUPABASE_URL and SUPABASE_ANON_KEY else None

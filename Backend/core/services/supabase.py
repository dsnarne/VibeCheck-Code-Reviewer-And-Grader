from supabase import create_client
import dotenv
import os

# Load .env file from the project root
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
env_path = os.path.join(project_root, ".env")
dotenv.load_dotenv(env_path)

# Get Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_PROJECT_ID = os.environ.get("SUPABASE_PROJECT_ID")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

# Construct URL from project ID if URL is not provided
if not SUPABASE_URL and SUPABASE_PROJECT_ID:
    SUPABASE_URL = f"https://{SUPABASE_PROJECT_ID}.supabase.co"

# Only create client if both URL and KEY are available
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY) if SUPABASE_URL and SUPABASE_ANON_KEY else None

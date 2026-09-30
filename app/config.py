# app/config.py — Configuration and constants
import os

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

DEFAULT_LABOUR_RATE = 450.0
VAT_RATE = 0.15
MAX_IMAGE_SIZE = 7_000_000  # ~5MB in base64
CURRENCY = "R"

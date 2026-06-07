import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

response = supabase.table("reports").select("*").order("created_at", desc=True).limit(5).execute()
print("LATEST 5 REPORTS:")
for r in response.data:
    print(f"ID: {r['id']}, Status: {r['status']}, Violation: {r.get('violation_type')}, OCR: {r.get('ocr_plate')}")

import threading
import time
import os
from fastapi import FastAPI
from app.services.ai_engine import AIEngine
from app.db.database import supabase
from app.routers import users

app = FastAPI(title="CivicEye Backend", version="1.0.0")

# Include the Auth router so your Login/Signup still works
app.include_router(users.router)

# Ensure a temp folder exists to store images during processing
if not os.path.exists("temp"):
    os.makedirs("temp")

def security_guard_logic():
    """
    This function runs in the background and checks Supabase 
    every 5 seconds for 'Pending' reports.
    """
    print("📡 Guard is watching the Supabase logbook...")
    
    while True:
        try:
            # 1. Ask Supabase: "Are there any reports waiting for AI analysis?"
            # We look for rows where status is 'Pending'
            print(f"⏰ Checking database at {time.ctime()}...")
            response = supabase.table("reports").select("*").eq("status", "Pending").execute()
            
            reports = response.data

            if reports:
                for report in reports:
                    report_id = report['id']
                    image_name = report['image_url']
                    print(f"🔍 Found a violation to check: {image_name}")

                    # 2. Download the image from Supabase Storage 'evidence' bucket
                    local_path = f"temp/{image_name}"
                    try:
                        with open(local_path, "wb") as f:
                            # Make sure your bucket name is 'evidence'
                            f.write(supabase.storage.from_("evidence").download(image_name))
                        
                        # 3. Run the AI Engine (YOLOv8 + OCR)
                        violation, plate = AIEngine.process_image(local_path)
                        print(f"🤖 AI Analysis Result: {violation}, Plate: {plate}")

                        # 4. Update the report in the database with results
                        supabase.table("reports").update({
                            "violation_type": violation,
                            "ocr_plate": plate,
                            "status": "Verified",
                            "fine_amount": 1000 if violation != "Clear" else 0
                        }).eq("id", report_id).execute()
                        
                        print(f"✅ Report {report_id} successfully updated in Supabase.")

                        # Optional: Clean up the temp file
                        if os.path.exists(local_path):
                            os.remove(local_path)

                    except Exception as download_error:
                        print(f"❌ Error processing report {report_id}: {download_error}")

        except Exception as e:
            # This handles the 'getaddrinfo failed' error if internet drops
            print(f"⚠️ Guard noticed a connection error: {e}. Retrying in 10s...")
            time.sleep(10)
            continue
        
        # Wait 5 seconds before checking the database again
        time.sleep(5)

@app.on_event("startup")
async def startup_event():
    """Starts the Security Guard thread when the FastAPI server turns on."""
    thread = threading.Thread(target=security_guard_logic, daemon=True)
    thread.start()

@app.get("/")
async def root():
    return {
        "status": "online",
        "mode": "Polling (Option A)",
        "message": "CivicEye AI Backend is watching for violations."
    }
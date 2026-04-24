from fastapi import APIRouter, HTTPException
from app.services.ai_engine import AIEngine
from app.db.database import supabase
import os

router = APIRouter(prefix="/reports", tags=["Reports Analysis"])

@router.post("/analyze/{report_id}")
async def analyze_report(report_id: str):
    """
    Called by Flutter after a citizen submits a report.
    Triggers AI analysis and updates the record in Supabase.
    """
    try:
        # 1. Fetch the report details from Supabase
        response = supabase.table("reports").select("*").eq("id", report_id).single().execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Report ID not found in database.")

        report_data = response.data
        image_url = report_data['image_url']
        
        # 2. Download the image to a local temp folder
        if not os.path.exists('temp'):
            os.makedirs('temp')
        
        local_path = os.path.join('temp', image_url)
        
        with open(local_path, 'wb+') as f:
            res = supabase.storage.from_('evidence').download(image_url)
            f.write(res)

        # 3. Run the AI Engine
        print(f"🧠 AI starting analysis for Report: {report_id}")
        violation, plate = AIEngine.process_image(local_path)

        # 4. Update the report in Supabase with AI results
        # We set status to 'Verified' so it appears for the Police
        fine_amounts = {"No Helmet": 1035, "Triple Riding": 1200, "Signal Jump": 1000, "Clear": 0}
        
        update_res = supabase.table("reports").update({
            "violation_type": violation,
            "ocr_plate": plate,
            "fine_amount": fine_amounts.get(violation, 0),
            "status": "Verified" 
        }).eq("id", report_id).execute()

        return {
            "status": "success",
            "report_id": report_id,
            "ai_result": {
                "violation": violation,
                "plate": plate
            }
        }

    except Exception as e:
        print(f"❌ API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
import os
import json
import uuid
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from services.queue_service import QueueService
from worker import process_video_job

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

queue_service = QueueService()

os.makedirs("videos", exist_ok=True)
app.mount("/videos", StaticFiles(directory="videos"), name="videos")


@app.post("/generate")
async def generate_video(
    prompt: str = Form(...),
    face_image: UploadFile = File(None)
):
    try:
        job_id = str(uuid.uuid4())

        job_data = {
            "id": job_id,
            "status": "pending",
            "prompt": prompt,
            "created_at": datetime.now().isoformat(),
            "video_path": None
        }

        queue_service.add_job(job_data)

        # Run synchronously (IMPORTANT for Render free tier)
        process_video_job(job_id, json.dumps(job_data))

        return {
            "success": True,
            "job_id": job_id,
            "status": "completed"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    job = queue_service.get_job(job_id)

    if not job:
        return {"detail": "Job not found"}

    video_url = None
    if job.get("video_path"):
        video_url = f"https://director-ai.onrender.com/{job['video_path']}"

    return {
        "success": True,
        "status": job["status"],
        "video_url": video_url
    }


@app.get("/")
def root():
    return {"message": "Director AI API running"}
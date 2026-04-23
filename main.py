import os
import json
import uuid
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from services.queue_service import QueueService
from worker import process_video_job

app = FastAPI()

# CORS
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

        face_path = None
        if face_image and face_image.filename:
            os.makedirs("temp", exist_ok=True)
            face_path = f"temp/{job_id}.jpg"
            with open(face_path, "wb") as f:
                f.write(await face_image.read())

        job_data = {
            "id": job_id,
            "status": "pending",
            "prompt": prompt,
            "face_path": face_path,
            "created_at": datetime.now().isoformat(),
            "video_path": None,
            "error": None
        }

        queue_service.add_job(job_data)

        # 🔥 IMPORTANT FIX (shared queue)
        process_video_job(job_id, json.dumps(job_data), queue_service)

        return {
            "success": True,
            "job_id": job_id,
            "status": "pending"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    job = queue_service.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    video_url = None
    if job.get("video_path"):
        base_url = os.getenv("BASE_URL", "https://director-ai.onrender.com")
        video_url = f"{base_url}/videos/{job_id}.mp4"

    return {
        "success": True,
        "status": job["status"],
        "video_url": video_url,
        "error": job.get("error")
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "queue_size": queue_service.get_queue_size()
    }


@app.get("/")
def root():
    return {"message": "Director AI API running"}
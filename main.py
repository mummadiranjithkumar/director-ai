import os
import json
import uuid
from dotenv import load_dotenv
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response

from worker import process_video_job

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://director-ai.onrender.com")

app = FastAPI(title="Director AI Video API")

# In-memory job storage (TEMP FIX)
JOBS = {}

# CORS
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response: Response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static
os.makedirs("videos", exist_ok=True)
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

# ---------------------------
# GENERATE
# ---------------------------
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
            "status": "processing",
            "prompt": prompt,
            "face_path": face_path,
            "created_at": datetime.now().isoformat(),
            "video_path": None,
            "error": None
        }

        # SAVE IN MEMORY
        JOBS[job_id] = job_data

        # RUN DIRECTLY (NO CELERY)
        process_video_job(job_id, json.dumps(job_data))

        return {
            "success": True,
            "job_id": job_id,
            "status": "processing"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# STATUS
# ---------------------------
@app.get("/status/{job_id}")
async def get_status(job_id: str):
    job = JOBS.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    video_url = None
    if job.get("video_path"):
        video_url = f"{BASE_URL}/{job['video_path']}"

    return {
        "success": True,
        "job_id": job_id,
        "status": job["status"],
        "video_url": video_url,
        "error": job.get("error")
    }


# ---------------------------
# ROOT
# ---------------------------
@app.get("/")
async def root():
    return {"message": "Director AI running 🚀"}
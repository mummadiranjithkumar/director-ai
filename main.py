"""
Director AI Video App - Scalable FastAPI Backend (FINAL STABLE)
"""
import os
import json
import uuid
from dotenv import load_dotenv

from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, Response

from services.queue_service import QueueService
from worker import process_video_job

# ✅ Load environment
load_dotenv()

# ✅ Base URL (ngrok or localhost)
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

app = FastAPI(title="Director AI Video API")

# ---------------------------
# 🔥 FORCE CORS (FINAL FIX)
# ---------------------------
@app.middleware("http")
async def add_cors_headers(request, call_next):
    response: Response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    return response

# ---------------------------
# CORS (KEEP THIS ALSO)
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# STATIC FILES
# ---------------------------
os.makedirs("videos", exist_ok=True)
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

# ---------------------------
# SERVICES
# ---------------------------
queue_service = QueueService()

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

        # Save face image
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

        # Send to worker (synchronous if TEST_MODE, else Celery)
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        if test_mode:
            # Run synchronously for deployment
            process_video_job(job_id, json.dumps(job_data))
        else:
            # Use Celery for production
            process_video_job.delay(job_id, json.dumps(job_data))

        return JSONResponse({
            "success": True,
            "job_id": job_id,
            "status": "pending"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# STATUS
# ---------------------------
@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    try:
        job = queue_service.get_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # ✅ FIXED VIDEO URL (ngrok compatible)
        video_url = None
        if job.get("video_path"):
            video_url = f"{BASE_URL}/{job['video_path']}"

        return JSONResponse({
            "success": True,
            "job_id": job_id,
            "status": job["status"],
            "video_url": video_url,
            "error": job.get("error"),
            "created_at": job["created_at"],
            "updated_at": job.get("updated_at")
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# HEALTH
# ---------------------------
@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "queue_size": queue_service.get_queue_size()
    })


# ---------------------------
# ROOT
# ---------------------------
@app.get("/")
async def root():
    return JSONResponse({
        "message": "Director AI Video API",
        "version": "1.0.0"
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
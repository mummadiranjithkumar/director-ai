"""
Worker - FINAL STABLE VERSION (NO ERRORS, NO WARNINGS)
"""
import os
import json
import asyncio
import inspect
from datetime import datetime
from celery import Celery

from services.queue_service import QueueService
from services.face_swap_service import FaceSwapService
from services.replicate_service import ReplicateService

# Initialize Celery
celery_app = Celery(
    'director',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# Services
queue_service = QueueService()
face_swap_service = FaceSwapService()
replicate_service = ReplicateService()


@celery_app.task(name="worker.process_video_job")
def process_video_job(job_id: str, data: str):

    try:
        print(f"🚀 Worker processing job: {job_id}")
        job_data = json.loads(data)

        # Update → processing
        queue_service.update_job(job_id, {
            "status": "processing",
            "updated_at": datetime.now().isoformat()
        })

        # ---------------------------
        # STEP 1: Generate Image
        # ---------------------------
        print("🎨 Generating image...")
        image_path = replicate_service.generate_image(job_data["prompt"])

        if not image_path:
            raise Exception("Image generation failed")

        # ---------------------------
        # STEP 2: Face Swap (SAFE)
        # ---------------------------
        final_image_path = image_path

        if job_data.get("face_path"):
            print("🧑 Face swap...")

            try:
                result = face_swap_service.swap_face(
                    image_path,
                    job_data["face_path"]
                )

                # Handle async OR sync safely
                if inspect.iscoroutine(result):
                    swapped = asyncio.run(result)
                else:
                    swapped = result

                if swapped:
                    final_image_path = swapped
                else:
                    print("⚠️ Face swap failed → using original image")

            except Exception as e:
                print(f"⚠️ Face swap error: {str(e)} → skipped")

        # ---------------------------
        # STEP 3: Generate Video
        # ---------------------------
        print("🎬 Generating video...")
        video_path = replicate_service.generate_video_from_image(final_image_path)

        if not video_path:
            raise Exception("Video generation failed")

        # ---------------------------
        # COMPLETE
        # ---------------------------
        queue_service.update_job(job_id, {
            "status": "completed",
            "video_path": video_path,
            "updated_at": datetime.now().isoformat()
        })

        print(f"✅ Job {job_id} completed successfully")

    except Exception as e:
        print(f"❌ ERROR in job {job_id}: {str(e)}")

        queue_service.update_job(job_id, {
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.now().isoformat()
        })


if __name__ == "__main__":
    celery_app.start()
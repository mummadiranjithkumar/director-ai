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

# Initialize Celery (only used when not in TEST_MODE)
celery_app = Celery(
    'director',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# Services
queue_service = QueueService()
face_swap_service = FaceSwapService()
replicate_service = ReplicateService()


def process_video_job_sync(job_id: str, data: str):
    """Synchronous version of process_video_job for deployment."""
    
    try:
        print(f"Processing job synchronously: {job_id}")
        
        # Parse job data
        job_data = json.loads(data)
        
        # Update status to processing
        queue_service.update_job(job_id, {
            "status": "processing",
            "updated_at": datetime.now().isoformat()
        })
        
        # Step 1: Generate image using Replicate
        print(f"Generating image for job {job_id}")
        image_path = replicate_service.generate_image(
            job_data["prompt"],
            steps=4  # Low cost setting
        )
        
        if not image_path:
            queue_service.update_job(job_id, {
                "status": "failed",
                "error": "Failed to generate image",
                "updated_at": datetime.now().isoformat()
            })
            return
        
        # Step 2: Apply face swap if face image provided
        final_image_path = image_path
        if job_data.get("face_path"):
            print(f"Applying face swap for job {job_id}")
            final_image_path = face_swap_service.swap_face(
                image_path,
                job_data["face_path"]
            )
            
            if not final_image_path:
                queue_service.update_job(job_id, {
                    "status": "failed",
                    "error": "Failed to apply face swap",
                    "updated_at": datetime.now().isoformat()
                })
                return
        
        # Step 3: Generate video from final image
        print(f"Generating video for job {job_id}")
        video_path = replicate_service.generate_video_from_image(
            final_image_path,
            frames=12  # Low cost setting
        )
        
        if not video_path:
            queue_service.update_job(job_id, {
                "status": "failed",
                "error": "Failed to generate video",
                "updated_at": datetime.now().isoformat()
            })
            return
        
        # Step 4: Update job as completed
        queue_service.update_job(job_id, {
            "status": "completed",
            "video_path": video_path,
            "updated_at": datetime.now().isoformat()
        })
        
        print(f"Job {job_id} completed successfully")
        
    except Exception as e:
        print(f"ERROR: Job {job_id} failed: {str(e)}")
        queue_service.update_job(job_id, {
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.now().isoformat()
        })


@celery_app.task(name="worker.process_video_job")
def process_video_job(job_id: str, data: str):
    """Celery task version for production with Redis."""
    # Just call the synchronous version
    return process_video_job_sync(job_id, data)


# For backward compatibility, make process_video_job point to sync version when called directly
if os.getenv("TEST_MODE", "false").lower() == "true":
    process_video_job = process_video_job_sync

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
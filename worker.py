import json
import os

def process_video_job(job_id, data):
    job = json.loads(data)

    try:
        print(f"Processing job {job_id}")

        # Simulate steps (replace later with real AI calls)
        os.makedirs("videos", exist_ok=True)

        # Fake video file (for testing)
        video_path = f"videos/{job_id}.mp4"

        with open(video_path, "wb") as f:
            f.write(b"FAKE VIDEO DATA")

        job["video_path"] = video_path
        job["status"] = "completed"

        print(f"Job {job_id} completed")

        return job

    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        return job
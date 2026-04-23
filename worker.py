import json
import os
from datetime import datetime
from dotenv import load_dotenv

from moviepy.editor import (
    ColorClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    VideoFileClip
)

load_dotenv()


def process_video_job(job_id, data, queue_service):
    try:
        print(f"Processing job {job_id}")
        job_data = json.loads(data)

        # update status
        queue_service.update_job(job_id, {
            "status": "processing"
        })

        test_mode = os.getenv("TEST_MODE", "true").lower() == "true"

        if test_mode:
            video_path = generate_test_video(job_id, job_data["prompt"])
        else:
            raise ValueError("Only TEST_MODE supported for now")

        queue_service.update_job(job_id, {
            "status": "completed",
            "video_path": video_path
        })

        print(f"Job {job_id} completed")

    except Exception as e:
        print("ERROR:", str(e))
        queue_service.update_job(job_id, {
            "status": "failed",
            "error": str(e)
        })


def generate_test_video(job_id, prompt):
    os.makedirs("videos", exist_ok=True)

    clips = []
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

    for i in range(3):
        bg = ColorClip(size=(854, 480), color=colors[i], duration=3)

        txt = TextClip(
            f"{prompt[:20]}...",
            fontsize=50,
            color="white"
        ).set_position("center").set_duration(3)

        clip = CompositeVideoClip([bg, txt])
        clips.append(clip)

    final = concatenate_videoclips(clips)

    output_path = f"videos/{job_id}.mp4"
    final.write_videofile(output_path, fps=24, codec="libx264")

    for c in clips:
        c.close()
    final.close()

    return output_path
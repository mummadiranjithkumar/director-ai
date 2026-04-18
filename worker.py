import json
import os
import requests
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, concatenate_videoclips

# Load environment variables
load_dotenv()

from services.queue_service import QueueService
from services.face_swap_service import FaceSwapService

# Services
queue_service = QueueService()
face_swap_service = FaceSwapService()


def process_video_job(job_id, data):
    """Process video job using real Replicate AI video generation or TEST_MODE."""
    
    try:
        print(f"Processing job {job_id}")
        job_data = json.loads(data)
        
        # Update status to processing
        queue_service.update_job(job_id, {
            "status": "processing",
            "updated_at": datetime.now().isoformat()
        })
        
        # Check if TEST_MODE is enabled
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        
        if test_mode:
            print("TEST MODE: generating fake clips")
            video_path = generate_test_video_clips(job_id, job_data["prompt"])
        else:
            # Real Replicate video generation
            print("REAL MODE: using Replicate API")
            
            # Check for Replicate API token
            api_token = os.getenv("REPLICATE_API_TOKEN")
            if not api_token:
                raise ValueError("REPLICATE_API_TOKEN not found in environment variables")
            
            print("Sending request to Replicate...")
            
            # Import Replicate SDK
            import replicate
            
            # Use zeroscope text-to-video model
            print(f"Generating video for prompt: {job_data['prompt']}")
            
            # Run Replicate model
            output = replicate.run(
                "cjwbw/zeroscope-v2-xl",
                input={
                    "prompt": job_data["prompt"],
                    "num_frames": 48,  # ~2 seconds at 24fps
                    "width": 854,
                    "height": 480,
                    "guidance_scale": 7.5
                }
            )
            
            print("Video generation completed")
            video_url = output
            
            # Download the generated video
            print("Downloading video...")
            video_path = download_video_from_url(video_url, job_id)
            
            if not video_path:
                raise ValueError("Failed to download video from Replicate")
        
        print("Video saved successfully")
        
        # Update job as completed
        queue_service.update_job(job_id, {
            "status": "completed",
            "video_path": video_path,
            "updated_at": datetime.now().isoformat()
        })
        
        print(f"Job {job_id} completed successfully")
        print(f"Final video: {video_path}")
        
    except Exception as e:
        print(f"ERROR: Job {job_id} failed: {str(e)}")
        queue_service.update_job(job_id, {
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.now().isoformat()
        })


def generate_test_video_clips(job_id: str, prompt: str) -> str:
    """Generate fake video clips using MoviePy for testing."""
    
    try:
        print("TEST MODE: Creating fake video clips...")
        
        # Create temporary directory for clips
        os.makedirs("temp/clips", exist_ok=True)
        
        clips = []
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Red, Green, Blue
        duration = 3  # 3 seconds per clip
        
        for i in range(3):
            print(f"Creating fake clip {i+1}...")
            
            # Create colored background
            bg_clip = ColorClip(size=(854, 480), color=colors[i], duration=duration)
            
            # Add text overlay
            txt_clip = TextClip(
                f"Clip {i+1}\n{prompt[:30]}...",
                fontsize=60,
                color='white',
                bg_color='transparent'
            ).set_position('center').set_duration(duration)
            
            # Composite video
            composite = CompositeVideoClip([bg_clip, txt_clip])
            
            # Save clip
            clip_path = f"temp/clips/test_clip_{i+1}.mp4"
            composite.write_videofile(
                clip_path,
                fps=24,
                codec='libx264',
                audio=False,
                verbose=False,
                logger=None
            )
            
            clips.append(VideoFileClip(clip_path))
            print(f"Created clip {i+1}: {clip_path}")
            
            # Clean up
            composite.close()
            bg_clip.close()
            txt_clip.close()
        
        print("Merging clips...")
        
        # Merge clips
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Ensure videos directory exists
        os.makedirs("videos", exist_ok=True)
        
        # Save final video
        output_path = f"videos/{job_id}.mp4"
        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio=False,
            verbose=False,
            logger=None
        )
        
        # Clean up
        for clip in clips:
            clip.close()
        final_video.close()
        
        print(f"TEST MODE: Successfully created merged video: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error generating test video: {str(e)}")
        return None


def download_video_from_url(video_url: str, job_id: str) -> str:
    """Download video from Replicate URL and save locally."""
    
    try:
        # Ensure videos directory exists
        os.makedirs("videos", exist_ok=True)
        
        # Download video
        response = requests.get(video_url, timeout=300)  # 5 minute timeout
        
        if response.status_code != 200:
            print(f"Failed to download video: HTTP {response.status_code}")
            return None
        
        # Save video locally
        video_path = f"videos/{job_id}.mp4"
        
        with open(video_path, "wb") as f:
            f.write(response.content)
        
        print(f"Video downloaded and saved to: {video_path}")
        return video_path
        
    except Exception as e:
        print(f"Error downloading video: {str(e)}")
        return None
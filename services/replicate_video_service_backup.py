"""
Replicate video generation service.
"""
import os
import cv2
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Replicate configuration
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

def generate_video(prompt: str) -> str:
    """Generate cinematic video using Replicate API with SDXL fallback pipeline."""
    
    # Check TEST_MODE first
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    
    if test_mode:
        print("TEST_MODE enabled - returning local test video")
        return "/videos/test_video.mp4"
    
    # Verify token loading
    if not REPLICATE_API_TOKEN:
        print("ERROR: REPLICATE_API_TOKEN not configured")
        return "/videos/test_video.mp4"
    
    print(f"Replicate API token loaded (length: {len(REPLICATE_API_TOKEN)})")
    
    print("Replicate video generation started")
    print(f"Prompt: {prompt}")
    
    try:
        import replicate
        
        print("Using SDXL fallback pipeline")
        
        # Generate image using SDXL
        image = replicate.run(
            "stability-ai/sdxl",
            input={
                "prompt": prompt
            }
        )
        
        print("SDXL image generated")
        image_url = image[0]
        print(f"Image URL: {image_url}")
        
        # Download and save image as frame
        frame_path = download_and_save_image(image_url)
        
        # Create simple video from image
        video_path = create_video_from_image(frame_path)
        
        return video_path
        
    except Exception as e:
        print(f"ERROR: Replicate video generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return "/videos/test_video.mp4"


def download_and_save_image(image_url: str) -> str:
    """Download image from Replicate and save as frame."""
    
    try:
        print(f"Downloading image from: {image_url}")
        
        # Download image
        response = requests.get(image_url, timeout=60)
        
        if response.status_code != 200:
            print(f"Failed to download image: {response.status_code}")
            return None
        
        # Save image as frame
        frame_path = os.path.join("videos", "frame.jpg")
        
        # Ensure videos directory exists
        os.makedirs("videos", exist_ok=True)
        
        with open(frame_path, "wb") as f:
            f.write(response.content)
        
        print(f"Image saved as frame: {frame_path}")
        return frame_path
        
    except Exception as e:
        print(f"ERROR: Image download failed: {str(e)}")
        return None


def create_video_from_image(frame_path: str) -> str:
    """Create simple 3-second video from image using OpenCV."""
    
    try:
        if not frame_path or not os.path.exists(frame_path):
            print("ERROR: Frame image not available")
            return "/videos/test_video.mp4"
        
        print(f"Creating video from image: {frame_path}")
        
        # Read the image
        frame = cv2.imread(frame_path)
        if frame is None:
            print("ERROR: Could not read frame image")
            return "/videos/test_video.mp4"
        
        # Get video dimensions
        height, width, layers = frame.shape
        size = (width, height)
        
        # Create video writer
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"sdxl_video_{timestamp}.mp4"
        video_path = os.path.join("videos", video_filename)
        
        # Use MP4V codec for compatibility
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 30
        duration = 3  # 3 seconds
        total_frames = fps * duration
        
        # Create video writer
        out = cv2.VideoWriter(video_path, fourcc, fps, size)
        
        # Write the same frame for 3 seconds
        for i in range(total_frames):
            out.write(frame)
        
        # Release video writer
        out.release()
        
        print(f"Video created successfully: {video_path}")
        return video_filename
        
    except Exception as e:
        print(f"ERROR: Video creation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return "/videos/test_video.mp4"


def download_and_save_video(video_url: str) -> str:
    """Download video from Replicate and save locally."""
    
    try:
        print(f"Downloading video from: {video_url}")
        
        # Download video
        response = requests.get(video_url, timeout=60)
        
        if response.status_code != 200:
            print(f"Failed to download video: {response.status_code}")
            return "/videos/test_video.mp4"
        
        # Save video locally
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"replicate_video_{timestamp}.mp4"
        filepath = os.path.join("videos", filename)
        
        # Ensure videos directory exists
        os.makedirs("videos", exist_ok=True)
        
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        print(f"Video saved locally: {filepath}")
        return filename
        
    except Exception as e:
        print(f"ERROR: Video download failed: {str(e)}")
        return "/videos/test_video.mp4"


def create_cinematic_prompt(story: str) -> str:
    """Convert user story into cinematic prompt."""
    
    cinematic_prompt = f"cinematic scene: {story}, dramatic lighting, film look, ultra realistic, 4k, shallow depth of field, cinematic composition"
    
    print(f"Generated cinematic prompt: {cinematic_prompt}")
    return cinematic_prompt

import os
import traceback
from datetime import datetime
from typing import List

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from services.face_swap_service import process_face, simple_face_swap
from services.replicate_video_service import generate_video, create_cinematic_prompt

app = FastAPI()

# CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("videos", exist_ok=True)
os.makedirs("temp", exist_ok=True)

app.mount("/videos", StaticFiles(directory="videos"), name="videos")
app.mount("/temp", StaticFiles(directory="temp"), name="temp")


# -----------------------------
# STORY SPLIT
# -----------------------------
def split_story(story: str, n: int):
    words = story.split()
    chunk = len(words) // n
    return [
        " ".join(words[i * chunk:(i + 1) * chunk])
        for i in range(n)
    ]


# -----------------------------
# MAIN GENERATION
# -----------------------------
def generate_story_video(story: str, scenes: int, face_image=None):
    """Generate story video with optional face swap."""
    
    # Check if TEST_MODE is enabled and return dummy video immediately
    from utils.config import TEST_MODE
    if TEST_MODE:
        print("TEST_MODE enabled - returning dummy video")
        return {"video_url": "test_video.mp4", "face_url": None}
    
    # Step 1: Process uploaded face image
    processed_face = None
    if face_image:
        print("Processing uploaded face image...")
        processed_face = process_face_swap(face_image)
    
    # Step 2: Generate video using Replicate
    print("Generating video with Replicate...")
    
    # Create cinematic prompt
    cinematic_prompt = create_cinematic_prompt(story)
    
    # Generate video with Replicate
    video_filename = generate_video(cinematic_prompt)
    
    # Return both face and video URLs
    result = {"video_url": video_filename}
    
    if processed_face:
        print("Face processing completed successfully")
        face_filename = os.path.basename(processed_face)
        result["face_url"] = face_filename
    else:
        result["face_url"] = None
    
    return result


def process_face_swap(face_image):
    """Process uploaded face image for local face swapping."""
    print(f"Processing local face swap for: {face_image.filename}")
    
    # Save uploaded face image temporarily
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_filename = f"temp_face_{timestamp}.jpg"
    temp_path = os.path.join("temp", temp_filename)
    
    # Ensure temp directory exists
    os.makedirs("temp", exist_ok=True)
    
    # Save uploaded face image
    with open(temp_path, "wb") as f:
        f.write(face_image.file.read())
    
    print(f"Face saved temporarily: {temp_filename}")
    
    # Use default target image
    target_image_path = "assets/default_target.jpg"
    
    # Use local face swap service
    print("Using local face swap instead of Replicate")
    processed_path = simple_face_swap(temp_path, target_image_path)
    
    return processed_path


def merge_face_with_video(face_path, video_path):
    """Merge processed face with video (placeholder)."""
    print(f"Merging face {face_path} with video {video_path}")
    # TODO: Implement actual face merge
    # For now, return original video
    return video_path


# -----------------------------
# API ENDPOINT
# -----------------------------
@app.post("/generate-story-video")
async def generate_story_video_endpoint(
    request: Request,
    story: str = Form(...),
    scenes: int = Form(2),
    face_image: UploadFile = File(None)
):
    try:
        result = generate_story_video(story, scenes, face_image)
        
        # Handle response format
        if result.get("face_url"):
            # Face processing result
            face_url = str(request.base_url) + "videos/" + result["face_url"]
            print(f"Final clean URL: {face_url}")
            return {
                "success": True,
                "face_url": face_url,
                "video_url": None
            }
        else:
            # Video generation result
            video_url = str(request.base_url) + "videos/" + result["video_url"]
            print(f"Final clean URL: {video_url}")
            return {
                "success": True,
                "face_url": None,
                "video_url": video_url
            }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
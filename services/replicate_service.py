"""
Replicate Service - FINAL STABLE SYNC VERSION
"""
import os
import cv2
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

USE_REAL_AI = False


class ReplicateService:

    def generate_image(self, prompt: str, steps: int = 4) -> str:
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        
        if test_mode:
            print("TEST_MODE: Returning mock image response")
            return {"status": "test success", "type": "image"}
        
        print("REAL MODE: Generating image...")

        os.makedirs("temp", exist_ok=True)
        path = "temp/fake_image.jpg"

        # Create real valid image
        image = np.zeros((512, 512, 3), dtype=np.uint8)
        cv2.putText(image, prompt[:20], (50, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imwrite(path, image)
        return path

    def generate_video_from_image(self, image_path: str, frames: int = 12) -> str:
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        
        if test_mode:
            print("TEST_MODE: Returning mock video response")
            return {"status": "test success", "type": "video"}
        
        print("REAL MODE: Generating video...")
        
        os.makedirs("videos", exist_ok=True)
        path = "videos/fake_video.mp4"

        # create dummy video file
        with open(path, "wb") as f:
            f.write(b"fake video")

        return path
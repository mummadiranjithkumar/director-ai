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
        print("⚠️ FAKE IMAGE MODE")

        os.makedirs("temp", exist_ok=True)
        path = "temp/fake_image.jpg"

        # Create real valid image
        image = np.zeros((512, 512, 3), dtype=np.uint8)
        cv2.putText(image, prompt[:20], (50, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imwrite(path, image)
        return path

    def generate_video_from_image(self, image_path: str, frames: int = 12) -> str:
        print("⚠️ FAKE VIDEO MODE")

        os.makedirs("videos", exist_ok=True)
        path = "videos/fake_video.mp4"

        # create dummy video file
        with open(path, "wb") as f:
            f.write(b"fake video")

        return path
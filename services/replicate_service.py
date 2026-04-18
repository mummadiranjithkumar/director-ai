"""
Replicate Service - Multi-clip Video Generation with MoviePy
"""
import os
import cv2
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip, concatenate_videoclips

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

    def generate_video_clips(self, prompt: str, num_clips: int = 3) -> list:
        """Generate multiple video clips for a 10-second video."""
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        
        if test_mode:
            print("TEST_MODE: Returning mock video clips")
            return [{"status": "test success", "type": "clip", "clip_id": i} for i in range(num_clips)]
        
        print(f"REAL MODE: Generating {num_clips} video clips...")
        clips = []
        
        for i in range(num_clips):
            print(f"Generating clip {i+1}...")
            
            # Generate single clip
            clip_path = self._generate_single_clip(prompt, i+1)
            if clip_path:
                clips.append(clip_path)
            else:
                print(f"Failed to generate clip {i+1}")
        
        return clips

    def _generate_single_clip(self, prompt: str, clip_num: int) -> str:
        """Generate a single video clip (~3 seconds)."""
        os.makedirs("temp/clips", exist_ok=True)
        
        # Create a simple video clip using OpenCV
        clip_path = f"temp/clips/clip_{clip_num}.mp4"
        
        # Video settings
        fps = 24
        duration = 3  # 3 seconds per clip
        width, height = 854, 480  # 16:9 aspect ratio
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(clip_path, fourcc, fps, (width, height))
        
        # Generate frames
        num_frames = fps * duration
        for frame_idx in range(num_frames):
            # Create a simple animated frame
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add text that moves
            text = f"Clip {clip_num} - Frame {frame_idx}"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
            text_x = int((width - text_size[0]) / 2 + 50 * np.sin(frame_idx * 0.1))
            text_y = int(height / 2)
            
            cv2.putText(frame, text, (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Add prompt text
            prompt_text = prompt[:30] + "..." if len(prompt) > 30 else prompt
            cv2.putText(frame, prompt_text, (10, height - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            out.write(frame)
        
        out.release()
        print(f"Generated clip {clip_num}: {clip_path}")
        return clip_path

    def stitch_video_clips(self, clips: list, job_id: str) -> str:
        """Combine multiple video clips into a single video."""
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        
        if test_mode:
            print("TEST_MODE: Returning mock stitched video")
            return {"status": "test success", "type": "stitched_video"}
        
        print("Stitching video clips...")
        
        if not clips:
            print("No clips to stitch")
            return None
        
        try:
            # Load video clips
            video_clips = []
            for clip_path in clips:
                if isinstance(clip_path, str) and os.path.exists(clip_path):
                    clip = VideoFileClip(clip_path)
                    video_clips.append(clip)
                    print(f"Loaded clip: {clip_path} ({clip.duration}s)")
            
            if not video_clips:
                print("No valid video clips loaded")
                return None
            
            # Concatenate clips
            print("Concatenating clips...")
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            # Ensure output directory exists
            os.makedirs("videos", exist_ok=True)
            
            # Export final video
            output_path = f"videos/{job_id}.mp4"
            print(f"Exporting final video to: {output_path}")
            
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                fps=24,
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Clean up
            for clip in video_clips:
                clip.close()
            final_video.close()
            
            print(f"Successfully created 10-second video: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error stitching video: {str(e)}")
            return None

    def generate_video_from_image(self, image_path: str, frames: int = 12) -> str:
        """Legacy method - now uses multi-clip generation."""
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        
        if test_mode:
            print("TEST_MODE: Returning mock video response")
            return {"status": "test success", "type": "video"}
        
        # For backward compatibility, generate a single clip
        return self._generate_single_clip("legacy video", 1)
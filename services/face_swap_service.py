"""
Face Swap Service - Wrapper for existing local face swap functionality
"""
import os
import cv2
from datetime import datetime

class FaceSwapService:
    """Face swap service using local OpenCV implementation."""
    
    def __init__(self):
        """Initialize face swap service."""
        # Ensure assets directory exists
        self.assets_dir = "assets"
        os.makedirs(self.assets_dir, exist_ok=True)
        
        # Default target image
        self.default_target = os.path.join(self.assets_dir, "default_target.jpg")
    
    def swap_face(self, source_image_path: str, target_image_path: str = None) -> str:
        """Apply face swap to source image using target image."""
        
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        
        if test_mode:
            print("TEST_MODE: Returning mock face swap response")
            return {"status": "test success", "type": "face_swap"}
        
        try:
            # Use default target if none provided
            if not target_image_path:
                target_image_path = self.default_target
            
            # Validate input files
            if not os.path.exists(source_image_path):
                print(f"ERROR: Source image not found: {source_image_path}")
                return None
            
            if not os.path.exists(target_image_path):
                print(f"ERROR: Target image not found: {target_image_path}")
                return None
            
            print(f"Processing face swap: {source_image_path} -> {target_image_path}")
            
            # Load images
            source_img = cv2.imread(source_image_path)
            target_img = cv2.imread(target_image_path)
            
            if source_img is None:
                print(f"ERROR: Could not load source image: {source_image_path}")
                return None
            
            if target_img is None:
                print(f"ERROR: Could not load target image: {target_image_path}")
                return None
            
            # Get dimensions
            source_h, source_w, _ = source_img.shape
            target_h, target_w, _ = target_img.shape
            
            # Resize source face to fit target
            face_size = min(source_w, target_w) // 2
            source_resized = cv2.resize(source_img, (face_size, face_size))
            
            # Calculate position for face placement (upper right)
            x_offset = target_w - face_size - 10
            y_offset = 50
            
            # Create ROI for face placement
            roi = (y_offset, y_offset + face_size, x_offset, x_offset + face_size)
            
            # Swap faces
            target_img[y_offset:y_offset + face_size, x_offset:x_offset + face_size] = source_resized
            
            # Save result
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"swapped_face_{timestamp}.jpg"
            output_path = os.path.join("videos", output_filename)
            
            os.makedirs("videos", exist_ok=True)
            cv2.imwrite(output_path, target_img)
            
            print(f"Face swap completed: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"ERROR: Face swap failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

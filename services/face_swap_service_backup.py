"""
Local face swap service using OpenCV.
"""
import os
import cv2
import numpy as np
from datetime import datetime


def simple_face_swap(source_image_path: str, target_image_path: str) -> str:
    """Simple face swap using OpenCV."""
    
    print("Local face swap started")
    print(f"Source image: {source_image_path}")
    print(f"Target image: {target_image_path}")
    
    try:
        # Use absolute paths
        source_abs_path = os.path.abspath(source_image_path)
        target_abs_path = os.path.abspath(target_image_path)
        
        print(f"Absolute source path: {source_abs_path}")
        print(f"Absolute target path: {target_abs_path}")
        
        # Validate target image exists
        if not os.path.exists(target_abs_path):
            print(f"ERROR: Target image not found: {target_abs_path}")
            return None
        
        # Load images
        source_img = cv2.imread(source_abs_path)
        target_img = cv2.imread(target_abs_path)
        
        if source_img is None:
            print(f"ERROR: Could not load source image: {source_abs_path}")
            return None
        
        if target_img is None:
            print(f"ERROR: Could not load target image: {target_abs_path}")
            return None
        
        print("Target image loaded successfully")
        print(f"Source image shape: {source_img.shape}")
        print(f"Target image shape: {target_img.shape}")
        
        # Get dimensions
        h, w = target_img.shape[:2]
        
        # Resize source face to fit proportionally
        # Calculate scaling factor to fit within 1/3 of target image
        max_face_size = min(w, h) // 3
        source_h, source_w = source_img.shape[:2]
        
        # Calculate scaling factor
        scale_factor = min(max_face_size / source_w, max_face_size / source_h)
        new_w = int(source_w * scale_factor)
        new_h = int(source_h * scale_factor)
        
        # Resize source image
        resized_source = cv2.resize(source_img, (new_w, new_h))
        
        print(f"Resized source to: {new_w}x{new_h}")
        
        # Calculate position to place face (center of target)
        start_x = (w - new_w) // 2
        start_y = (h - new_h) // 2
        
        print(f"Placing face at position: ({start_x}, {start_y})")
        
        # Create a copy of target image
        result_img = target_img.copy()
        
        # Simple overlay: place resized source face on target
        # Ensure we don't go out of bounds
        end_x = min(start_x + new_w, w)
        end_y = min(start_y + new_h, h)
        
        # Place the face with simple blending
        result_img[start_y:end_y, start_x:end_x] = resized_source[:end_y-start_y, :end_x-start_x]
        
        # Save result to videos folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"swapped_face_{timestamp}.jpg"
        output_path = os.path.join("videos", output_filename)
        
        # Ensure videos directory exists
        os.makedirs("videos", exist_ok=True)
        
        # Save the result
        cv2.imwrite(output_path, result_img)
        
        print(f"Face swap completed")
        print(f"Saved at: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"ERROR: Face swap failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def process_face(face_image):
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
    processed_path = simple_face_swap(temp_path, target_image_path)
    
    return processed_path

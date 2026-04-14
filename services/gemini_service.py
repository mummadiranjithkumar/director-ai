"""
Gemini API service for scene prompt generation.
"""
import os
from typing import List

# Import configuration
from utils.config import GEMINI_API_KEY, TEST_MODE

def generate_scene_prompts(story: str, num_scenes: int) -> List[str]:
    """Generate scene prompts using Gemini API."""
    try:
        print("Generating scene prompts with Gemini")
        
        # For now, return basic scene splitting logic
        # This can be enhanced with actual Gemini API calls later
        sentences = [s.strip() for s in story.split('.') if s.strip()]
        
        # Limit scenes in TEST_MODE
        if TEST_MODE:
            num_scenes = min(1, num_scenes)  # Limit to 1 scene in test mode
            print(f"🧪 TEST MODE: Limiting scenes to {num_scenes}")
        
        # Ensure we have exactly the requested number of scenes
        scenes = []
        if len(sentences) >= num_scenes:
            scenes = sentences[:num_scenes]
        else:
            # Not enough sentences, extend content
            scenes = sentences.copy()
            while len(scenes) < num_scenes:
                if len(scenes) > 0:
                    # Duplicate and modify last scene
                    base_scene = scenes[-1]
                    modified_scene = f"{base_scene} (continued)"
                    scenes.append(modified_scene)
                else:
                    scenes.append(story)
        
        scenes = scenes[:num_scenes]
        
        print(f"Generated {len(scenes)} scene prompts")
        return scenes
        
    except Exception as e:
        print(f"Gemini service error: {str(e)}")
        # Fallback to basic splitting
        sentences = [s.strip() for s in story.split('.') if s.strip()]
        return sentences[:num_scenes]

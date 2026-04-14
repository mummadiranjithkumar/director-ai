"""
Queue Service - Redis job management
"""
import os
import json
import redis
from datetime import datetime
from typing import Dict, Optional

class QueueService:
    """Redis-based job queue management."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True
        )
        self.job_prefix = "director:job:"
        
    def add_job(self, job_data: Dict) -> bool:
        """Add job to Redis queue."""
        try:
            # Store job data
            job_key = f"{self.job_prefix}{job_data['id']}"
            self.redis_client.set(job_key, json.dumps(job_data))
            
            # Add to processing queue
            queue_data = {
                "job_id": job_data["id"],
                "action": "process",
                "timestamp": datetime.now().isoformat()
            }
            self.redis_client.lpush("director:queue", json.dumps(queue_data))
            
            print(f"Job {job_data['id']} added to queue")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to add job to queue: {str(e)}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID."""
        try:
            job_key = f"{self.job_prefix}{job_id}"
            job_data = self.redis_client.get(job_key)
            
            if job_data:
                return json.loads(job_data)
            return None
            
        except Exception as e:
            print(f"ERROR: Failed to get job {job_id}: {str(e)}")
            return None
    
    def update_job(self, job_id: str, updates: Dict) -> bool:
        """Update job status and data."""
        try:
            job_key = f"{self.job_prefix}{job_id}"
            
            # Get current job data
            current_data = self.get_job(job_id)
            if not current_data:
                return False
            
            # Update with new data
            updated_data = {**current_data, **updates}
            updated_data["updated_at"] = datetime.now().isoformat()
            
            # Save updated job
            self.redis_client.set(job_key, json.dumps(updated_data))
            
            print(f"Job {job_id} updated: {updates}")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to update job {job_id}: {str(e)}")
            return False
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        try:
            return self.redis_client.llen("director:queue")
        except Exception as e:
            print(f"ERROR: Failed to get queue size: {str(e)}")
            return 0

"""
Queue Service - In-Memory (NO REDIS)
"""

from datetime import datetime
from typing import Dict, Optional

class QueueService:
    def __init__(self):
        self.jobs = {}

    def add_job(self, job_data: Dict) -> bool:
        try:
            self.jobs[job_data["id"]] = job_data
            print(f"Job {job_data['id']} added")
            return True
        except Exception as e:
            print(f"ERROR adding job: {str(e)}")
            return False

    def get_job(self, job_id: str) -> Optional[Dict]:
        return self.jobs.get(job_id)

    def update_job(self, job_id: str, updates: Dict) -> bool:
        if job_id not in self.jobs:
            print(f"Job {job_id} not found")
            return False

        self.jobs[job_id].update(updates)
        self.jobs[job_id]["updated_at"] = datetime.now().isoformat()

        print(f"Job {job_id} updated: {updates}")
        return True

    def get_queue_size(self) -> int:
        return len(self.jobs)
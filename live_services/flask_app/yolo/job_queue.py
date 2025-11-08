import threading
from collections import deque
from models import Job, JobStatus
from datetime import datetime

class JobQueue:
    def __init__(self):
        self.jobs = {}
        self.queue = deque()
        self.lock = threading.Lock()
        self.current_job = None
        
    def add_job(self, job: Job):
        with self.lock:
            self.jobs[job.job_id] = job
            self.queue.append(job.job_id)
            job.status = JobStatus.PENDING
    
    def get_job(self, job_id: str):
        with self.lock:
            return self.jobs.get(job_id)
    
    def update_job(self, job_id: str, **kwargs):
        with self.lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                for key, value in kwargs.items():
                    if hasattr(job, key):
                        setattr(job, key, value)
    
    def get_next_job(self):
        with self.lock:
            if self.current_job:
                current = self.jobs.get(self.current_job)
                if current and current.status == JobStatus.PROCESSING:
                    return None
            
            while self.queue:
                job_id = self.queue.popleft()
                job = self.jobs.get(job_id)
                if job and job.status == JobStatus.PENDING:
                    job.status = JobStatus.PROCESSING
                    job.started_at = datetime.now()
                    self.current_job = job_id
                    return job
            return None
    
    def complete_job(self, job_id: str):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id].status = JobStatus.COMPLETED
                self.jobs[job_id].completed_at = datetime.now()
                if self.current_job == job_id:
                    self.current_job = None
    
    def fail_job(self, job_id: str, error_message: str):
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id].status = JobStatus.ERROR
                self.jobs[job_id].error_message = error_message
                self.jobs[job_id].completed_at = datetime.now()
                if self.current_job == job_id:
                    self.current_job = None
    
    def get_all_jobs(self):
        with self.lock:
            return [job.to_dict() for job in self.jobs.values()]

job_queue = JobQueue()


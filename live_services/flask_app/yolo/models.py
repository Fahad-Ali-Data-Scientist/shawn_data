from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class JobType(Enum):
    VIDEO = "video"
    COUNTING = "counting"

@dataclass
class Job:
    job_id: str
    job_type: JobType
    filename: str
    status: JobStatus
    progress: int = 0
    current_frame: int = 0
    total_frames: int = 0
    unique_objects: int = 0
    class_counts: dict = None
    output_filename: str = ""
    error_message: str = ""
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.class_counts is None:
            self.class_counts = {}
    
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'job_type': self.job_type.value,
            'filename': self.filename,
            'status': self.status.value,
            'progress': self.progress,
            'current_frame': self.current_frame,
            'total_frames': self.total_frames,
            'unique_objects': self.unique_objects,
            'class_counts': self.class_counts,
            'output_filename': self.output_filename,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict

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

@dataclass
class LiveCameraSession:
    """Model for live camera detection sessions"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    frame_count: int = 0
    detections_history: list = field(default_factory=list)
    class_counts: Dict[str, int] = field(default_factory=dict)
    total_objects_detected: int = 0
    
    def add_detection(self, detections):
        """Add detection result to session history"""
        self.frame_count += 1
        timestamp = datetime.now()
        
        # Update class counts
        for detection in detections:
            class_name = detection['class']
            self.class_counts[class_name] = self.class_counts.get(class_name, 0) + 1
        
        # Store detection entry
        self.detections_history.append({
            'frame': self.frame_count,
            'timestamp': timestamp.isoformat(),
            'detections': detections,
            'count': len(detections)
        })
        
        self.total_objects_detected += len(detections)
    
    def get_summary(self):
        """Get summary statistics for the session"""
        return {
            'session_id': self.session_id,
            'duration': (datetime.now() - self.created_at).total_seconds(),
            'total_frames': self.frame_count,
            'total_objects': self.total_objects_detected,
            'class_counts': self.class_counts,
            'avg_objects_per_frame': self.total_objects_detected / self.frame_count if self.frame_count > 0 else 0
        }
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'frame_count': self.frame_count,
            'total_objects_detected': self.total_objects_detected,
            'class_counts': self.class_counts,
            'detections_history': self.detections_history
        }


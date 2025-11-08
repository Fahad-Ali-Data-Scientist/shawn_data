import threading
import time
from models import JobStatus

class Worker:
    def __init__(self, model, tracker_cfg, conf, iou, imgsz, device, job_queue, upload_folder, output_folder):
        self.model = model
        self.tracker_cfg = tracker_cfg
        self.conf = conf
        self.iou = iou
        self.imgsz = imgsz
        self.device = device
        self.job_queue = job_queue
        self.upload_folder = upload_folder
        self.output_folder = output_folder
        self.running = False
        self.thread = None
    
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._process_jobs, daemon=True)
            self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _process_jobs(self):
        from video_processor import process_video
        import os
        
        while self.running:
            job = self.job_queue.get_next_job()
            
            if job:
                input_path = os.path.join(self.upload_folder, f"{job.job_id}_input.mp4")
                output_filename = f"{job.job_id}_output.mp4"
                output_path = os.path.join(self.output_folder, output_filename)
                
                self.job_queue.update_job(job.job_id, output_filename=output_filename)
                
                process_video(
                    self.model,
                    job,
                    input_path,
                    output_path,
                    self.tracker_cfg,
                    self.conf,
                    self.iou,
                    self.imgsz,
                    self.device,
                    self.job_queue
                )
            else:
                time.sleep(1)


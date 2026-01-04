import cv2
import os
from collections import defaultdict
from .models import JobType
from .deepsort_tracker import DeepSORTTracker

def process_video(model, job, input_path, output_path, tracker_cfg, conf, iou, imgsz, device, job_queue):
    try:
        cap = cv2.VideoCapture(input_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        job_queue.update_job(job.job_id, total_frames=total_frames)
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        if job.job_type == JobType.COUNTING:
            result = process_video_counting(model, job, input_path, writer, tracker_cfg, conf, iou, imgsz, device, job_queue, total_frames)
        else:
            result = process_video_simple(model, job, input_path, writer, conf, iou, imgsz, job_queue, total_frames)
        
        writer.release()
        
        # Create compressed version for viewing
        compressed_path = output_path.replace('_output.mp4', '_view.mp4')
        compress_video(output_path, compressed_path)
        
        job_queue.complete_job(job.job_id)
        
    except Exception as e:
        job_queue.fail_job(job.job_id, str(e))
        if 'writer' in locals():
            writer.release()

def compress_video(input_path, output_path, target_height=720):
    """Compress video for web viewing while maintaining aspect ratio"""
    try:
        cap = cv2.VideoCapture(input_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Calculate new dimensions maintaining aspect ratio
        if height > target_height:
            new_height = target_height
            new_width = int((target_height / height) * width)
        else:
            new_width = width
            new_height = height
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, fps, (new_width, new_height))
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if height > target_height:
                frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            writer.write(frame)
        
        cap.release()
        writer.release()
        
    except Exception as e:
        print(f"Error compressing video: {e}")
        # If compression fails, copy original
        import shutil
        shutil.copy(input_path, output_path)

def process_video_simple(model, job, input_path, writer, conf, iou, imgsz, job_queue, total_frames):
    results = model(input_path, stream=True, conf=conf, iou=iou, imgsz=imgsz, verbose=False)
    
    frame_count = 0
    for result in results:
        frame = result.plot()
        writer.write(frame)
        frame_count += 1
        
        progress = int((frame_count / total_frames) * 100) if total_frames > 0 else 0
        job_queue.update_job(job.job_id, progress=progress, current_frame=frame_count)

def process_video_counting(model, job, input_path, writer, tracker_cfg, conf, iou, imgsz, device, job_queue, total_frames):
    # Initialize Deep SORT tracker
    deepsort_tracker = DeepSORTTracker(
        max_age=30,
        n_init=3,
        nms_max_overlap=1.0,
        max_cosine_distance=0.2,
        embedder="mobilenet",
        half=True,
        bgr=True
    )
    
    # Run YOLO detection in streaming mode (without built-in tracking)
    results_stream = model.predict(
        source=input_path,
        stream=True,
        conf=conf,
        iou=iou,
        imgsz=imgsz,
        device=device,
        verbose=False
    )
    
    frame_count = 0
    for result in results_stream:
        frame = result.orig_img  # Get original BGR frame
        if frame is None:
            continue
        
        # Update Deep SORT tracker with detections
        tracks = deepsort_tracker.update(result.boxes, frame)
        
        # Draw tracks on frame
        frame = deepsort_tracker.draw_tracks(frame, tracks, model)
        
        # Draw counting overlay
        frame = deepsort_tracker.draw_overlay(frame)
        
        # Write frame
        writer.write(frame)
        frame_count += 1
        
        # Update job progress
        counts = deepsort_tracker.get_counts()
        progress = int((frame_count / total_frames) * 100) if total_frames > 0 else 0
        job_queue.update_job(
            job.job_id,
            progress=progress,
            current_frame=frame_count,
            unique_objects=counts['total'],
            class_counts=counts['per_class']
        )


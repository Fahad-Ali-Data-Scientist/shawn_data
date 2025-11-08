import cv2
import os
from collections import defaultdict
from models import JobType

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
    seen_ids_global = set()
    seen_ids_per_class = defaultdict(set)
    
    results_stream = model.track(
        source=input_path,
        tracker=tracker_cfg,
        stream=True,
        conf=conf,
        iou=iou,
        imgsz=imgsz,
        device=device,
        persist=True,
        verbose=False
    )
    
    frame_count = 0
    for result in results_stream:
        frame = result.plot()
        
        boxes = result.boxes
        if boxes is not None and len(boxes) > 0 and boxes.id is not None:
            ids = boxes.id.int().tolist()
            cls = boxes.cls.int().tolist()
            for tid, c in zip(ids, cls):
                cname = model.names.get(int(c), str(int(c)))
                seen_ids_global.add(int(tid))
                seen_ids_per_class[cname].add(int(tid))
        
        overlay_height = 40 + (len(seen_ids_per_class) * 30)
        cv2.rectangle(frame, (10, 10), (400, overlay_height), (0, 0, 0), -1)
        cv2.putText(frame, f"Total Unique Objects: {len(seen_ids_global)}",
                   (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        y_pos = 70
        for cls_name, ids in sorted(seen_ids_per_class.items(), key=lambda x: len(x[1]), reverse=True):
            cv2.putText(frame, f"{cls_name}: {len(ids)}",
                       (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y_pos += 30
        
        writer.write(frame)
        frame_count += 1
        
        progress = int((frame_count / total_frames) * 100) if total_frames > 0 else 0
        class_counts = {cls_name: len(ids) for cls_name, ids in seen_ids_per_class.items()}
        job_queue.update_job(
            job.job_id,
            progress=progress,
            current_frame=frame_count,
            unique_objects=len(seen_ids_global),
            class_counts=class_counts
        )

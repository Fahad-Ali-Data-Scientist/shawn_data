"""
Deep SORT Tracker Wrapper for YOLO Object Detection
Provides tracking functionality using deep-sort-realtime library
"""
import cv2
import numpy as np
from collections import defaultdict
from deep_sort_realtime.deepsort_tracker import DeepSort


class DeepSORTTracker:
    """
    Wrapper class for Deep SORT tracker optimized for YOLO detections
    """
    
    def __init__(self, max_age=30, n_init=3, nms_max_overlap=1.0, 
                 max_cosine_distance=0.2, embedder="torchreid", 
                 half=True, bgr=True):
        """
        Initialize Deep SORT tracker
        
        Args:
            max_age: Maximum number of frames to keep track without detection
            n_init: Number of consecutive detections before track is confirmed
            nms_max_overlap: Maximum overlap for NMS
            max_cosine_distance: Maximum cosine distance for matching
            embedder: Feature embedder type ("mobilenet" or "torchreid")
            half: Use half precision for embeddings
            bgr: Input images are in BGR format
        """
        self.tracker = DeepSort(
            max_age=max_age,
            n_init=n_init,
            nms_max_overlap=nms_max_overlap,
            max_cosine_distance=max_cosine_distance,
            embedder=embedder,
            half=half,
            bgr=bgr
        )
        
        # Counting structures
        self.seen_ids_global = set()
        self.seen_ids_per_class = defaultdict(set)
        
    def update(self, detections, frame):
        """
        Update tracker with new detections
        
        Args:
            detections: YOLO detection results (boxes object)
            frame: Current frame (BGR numpy array)
            model: YOLO model for class names
            
        Returns:
            tracks: List of Track objects from Deep SORT
        """
        # Build detections for Deep SORT: [[x1,y1,x2,y2], conf, class_name]
        dets = []
        if detections is not None and len(detections) > 0:
            xyxy = detections.xyxy.cpu().numpy()
            confs = detections.conf.cpu().numpy()
            clss = detections.cls.cpu().numpy().astype(int)
            
            for (x1, y1, x2, y2), cf, ci in zip(xyxy, confs, clss):
                dets.append([
                    [float(x1), float(y1), float(x2), float(y2)],
                    float(cf),
                    int(ci)  # Keep as int for now, will convert to name later
                ])
        
        # Update tracker
        tracks = self.tracker.update_tracks(dets, frame=frame)
        
        return tracks
    
    def update_counts(self, track, class_name):
        """
        Update counting statistics for a confirmed track
        
        Args:
            track: Deep SORT Track object
            class_name: Class name string
        """
        tid = int(track.track_id)
        self.seen_ids_global.add(tid)
        if class_name:
            self.seen_ids_per_class[class_name].add(tid)
    
    def draw_tracks(self, frame, tracks, model):
        """
        Draw tracking boxes and IDs on frame
        
        Args:
            frame: Frame to draw on
            tracks: List of Track objects
            model: YOLO model for class names
            
        Returns:
            frame: Frame with drawn tracks
        """
        for t in tracks:
            if not t.is_confirmed():
                continue
                
            tid = int(t.track_id)
            ltrb = t.to_ltrb()  # left, top, right, bottom
            x1, y1, x2, y2 = map(int, ltrb)
            
            # Get class name from detection
            cls_name = None
            if t.get_det_class() is not None:
                cls_idx = int(t.get_det_class())
                cls_name = model.names.get(cls_idx, str(cls_idx))
            
            # Update counts
            self.update_counts(t, cls_name)
            
            # Draw box + id
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"ID {tid}" + (f" | {cls_name}" if cls_name else "")
            
            # Draw text with background
            cv2.putText(frame, label, (x1, max(0, y1-7)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
            cv2.putText(frame, label, (x1, max(0, y1-7)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return frame
    
    def draw_overlay(self, frame):
        """
        Draw counting overlay on frame
        
        Args:
            frame: Frame to draw on
            
        Returns:
            frame: Frame with overlay
        """
        # Calculate overlay size
        overlay_height = 40 + (min(len(self.seen_ids_per_class), 3) * 30)
        cv2.rectangle(frame, (10, 10), (380, overlay_height), (0, 0, 0), -1)
        
        # Draw total count
        cv2.putText(frame, f"Unique objects: {len(self.seen_ids_global)}",
                   (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        
        # Draw top 3 classes
        top = sorted(((k, len(v)) for k, v in self.seen_ids_per_class.items()),
                    key=lambda x: x[1], reverse=True)[:3]
        y = 80
        for k, v in top:
            cv2.putText(frame, f"{k}: {v}", (20, y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
            y += 25
        
        return frame
    
    def get_counts(self):
        """
        Get current counting statistics
        
        Returns:
            dict: Dictionary with total and per-class counts
        """
        return {
            'total': len(self.seen_ids_global),
            'per_class': {cls_name: len(ids) for cls_name, ids in self.seen_ids_per_class.items()}
        }
    
    def reset(self):
        """Reset tracker and counts"""
        self.tracker = DeepSort(
            max_age=30,
            n_init=3,
            nms_max_overlap=1.0,
            max_cosine_distance=0.2,
            embedder="mobilenet",
            half=True,
            bgr=True
        )
        self.seen_ids_global = set()
        self.seen_ids_per_class = defaultdict(set)


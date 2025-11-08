"""
WebSocket handler for live camera detection
Manages real-time video stream processing and detection
"""
import uuid
from datetime import datetime
from .models import LiveCameraSession

# Store active sessions
active_sessions = {}

def create_session():
    """Create a new live camera session"""
    session_id = str(uuid.uuid4())
    session = LiveCameraSession(session_id=session_id)
    active_sessions[session_id] = session
    return session

def get_session(session_id):
    """Get an existing session"""
    return active_sessions.get(session_id)

def delete_session(session_id):
    """Delete a session"""
    if session_id in active_sessions:
        del active_sessions[session_id]

def process_frame(model, frame_data, session_id, conf=0.25, iou=0.45, imgsz=640):
    """
    Process a single frame from live camera feed
    
    Args:
        model: YOLO model instance
        frame_data: Base64 encoded image data or numpy array
        session_id: Session identifier
        conf: Confidence threshold
        iou: IOU threshold
        imgsz: Image size
    
    Returns:
        dict: Detection results with annotated image and statistics
    """
    import base64
    import io
    import numpy as np
    from PIL import Image
    
    try:
        # Get or create session
        session = get_session(session_id)
        if not session:
            session = create_session()
            session_id = session.session_id
        
        # Decode base64 image
        if isinstance(frame_data, str):
            # Remove data URL prefix if present
            if ',' in frame_data:
                frame_data = frame_data.split(',')[1]
            
            image_bytes = base64.b64decode(frame_data)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            frame = np.array(image)
            # Convert RGB to BGR for OpenCV/YOLO
            frame = frame[..., ::-1].copy()
        else:
            frame = frame_data
        
        # Run YOLO detection
        results = model(frame, conf=conf, iou=iou, imgsz=imgsz, verbose=False)
        result = results[0]
        
        # Get annotated frame
        annotated_frame = result.plot()
        
        # Convert back to RGB for web display
        annotated_rgb = annotated_frame[..., ::-1]
        
        # Convert to base64
        pil_image = Image.fromarray(annotated_rgb)
        buffered = io.BytesIO()
        pil_image.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Extract detections
        detections = []
        boxes = result.boxes
        if boxes is not None and len(boxes) > 0:
            cls_vals = boxes.cls.tolist() if hasattr(boxes.cls, 'tolist') else [int(x) for x in boxes.cls]
            conf_vals = boxes.conf.tolist() if hasattr(boxes.conf, 'tolist') else [float(x) for x in boxes.conf]
            
            for c, cf in zip(cls_vals, conf_vals):
                name = model.names.get(int(c), str(c))
                detections.append({
                    "class": name,
                    "confidence": float(cf)
                })
        
        # Update session with detection data
        session.add_detection(detections)
        
        # Calculate current frame statistics
        class_counts_current = {}
        for det in detections:
            class_name = det['class']
            class_counts_current[class_name] = class_counts_current.get(class_name, 0) + 1
        
        return {
            'success': True,
            'session_id': session_id,
            'annotated_image': f'data:image/jpeg;base64,{img_str}',
            'detections': detections,
            'current_counts': class_counts_current,
            'session_stats': {
                'total_frames': session.frame_count,
                'total_objects': session.total_objects_detected,
                'cumulative_counts': session.class_counts
            },
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"Error processing frame: {e}")
        return {
            'success': False,
            'error': str(e)
        }


from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from ultralytics import YOLO
from ultralytics.utils import ROOT
from PIL import Image
import io
import base64
import numpy as np
import os
import uuid
from datetime import datetime

# Import from utils package
from utils.models import Job, JobType, JobStatus, LiveCameraSession
from utils.job_queue import job_queue
from utils.worker import Worker
from utils.websocket_handler import create_session, get_session, delete_session, process_frame, active_sessions
from utils.export_handler import export_to_pdf, export_to_docx, export_to_excel

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

# Initialize SocketIO for WebSocket support
socketio = SocketIO(app, cors_allowed_origins="*", max_size=50 * 1024 * 1024)

# MODEL_PATH = "/home/ubuntu/Annotations/pending/runs/train/yolov11l_merged_new/weights/best.pt"
MODEL_PATH = '/home/ubuntu/Annotations/training/runs/train/yolov11l_merged_new2/weights/best.pt'  
TRACKER_CFG = str(ROOT / "cfg/trackers/bytetrack.yaml")
CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.45
IMGSZ = 640
DEVICE = "0"

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
EXPORT_FOLDER = 'exports'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(EXPORT_FOLDER, exist_ok=True)

print(f"Loading YOLO model from: {MODEL_PATH}")
model = YOLO(MODEL_PATH)
print("Model loaded successfully!")

worker = Worker(model, TRACKER_CFG, CONF_THRESHOLD, IOU_THRESHOLD, IMGSZ, DEVICE, job_queue, UPLOAD_FOLDER, OUTPUT_FOLDER)
worker.start()

def pil_bytes_to_bgr_numpy(image_bytes: bytes):
    pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    arr = np.array(pil)
    bgr = arr[..., ::-1].copy()
    return bgr

def numpy_img_to_data_uri(img_np: np.ndarray, fmt="png"):
    pil = Image.fromarray(img_np)
    buf = io.BytesIO()
    pil.save(buf, format=fmt.upper())
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/{fmt};base64,{data}"

# ============= HTTP ROUTES =============

@app.route("/")
def index():
    """Start page with two options"""
    return render_template("index.html")

@app.route("/video-detection")
def video_detection():
    """Video upload detection page (existing functionality)"""
    return render_template("video_detection.html")

@app.route("/live-camera")
def live_camera():
    """Live camera detection page (new functionality)"""
    return render_template("live_camera.html")

@app.route("/predict_image", methods=["POST"])
def predict_image():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        img_bytes = file.read()
        img_bgr = pil_bytes_to_bgr_numpy(img_bytes)

        results = model(img_bgr, conf=CONF_THRESHOLD, iou=IOU_THRESHOLD, imgsz=IMGSZ)
        res = results[0]

        annotated = res.plot()
        display_img = annotated[..., ::-1]

        data_uri = numpy_img_to_data_uri(display_img, fmt="png")

        detections = []
        boxes = res.boxes
        if boxes is not None and len(boxes) > 0:
            cls_vals = boxes.cls.tolist() if hasattr(boxes.cls, 'tolist') else [int(x) for x in boxes.cls]
            conf_vals = boxes.conf.tolist() if hasattr(boxes.conf, 'tolist') else [float(x) for x in boxes.conf]
            
            for c, cf in zip(cls_vals, conf_vals):
                name = model.names.get(int(c), str(c))
                detections.append({
                    "class": name,
                    "confidence": float(cf)
                })

        return jsonify({
            "success": True,
            "image": data_uri,
            "detections": detections,
            "total_detections": len(detections)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/predict_video", methods=["POST"])
def predict_video():
    if "video" not in request.files:
        return jsonify({"error": "No video provided"}), 400

    file = request.files["video"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        job_id = str(uuid.uuid4())
        input_filename = f"{job_id}_input.mp4"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        
        file.save(input_path)
        
        job = Job(
            job_id=job_id,
            job_type=JobType.VIDEO,
            filename=file.filename,
            status=JobStatus.PENDING
        )
        
        job_queue.add_job(job)
        
        return jsonify({
            "success": True,
            "job_id": job_id
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/predict_video_counting", methods=["POST"])
def predict_video_counting():
    if "video" not in request.files:
        return jsonify({"error": "No video provided"}), 400

    file = request.files["video"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        job_id = str(uuid.uuid4())
        input_filename = f"{job_id}_input.mp4"
        input_path = os.path.join(UPLOAD_FOLDER, input_filename)
        
        file.save(input_path)
        
        job = Job(
            job_id=job_id,
            job_type=JobType.COUNTING,
            filename=file.filename,
            status=JobStatus.PENDING
        )
        
        job_queue.add_job(job)
        
        return jsonify({
            "success": True,
            "job_id": job_id
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/job/<job_id>")
def get_job(job_id):
    job = job_queue.get_job(job_id)
    if job:
        return jsonify(job.to_dict())
    return jsonify({"error": "Job not found"}), 404

@app.route("/jobs")
def get_all_jobs():
    jobs = job_queue.get_all_jobs()
    return jsonify({"jobs": jobs})

@app.route("/download/<filename>")
def download_file(filename):
    try:
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True, download_name=f"detected_{filename}")
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/view/<filename>")
def view_file(filename):
    try:
        # Serve compressed version for viewing
        view_filename = filename.replace('_output.mp4', '_view.mp4')
        filepath = os.path.join(OUTPUT_FOLDER, view_filename)
        
        # Fallback to original if compressed doesn't exist
        if not os.path.exists(filepath):
            filepath = os.path.join(OUTPUT_FOLDER, filename)
        
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='video/mp4')
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============= EXPORT ROUTES =============

@app.route("/export/<format>/<session_id>", methods=["GET"])
def export_session(format, session_id):
    """Export live camera session data to PDF, DOCX, or Excel"""
    try:
        session = get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        # Get session data
        session_dict = session.to_dict()
        summary = session.get_summary()
        
        # Merge data
        export_data = {**session_dict, **summary}
        
        # Generate export based on format
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format.lower() == 'pdf':
            filename = f"detection_report_{timestamp}.pdf"
            output_path = os.path.join(EXPORT_FOLDER, filename)
            export_to_pdf(export_data, output_path)
            return send_file(output_path, as_attachment=True, download_name=filename)
        
        elif format.lower() == 'docx':
            filename = f"detection_report_{timestamp}.docx"
            output_path = os.path.join(EXPORT_FOLDER, filename)
            export_to_docx(export_data, output_path)
            return send_file(output_path, as_attachment=True, download_name=filename)
        
        elif format.lower() == 'excel' or format.lower() == 'xlsx':
            filename = f"detection_report_{timestamp}.xlsx"
            output_path = os.path.join(EXPORT_FOLDER, filename)
            export_to_excel(export_data, output_path)
            return send_file(output_path, as_attachment=True, download_name=filename)
        
        else:
            return jsonify({"error": "Unsupported format. Use pdf, docx, or excel"}), 400

    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({"error": str(e)}), 500

# ============= WEBSOCKET EVENTS =============

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f'Client connected: {request.sid}')
    emit('connected', {'status': 'success', 'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f'Client disconnected: {request.sid}')

@socketio.on('start_session')
def handle_start_session():
    """Create a new live detection session"""
    try:
        session = create_session()
        emit('session_started', {
            'success': True,
            'session_id': session.session_id,
            'message': 'Session created successfully'
        })
    except Exception as e:
        emit('session_started', {
            'success': False,
            'error': str(e)
        })

@socketio.on('process_frame')
def handle_process_frame(data):
    """Process a single frame from live camera"""
    try:
        frame_data = data.get('frame')
        session_id = data.get('session_id')
        
        if not frame_data:
            emit('detection_result', {'success': False, 'error': 'No frame data provided'})
            return
        
        # Process frame with YOLO
        result = process_frame(
            model=model,
            frame_data=frame_data,
            session_id=session_id,
            conf=CONF_THRESHOLD,
            iou=IOU_THRESHOLD,
            imgsz=IMGSZ
        )
        
        # Send result back to client
        emit('detection_result', result)
    
    except Exception as e:
        print(f"Frame processing error: {e}")
        emit('detection_result', {
            'success': False,
            'error': str(e)
        })

@socketio.on('stop_session')
def handle_stop_session(data):
    """Stop a live detection session"""
    try:
        session_id = data.get('session_id')
        session = get_session(session_id)
        
        if session:
            summary = session.get_summary()
            emit('session_stopped', {
                'success': True,
                'summary': summary,
                'message': 'Session stopped successfully'
            })
        else:
            emit('session_stopped', {
                'success': False,
                'error': 'Session not found'
            })
    
    except Exception as e:
        emit('session_stopped', {
            'success': False,
            'error': str(e)
        })

@socketio.on('get_session_stats')
def handle_get_session_stats(data):
    """Get current session statistics"""
    try:
        session_id = data.get('session_id')
        session = get_session(session_id)
        
        if session:
            emit('session_stats', {
                'success': True,
                'stats': session.get_summary()
            })
        else:
            emit('session_stats', {
                'success': False,
                'error': 'Session not found'
            })
    
    except Exception as e:
        emit('session_stats', {
            'success': False,
            'error': str(e)
        })

if __name__ == "__main__":
    print("=" * 60)
    print("YOLO Detection Web App with Live Camera Support")
    print("=" * 60)
    print(f"Model Path: {MODEL_PATH}")
    print(f"Device: {DEVICE}")
    print("=" * 60)
    print("Starting Flask server with WebSocket support...")
    print("Open http://localhost:5000 in your browser")
    print("=" * 60)
    
    # Use socketio.run instead of app.run for WebSocket support
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)

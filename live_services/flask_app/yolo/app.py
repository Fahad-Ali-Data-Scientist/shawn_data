from flask import Flask, render_template, request, jsonify, send_file
from ultralytics import YOLO
from ultralytics.utils import ROOT
from PIL import Image
import io
import base64
import numpy as np
import os
import uuid
from models import Job, JobType, JobStatus
from job_queue import job_queue
from worker import Worker

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

MODEL_PATH = '/home/ubuntu/Annotations/pending/runs/train/yolov11l_merged2/weights/best.pt'
MODEL_PATH = '/home/ubuntu/Annotations/pending/runs/train/yolov11l_merged_new/weights/best.pt'
TRACKER_CFG = str(ROOT / "cfg/trackers/bytetrack.yaml")
CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.45
IMGSZ = 640
DEVICE = "0"

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

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

@app.route("/")
def index():
    return render_template("index.html")

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

if __name__ == "__main__":
    print("=" * 60)
    print("YOLO Detection Web App")
    print("=" * 60)
    print(f"Model Path: {MODEL_PATH}")
    print(f"Device: {DEVICE}")
    print("=" * 60)
    print("Starting Flask server...")
    print("Open http://localhost:5000 in your browser")
    print("=" * 60)
    
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)

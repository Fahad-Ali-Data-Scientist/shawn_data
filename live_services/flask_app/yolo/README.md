# YOLO Detection Web App

Professional Flask web application for object detection using YOLO.

## Features

- **Image Detection** - Upload images and get instant object detection results
- **Video Detection** - Process videos with frame-by-frame object detection
- **Video Detection with Counting** - Track and count unique objects using ByteTrack
- **Job Queue System** - All users can see all processing jobs
- **Background Processing** - Videos process in background, survives page refresh
- **One Job at a Time** - Queue system processes one video at a time

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure model path in `app.py`:
```python
MODEL_PATH = "path/to/your/best.pt"
DEVICE = "0"  # or "cpu"
```

3. Run:
```bash
python app.py
```

4. Open: http://localhost:5000

## Project Structure

```
├── app.py                  # Main Flask application
├── models.py               # Data models (Job, JobStatus, JobType)
├── job_queue.py            # Job queue management
├── worker.py               # Background worker thread
├── video_processor.py      # Video processing logic
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html         # Web interface
├── static/
│   └── css/
│       └── style.css      # Styles
├── uploads/               # Temporary uploads
└── outputs/               # Processed videos
```

## Configuration

Edit `app.py`:

```python
MODEL_PATH = "path/to/your/best.pt"
CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.45
IMGSZ = 640
DEVICE = "0"  # "cpu" or "0" for GPU
```

## How It Works

1. **Image Detection**: Instant processing, no queue
2. **Video Upload**: Files saved, job added to queue
3. **Background Worker**: Processes one job at a time
4. **Queue Tab**: Shows all jobs and their status
5. **Persistence**: Refresh doesn't stop processing
6. **Download**: Completed videos can be viewed/downloaded

## Job Queue

- Jobs are processed one at a time
- Pending jobs wait in queue
- All users see all jobs
- Processing continues even if user refreshes
- Real-time progress updates

## Production Deployment

```bash
gunicorn -w 1 -b 0.0.0.0:5000 --timeout 600 app:app
```

Note: Use `-w 1` (single worker) to ensure job queue works correctly.

## License

MIT License

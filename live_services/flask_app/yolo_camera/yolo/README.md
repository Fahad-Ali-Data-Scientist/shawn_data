# YOLO Detection System

Web-based object detection with live camera and video upload support.

## Quick Start (3 Steps!)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Model Path
Edit `app.py` line 18:
```python
MODEL_PATH = "path/to/your/best.pt"
```

### 3. Run with HTTPS
```bash
./start_https_simple.sh
```

**Done!** Share the HTTPS URL with clients. Camera works for everyone - no setup needed!

📖 See `START_HERE.txt` for detailed guide.

## Features

**Option 1: Video Upload Detection**
- Upload images or videos for detection
- Object tracking and counting
- Download processed videos

**Option 2: Live Camera Detection**
- Real-time camera detection
- Live statistics
- Export results (PDF, DOCX, Excel)

## Access from Other Devices

```bash
# Find your server IP
ipconfig      # Windows
ifconfig      # Mac/Linux

# Access from any device on same network
http://YOUR_IP:5000
```

**For Live Camera on HTTP:** See `ENABLE_CAMERA_HTTP.txt` to enable camera in browser.

---

That's it! 🚀

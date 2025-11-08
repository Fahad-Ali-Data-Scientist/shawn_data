// YOLO Detection System - Live Camera JavaScript
// Handles real-time camera feed and WebSocket communication

// Initialize Socket.IO connection
const socket = io();

// Global variables
let sessionId = null;
let isRunning = false;
let videoStream = null;
let processingFrame = false;
let sessionStartTime = null;
let fpsCounter = 0;
let lastFrameTime = Date.now();
let durationInterval = null;

// DOM elements
const cameraFeed = document.getElementById('cameraFeed');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const statusIndicator = document.getElementById('statusIndicator');

// Initialize status
statusIndicator.classList.add('inactive');

// Socket.IO Event Handlers
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    if (isRunning) {
        stopCamera();
    }
});

socket.on('session_started', (data) => {
    if (data.success) {
        sessionId = data.session_id;
        console.log('Session started:', sessionId);
        sessionStartTime = Date.now();
        startProcessing();
    } else {
        alert('Error starting session: ' + data.error);
        stopCamera();
    }
});

socket.on('detection_result', (data) => {
    if (data.success) {
        updateUI(data);
        processingFrame = false;
        
        // Update FPS
        const now = Date.now();
        const elapsed = (now - lastFrameTime) / 1000;
        fpsCounter = elapsed > 0 ? (1 / elapsed).toFixed(1) : 0;
        document.getElementById('fpsCounter').textContent = fpsCounter;
        lastFrameTime = now;
    } else {
        console.error('Detection error:', data.error);
        processingFrame = false;
    }
});

socket.on('session_stopped', (data) => {
    if (data.success) {
        console.log('Session stopped:', data.summary);
    }
});

// Camera Functions
async function startCamera() {
    try {
        // Check if getUserMedia is supported
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert('Camera access is not supported in this browser.\n\nPlease use:\n- Chrome or Firefox\n- Access via http://localhost:5000 (not IP address)\n- Or enable camera for this site in browser settings');
            return;
        }

        // Try different camera constraints (fallback options)
        let videoStream = null;
        let error = null;
        
        // Try 1: With ideal resolution and environment camera
        try {
            const constraints1 = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'environment'
                }
            };
            videoStream = await navigator.mediaDevices.getUserMedia(constraints1);
        } catch (e) {
            error = e;
            console.log('Try 1 failed, trying fallback...');
            
            // Try 2: Simple video request without specific camera
            try {
                const constraints2 = {
                    video: {
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    }
                };
                videoStream = await navigator.mediaDevices.getUserMedia(constraints2);
            } catch (e2) {
                error = e2;
                console.log('Try 2 failed, trying basic...');
                
                // Try 3: Most basic request
                try {
                    videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
                } catch (e3) {
                    error = e3;
                }
            }
        }

        if (!videoStream) {
            throw error;
        }
        
        // Create video element to capture frames
        const video = document.createElement('video');
        video.srcObject = videoStream;
        video.autoplay = true;
        video.playsInline = true;
        video.muted = true;
        
        video.onloadedmetadata = () => {
            video.play();
            isRunning = true;
            
            // Update UI
            startBtn.disabled = true;
            stopBtn.disabled = false;
            statusIndicator.classList.remove('inactive');
            statusIndicator.classList.add('active');
            
            // Start session
            socket.emit('start_session');
            
            // Start duration counter
            durationInterval = setInterval(updateDuration, 1000);
            
            // Enable export buttons
            document.getElementById('exportPdfBtn').disabled = false;
            document.getElementById('exportDocxBtn').disabled = false;
            document.getElementById('exportExcelBtn').disabled = false;
        };
        
        // Store video element and stream for frame capture
        window.liveVideo = video;
        window.videoStream = videoStream;
        
    } catch (error) {
        console.error('Camera Error:', error);
        
        let errorMsg = 'Could not access camera.\n\n';
        
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            errorMsg += '❌ Permission denied. Please:\n';
            errorMsg += '1. Click the camera icon in address bar\n';
            errorMsg += '2. Allow camera access for this site\n';
            errorMsg += '3. Refresh the page';
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
            errorMsg += '❌ No camera found. Please:\n';
            errorMsg += '1. Check if camera is connected\n';
            errorMsg += '2. Close other apps using camera\n';
            errorMsg += '3. Try a different browser';
        } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
            errorMsg += '❌ Camera is already in use. Please:\n';
            errorMsg += '1. Close other apps/tabs using camera\n';
            errorMsg += '2. Restart your browser\n';
            errorMsg += '3. Try again';
        } else if (error.name === 'NotSupportedError') {
            errorMsg += '❌ HTTPS Required!\n\n';
            errorMsg += 'For security, browsers require HTTPS for camera.\n\n';
            errorMsg += '✅ Solution:\n';
            errorMsg += '1. Access via: http://localhost:5000\n';
            errorMsg += '2. Or use HTTPS in production\n\n';
            errorMsg += 'Current URL: ' + window.location.href;
        } else {
            errorMsg += '❌ Error: ' + error.name + '\n\n';
            errorMsg += 'Camera requires HTTPS or localhost.\n\n';
            errorMsg += '✅ TO USE WITH HTTP + IP ADDRESS:\n';
            errorMsg += '1. Close Chrome completely\n';
            errorMsg += '2. Launch Chrome with command:\n\n';
            errorMsg += 'chrome --unsafely-treat-insecure-origin-as-secure="' + window.location.origin + '" --user-data-dir=C:\\temp\\chrome\n\n';
            errorMsg += '3. See ENABLE_CAMERA_HTTP.txt for details';
        }
        
        alert(errorMsg);
        
        // Show additional help in console
        console.log('%c🎥 CAMERA ACCESS BLOCKED', 'color: red; font-size: 16px; font-weight: bold;');
        console.log('%cTo enable camera on HTTP:', 'color: blue; font-size: 14px;');
        console.log('%c1. Close ALL Chrome windows', 'color: green;');
        console.log('%c2. Run this command:', 'color: green;');
        console.log('%cchrome --unsafely-treat-insecure-origin-as-secure="' + window.location.origin + '" --user-data-dir=C:\\temp\\chrome', 'background: yellow; color: black; padding: 5px;');
        console.log('%c3. Open: ' + window.location.href, 'color: green;');
        console.log('%c\nSee ENABLE_CAMERA_HTTP.txt for full instructions', 'color: blue; font-style: italic;');
    }
}

function stopCamera() {
    isRunning = false;
    
    // Stop video stream
    if (window.videoStream) {
        window.videoStream.getTracks().forEach(track => track.stop());
        window.videoStream = null;
    }
    
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
    
    // Clear video
    if (window.liveVideo) {
        window.liveVideo.srcObject = null;
        window.liveVideo = null;
    }
    
    // Stop duration counter
    if (durationInterval) {
        clearInterval(durationInterval);
        durationInterval = null;
    }
    
    // Update UI
    startBtn.disabled = false;
    stopBtn.disabled = true;
    statusIndicator.classList.remove('active');
    statusIndicator.classList.add('inactive');
    cameraFeed.src = '';
    
    // Notify server
    if (sessionId) {
        socket.emit('stop_session', { session_id: sessionId });
    }
    
    console.log('Camera stopped');
}

function startProcessing() {
    if (!isRunning) return;
    
    // Capture and process frame
    if (!processingFrame && window.liveVideo && window.liveVideo.readyState === 4) {
        processingFrame = true;
        captureFrame();
    }
    
    // Schedule next frame
    setTimeout(startProcessing, 100); // Process ~10 frames per second
}

function captureFrame() {
    try {
        const video = window.liveVideo;
        
        // Create canvas to capture frame
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Convert to base64
        const frameData = canvas.toDataURL('image/jpeg', 0.8);
        
        // Send to server for processing
        socket.emit('process_frame', {
            frame: frameData,
            session_id: sessionId
        });
        
    } catch (error) {
        console.error('Error capturing frame:', error);
        processingFrame = false;
    }
}

// UI Update Functions
function updateUI(data) {
    // Update camera feed with annotated image
    if (data.annotated_image) {
        cameraFeed.src = data.annotated_image;
    }
    
    // Update statistics
    if (data.session_stats) {
        document.getElementById('totalFrames').textContent = data.session_stats.total_frames || 0;
        document.getElementById('totalObjects').textContent = data.session_stats.total_objects || 0;
    }
    
    // Update current frame detections
    document.getElementById('currentObjects').textContent = data.detections ? data.detections.length : 0;
    
    // Update class counts
    updateClassCounts(data.session_stats?.cumulative_counts || {});
    
    // Add to detection log
    if (data.detections && data.detections.length > 0) {
        addToDetectionLog(data.detections, data.timestamp);
    }
}

function updateClassCounts(counts) {
    const container = document.getElementById('classCounts');
    
    if (Object.keys(counts).length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--text-secondary); font-size: 0.875rem;">No detections yet</p>';
        return;
    }
    
    let html = '';
    const sortedCounts = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    
    sortedCounts.forEach(([className, count]) => {
        html += `
            <div class="class-count-item">
                <span style="font-weight: 600;">${className}</span>
                <span style="color: var(--primary-color); font-weight: 700;">${count}</span>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function addToDetectionLog(detections, timestamp) {
    const log = document.getElementById('detectionLog');
    
    // Clear "waiting" message if present
    if (log.querySelector('p')) {
        log.innerHTML = '';
    }
    
    const time = new Date(timestamp).toLocaleTimeString();
    const classes = detections.map(d => d.class).join(', ');
    
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.innerHTML = `
        <div class="log-time">${time}</div>
        <div>${detections.length} object(s): ${classes}</div>
    `;
    
    // Add to top of log
    log.insertBefore(entry, log.firstChild);
    
    // Keep only last 20 entries
    while (log.children.length > 20) {
        log.removeChild(log.lastChild);
    }
}

function updateDuration() {
    if (!sessionStartTime) return;
    
    const elapsed = Math.floor((Date.now() - sessionStartTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    
    document.getElementById('sessionDuration').textContent = 
        `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

// Export Functions
async function exportResults(format) {
    if (!sessionId) {
        alert('No active session to export');
        return;
    }
    
    try {
        const btn = document.getElementById(`export${format.charAt(0).toUpperCase() + format.slice(1)}Btn`);
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Exporting...';
        
        // Download file
        window.location.href = `/export/${format}/${sessionId}`;
        
        // Reset button after delay
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }, 2000);
        
    } catch (error) {
        console.error('Export error:', error);
        alert('Error exporting results: ' + error);
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (isRunning) {
        stopCamera();
    }
});

// Handle visibility change (pause when tab is hidden)
document.addEventListener('visibilitychange', () => {
    if (document.hidden && isRunning) {
        // Optionally pause processing when tab is hidden
        console.log('Tab hidden, continuing processing...');
    }
});


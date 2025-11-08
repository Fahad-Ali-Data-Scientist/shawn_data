// YOLO Detection System - Video App JavaScript
// Handles image detection, video upload, and job queue management

let currentImageFile = null;
let currentVideoFile = null;
let currentCountingFile = null;
let pollInterval = null;

function switchTab(tabName, event) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    
    document.getElementById('tab-' + tabName).classList.add('active');
    event.target.classList.add('active');

    if (tabName === 'queue') {
        loadAllJobs();
        if (!pollInterval) {
            pollInterval = setInterval(loadAllJobs, 2000);
        }
    } else {
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    }
}

function handleImageUpload(input) {
    if (input.files && input.files[0]) {
        currentImageFile = input.files[0];
        document.getElementById('image-detect-btn').disabled = false;
        
        const uploadArea = document.getElementById('image-upload-area');
        uploadArea.classList.add('has-file');
        uploadArea.innerHTML = `
            <div class="upload-icon">✅</div>
            <h3>${currentImageFile.name}</h3>
            <p style="color: #10b981; font-weight: 600;">Ready to detect objects</p>
        `;
    }
}

function handleVideoUpload(input) {
    if (input.files && input.files[0]) {
        currentVideoFile = input.files[0];
        document.getElementById('video-detect-btn').disabled = false;
        
        const uploadArea = document.getElementById('video-upload-area');
        uploadArea.classList.add('has-file');
        uploadArea.innerHTML = `
            <div class="upload-icon">✅</div>
            <h3>${currentVideoFile.name}</h3>
            <p style="color: #10b981; font-weight: 600;">Ready to add to queue</p>
        `;
    }
}

function handleCountingUpload(input) {
    if (input.files && input.files[0]) {
        currentCountingFile = input.files[0];
        document.getElementById('counting-detect-btn').disabled = false;
        
        const uploadArea = document.getElementById('counting-upload-area');
        uploadArea.classList.add('has-file');
        uploadArea.innerHTML = `
            <div class="upload-icon">✅</div>
            <h3>${currentCountingFile.name}</h3>
            <p style="color: #10b981; font-weight: 600;">Ready to add to queue</p>
        `;
    }
}

async function detectImage() {
    if (!currentImageFile) return;

    const btn = document.getElementById('image-detect-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Detecting...';

    const formData = new FormData();
    formData.append('image', currentImageFile);

    try {
        const response = await fetch('/predict_image', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            document.getElementById('result-image').src = data.image;
            document.getElementById('image-result').classList.add('show');

            const detectionsDiv = document.getElementById('image-detections');
            if (data.detections.length > 0) {
                let html = `<div class="detections-summary">Found ${data.total_detections} object(s)</div>`;
                data.detections.forEach(d => {
                    html += `
                        <div class="detection-item">
                            <span class="detection-class">${d.class}</span>
                            <span class="detection-conf">${(d.confidence * 100).toFixed(1)}%</span>
                        </div>
                    `;
                });
                detectionsDiv.innerHTML = html;
            } else {
                detectionsDiv.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No objects detected</p>';
            }
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error processing image: ' + error);
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Detect Objects';
    }
}

async function submitVideo() {
    if (!currentVideoFile) return;

    const btn = document.getElementById('video-detect-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Uploading...';

    const formData = new FormData();
    formData.append('video', currentVideoFile);

    try {
        const response = await fetch('/predict_video', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            alert('Video added to queue! Job ID: ' + data.job_id);
            switchTab('queue', {target: document.querySelectorAll('.tab')[3]});
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error);
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Add to Queue';
    }
}

async function submitCounting() {
    if (!currentCountingFile) return;

    const btn = document.getElementById('counting-detect-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Uploading...';

    const formData = new FormData();
    formData.append('video', currentCountingFile);

    try {
        const response = await fetch('/predict_video_counting', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            alert('Video added to queue! Job ID: ' + data.job_id);
            switchTab('queue', {target: document.querySelectorAll('.tab')[3]});
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error);
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Add to Queue';
    }
}

async function loadAllJobs() {
    try {
        const response = await fetch('/jobs');
        const data = await response.json();
        
        const container = document.getElementById('jobs-container');
        
        if (data.jobs.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--text-secondary); padding: 40px;">No jobs in queue</p>';
            return;
        }

        let html = '';
        data.jobs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        
        data.jobs.forEach(job => {
            const statusColor = {
                'pending': '#f59e0b',
                'processing': '#2563eb',
                'completed': '#10b981',
                'error': '#ef4444'
            }[job.status];

            html += `
                <div class="job-card" style="background: var(--bg-secondary); padding: 20px; margin-bottom: 16px; border-radius: 10px; border-left: 4px solid ${statusColor};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div>
                            <strong>${job.filename}</strong>
                            <span style="margin-left: 12px; padding: 4px 12px; background: ${statusColor}; color: white; border-radius: 12px; font-size: 0.875rem;">${job.status.toUpperCase()}</span>
                        </div>
                        <div style="color: var(--text-secondary); font-size: 0.875rem;">${job.job_type}</div>
                    </div>
            `;

            if (job.status === 'processing' || job.status === 'completed') {
                html += `
                    <div style="margin-bottom: 8px;">
                        <div style="width: 100%; height: 8px; background: var(--bg-tertiary); border-radius: 4px; overflow: hidden;">
                            <div style="width: ${job.progress}%; height: 100%; background: ${statusColor}; transition: width 0.3s;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-top: 4px; font-size: 0.875rem; color: var(--text-secondary);">
                            <span>Frame ${job.current_frame} / ${job.total_frames}</span>
                            <span>${job.progress}%</span>
                        </div>
                    </div>
                `;

                if (job.job_type === 'counting' && job.unique_objects > 0) {
                    html += `<div style="margin-top: 8px; font-size: 0.875rem; color: var(--text-secondary);">Unique Objects: ${job.unique_objects}</div>`;
                }
            }

            if (job.status === 'completed' && job.output_filename) {
                html += `
                    <div style="margin-top: 12px;">
                        <button class="btn" onclick="window.open('/view/${job.output_filename}', '_blank')" style="padding: 8px 16px; font-size: 0.875rem; margin-right: 8px;">
                            ▶️ View
                        </button>
                        <button class="btn btn-secondary" onclick="window.location.href='/download/${job.output_filename}'" style="padding: 8px 16px; font-size: 0.875rem;">
                            💾 Download
                        </button>
                    </div>
                `;
            }

            if (job.status === 'error') {
                html += `<div style="margin-top: 8px; color: #ef4444; font-size: 0.875rem;">Error: ${job.error_message}</div>`;
            }

            html += '</div>';
        });

        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading jobs:', error);
    }
}

window.addEventListener('beforeunload', () => {
    if (pollInterval) {
        clearInterval(pollInterval);
    }
});


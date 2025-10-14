// Avatar JavaScript

const photoUploadArea = document.getElementById('photo-upload-area');
const photoInput = document.getElementById('photo-input');
const photoPreview = document.getElementById('photo-preview');
const previewImage = document.getElementById('preview-image');
const removePhotoBtn = document.getElementById('remove-photo');
const createAvatarBtn = document.getElementById('create-avatar-btn');
const deleteAvatarBtn = document.getElementById('delete-avatar-btn');
const videoText = document.getElementById('video-text');
const videoCharCount = document.getElementById('video-char-count');
const videoVoice = document.getElementById('video-voice');
const generateVideoBtn = document.getElementById('generate-video-btn');
const progressSection = document.getElementById('progress-section');
const progressText = document.getElementById('progress-text');
const videoResultSection = document.getElementById('video-result-section');
const videoPlayer = document.getElementById('video-player');
const downloadVideoBtn = document.getElementById('download-video-btn');
const newVideoBtn = document.getElementById('new-video-btn');

let selectedPhoto = null;

// Photo upload area click
if (photoUploadArea) {
    photoUploadArea.addEventListener('click', () => {
        photoInput.click();
    });
}

// Photo input change
if (photoInput) {
    photoInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handlePhotoSelect(e.target.files[0]);
        }
    });
}

// Handle photo selection
function handlePhotoSelect(file) {
    selectedPhoto = file;
    
    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        photoUploadArea.style.display = 'none';
        photoPreview.style.display = 'flex';
        createAvatarBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

// Remove photo
if (removePhotoBtn) {
    removePhotoBtn.addEventListener('click', () => {
        selectedPhoto = null;
        photoInput.value = '';
        photoUploadArea.style.display = 'flex';
        photoPreview.style.display = 'none';
        createAvatarBtn.disabled = true;
    });
}

// Create avatar
if (createAvatarBtn) {
    createAvatarBtn.addEventListener('click', async () => {
        if (!selectedPhoto) return;
        
        const formData = new FormData();
        formData.append('photo', selectedPhoto);
        
        setLoading(createAvatarBtn, true);
        progressSection.style.display = 'block';
        progressText.textContent = '🎨 Creating your AI avatar... (this may take up to 5 minutes)';
        
        try {
            const data = await uploadFile('/api/avatar/create', formData);
            
            if (data.success) {
                const message = data.fallback 
                    ? 'Avatar created successfully (using original photo)! Refreshing...'
                    : 'Avatar created successfully! Refreshing...';
                showFlashMessage(message, 'success');
                
                // Reload page to show new avatar
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                throw new Error(data.error || 'Avatar creation failed');
            }
        } catch (error) {
            showFlashMessage(error.message, 'error');
            setLoading(createAvatarBtn, false);
            progressSection.style.display = 'none';
        }
    });
}

// Character count for video text
if (videoText) {
    videoText.addEventListener('input', () => {
        const count = videoText.value.length;
        videoCharCount.textContent = count;
        
        if (count > 1000) {
            videoCharCount.style.color = 'var(--danger-color)';
        } else {
            videoCharCount.style.color = 'var(--text-light)';
        }
    });
}

// Generate video
if (generateVideoBtn) {
    generateVideoBtn.addEventListener('click', async () => {
        const text = videoText.value.trim();
        
        if (!text) {
            showFlashMessage('Please enter some text', 'error');
            return;
        }
        
        if (text.length > 1000) {
            showFlashMessage('Text exceeds maximum length of 1000 characters', 'error');
            return;
        }
        
        const voice = videoVoice.value;
        const useLipsync = document.getElementById('use-lipsync').checked;
        
        setLoading(generateVideoBtn, true);
        videoResultSection.style.display = 'none';
        progressSection.style.display = 'block';
        
        if (useLipsync) {
            progressText.textContent = '🎭 Generating avatar video with Replicate AI lip-sync... (30-90 seconds, please wait!)';
        } else {
            progressText.textContent = '🎬 Generating avatar video... (usually takes 10-30 seconds)';
        }
        
        try {
            const response = await fetch('/api/avatar/generate-video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    voice: voice,
                    use_lipsync: useLipsync
                })
            });
            
            const data = await response.json();
            
        if (data.success) {
            // Load video
            videoPlayer.src = data.video_url;
            downloadVideoBtn.href = data.video_url;
            downloadVideoBtn.download = 'avatar_video.mp4';
                
                // Show result
                progressSection.style.display = 'none';
                videoResultSection.style.display = 'block';
                
                const message = data.lipsync_applied 
                    ? 'Avatar video with AI lip-sync generated successfully! 🎭'
                    : 'Avatar video generated successfully!';
                showFlashMessage(message, 'success');
            } else {
                throw new Error(data.error || 'Video generation failed');
            }
        } catch (error) {
            showFlashMessage(error.message, 'error');
            progressSection.style.display = 'none';
        } finally {
            setLoading(generateVideoBtn, false);
        }
    });
}

// New video
if (newVideoBtn) {
    newVideoBtn.addEventListener('click', () => {
        videoText.value = '';
        videoCharCount.textContent = '0';
        videoPlayer.src = '';
        
        videoResultSection.style.display = 'none';
    });
}

// Delete avatar
if (deleteAvatarBtn) {
    deleteAvatarBtn.addEventListener('click', async () => {
        if (!confirm('Are you sure you want to delete your avatar? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch('/api/avatar/delete', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                showFlashMessage('Avatar deleted successfully! Refreshing...', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showFlashMessage(data.error || 'Failed to delete avatar', 'error');
            }
        } catch (error) {
            showFlashMessage('Error deleting avatar: ' + error.message, 'error');
        }
    });
}


// Voice Cloning JavaScript

const audioUploadArea = document.getElementById('audio-upload-area');
const audioInput = document.getElementById('audio-input');
const audioPreview = document.getElementById('audio-preview');
const previewAudio = document.getElementById('preview-audio');
const removeAudioBtn = document.getElementById('remove-audio');
const voiceName = document.getElementById('voice-name');
const voiceDescription = document.getElementById('voice-description');
const cloneVoiceBtn = document.getElementById('clone-voice-btn');
const progressSection = document.getElementById('progress-section');
const progressText = document.getElementById('progress-text');
const clonedVoicesList = document.getElementById('cloned-voices-list');
const previewSection = document.getElementById('preview-section');
const previewPlayer = document.getElementById('preview-player');
const previewText = document.getElementById('preview-text');
const regeneratePreviewBtn = document.getElementById('regenerate-preview-btn');
const closePreviewBtn = document.getElementById('close-preview-btn');

let selectedAudio = null;
let currentPreviewVoiceId = null;

// Audio upload area click
if (audioUploadArea) {
    audioUploadArea.addEventListener('click', () => {
        audioInput.click();
    });
}

// Audio input change
if (audioInput) {
    audioInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleAudioSelect(e.target.files[0]);
        }
    });
}

// Handle audio selection
function handleAudioSelect(file) {
    selectedAudio = file;
    
    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        previewAudio.src = e.target.result;
        audioUploadArea.style.display = 'none';
        audioPreview.style.display = 'flex';
        updateCloneButton();
    };
    reader.readAsDataURL(file);
}

// Remove audio
if (removeAudioBtn) {
    removeAudioBtn.addEventListener('click', () => {
        selectedAudio = null;
        audioInput.value = '';
        audioUploadArea.style.display = 'flex';
        audioPreview.style.display = 'none';
        updateCloneButton();
    });
}

// Update clone button state
function updateCloneButton() {
    const name = voiceName.value.trim();
    cloneVoiceBtn.disabled = !selectedAudio || !name;
}

// Voice name input
if (voiceName) {
    voiceName.addEventListener('input', updateCloneButton);
}

// Clone voice
if (cloneVoiceBtn) {
    cloneVoiceBtn.addEventListener('click', async () => {
        if (!selectedAudio) return;
        
        const name = voiceName.value.trim();
        const description = voiceDescription.value.trim();
        
        if (!name) {
            showFlashMessage('Please enter a voice name', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('audio', selectedAudio);
        formData.append('voice_name', name);
        if (description) {
            formData.append('voice_description', description);
        }
        
        setLoading(cloneVoiceBtn, true);
        progressSection.style.display = 'block';
        progressText.textContent = '🎤 Cloning your voice... (this may take 30-60 seconds)';
        
        try {
            const data = await uploadFile('/voice-clone/clone', formData);
            
            if (data.success) {
                showFlashMessage(data.message, 'success');
                
                // Reset form
                selectedAudio = null;
                audioInput.value = '';
                voiceName.value = '';
                voiceDescription.value = '';
                audioUploadArea.style.display = 'flex';
                audioPreview.style.display = 'none';
                
                // Reload page to show new voice
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                throw new Error(data.error || 'Voice cloning failed');
            }
        } catch (error) {
            showFlashMessage(error.message, 'error');
            setLoading(cloneVoiceBtn, false);
            progressSection.style.display = 'none';
        }
    });
}

// Preview voice
document.addEventListener('click', async (e) => {
    if (e.target.closest('.preview-voice-btn')) {
        const btn = e.target.closest('.preview-voice-btn');
        const voiceId = btn.dataset.voiceId;
        await previewVoice(voiceId);
    }
});

async function previewVoice(voiceId) {
    currentPreviewVoiceId = voiceId;
    const text = previewText.value.trim() || 'Hello! This is a preview of your cloned voice.';
    
    progressSection.style.display = 'block';
    progressText.textContent = '🔊 Generating preview...';
    
    try {
        const response = await fetch('/voice-clone/preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                voice_id: voiceId,
                text: text
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            previewPlayer.src = data.audio_url;
            previewSection.style.display = 'block';
            progressSection.style.display = 'none';
            previewPlayer.play();
        } else {
            throw new Error(data.error || 'Preview generation failed');
        }
    } catch (error) {
        showFlashMessage(error.message, 'error');
        progressSection.style.display = 'none';
    }
}

// Regenerate preview
if (regeneratePreviewBtn) {
    regeneratePreviewBtn.addEventListener('click', async () => {
        if (currentPreviewVoiceId) {
            await previewVoice(currentPreviewVoiceId);
        }
    });
}

// Close preview
if (closePreviewBtn) {
    closePreviewBtn.addEventListener('click', () => {
        previewSection.style.display = 'none';
        previewPlayer.pause();
        previewPlayer.src = '';
        currentPreviewVoiceId = null;
    });
}

// Delete voice
document.addEventListener('click', async (e) => {
    if (e.target.closest('.delete-voice-btn')) {
        const btn = e.target.closest('.delete-voice-btn');
        const voiceId = btn.dataset.voiceId;
        
        if (!confirm('Are you sure you want to delete this cloned voice? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch('/voice-clone/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    voice_id: voiceId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showFlashMessage('Voice deleted successfully! Refreshing...', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                showFlashMessage(data.error || 'Failed to delete voice', 'error');
            }
        } catch (error) {
            showFlashMessage('Error deleting voice: ' + error.message, 'error');
        }
    }
});


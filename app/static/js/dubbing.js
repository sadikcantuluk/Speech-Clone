// Video Dubbing JavaScript

const uploadArea = document.getElementById('upload-area');
const videoInput = document.getElementById('video-input');
const fileInfo = document.getElementById('file-info');
const fileName = document.getElementById('file-name');
const fileSize = document.getElementById('file-size');
const removeFileBtn = document.getElementById('remove-file-btn');
const optionsSection = document.getElementById('options-section');
const sourceLanguageSelect = document.getElementById('source-language');
const targetLanguageSelect = document.getElementById('target-language');
const voiceSelect = document.getElementById('voice-select');
const speedFactor = document.getElementById('speed-factor');
const speedValue = document.getElementById('speed-value');
const dubBtn = document.getElementById('dub-btn');
const progressSection = document.getElementById('progress-section');
const progressStatus = document.getElementById('progress-status');
const resultSection = document.getElementById('result-section');
const resultVideo = document.getElementById('result-video');
const languagesInfo = document.getElementById('languages-info');
const voiceInfo = document.getElementById('voice-info');
const originalText = document.getElementById('original-text');
const translatedText = document.getElementById('translated-text');
const downloadBtn = document.getElementById('download-btn');
const newDubbingBtn = document.getElementById('new-dubbing-btn');

let selectedFile = null;
let availableLanguages = [];
let availableVoices = [];

// Load languages and voices on page load
loadLanguages();
loadVoices();

// Speed factor change handler
speedFactor.addEventListener('input', (e) => {
    const value = parseFloat(e.target.value);
    speedValue.textContent = `${value.toFixed(1)}x (${value === 1.0 ? 'Normal' : value < 1.0 ? 'Slow' : 'Fast'})`;
});

// Upload area click
uploadArea.addEventListener('click', () => {
    videoInput.click();
});

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'var(--primary-color)';
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.borderColor = 'var(--border-color)';
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'var(--border-color)';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

// File input change
videoInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

// Handle file selection
function handleFileSelect(file) {
    // Validate file type
    const validTypes = ['video/mp4', 'video/avi', 'video/x-msvideo', 'video/quicktime', 'video/x-matroska', 'video/webm'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp4|avi|mov|mkv|webm)$/i)) {
        showFlashMessage('Invalid file type. Please upload a video file.', 'error');
        return;
    }
    
    // Validate file size (200 MB)
    const maxSize = 200 * 1024 * 1024;
    if (file.size > maxSize) {
        showFlashMessage('File size exceeds 200 MB limit.', 'error');
        return;
    }
    
    selectedFile = file;
    
    // Show file info
    uploadArea.style.display = 'none';
    fileInfo.style.display = 'flex';
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    
    // Show options section
    optionsSection.style.display = 'block';
    dubBtn.disabled = false;
}

// Remove file
removeFileBtn.addEventListener('click', () => {
    selectedFile = null;
    videoInput.value = '';
    uploadArea.style.display = 'flex';
    fileInfo.style.display = 'none';
    optionsSection.style.display = 'none';
    dubBtn.disabled = true;
});

// Load available languages
async function loadLanguages() {
    try {
        const response = await fetch('/dubbing/languages');
        const data = await response.json();
        
        if (data.success) {
            availableLanguages = data.languages;
            
            // Populate language selects
            sourceLanguageSelect.innerHTML = '<option value="">Auto-detect</option>';
            targetLanguageSelect.innerHTML = '';
            
            data.languages.forEach(lang => {
                const sourceOption = document.createElement('option');
                sourceOption.value = lang.code;
                sourceOption.textContent = lang.name;
                sourceLanguageSelect.appendChild(sourceOption);
                
                const targetOption = document.createElement('option');
                targetOption.value = lang.code;
                targetOption.textContent = lang.name;
                if (lang.code === 'en') {
                    targetOption.selected = true;
                }
                targetLanguageSelect.appendChild(targetOption);
            });
        }
    } catch (error) {
        console.error('Failed to load languages:', error);
    }
}

// Load available voices
async function loadVoices() {
    try {
        const response = await fetch('/dubbing/voices');
        const data = await response.json();
        
        if (data.success) {
            availableVoices = data.voices;
            
            // Populate voice select
            voiceSelect.innerHTML = '';
            
            // Group by type
            const standardVoices = data.voices.filter(v => v.type === 'standard');
            const clonedVoices = data.voices.filter(v => v.type === 'cloned');
            
            // Add standard voices
            if (standardVoices.length > 0) {
                const standardGroup = document.createElement('optgroup');
                standardGroup.label = 'Standard Voices';
                standardVoices.forEach(voice => {
                    const option = document.createElement('option');
                    option.value = `standard:${voice.id}`;
                    option.textContent = `${voice.name} - ${voice.description}`;
                    standardGroup.appendChild(option);
                });
                voiceSelect.appendChild(standardGroup);
            }
            
            // Add cloned voices
            if (clonedVoices.length > 0) {
                const clonedGroup = document.createElement('optgroup');
                clonedGroup.label = 'Cloned Voices';
                clonedVoices.forEach(voice => {
                    const option = document.createElement('option');
                    option.value = `cloned:${voice.id}`;
                    option.textContent = `${voice.name} - ${voice.description}`;
                    clonedGroup.appendChild(option);
                });
                voiceSelect.appendChild(clonedGroup);
            }
        }
    } catch (error) {
        console.error('Failed to load voices:', error);
    }
}

// Start dubbing
dubBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    const formData = new FormData();
    formData.append('video', selectedFile);
    
    const sourceLanguage = sourceLanguageSelect.value;
    if (sourceLanguage) {
        formData.append('source_language', sourceLanguage);
    }
    
    const targetLanguage = targetLanguageSelect.value;
    formData.append('target_language', targetLanguage);
    
    const voiceValue = voiceSelect.value;
    const [voiceType, voiceId] = voiceValue.split(':');
    formData.append('voice', voiceId);
    formData.append('voice_type', voiceType);
    
    const speed = speedFactor.value;
    formData.append('speed_factor', speed);
    
    // Show progress
    optionsSection.style.display = 'none';
    uploadArea.style.display = 'none';
    fileInfo.style.display = 'none';
    resultSection.style.display = 'none';
    progressSection.style.display = 'block';
    progressStatus.textContent = 'Extracting audio from video...';
    
    try {
        // Simulate progress updates
        const progressMessages = [
            'Extracting audio from video...',
            'Transcribing audio...',
            'Translating to target language...',
            'Generating new speech...',
            'Merging audio with video...'
        ];
        
        let messageIndex = 0;
        const progressInterval = setInterval(() => {
            messageIndex = (messageIndex + 1) % progressMessages.length;
            progressStatus.textContent = progressMessages[messageIndex];
        }, 3000);
        
        const data = await uploadFile('/dubbing/process', formData);
        
        clearInterval(progressInterval);
        
        if (data.success) {
            // Show result
            resultVideo.src = data.video_url;
            downloadBtn.href = data.video_url;
            
            const sourceLang = availableLanguages.find(l => l.code === data.detected_language);
            const targetLang = availableLanguages.find(l => l.code === data.target_language);
            languagesInfo.textContent = `${sourceLang ? sourceLang.name : 'Auto-detected'} → ${targetLang.name}`;
            
            const selectedVoice = availableVoices.find(v => v.id === voiceId);
            voiceInfo.textContent = selectedVoice ? selectedVoice.name : voiceId;
            
            originalText.textContent = data.original_text || 'N/A';
            translatedText.textContent = data.translated_text || 'N/A';
            
            // Show speed factor info if available
            if (data.speed_factor && data.speed_factor !== 1.0) {
                const speedInfo = document.createElement('div');
                speedInfo.className = 'info-item';
                speedInfo.innerHTML = `
                    <div class="info-label"><i class="fas fa-tachometer-alt"></i> Speed Adjustment</div>
                    <div class="info-value">Applied ${data.speed_factor.toFixed(1)}x speed factor</div>
                `;
                document.querySelector('.result-info').appendChild(speedInfo);
            }
            
            progressSection.style.display = 'none';
            resultSection.style.display = 'block';
            
            showFlashMessage('Video dubbed successfully!', 'success');
        } else {
            throw new Error(data.error || 'Dubbing failed');
        }
    } catch (error) {
        showFlashMessage(error.message, 'error');
        
        // Reset
        progressSection.style.display = 'none';
        uploadArea.style.display = 'flex';
        fileInfo.style.display = 'none';
        selectedFile = null;
        videoInput.value = '';
        dubBtn.disabled = true;
    }
});

// New dubbing
newDubbingBtn.addEventListener('click', () => {
    selectedFile = null;
    videoInput.value = '';
    
    resultSection.style.display = 'none';
    uploadArea.style.display = 'flex';
    dubBtn.disabled = true;
});


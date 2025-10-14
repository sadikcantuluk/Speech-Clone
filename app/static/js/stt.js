// Speech-to-Text JavaScript

const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const fileInfo = document.getElementById('file-info');
const fileName = document.getElementById('file-name');
const removeFileBtn = document.getElementById('remove-file');
const transcribeBtn = document.getElementById('transcribe-btn');
const progressSection = document.getElementById('progress-section');
const resultSection = document.getElementById('result-section');
const resultContent = document.getElementById('result-content');
const copyBtn = document.getElementById('copy-btn');
const downloadBtn = document.getElementById('download-btn');
const newTranscriptionBtn = document.getElementById('new-transcription-btn');
const languageSelect = document.getElementById('language');

let selectedFile = null;
let transcriptionText = '';

// Upload area click
uploadArea.addEventListener('click', () => {
    fileInput.click();
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
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

// Handle file selection
function handleFileSelect(file) {
    selectedFile = file;
    
    // Show file info
    uploadArea.style.display = 'none';
    fileInfo.style.display = 'flex';
    fileName.textContent = `${file.name} (${formatFileSize(file.size)})`;
    transcribeBtn.disabled = false;
}

// Remove file
removeFileBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    uploadArea.style.display = 'flex';
    fileInfo.style.display = 'none';
    transcribeBtn.disabled = true;
});

// Transcribe
transcribeBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    const language = languageSelect.value;
    if (language) {
        formData.append('language', language);
    }
    
    const translateTo = document.getElementById('translate-to').value;
    if (translateTo) {
        formData.append('translate_to', translateTo);
    }
    
    // Show progress
    uploadArea.style.display = 'none';
    fileInfo.style.display = 'none';
    resultSection.style.display = 'none';
    progressSection.style.display = 'block';
    
    try {
        const data = await uploadFile('/api/stt/transcribe', formData);
        
        if (data.success) {
            transcriptionText = data.text;
            resultContent.textContent = data.text;
            
            // Show result
            progressSection.style.display = 'none';
            resultSection.style.display = 'block';
            
            showFlashMessage('Transcription completed successfully!', 'success');
        } else {
            throw new Error(data.error || 'Transcription failed');
        }
    } catch (error) {
        showFlashMessage(error.message, 'error');
        
        // Reset
        progressSection.style.display = 'none';
        uploadArea.style.display = 'flex';
        fileInfo.style.display = 'none';
        selectedFile = null;
        fileInput.value = '';
        transcribeBtn.disabled = true;
    }
});

// Copy to clipboard
copyBtn.addEventListener('click', () => {
    copyToClipboard(transcriptionText);
});

// Download as TXT
downloadBtn.addEventListener('click', () => {
    downloadTextFile(transcriptionText, 'transcription.txt');
    showFlashMessage('Downloaded successfully!', 'success');
});

// New transcription
newTranscriptionBtn.addEventListener('click', () => {
    selectedFile = null;
    transcriptionText = '';
    fileInput.value = '';
    
    resultSection.style.display = 'none';
    uploadArea.style.display = 'flex';
    transcribeBtn.disabled = true;
});


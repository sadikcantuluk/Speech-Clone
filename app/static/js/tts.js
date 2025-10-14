// Text-to-Speech JavaScript

const textInput = document.getElementById('text-input');
const charCount = document.getElementById('char-count');
const voiceSelect = document.getElementById('voice-select');
const qualitySelect = document.getElementById('quality-select');
const generateBtn = document.getElementById('generate-btn');
const progressSection = document.getElementById('progress-section');
const resultSection = document.getElementById('result-section');
const audioPlayer = document.getElementById('audio-player');
const downloadAudioBtn = document.getElementById('download-audio-btn');
const newGenerationBtn = document.getElementById('new-generation-btn');

let currentAudioUrl = null;

// Character count
textInput.addEventListener('input', () => {
    const count = textInput.value.length;
    charCount.textContent = count;
    
    if (count > 1000) {
        charCount.style.color = 'var(--danger-color)';
    } else {
        charCount.style.color = 'var(--text-light)';
    }
});

// Generate speech
generateBtn.addEventListener('click', async () => {
    const text = textInput.value.trim();
    
    if (!text) {
        showFlashMessage('Please enter some text', 'error');
        return;
    }
    
    if (text.length > 1000) {
        showFlashMessage('Text exceeds maximum length of 1000 characters', 'error');
        return;
    }
    
    const voice = voiceSelect.value;
    const quality = qualitySelect.value;
    const translateTo = document.getElementById('translate-to-select').value;
    
    // Show progress
    resultSection.style.display = 'none';
    progressSection.style.display = 'block';
    
    try {
        const payload = {
            text: text,
            voice: voice,
            quality: quality
        };
        
        if (translateTo) {
            payload.translate_to = translateTo;
        }
        
        const response = await fetch('/api/tts/generate-json', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Load audio
            currentAudioUrl = data.audio_url;
            audioPlayer.src = currentAudioUrl;
            downloadAudioBtn.href = currentAudioUrl;
            downloadAudioBtn.download = 'speech.mp3';
            
            // Show result
            progressSection.style.display = 'none';
            resultSection.style.display = 'block';
            
            showFlashMessage('Speech generated successfully!', 'success');
        } else {
            throw new Error(data.error || 'Speech generation failed');
        }
    } catch (error) {
        showFlashMessage(error.message, 'error');
        progressSection.style.display = 'none';
    }
});

// New generation
newGenerationBtn.addEventListener('click', () => {
    textInput.value = '';
    charCount.textContent = '0';
    audioPlayer.src = '';
    currentAudioUrl = null;
    
    resultSection.style.display = 'none';
});


"""
Speech-to-Text API routes
"""
from flask import Blueprint, request, jsonify, session, current_app
from app.services.whisper_service import whisper_service
from app.utils.file_utils import save_uploaded_file, is_audio_file, is_video_file, cleanup_file, validate_file_size
import os
import subprocess
import imageio_ffmpeg

bp = Blueprint('stt', __name__)

@bp.route('/transcribe', methods=['POST'])
def transcribe():
    """Transcribe audio/video file to text"""
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Get optional language parameters
    source_language = request.form.get('language', None)  # Original audio language hint
    translate_to = request.form.get('translate_to', None)  # Target language for translation
    
    # Validate file type
    if not (is_audio_file(file.filename) or is_video_file(file.filename)):
        return jsonify({
            'success': False,
            'error': 'Invalid file type. Please upload audio or video file.'
        }), 400
    
    try:
        # Save uploaded file
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = save_uploaded_file(file, folder=upload_folder, prefix='stt')
        
        # Validate file size
        max_size = current_app.config['MAX_FILE_SIZE_BYTES']
        if not validate_file_size(file_path, max_size):
            cleanup_file(file_path)
            return jsonify({
                'success': False,
                'error': f'File size exceeds maximum allowed size of {current_app.config["MAX_FILE_SIZE_MB"]} MB'
            }), 400
        
        # Extract audio from video if needed
        audio_path = file_path
        if is_video_file(file.filename):
            audio_path = extract_audio_from_video(file_path)
            if not audio_path:
                cleanup_file(file_path)
                return jsonify({
                    'success': False,
                    'error': 'Failed to extract audio from video'
                }), 500
        
        # Transcribe audio (and translate if requested)
        result = whisper_service.transcribe_audio(audio_path, source_language, translate_to)
        
        # Cleanup files
        cleanup_file(file_path)
        if audio_path != file_path:
            cleanup_file(audio_path)
        
        if result['success']:
            return jsonify({
                'success': True,
                'text': result['text'],
                'language': result.get('language')
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/transcribe-with-timestamps', methods=['POST'])
def transcribe_with_timestamps():
    """Transcribe audio/video with word-level timestamps"""
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    language = request.form.get('language', None)
    
    if not (is_audio_file(file.filename) or is_video_file(file.filename)):
        return jsonify({
            'success': False,
            'error': 'Invalid file type. Please upload audio or video file.'
        }), 400
    
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = save_uploaded_file(file, folder=upload_folder, prefix='stt')
        
        # Validate file size
        max_size = current_app.config['MAX_FILE_SIZE_BYTES']
        if not validate_file_size(file_path, max_size):
            cleanup_file(file_path)
            return jsonify({
                'success': False,
                'error': f'File size exceeds maximum allowed size of {current_app.config["MAX_FILE_SIZE_MB"]} MB'
            }), 400
        
        audio_path = file_path
        if is_video_file(file.filename):
            audio_path = extract_audio_from_video(file_path)
        
        result = whisper_service.transcribe_with_timestamps(audio_path, language)
        
        cleanup_file(file_path)
        if audio_path != file_path:
            cleanup_file(audio_path)
        
        if result['success']:
            return jsonify({
                'success': True,
                'text': result['text'],
                'words': result.get('words', []),
                'language': result.get('language')
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def extract_audio_from_video(video_path):
    """Extract audio from video file using ffmpeg"""
    try:
        audio_path = video_path.rsplit('.', 1)[0] + '_audio.mp3'
        
        # Get ffmpeg executable from imageio
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        
        # Use subprocess to run ffmpeg directly
        cmd = [
            ffmpeg_exe,
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'libmp3lame',
            '-b:a', '192k',
            '-y',  # Overwrite output
            audio_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"FFmpeg error: {result.stderr}")
            return None
        
        # Check if audio file was created
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            return audio_path
        else:
            print("Error: Audio file was not created or is empty")
            return None
            
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return None


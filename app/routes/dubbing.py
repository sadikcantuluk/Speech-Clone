"""
Video Dubbing API routes
"""
from flask import Blueprint, request, jsonify, session, current_app, send_file
from app.services.dubbing_service import dubbing_service
from app.utils.file_utils import save_uploaded_file, cleanup_file, validate_file_size, is_video_file
from app.utils.validators import sanitize_text
import os

bp = Blueprint('dubbing', __name__)


@bp.route('/process', methods=['POST'])
def process_dubbing():
    """Process video dubbing"""
    
    # Check if video file is present
    if 'video' not in request.files:
        return jsonify({'success': False, 'error': 'No video file provided'}), 400
    
    video_file = request.files['video']
    
    if video_file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Validate file type
    if not is_video_file(video_file.filename):
        return jsonify({
            'success': False,
            'error': 'Invalid file type. Please upload a video file (mp4, avi, mov, mkv, webm).'
        }), 400
    
    # Get dubbing parameters
    target_language = request.form.get('target_language', 'en').strip()
    voice = request.form.get('voice', 'alloy').strip()
    voice_type = request.form.get('voice_type', 'standard').strip()  # 'standard' or 'cloned'
    source_language = request.form.get('source_language', None)
    speed_factor = request.form.get('speed_factor', '1.0')
    
    # Validate parameters
    if not target_language:
        return jsonify({'success': False, 'error': 'Target language is required'}), 400
    
    if not voice:
        return jsonify({'success': False, 'error': 'Voice is required'}), 400
    
    # Parse and validate speed factor
    try:
        speed_factor = float(speed_factor)
        if speed_factor <= 0 or speed_factor > 3.0:
            return jsonify({'success': False, 'error': 'Speed factor must be between 0.1 and 3.0'}), 400
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid speed factor'}), 400
    
    try:
        # Save uploaded video
        upload_folder = current_app.config['UPLOAD_FOLDER']
        video_path = save_uploaded_file(video_file, folder=upload_folder, prefix='dubbing')
        
        # Validate file size (max 200MB as configured)
        max_size = current_app.config['MAX_FILE_SIZE_BYTES']
        if not validate_file_size(video_path, max_size):
            cleanup_file(video_path)
            return jsonify({
                'success': False,
                'error': f'Video file size exceeds maximum allowed size of {current_app.config["MAX_FILE_SIZE_MB"]} MB'
            }), 400
        
        # Process dubbing
        result = dubbing_service.dub_video(
            video_path=video_path,
            target_language=target_language,
            voice=voice,
            voice_type=voice_type,
            source_language=source_language if source_language else None,
            speed_factor=speed_factor
        )
        
        # Cleanup uploaded video
        cleanup_file(video_path)
        
        if result['success']:
            # Store dubbing info in session
            session['last_dubbing'] = {
                'output_path': result['output_path'],
                'original_text': result['original_text'],
                'translated_text': result['translated_text'],
                'target_language': result['target_language'],
                'voice': result['voice']
            }
            session.modified = True
            
            # Get filename for direct access
            filename = os.path.basename(result['output_path'])
            
            return jsonify({
                'success': True,
                'message': 'Video dubbed successfully!',
                'video_url': f'/temp/{filename}',
                'original_text': result['original_text'][:500],  # First 500 chars
                'translated_text': result['translated_text'][:500],  # First 500 chars
                'detected_language': result['detected_language'],
                'target_language': result['target_language'],
                'voice': result['voice'],
                'voice_type': result['voice_type'],
                'speed_factor': result.get('speed_factor', 1.0),
                'original_duration': result.get('original_duration'),
                'final_duration': result.get('final_duration')
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/download', methods=['GET'])
def download_dubbed_video():
    """Download last dubbed video"""
    
    last_dubbing = session.get('last_dubbing')
    
    if not last_dubbing or 'output_path' not in last_dubbing:
        return jsonify({'success': False, 'error': 'No dubbed video available'}), 404
    
    output_path = last_dubbing['output_path']
    
    if not os.path.exists(output_path):
        return jsonify({'success': False, 'error': 'Dubbed video file not found'}), 404
    
    return send_file(
        output_path,
        mimetype='video/mp4',
        as_attachment=True,
        download_name='dubbed_video.mp4'
    )


@bp.route('/languages', methods=['GET'])
def get_languages():
    """Get available languages for dubbing"""
    
    languages = [
        {'code': 'en', 'name': 'English'},
        {'code': 'tr', 'name': 'Turkish'},
        {'code': 'es', 'name': 'Spanish'},
        {'code': 'fr', 'name': 'French'},
        {'code': 'de', 'name': 'German'},
        {'code': 'it', 'name': 'Italian'},
        {'code': 'pt', 'name': 'Portuguese'},
        {'code': 'ru', 'name': 'Russian'},
        {'code': 'ja', 'name': 'Japanese'},
        {'code': 'ko', 'name': 'Korean'},
        {'code': 'zh', 'name': 'Chinese'},
        {'code': 'ar', 'name': 'Arabic'},
        {'code': 'hi', 'name': 'Hindi'},
        {'code': 'nl', 'name': 'Dutch'},
        {'code': 'pl', 'name': 'Polish'}
    ]
    
    return jsonify({'success': True, 'languages': languages})


@bp.route('/voices', methods=['GET'])
def get_voices():
    """Get available voices for dubbing (standard + cloned)"""
    
    # Standard OpenAI voices
    standard_voices = [
        {'id': 'alloy', 'name': 'Alloy', 'type': 'standard', 'description': 'Neutral and balanced'},
        {'id': 'echo', 'name': 'Echo', 'type': 'standard', 'description': 'Male voice'},
        {'id': 'fable', 'name': 'Fable', 'type': 'standard', 'description': 'Warm and expressive'},
        {'id': 'onyx', 'name': 'Onyx', 'type': 'standard', 'description': 'Deep male voice'},
        {'id': 'nova', 'name': 'Nova', 'type': 'standard', 'description': 'Female voice'},
        {'id': 'shimmer', 'name': 'Shimmer', 'type': 'standard', 'description': 'Soft female voice'}
    ]
    
    # Get cloned voices from session
    cloned_voices_data = session.get('cloned_voices', [])
    cloned_voices = [
        {
            'id': v['voice_id'],
            'name': f"{v['name']} (Cloned)",
            'type': 'cloned',
            'description': v.get('description', 'Custom cloned voice')
        }
        for v in cloned_voices_data
    ]
    
    # Combine all voices
    all_voices = standard_voices + cloned_voices
    
    return jsonify({
        'success': True,
        'voices': all_voices,
        'standard_count': len(standard_voices),
        'cloned_count': len(cloned_voices)
    })


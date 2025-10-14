"""
Avatar API routes
"""
from flask import Blueprint, request, jsonify, session, send_file, current_app
from app.services.avatar_service import avatar_service
from app.services.tts_service import tts_service
from app.utils.file_utils import save_uploaded_file, is_image_file, cleanup_file, validate_file_size
from app.utils.validators import validate_text_length, sanitize_text
import os

bp = Blueprint('avatar', __name__)

@bp.route('/create', methods=['POST'])
def create_avatar():
    """Create avatar from user photo"""
    
    if 'photo' not in request.files:
        return jsonify({'success': False, 'error': 'No photo provided'}), 400
    
    photo = request.files['photo']
    
    if photo.filename == '':
        return jsonify({'success': False, 'error': 'No photo selected'}), 400
    
    if not is_image_file(photo.filename):
        return jsonify({
            'success': False,
            'error': 'Invalid file type. Please upload an image file (JPG, PNG, WEBP).'
        }), 400
    
    try:
        # Save uploaded photo
        upload_folder = current_app.config['UPLOAD_FOLDER']
        photo_path = save_uploaded_file(photo, folder=upload_folder, prefix='photo')
        
        # Validate file size (25MB max for images)
        max_size = 25 * 1024 * 1024
        if not validate_file_size(photo_path, max_size):
            cleanup_file(photo_path)
            return jsonify({
                'success': False,
                'error': 'Photo size exceeds maximum allowed size of 25 MB'
            }), 400
        
        # Process photo
        process_result = avatar_service.process_user_photo(photo_path)
        
        if not process_result['success']:
            cleanup_file(photo_path)
            return jsonify({'success': False, 'error': process_result['error']}), 500
        
        processed_path = process_result['processed_path']
        
        # Create avatar
        avatar_result = avatar_service.create_avatar_from_photo(processed_path)
        
        # Cleanup temporary files
        cleanup_file(photo_path)
        cleanup_file(processed_path)
        
        if avatar_result['success']:
            # Store avatar in session
            session['avatar'] = {
                'avatar_url': avatar_result['avatar_url'],
                'avatar_path': avatar_result['avatar_path']
            }
            
            return jsonify({
                'success': True,
                'message': 'Avatar created successfully',
                'avatar_url': avatar_result['avatar_url']
            })
        else:
            return jsonify({'success': False, 'error': avatar_result['error']}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/generate-video', methods=['POST'])
def generate_avatar_video():
    """Generate video with avatar speaking text"""
    
    data = request.get_json() if request.is_json else request.form
    text = data.get('text', '').strip()
    voice = data.get('voice', 'alloy')
    
    # Get lip-sync option (handle both string and boolean)
    use_lipsync_raw = data.get('use_lipsync', False)
    if isinstance(use_lipsync_raw, bool):
        use_lipsync = use_lipsync_raw
    elif isinstance(use_lipsync_raw, str):
        use_lipsync = use_lipsync_raw.lower() in ['true', '1', 'yes']
    else:
        use_lipsync = False
    
    # Check if user has avatar
    avatar = session.get('avatar', {})
    avatar_path = avatar.get('avatar_path')
    
    if not avatar_path or not os.path.exists(avatar_path):
        return jsonify({
            'success': False,
            'error': 'No avatar found. Please create an avatar first.'
        }), 400
    
    # Validate text
    if not text:
        return jsonify({'success': False, 'error': 'Text is required'}), 400
    
    text = sanitize_text(text)
    
    max_length = current_app.config['MAX_TEXT_LENGTH']
    if not validate_text_length(text, max_length):
        return jsonify({
            'success': False,
            'error': f'Text exceeds maximum length of {max_length} characters'
        }), 400
    
    try:
        # Generate speech
        tts_result = tts_service.generate_speech(text, voice)
        
        if not tts_result['success']:
            return jsonify({'success': False, 'error': tts_result['error']}), 500
        
        audio_path = tts_result['audio_path']
        
        # Generate video with avatar (with optional lip-sync)
        video_result = avatar_service.generate_avatar_video(avatar_path, audio_path, use_lipsync=use_lipsync)
        
        # Cleanup audio file
        cleanup_file(audio_path)
        
        if video_result['success']:
            video_path = video_result['video_path']
            
            # Store in session for download
            session['last_video_path'] = video_path
            
            # Get filename for direct access
            filename = os.path.basename(video_path)
            
            return jsonify({
                'success': True,
                'message': 'Avatar video generated successfully',
                'duration': video_result['duration'],
                'video_url': f'/temp/{filename}',
                'lipsync_applied': video_result.get('lipsync_applied', False)
            })
        else:
            return jsonify({'success': False, 'error': video_result['error']}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/download-video', methods=['GET'])
def download_video():
    """Download generated avatar video"""
    
    video_path = session.get('last_video_path')
    
    if not video_path or not os.path.exists(video_path):
        return jsonify({'success': False, 'error': 'No video file available'}), 404
    
    return send_file(
        video_path,
        mimetype='video/mp4',
        as_attachment=True,
        download_name='avatar_video.mp4'
    )

@bp.route('/status', methods=['GET'])
def avatar_status():
    """Check if user has avatar"""
    
    avatar = session.get('avatar', {})
    avatar_url = avatar.get('avatar_url')
    
    return jsonify({
        'success': True,
        'has_avatar': bool(avatar_url),
        'avatar_url': avatar_url
    })

@bp.route('/delete', methods=['POST'])
def delete_avatar():
    """Delete user's avatar"""
    try:
        # Get avatar from session
        avatar = session.get('avatar', {})
        avatar_path = avatar.get('avatar_path')
        
        # Delete physical file if exists
        if avatar_path and os.path.exists(avatar_path):
            cleanup_file(avatar_path)
        
        # Clear avatar from session
        session.pop('avatar', None)
        
        return jsonify({
            'success': True,
            'message': 'Avatar deleted successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


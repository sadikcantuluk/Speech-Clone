"""
Voice cloning API routes
"""
from flask import Blueprint, request, jsonify, session, render_template, current_app, send_from_directory
from app.services.voice_clone_service import voice_clone_service
from app.utils.file_utils import save_uploaded_file, cleanup_file, validate_file_size
from app.utils.validators import sanitize_text
import os

bp = Blueprint('voice_clone', __name__)

@bp.route('/')
def index():
    """Voice cloning page"""
    # Get user's cloned voices from session
    cloned_voices = session.get('cloned_voices', [])
    return render_template('voice_clone.html', cloned_voices=cloned_voices)

@bp.route('/clone', methods=['POST'])
def clone_voice():
    """Clone a voice from uploaded audio"""
    
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file provided'}), 400
    
    audio_file = request.files['audio']
    voice_name = request.form.get('voice_name', '').strip()
    voice_description = request.form.get('voice_description', '').strip()
    
    if audio_file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not voice_name:
        return jsonify({'success': False, 'error': 'Voice name is required'}), 400
    
    # Sanitize voice name
    voice_name = sanitize_text(voice_name)
    
    try:
        # Save uploaded audio
        upload_folder = current_app.config['UPLOAD_FOLDER']
        audio_path = save_uploaded_file(audio_file, folder=upload_folder, prefix='voice_clone')
        
        # Validate file size (max 10MB for voice samples)
        max_size = 10 * 1024 * 1024
        if not validate_file_size(audio_path, max_size):
            cleanup_file(audio_path)
            return jsonify({
                'success': False,
                'error': 'Audio file size exceeds maximum allowed size of 10 MB'
            }), 400
        
        # Clone the voice
        result = voice_clone_service.clone_voice(
            audio_path, 
            voice_name,
            voice_description
        )
        
        # Cleanup uploaded file
        cleanup_file(audio_path)
        
        if result['success']:
            # Store cloned voice in session
            cloned_voices = session.get('cloned_voices', [])
            
            # Check if voice already exists (by name)
            existing_voice = next((v for v in cloned_voices if v['name'] == voice_name), None)
            
            if existing_voice:
                # Update existing voice
                existing_voice['voice_id'] = result['voice_id']
                existing_voice['description'] = voice_description
            else:
                # Add new voice
                cloned_voices.append({
                    'voice_id': result['voice_id'],
                    'name': voice_name,
                    'description': voice_description or ''
                })
            
            session['cloned_voices'] = cloned_voices
            session.modified = True
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'voice_id': result['voice_id'],
                'voice_name': voice_name
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/preview', methods=['POST'])
def preview_voice():
    """Preview a cloned voice with sample text"""
    
    data = request.get_json()
    voice_id = data.get('voice_id')
    text = data.get('text', 'Hello! This is a preview of your cloned voice.').strip()
    
    if not voice_id:
        return jsonify({'success': False, 'error': 'Voice ID is required'}), 400
    
    # Sanitize text
    text = sanitize_text(text)
    
    try:
        # Generate speech with cloned voice
        result = voice_clone_service.generate_speech_with_cloned_voice(text, voice_id)
        
        if result['success']:
            audio_path = result['audio_path']
            filename = os.path.basename(audio_path)
            
            return jsonify({
                'success': True,
                'audio_url': f'/temp/{filename}'
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/list', methods=['GET'])
def list_voices():
    """Get list of cloned voices"""
    cloned_voices = session.get('cloned_voices', [])
    return jsonify({
        'success': True,
        'voices': cloned_voices
    })

@bp.route('/delete', methods=['POST'])
def delete_voice():
    """Delete a cloned voice"""
    
    data = request.get_json()
    voice_id = data.get('voice_id')
    
    if not voice_id:
        return jsonify({'success': False, 'error': 'Voice ID is required'}), 400
    
    try:
        # Delete from ElevenLabs
        result = voice_clone_service.delete_cloned_voice(voice_id)
        
        if result['success']:
            # Remove from session
            cloned_voices = session.get('cloned_voices', [])
            cloned_voices = [v for v in cloned_voices if v['voice_id'] != voice_id]
            session['cloned_voices'] = cloned_voices
            session.modified = True
            
            return jsonify({
                'success': True,
                'message': 'Voice deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


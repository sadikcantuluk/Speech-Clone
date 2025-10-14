"""
Text-to-Speech API routes
"""
from flask import Blueprint, request, jsonify, session, send_file, current_app
from app.services.tts_service import tts_service
from app.services.voice_clone_service import voice_clone_service
from app.utils.validators import validate_text_length, sanitize_text
from app.utils.file_utils import cleanup_file
import os

bp = Blueprint('tts', __name__)

@bp.route('/generate', methods=['POST'])
def generate_speech():
    """Generate speech from text"""
    
    data = request.get_json() if request.is_json else request.form
    text = data.get('text', '').strip()
    voice = data.get('voice', 'alloy')
    quality = data.get('quality', 'standard')
    
    # Validate text
    if not text:
        return jsonify({'success': False, 'error': 'Text is required'}), 400
    
    # Sanitize text
    text = sanitize_text(text)
    
    # Validate text length
    max_length = current_app.config['MAX_TEXT_LENGTH']
    if not validate_text_length(text, max_length):
        return jsonify({
            'success': False,
            'error': f'Text exceeds maximum length of {max_length} characters'
        }), 400
    
    # Validate voice
    allowed_voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
    if voice not in allowed_voices:
        return jsonify({
            'success': False,
            'error': f'Invalid voice. Choose from: {", ".join(allowed_voices)}'
        }), 400
    
    try:
        # Generate speech
        if quality == 'hd':
            result = tts_service.generate_hd_speech(text, voice)
        else:
            result = tts_service.generate_speech(text, voice)
        
        if result['success']:
            audio_path = result['audio_path']
            
            # Return audio file
            return send_file(
                audio_path,
                mimetype='audio/mpeg',
                as_attachment=True,
                download_name=f'speech_{voice}.mp3'
            )
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/generate-json', methods=['POST'])
def generate_speech_json():
    """Generate speech and return JSON with file info"""
    
    data = request.get_json() if request.is_json else request.form
    text = data.get('text', '').strip()
    voice = data.get('voice', 'alloy')
    quality = data.get('quality', 'standard')
    translate_to = data.get('translate_to', None)  # Optional translation
    
    if not text:
        return jsonify({'success': False, 'error': 'Text is required'}), 400
    
    text = sanitize_text(text)
    
    max_length = current_app.config['MAX_TEXT_LENGTH']
    if not validate_text_length(text, max_length):
        return jsonify({
            'success': False,
            'error': f'Text exceeds maximum length of {max_length} characters'
        }), 400
    
    # Check if it's a cloned voice
    is_cloned = voice.startswith('cloned:')
    
    try:
        if is_cloned:
            # Use ElevenLabs for cloned voice
            voice_id = voice.replace('cloned:', '')
            result = voice_clone_service.generate_speech_with_cloned_voice(text, voice_id)
        else:
            # Use OpenAI for standard voices
            allowed_voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
            if voice not in allowed_voices:
                return jsonify({
                    'success': False,
                    'error': f'Invalid voice. Choose from: {", ".join(allowed_voices)}'
                }), 400
            
            if quality == 'hd':
                result = tts_service.generate_hd_speech(text, voice)
            else:
                result = tts_service.generate_speech(text, voice, translate_to=translate_to)
        
        if result['success']:
            # Store audio path in session for later download
            session['last_audio_path'] = result['audio_path']
            
            # Get filename for direct access
            import os
            filename = os.path.basename(result['audio_path'])
            
            return jsonify({
                'success': True,
                'message': 'Speech generated successfully',
                'voice': voice,
                'quality': result.get('quality', 'standard'),
                'audio_url': f'/temp/{filename}'
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/download', methods=['GET'])
def download_audio():
    """Download last generated audio"""
    
    audio_path = session.get('last_audio_path')
    
    if not audio_path or not os.path.exists(audio_path):
        return jsonify({'success': False, 'error': 'No audio file available'}), 404
    
    return send_file(
        audio_path,
        mimetype='audio/mpeg',
        as_attachment=True,
        download_name='speech.mp3'
    )

@bp.route('/voices', methods=['GET'])
def get_voices():
    """Get available voices"""
    voices = [
        {'id': 'alloy', 'name': 'Alloy', 'description': 'Neutral and balanced'},
        {'id': 'echo', 'name': 'Echo', 'description': 'Male voice'},
        {'id': 'fable', 'name': 'Fable', 'description': 'Warm and expressive'},
        {'id': 'onyx', 'name': 'Onyx', 'description': 'Deep male voice'},
        {'id': 'nova', 'name': 'Nova', 'description': 'Female voice'},
        {'id': 'shimmer', 'name': 'Shimmer', 'description': 'Soft female voice'}
    ]
    return jsonify({'success': True, 'voices': voices})


"""
Main application routes
"""
from flask import Blueprint, render_template, session, send_from_directory, current_app
import os

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Landing page - redirect to dashboard"""
    return render_template('dashboard.html')

@bp.route('/dashboard')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@bp.route('/stt')
def stt_page():
    """Speech-to-Text page"""
    return render_template('stt.html')

@bp.route('/tts')
def tts_page():
    """Text-to-Speech page"""
    # Get cloned voices from session
    cloned_voices = session.get('cloned_voices', [])
    return render_template('tts.html', cloned_voices=cloned_voices)

@bp.route('/dubbing')
def dubbing_page():
    """Video dubbing page"""
    # Get cloned voices from session for dubbing options
    cloned_voices = session.get('cloned_voices', [])
    return render_template('dubbing.html', cloned_voices=cloned_voices)

@bp.route('/temp/<path:filename>')
def serve_temp_file(filename):
    """Serve files from temp folder"""
    temp_folder = os.path.abspath(current_app.config['TEMP_FOLDER'])
    return send_from_directory(temp_folder, filename)


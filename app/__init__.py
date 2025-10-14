"""
Flask Application Factory
"""
from flask import Flask
from flask_cors import CORS
from config import config
import os

def create_app(config_name='default'):
    """Create and configure Flask application"""
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    from app.routes import main, stt, tts, avatar, voice_clone
    
    app.register_blueprint(main.bp)
    app.register_blueprint(stt.bp, url_prefix='/api/stt')
    app.register_blueprint(tts.bp, url_prefix='/api/tts')
    app.register_blueprint(avatar.bp, url_prefix='/api/avatar')
    app.register_blueprint(voice_clone.bp, url_prefix='/voice-clone')
    
    return app


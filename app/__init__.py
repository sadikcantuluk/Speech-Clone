"""
Flask Application Factory
"""
from flask import Flask
from flask_cors import CORS
from config import config
import os
import logging
import sys

def setup_logging(app, config_name):
    """Configure application logging"""
    
    # Set log level based on environment
    if config_name == 'development':
        log_level = logging.INFO
        app.logger.setLevel(log_level)
        
        # Create console handler with formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to app logger
        app.logger.addHandler(console_handler)
        
        # Also configure root logger for our services
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(console_handler)
        
        app.logger.info("🔧 Debug logging enabled for STT troubleshooting")
    else:
        # Production logging
        log_level = logging.WARNING
        app.logger.setLevel(log_level)

def create_app(config_name='default'):
    """Create and configure Flask application"""
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Configure logging
    setup_logging(app, config_name)
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    from app.routes import main, stt, tts, dubbing, voice_clone
    
    app.register_blueprint(main.bp)
    app.register_blueprint(stt.bp, url_prefix='/api/stt')
    app.register_blueprint(tts.bp, url_prefix='/api/tts')
    app.register_blueprint(dubbing.bp, url_prefix='/dubbing')
    app.register_blueprint(voice_clone.bp, url_prefix='/voice-clone')
    
    return app


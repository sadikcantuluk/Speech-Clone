import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_APP = os.getenv('FLASK_APP', 'app')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Replicate (for Wav2Lip lip-sync)
    REPLICATE_API_KEY = os.getenv('REPLICATE_API_KEY')
    
    # MiniMax (for voice cloning)
    MINIMAX_API_KEY = os.getenv('MINIMAX_API_KEY')
    MINIMAX_GROUP_ID = os.getenv('MINIMAX_GROUP_ID', '')
    
    # File Upload Settings
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 200))
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', 1000))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    TEMP_FOLDER = 'temp'
    
    # Allowed file extensions
    ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
    
    # Application
    APP_NAME = os.getenv('APP_NAME', 'Speech & Avatar App')
    APP_URL = os.getenv('APP_URL', 'http://localhost:5000')
    
    @staticmethod
    def init_app(app):
        """Initialize application with config"""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.TEMP_FOLDER, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


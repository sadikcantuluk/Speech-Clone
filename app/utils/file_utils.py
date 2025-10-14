"""
File handling utilities
"""
import os
from werkzeug.utils import secure_filename
from flask import current_app
import mimetypes

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, folder='uploads', prefix=''):
    """
    Save uploaded file securely
    
    Args:
        file: Uploaded file object
        folder: Folder to save file
        prefix: Prefix for filename
    
    Returns:
        str: Path to saved file
    """
    if not file:
        return None
    
    # Secure filename
    filename = secure_filename(file.filename)
    
    # Add prefix if provided
    if prefix:
        name, ext = os.path.splitext(filename)
        filename = f"{prefix}_{os.urandom(8).hex()}{ext}"
    else:
        name, ext = os.path.splitext(filename)
        filename = f"{os.urandom(8).hex()}{ext}"
    
    # Create folder if not exists
    os.makedirs(folder, exist_ok=True)
    
    # Save file
    file_path = os.path.join(folder, filename)
    file.save(file_path)
    
    return file_path

def get_file_extension(filename):
    """Get file extension"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def get_file_type(filename):
    """Get file MIME type"""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type

def is_audio_file(filename):
    """Check if file is audio"""
    ext = get_file_extension(filename)
    return ext in current_app.config['ALLOWED_AUDIO_EXTENSIONS']

def is_video_file(filename):
    """Check if file is video"""
    ext = get_file_extension(filename)
    return ext in current_app.config['ALLOWED_VIDEO_EXTENSIONS']

def is_image_file(filename):
    """Check if file is image"""
    ext = get_file_extension(filename)
    return ext in current_app.config['ALLOWED_IMAGE_EXTENSIONS']

def cleanup_file(file_path):
    """Delete file if exists"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception:
        pass
    return False

def get_file_size(file_path):
    """Get file size in bytes"""
    return os.path.getsize(file_path) if os.path.exists(file_path) else 0

def validate_file_size(file_path, max_size_bytes):
    """Validate file size"""
    return get_file_size(file_path) <= max_size_bytes


"""
OpenAI Whisper Speech-to-Text service
"""
import openai
from flask import current_app
import os
import mimetypes
import logging
import subprocess
import imageio_ffmpeg

class WhisperService:
    """Service for speech-to-text conversion using OpenAI Whisper"""
    
    def __init__(self):
        self.client = None
    
    def init_client(self):
        """Initialize OpenAI client with extended timeout"""
        if not self.client:
            api_key = current_app.config['OPENAI_API_KEY']
            if api_key:
                openai.api_key = api_key
                # Set timeout to 5 minutes for large file processing
                try:
                    openai.timeout = 300
                except:
                    pass  # Old version may not support this
                self.client = openai
        return self.client
    
    def validate_audio_file(self, audio_file_path):
        """
        Validate audio file before sending to API
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            dict: Validation result with details
        """
        try:
            if not os.path.exists(audio_file_path):
                return {
                    'valid': False,
                    'error': f'File does not exist: {audio_file_path}'
                }
            
            # Get file info
            file_size = os.path.getsize(audio_file_path)
            file_ext = os.path.splitext(audio_file_path)[1].lower()
            mime_type, _ = mimetypes.guess_type(audio_file_path)
            
            logging.info(f"🔍 Audio file validation:")
            logging.info(f"  📄 File: {os.path.basename(audio_file_path)}")
            logging.info(f"  📏 Size: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
            logging.info(f"  📎 Extension: {file_ext}")
            logging.info(f"  🏷️ MIME Type: {mime_type}")
            
            # Check file size (OpenAI limit is 25MB)
            max_size = 25 * 1024 * 1024  # 25MB
            if file_size > max_size:
                return {
                    'valid': False,
                    'error': f'File size ({file_size / 1024 / 1024:.2f} MB) exceeds OpenAI limit (25 MB)'
                }
            
            # Check if file is empty
            if file_size == 0:
                return {
                    'valid': False,
                    'error': 'File is empty'
                }
            
            # Check for MP3 specific issues
            if file_ext == '.mp3':
                logging.info("🔍 MP3 specific validation:")
                
                # Try to read first few bytes to check MP3 header
                with open(audio_file_path, 'rb') as f:
                    header = f.read(10)
                    logging.info(f"  📋 Header bytes: {header.hex()}")
                    
                    # Check for ID3 tag or MP3 frame header
                    if header.startswith(b'ID3'):
                        logging.info("  ✅ ID3 tag found")
                    elif header[0:2] == b'\xff\xfb' or header[0:2] == b'\xff\xf3' or header[0:2] == b'\xff\xf2':
                        logging.info("  ✅ MP3 frame header found")
                    else:
                        logging.warning(f"  ⚠️ Unusual MP3 header: {header[:4].hex()}")
            
            # Supported OpenAI formats
            openai_formats = {'.flac', '.m4a', '.mp3', '.mp4', '.mpeg', '.mpga', '.oga', '.ogg', '.wav', '.webm'}
            
            if file_ext not in openai_formats:
                return {
                    'valid': False,
                    'error': f'File format {file_ext} not supported by OpenAI. Supported: {sorted(openai_formats)}'
                }
            
            logging.info("✅ File validation passed")
            return {
                'valid': True,
                'file_size': file_size,
                'file_ext': file_ext,
                'mime_type': mime_type
            }
            
        except Exception as e:
            logging.error(f"❌ File validation error: {str(e)}")
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}'
            }
    
    def clean_mp3_file(self, input_path):
        """
        Clean MP3 file using ffmpeg to fix potential format issues
        
        Args:
            input_path: Path to original MP3 file
            
        Returns:
            str: Path to cleaned file, or None if failed
        """
        try:
            # Create output path
            input_dir = os.path.dirname(input_path)
            input_name = os.path.splitext(os.path.basename(input_path))[0]
            output_path = os.path.join(input_dir, f"{input_name}_cleaned.mp3")
            
            logging.info(f"🔧 Cleaning MP3 file: {os.path.basename(input_path)}")
            
            # Get ffmpeg executable
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            # Clean MP3 file - re-encode to ensure compatibility
            cmd = [
                ffmpeg_exe,
                '-i', input_path,
                '-acodec', 'libmp3lame',
                '-b:a', '192k',
                '-ar', '44100',  # Standard sample rate
                '-ac', '2',      # Stereo
                '-y',            # Overwrite output
                output_path
            ]
            
            logging.info(f"  🏃 Running: {' '.join(cmd[:3])} ... {cmd[-1]}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logging.error(f"❌ FFmpeg cleaning failed: {result.stderr}")
                return None
            
            # Check if cleaned file was created and is valid
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logging.info(f"✅ MP3 file cleaned successfully")
                logging.info(f"  📏 Original: {os.path.getsize(input_path)} bytes")
                logging.info(f"  📏 Cleaned: {os.path.getsize(output_path)} bytes")
                return output_path
            else:
                logging.error("❌ Cleaned file was not created or is empty")
                return None
                
        except Exception as e:
            logging.error(f"❌ MP3 cleaning error: {str(e)}")
            return None
    
    def transcribe_audio(self, audio_file_path, language=None, translate_to=None):
        """
        Transcribe audio file to text
        
        Args:
            audio_file_path: Path to audio file
            language: Optional language code for transcription hint (e.g., 'tr', 'en', 'de')
            translate_to: Optional language to translate the transcription to
        
        Returns:
            dict: Transcription result with text and metadata
        """
        try:
            logging.info(f"🎤 Starting transcription for: {os.path.basename(audio_file_path)}")
            
            # Validate audio file first
            validation = self.validate_audio_file(audio_file_path)
            if not validation['valid']:
                logging.error(f"❌ Audio file validation failed: {validation['error']}")
                return {
                    'success': False,
                    'error': f"File validation failed: {validation['error']}"
                }
            
            client = self.init_client()
            if not client:
                return {
                    'success': False,
                    'error': 'OpenAI client initialization failed'
                }
            
            # Log the parameters being sent
            logging.info(f"🔧 Transcription parameters:")
            logging.info(f"  🗣️ Language: {language if language else 'auto-detect'}")
            logging.info(f"  🌐 Translate to: {translate_to if translate_to else 'none'}")
            
            # First, transcribe the audio
            cleaned_file_path = None
            try:
                with open(audio_file_path, 'rb') as audio_file:
                    params = {
                        "model": "whisper-1",
                        "file": audio_file,
                    }
                    
                    if language:
                        params["language"] = language
                    
                    logging.info(f"📤 Sending request to OpenAI Whisper API...")
                    logging.info(f"  📋 Model: {params['model']}")
                    logging.info(f"  📄 File size: {validation['file_size']} bytes")
                    logging.info(f"  🏷️ File type: {validation['file_ext']}")
                    
                    response = client.audio.transcriptions.create(**params)
                    logging.info(f"✅ Received response from OpenAI")
                    
            except Exception as api_error:
                api_error_msg = str(api_error)
                logging.error(f"❌ First attempt failed: {api_error_msg}")
                
                # If it's an MP3 file and format error, try cleaning it
                if validation['file_ext'] == '.mp3' and "Invalid file format" in api_error_msg:
                    logging.info("🔄 Attempting to clean MP3 file and retry...")
                    
                    cleaned_file_path = self.clean_mp3_file(audio_file_path)
                    if cleaned_file_path:
                        # Retry with cleaned file
                        with open(cleaned_file_path, 'rb') as cleaned_audio:
                            params["file"] = cleaned_audio
                            logging.info(f"📤 Retrying with cleaned file...")
                            response = client.audio.transcriptions.create(**params)
                            logging.info(f"✅ Success with cleaned file!")
                    else:
                        raise api_error
                else:
                    raise api_error
            
            transcribed_text = response.text
            logging.info(f"📝 Transcription completed. Text length: {len(transcribed_text)} characters")
            
            # If translation is requested, translate using GPT
            if translate_to and translate_to != language:
                logging.info(f"🔄 Translating to {translate_to}...")
                translation_result = self.translate_text(transcribed_text, translate_to)
                if translation_result['success']:
                    transcribed_text = translation_result['translated_text']
                    logging.info(f"✅ Translation completed")
                else:
                    logging.warning(f"⚠️ Translation failed: {translation_result['error']}")
            
            # Cleanup temporary cleaned file if created
            if cleaned_file_path and os.path.exists(cleaned_file_path):
                try:
                    os.remove(cleaned_file_path)
                    logging.info(f"🧹 Cleaned up temporary file: {os.path.basename(cleaned_file_path)}")
                except:
                    pass
            
            return {
                'success': True,
                'text': transcribed_text,
                'original_language': language,
                'translated_to': translate_to if translate_to else None
            }
        except Exception as e:
            error_msg = str(e)
            logging.error(f"❌ Transcription error: {error_msg}")
            
            # Cleanup temporary cleaned file if created
            if cleaned_file_path and os.path.exists(cleaned_file_path):
                try:
                    os.remove(cleaned_file_path)
                    logging.info(f"🧹 Cleaned up temporary file after error: {os.path.basename(cleaned_file_path)}")
                except:
                    pass
            
            # Log additional details for debugging
            if "Invalid file format" in error_msg:
                logging.error("🔍 This appears to be a file format issue")
                logging.error(f"  📄 File: {audio_file_path}")
                if os.path.exists(audio_file_path):
                    logging.error(f"  📏 Size: {os.path.getsize(audio_file_path)} bytes")
                    with open(audio_file_path, 'rb') as f:
                        header = f.read(20)
                        logging.error(f"  📋 File header: {header.hex()}")
            
            return {
                'success': False,
                'error': error_msg
            }
    
    def translate_text(self, text, target_language):
        """
        Translate text to target language using OpenAI
        
        Args:
            text: Text to translate
            target_language: Target language code or name
        
        Returns:
            dict: Translation result
        """
        try:
            client = self.init_client()
            
            # Language code to name mapping
            lang_names = {
                'en': 'English',
                'tr': 'Turkish', 
                'de': 'German',
                'fr': 'French',
                'es': 'Spanish',
                'it': 'Italian',
                'pt': 'Portuguese',
                'ru': 'Russian',
                'ja': 'Japanese',
                'ko': 'Korean',
                'zh': 'Chinese'
            }
            
            target_lang_name = lang_names.get(target_language, target_language)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are a professional translator. Translate the following text to {target_lang_name}. Only provide the translation, no explanations."},
                    {"role": "user", "content": text}
                ],
                temperature=0.3
            )
            
            translated_text = response.choices[0].message.content
            
            return {
                'success': True,
                'translated_text': translated_text
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def transcribe_with_timestamps(self, audio_file_path, language=None):
        """
        Transcribe audio with word-level timestamps
        
        Args:
            audio_file_path: Path to audio file
            language: Optional language code
        
        Returns:
            dict: Transcription with timestamps
        """
        try:
            logging.info(f"🎤⏰ Starting transcription with timestamps for: {os.path.basename(audio_file_path)}")
            
            # Validate audio file first
            validation = self.validate_audio_file(audio_file_path)
            if not validation['valid']:
                logging.error(f"❌ Audio file validation failed: {validation['error']}")
                return {
                    'success': False,
                    'error': f"File validation failed: {validation['error']}"
                }
            
            client = self.init_client()
            if not client:
                return {
                    'success': False,
                    'error': 'OpenAI client initialization failed'
                }
            
            cleaned_file_path = None
            try:
                with open(audio_file_path, 'rb') as audio_file:
                    params = {
                        "model": "whisper-1",
                        "file": audio_file,
                        "response_format": "verbose_json",
                        "timestamp_granularities": ["word"]
                    }
                    
                    if language:
                        params["language"] = language
                    
                    logging.info(f"📤 Sending timestamp transcription request to OpenAI...")
                    logging.info(f"  📋 Model: {params['model']}")
                    logging.info(f"  📄 File size: {validation['file_size']} bytes")
                    logging.info(f"  🏷️ File type: {validation['file_ext']}")
                    logging.info(f"  ⏰ With word timestamps")
                    
                    response = client.audio.transcriptions.create(**params)
                    logging.info(f"✅ Received timestamp response from OpenAI")
                    
            except Exception as api_error:
                api_error_msg = str(api_error)
                logging.error(f"❌ First timestamp attempt failed: {api_error_msg}")
                
                # If it's an MP3 file and format error, try cleaning it
                if validation['file_ext'] == '.mp3' and "Invalid file format" in api_error_msg:
                    logging.info("🔄 Attempting to clean MP3 file and retry timestamp transcription...")
                    
                    cleaned_file_path = self.clean_mp3_file(audio_file_path)
                    if cleaned_file_path:
                        # Retry with cleaned file
                        with open(cleaned_file_path, 'rb') as cleaned_audio:
                            params["file"] = cleaned_audio
                            logging.info(f"📤 Retrying timestamp transcription with cleaned file...")
                            response = client.audio.transcriptions.create(**params)
                            logging.info(f"✅ Success with cleaned file (timestamps)!")
                    else:
                        raise api_error
                else:
                    raise api_error
            
            # Cleanup temporary cleaned file if created
            if cleaned_file_path and os.path.exists(cleaned_file_path):
                try:
                    os.remove(cleaned_file_path)
                    logging.info(f"🧹 Cleaned up temporary file (timestamps): {os.path.basename(cleaned_file_path)}")
                except:
                    pass
            
            return {
                'success': True,
                'text': response.text,
                'words': response.words if hasattr(response, 'words') else [],
                'language': response.language if hasattr(response, 'language') else language
            }
        except Exception as e:
            error_msg = str(e)
            logging.error(f"❌ Timestamp transcription error: {error_msg}")
            
            # Cleanup temporary cleaned file if created
            if cleaned_file_path and os.path.exists(cleaned_file_path):
                try:
                    os.remove(cleaned_file_path)
                    logging.info(f"🧹 Cleaned up temporary file after error (timestamps): {os.path.basename(cleaned_file_path)}")
                except:
                    pass
            
            # Log additional details for debugging
            if "Invalid file format" in error_msg:
                logging.error("🔍 This appears to be a file format issue (timestamp method)")
                logging.error(f"  📄 File: {audio_file_path}")
                if os.path.exists(audio_file_path):
                    logging.error(f"  📏 Size: {os.path.getsize(audio_file_path)} bytes")
                    with open(audio_file_path, 'rb') as f:
                        header = f.read(20)
                        logging.error(f"  📋 File header: {header.hex()}")
            
            return {
                'success': False,
                'error': error_msg
            }

# Global service instance
whisper_service = WhisperService()


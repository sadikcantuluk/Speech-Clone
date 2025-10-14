"""
OpenAI Whisper Speech-to-Text service
"""
import openai
from flask import current_app
import os

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
            client = self.init_client()
            
            # First, transcribe the audio
            with open(audio_file_path, 'rb') as audio_file:
                params = {
                    "model": "whisper-1",
                    "file": audio_file,
                }
                
                if language:
                    params["language"] = language
                
                response = client.audio.transcriptions.create(**params)
            
            transcribed_text = response.text
            
            # If translation is requested, translate using GPT
            if translate_to and translate_to != language:
                translation_result = self.translate_text(transcribed_text, translate_to)
                if translation_result['success']:
                    transcribed_text = translation_result['translated_text']
            
            return {
                'success': True,
                'text': transcribed_text,
                'original_language': language,
                'translated_to': translate_to if translate_to else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
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
            client = self.init_client()
            
            with open(audio_file_path, 'rb') as audio_file:
                params = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "response_format": "verbose_json",
                    "timestamp_granularities": ["word"]
                }
                
                if language:
                    params["language"] = language
                
                response = client.audio.transcriptions.create(**params)
            
            return {
                'success': True,
                'text': response.text,
                'words': response.words if hasattr(response, 'words') else [],
                'language': response.language if hasattr(response, 'language') else language
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global service instance
whisper_service = WhisperService()


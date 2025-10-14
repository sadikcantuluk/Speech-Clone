"""
Text-to-Speech service using OpenAI TTS
"""
import openai
from flask import current_app
import os
from pathlib import Path

class TTSService:
    """Service for text-to-speech conversion"""
    
    def __init__(self):
        self.client = None
    
    def init_client(self):
        """Initialize OpenAI client with extended timeout"""
        if not self.client:
            api_key = current_app.config['OPENAI_API_KEY']
            if api_key:
                openai.api_key = api_key
                # Set timeout to 5 minutes for TTS generation
                try:
                    openai.timeout = 300
                except:
                    pass  # Old version may not support this
                self.client = openai
        return self.client
    
    def generate_speech(self, text, voice="alloy", output_path=None, translate_to=None):
        """
        Generate speech from text
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            output_path: Path to save audio file
            translate_to: Optional language to translate text to before speech
        
        Returns:
            dict: Result with audio file path
        """
        try:
            client = self.init_client()
            
            # Translate text if requested
            speech_text = text
            if translate_to:
                translation_result = self.translate_text(text, translate_to)
                if translation_result['success']:
                    speech_text = translation_result['translated_text']
            
            # Generate unique filename if not provided
            if not output_path:
                temp_folder = current_app.config['TEMP_FOLDER']
                os.makedirs(temp_folder, exist_ok=True)
                output_path = os.path.join(temp_folder, f"tts_{os.urandom(8).hex()}.mp3")
            
            # Create speech
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=speech_text
            )
            
            # Save to file
            response.stream_to_file(output_path)
            
            return {
                'success': True,
                'audio_path': output_path,
                'voice': voice,
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
    
    def generate_hd_speech(self, text, voice="alloy", output_path=None):
        """
        Generate high-quality speech from text
        
        Args:
            text: Text to convert to speech
            voice: Voice to use
            output_path: Path to save audio file
        
        Returns:
            dict: Result with audio file path
        """
        try:
            client = self.init_client()
            
            if not output_path:
                temp_folder = current_app.config['TEMP_FOLDER']
                os.makedirs(temp_folder, exist_ok=True)
                output_path = os.path.join(temp_folder, f"tts_hd_{os.urandom(8).hex()}.mp3")
            
            response = client.audio.speech.create(
                model="tts-1-hd",
                voice=voice,
                input=text
            )
            
            response.stream_to_file(output_path)
            
            return {
                'success': True,
                'audio_path': output_path,
                'voice': voice,
                'quality': 'hd'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global service instance
tts_service = TTSService()


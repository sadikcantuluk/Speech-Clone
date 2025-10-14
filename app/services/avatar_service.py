"""
Avatar creation and video generation service
"""
import openai
from flask import current_app
import os
from PIL import Image
import requests
import subprocess
import imageio_ffmpeg
import replicate
import time

class AvatarService:
    """Service for avatar creation and video generation"""
    
    def __init__(self):
        self.client = None
    
    def init_client(self):
        """Initialize OpenAI client with extended timeout"""
        if not self.client:
            api_key = current_app.config['OPENAI_API_KEY']
            if api_key:
                openai.api_key = api_key
                # Set timeout to 5 minutes for image generation
                try:
                    openai.timeout = 300
                except:
                    pass  # Old version may not support this
                self.client = openai
        return self.client
    
    def create_avatar_from_photo(self, photo_path, prompt=None):
        """
        Create avatar from user photo using DALL-E
        
        Args:
            photo_path: Path to user's photo
            prompt: Optional custom prompt for avatar style
        
        Returns:
            dict: Result with avatar image URL/path
        """
        try:
            client = self.init_client()
            
            # Default professional avatar prompt
            if not prompt:
                prompt = ("Create a semi-realistic illustrated avatar based on the uploaded photo. "
                         "Maintain a strong likeness to the person — especially facial proportions, nose, jawline, and eye shape. "
                         "Render with smooth digital painting style, natural skin texture, and soft lighting that enhances facial depth. "
                         "Avoid over-smoothing; preserve subtle pores and natural shadows for realism. "
                         "Use well-balanced warm-neutral colors for skin tone and soft shading for dimension. "
                         "Keep eyes clear and expressive, with realistic highlights and accurate iris color. "
                         "Render hair with soft gradients and detailed strands, avoiding artificial sharpness. "
                         "Background should be neutral or softly gradient (light gray or beige), ensuring the face stands out naturally. "
                         "Output should be suitable for in-app avatars and AI chat interfaces, visually clean and professional. "
                         "Style reference: semi-realistic digital portrait illustration with light stylization (somewhere between realism and illustration)")
            
            # Use DALL-E image variation to create avatar
            with open(photo_path, 'rb') as image_file:
                response = client.images.create_variation(
                    image=image_file,
                    n=1,
                    size="1024x1024"
                )
            
            # Get generated image URL
            generated_image_url = response.data[0].url
            
            # Download the generated avatar
            temp_folder = os.path.abspath(current_app.config['TEMP_FOLDER'])
            os.makedirs(temp_folder, exist_ok=True)
            avatar_filename = f"avatar_{os.urandom(8).hex()}.png"
            avatar_path = os.path.join(temp_folder, avatar_filename)
            
            # Download image from URL
            img_response = requests.get(generated_image_url)
            with open(avatar_path, 'wb') as f:
                f.write(img_response.content)
            
            # Use /temp/ route for serving files
            avatar_url = f"/temp/{avatar_filename}"
            
            return {
                'success': True,
                'avatar_url': avatar_url,
                'avatar_path': avatar_path
            }
        except Exception as e:
            # Fallback: use processed photo if DALL-E fails
            print(f"DALL-E avatar creation failed: {e}. Using processed photo.")
            try:
                temp_folder = os.path.abspath(current_app.config['TEMP_FOLDER'])
                os.makedirs(temp_folder, exist_ok=True)
                avatar_filename = f"avatar_{os.urandom(8).hex()}.png"
                avatar_path = os.path.join(temp_folder, avatar_filename)
                
                import shutil
                shutil.copy(photo_path, avatar_path)
                
                avatar_url = f"/temp/{avatar_filename}"
                
                return {
                    'success': True,
                    'avatar_url': avatar_url,
                    'avatar_path': avatar_path,
                    'fallback': True
                }
            except Exception as fallback_error:
                return {
                    'success': False,
                    'error': str(fallback_error)
                }
    
    def generate_avatar_video(self, avatar_image_path, audio_path, output_path=None, use_lipsync=False):
        """
        Generate video with avatar and audio
        
        Args:
            avatar_image_path: Path to avatar image
            audio_path: Path to audio file
            output_path: Path to save output video
            use_lipsync: Whether to use Wav2Lip for lip-sync
        
        Returns:
            dict: Result with video path
        """
        try:
            # Generate output path if not provided
            if not output_path:
                temp_folder = os.path.abspath(current_app.config['TEMP_FOLDER'])
                os.makedirs(temp_folder, exist_ok=True)
                output_path = os.path.join(temp_folder, f"avatar_video_{os.urandom(8).hex()}.mp4")
            
            # Get audio duration
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            probe_cmd = [
                ffmpeg_exe.replace('ffmpeg', 'ffprobe'),
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                audio_path
            ]
            
            try:
                duration_result = subprocess.run(probe_cmd, capture_output=True, text=True)
                duration = float(duration_result.stdout.strip())
            except:
                duration = 10.0
            
            # If lip-sync is requested, use Wav2Lip
            if use_lipsync:
                lipsync_result = self.apply_wav2lip(avatar_image_path, audio_path, output_path)
                if lipsync_result['success']:
                    return {
                        'success': True,
                        'video_path': lipsync_result['video_path'],
                        'duration': duration,
                        'lipsync_applied': True
                    }
                else:
                    # If Wav2Lip fails, fall back to simple method
                    print(f"Wav2Lip failed: {lipsync_result['error']}. Falling back to simple method.")
            
            # Simple method: static image with audio
            cmd = [
                ffmpeg_exe,
                '-loop', '1',
                '-i', avatar_image_path,
                '-i', audio_path,
                '-c:v', 'libx264',
                '-tune', 'stillimage',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-pix_fmt', 'yuv420p',
                '-shortest',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f'FFmpeg error: {result.stderr}'
                }
            
            return {
                'success': True,
                'video_path': output_path,
                'duration': duration,
                'lipsync_applied': False
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def apply_wav2lip(self, image_path, audio_path, output_path):
        """
        Apply Wav2Lip for lip-sync using Replicate API
        
        Args:
            image_path: Path to avatar image
            audio_path: Path to audio file
            output_path: Path to save output video
        
        Returns:
            dict: Result with video path
        """
        try:
            # Get Replicate API key
            api_key = current_app.config.get('REPLICATE_API_KEY')
            if not api_key:
                return {
                    'success': False,
                    'error': 'REPLICATE_API_KEY not configured'
                }
            
            # Set API key
            os.environ['REPLICATE_API_TOKEN'] = api_key
            
            print(f"🎭 Starting Replicate Wav2Lip (this may take 30-90 seconds)...")
            
            # Convert files to file handles for Replicate
            # Replicate expects file paths or file handles
            try:
                print("🔄 Calling Replicate API...")
                
                # Try primary model with file paths
                with open(image_path, 'rb') as img_file, open(audio_path, 'rb') as audio_file:
                    output = replicate.run(
                        "devxpy/cog-wav2lip:8d65e3f4f4298520e079198b493c25adfc43c058ffec924f2aefc8010ed25eef",
                        input={
                            "face": img_file,
                            "audio": audio_file,
                            "pads": [0, 10, 0, 0],
                            "smooth": True,
                            "resize_factor": 1
                        }
                    )
                
            except Exception as e:
                # Try alternative model
                print(f"⚠️ Primary model failed, trying alternative: {e}")
                try:
                    with open(image_path, 'rb') as img_file, open(audio_path, 'rb') as audio_file:
                        output = replicate.run(
                            "yoyo-nb/Wav2Lip:c5f610555e2780238e695f8e9f2c0e1f7d76c2f7e91a1ef01e78da3125e0794f",
                            input={
                                "face": img_file,
                                "audio": audio_file
                            }
                        )
                except Exception as e2:
                    return {
                        'success': False,
                        'error': f'All Replicate models failed: {e2}'
                    }
            
            # Output is a URL to the generated video
            if not output:
                return {
                    'success': False,
                    'error': 'No output from Replicate'
                }
            
            # If output is a list, get first item
            video_url = output[0] if isinstance(output, list) else output
            
            # Handle FileOutput objects
            if hasattr(video_url, 'url'):
                video_url = video_url.url
            
            print(f"📥 Downloading result from Replicate: {video_url}")
            
            # Download the video
            video_response = requests.get(str(video_url), timeout=300, stream=True)
            video_response.raise_for_status()
            
            # Save to output path
            with open(output_path, 'wb') as f:
                for chunk in video_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify file
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"✅ Lip-sync video saved successfully: {output_path}")
                return {
                    'success': True,
                    'video_path': output_path
                }
            else:
                return {
                    'success': False,
                    'error': 'Downloaded video is empty or missing'
                }
                
        except Exception as e:
            print(f"❌ Replicate Wav2Lip error: {e}")
            return {
                'success': False,
                'error': f'Replicate Wav2Lip error: {str(e)}'
            }
    
    def process_user_photo(self, photo_path):
        """
        Process and optimize user photo for avatar creation
        
        Args:
            photo_path: Path to user's photo
        
        Returns:
            dict: Result with processed photo path
        """
        try:
            # Open and process image
            img = Image.open(photo_path)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to optimal size (1024x1024 for DALL-E)
            img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            
            # Create square image with padding if needed
            if img.size[0] != img.size[1]:
                # Create square canvas
                max_size = max(img.size)
                square_img = Image.new('RGB', (max_size, max_size), (255, 255, 255))
                # Paste image centered
                offset = ((max_size - img.size[0]) // 2, (max_size - img.size[1]) // 2)
                square_img.paste(img, offset)
                img = square_img
            
            # Save processed image
            temp_folder = current_app.config['TEMP_FOLDER']
            os.makedirs(temp_folder, exist_ok=True)
            processed_path = os.path.join(temp_folder, f"processed_{os.urandom(8).hex()}.png")
            img.save(processed_path, 'PNG', quality=95)
            
            return {
                'success': True,
                'processed_path': processed_path
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global service instance
avatar_service = AvatarService()


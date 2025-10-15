"""
Voice cloning service using MiniMax API
"""
import requests
import base64
from flask import current_app
import os
import json
import subprocess
import imageio_ffmpeg

class VoiceCloneService:
    """Service for voice cloning and custom voice management"""
    
    def __init__(self):
        self.base_url = "https://api.minimax.io/v1"
    
    def get_headers(self):
        """Get API headers"""
        api_key = current_app.config.get('MINIMAX_API_KEY')
        return {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def fix_duplicated_audio(self, audio_file_path):
        """
        Fix duplicated audio by cutting it in half from the middle
        
        This addresses the issue where MiniMax API sometimes returns
        duplicated audio content (same speech repeated twice)
        
        Args:
            audio_file_path: Path to the audio file to fix
            
        Returns:
            str: Path to the fixed audio file, or original path if fixing failed
        """
        try:
            print(f"🔧 Fixing duplicated audio: {os.path.basename(audio_file_path)}")
            
            # Get FFmpeg executable
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            # First, get the duration of the audio file
            duration_cmd = [
                ffmpeg_exe, 
                '-i', audio_file_path,
                '-f', 'null', '-'
            ]
            
            result = subprocess.run(duration_cmd, capture_output=True, text=True)
            duration_line = None
            
            # Parse duration from stderr (FFmpeg outputs info to stderr)
            for line in result.stderr.split('\n'):
                if 'Duration:' in line:
                    duration_line = line
                    break
            
            if not duration_line:
                print(f"⚠️ Could not get audio duration, returning original file")
                return audio_file_path
            
            # Extract duration in format "Duration: HH:MM:SS.ms"
            import re
            duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})', duration_line)
            if not duration_match:
                print(f"⚠️ Could not parse duration, returning original file")
                return audio_file_path
            
            hours, minutes, seconds = duration_match.groups()
            total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            
            print(f"📏 Original audio duration: {total_seconds:.2f} seconds")
            
            # Calculate half duration
            half_duration = total_seconds / 2
            print(f"✂️ Cutting to first half: {half_duration:.2f} seconds")
            
            # Create output path
            input_dir = os.path.dirname(audio_file_path)
            input_name = os.path.splitext(os.path.basename(audio_file_path))[0]
            fixed_path = os.path.join(input_dir, f"{input_name}_fixed.mp3")
            
            # Cut audio to first half using FFmpeg
            cut_cmd = [
                ffmpeg_exe,
                '-i', audio_file_path,
                '-t', str(half_duration),  # Duration to extract
                '-acodec', 'copy',         # Copy audio codec (faster)
                '-y',                      # Overwrite output
                fixed_path
            ]
            
            print(f"🏃 Running: {' '.join(cut_cmd[:3])} ... -t {half_duration:.2f} ... {os.path.basename(fixed_path)}")
            
            result = subprocess.run(cut_cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ FFmpeg cutting failed: {result.stderr}")
                return audio_file_path
            
            # Check if fixed file was created and is valid
            if os.path.exists(fixed_path) and os.path.getsize(fixed_path) > 0:
                print(f"✅ Audio fixed successfully!")
                print(f"  📏 Original: {os.path.getsize(audio_file_path)} bytes")
                print(f"  📏 Fixed: {os.path.getsize(fixed_path)} bytes")
                
                # Replace original file with fixed one
                os.remove(audio_file_path)
                os.rename(fixed_path, audio_file_path)
                print(f"🔄 Replaced original file with fixed version")
                
                return audio_file_path
            else:
                print(f"❌ Fixed file was not created or is empty")
                return audio_file_path
                
        except Exception as e:
            print(f"❌ Audio fixing error: {str(e)}")
            return audio_file_path
    
    def clone_voice(self, audio_file_path, voice_name, voice_description=None):
        """
        Clone a voice from audio file using MiniMax API
        
        Workflow:
        1. Upload source audio file
        2. Call voice clone API with file_id
        3. Generate preview audio and return voice_id
        
        Args:
            audio_file_path: Path to audio file (10 sec - 5 min, mp3/m4a/wav, max 20MB)
            voice_name: Name for the cloned voice (will be used as voice_id)
            voice_description: Optional description for the voice
        
        Returns:
            dict: Result with voice ID and info
        """
        try:
            api_key = current_app.config.get('MINIMAX_API_KEY')
            
            if not api_key:
                return {
                    'success': False,
                    'error': 'MiniMax API key not configured'
                }
            
            # Step 1: Check if video file and extract audio
            file_ext = os.path.splitext(audio_file_path)[1].lower()
            
            # If video file, extract audio first
            if file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                print(f"🎬 Video file detected, extracting audio...")
                
                # Extract audio using ffmpeg
                import subprocess
                import imageio_ffmpeg
                
                audio_output_path = audio_file_path.rsplit('.', 1)[0] + '_audio.mp3'
                ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
                
                cmd = [
                    ffmpeg_exe, '-i', audio_file_path, '-vn', '-acodec', 'libmp3lame',
                    '-b:a', '192k', '-y', audio_output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0 or not os.path.exists(audio_output_path):
                    return {
                        'success': False,
                        'error': f'Failed to extract audio from video: {result.stderr}'
                    }
                
                audio_file_path = audio_output_path
                print(f"✅ Audio extracted to: {audio_file_path}")
            
            # Step 2: Upload source audio file
            upload_url = f"{self.base_url}/files/upload"
            
            print(f"📤 Uploading file to MiniMax: {audio_file_path}")
            
            # Determine correct MIME type
            file_ext = os.path.splitext(audio_file_path)[1].lower()
            mime_types = {
                '.mp3': 'audio/mpeg',
                '.m4a': 'audio/mp4',
                '.wav': 'audio/wav'
            }
            mime_type = mime_types.get(file_ext, 'audio/mpeg')
            
            with open(audio_file_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(audio_file_path), f, mime_type)
                }
                data = {
                    'purpose': 'voice_clone'
                }
                
                upload_response = requests.post(
                    upload_url, 
                    headers={'Authorization': f'Bearer {api_key}'}, 
                    data=data, 
                    files=files,
                    timeout=60
                )
                
                print(f"📥 Upload response status: {upload_response.status_code}")
                print(f"📄 Upload response text: {upload_response.text[:500]}")
                
                upload_response.raise_for_status()
                
                try:
                    file_data = upload_response.json()
                except Exception as json_error:
                    return {
                        'success': False,
                        'error': f'Failed to parse upload response as JSON: {upload_response.text[:200]}'
                    }
                
                if file_data is None:
                    return {
                        'success': False,
                        'error': f'Upload response is None. Raw response: {upload_response.text[:200]}'
                    }
                
                # Try different response structures
                file_id = None
                if isinstance(file_data, dict):
                    file_id = (file_data.get('file', {}).get('file_id') or 
                              file_data.get('file_id') or 
                              file_data.get('data', {}).get('file_id'))
                
                print(f"🆔 Extracted file_id: {file_id}")
                
                if not file_id:
                    return {
                        'success': False,
                        'error': f'Failed to get file_id from upload response: {file_data}'
                    }
            
            # Step 3: Clone the voice
            clone_url = f"{self.base_url}/voice_clone"
            
            # Generate unique voice_id from voice_name
            # Remove special characters and non-ASCII characters (Turkish chars, etc.)
            import re
            import unicodedata
            
            # Normalize and remove accents/diacritics
            voice_name_normalized = unicodedata.normalize('NFKD', voice_name)
            voice_name_ascii = voice_name_normalized.encode('ASCII', 'ignore').decode('ASCII')
            
            # Keep only alphanumeric and underscores
            voice_name_clean = re.sub(r'[^a-zA-Z0-9_]', '_', voice_name_ascii.lower())
            
            # Remove consecutive underscores and leading/trailing underscores
            voice_name_clean = re.sub(r'_+', '_', voice_name_clean).strip('_')
            
            # Generate unique voice_id
            voice_id = f"{voice_name_clean}_{os.urandom(4).hex()}"
            
            # Ensure voice_id is not empty
            if not voice_name_clean:
                voice_id = f"voice_{os.urandom(6).hex()}"

            print(f"🎤 Cloning voice with ID: {voice_id}")
            
            clone_payload = {
                "file_id": file_id,
                "voice_id": voice_id,
                "text": voice_description or "This is a cloned voice for text-to-speech.",
                "model": "speech-2.5-hd-preview"
            }
            
            clone_headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            clone_response = requests.post(
                clone_url,
                headers=clone_headers,
                json=clone_payload,
                timeout=120
            )

            print(f"📥 Clone response status: {clone_response.status_code}")
            print(f"📄 Clone response body: {clone_response.text}")

            clone_response.raise_for_status()
            
            # Check response for success
            clone_result = clone_response.json()
            if 'base_resp' in clone_result:
                base_resp = clone_result['base_resp']
                if base_resp.get('status_code') != 0:
                    error_msg = base_resp.get('status_msg', 'Unknown error')
                    
                    # Make error messages more user-friendly
                    if 'too short' in error_msg.lower():
                        error_msg = 'Ses dosyanız çok kısa! En az 10 saniye uzunluğunda bir ses/video yükleyin.'
                    elif 'invalid character' in error_msg.lower():
                        error_msg = 'Geçersiz karakter! Lütfen sadece İngilizce harfler kullanın.'
                    elif 'insufficient balance' in error_msg.lower():
                        error_msg = 'MiniMax API hesabınızda yetersiz bakiye var. Lütfen hesabınıza kredi yükleyin.'
                    
                    return {
                        'success': False,
                        'error': f"{error_msg}"
                    }

            print(f"✅ Voice cloned successfully: {voice_id}")
            
            return {
                'success': True,
                'voice_id': voice_id,
                'voice_name': voice_name,
                'message': f'Voice "{voice_name}" cloned successfully!'
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            try:
                if hasattr(e.response, 'text'):
                    error_msg = f"{e.response.status_code}: {e.response.text}"
            except:
                pass
            return {
                'success': False,
                'error': f'Voice cloning failed: {error_msg}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Voice cloning failed: {str(e)}'
            }
    
    def generate_speech_with_cloned_voice(self, text, voice_id, output_path=None):
        """
        Generate speech using a cloned voice with MiniMax T2A API
        
        Args:
            text: Text to convert to speech
            voice_id: ID of the cloned voice
            output_path: Path to save audio file
        
        Returns:
            dict: Result with audio file path
        """
        try:
            api_key = current_app.config.get('MINIMAX_API_KEY')
            group_id = current_app.config.get('MINIMAX_GROUP_ID', '')
            
            if not api_key:
                return {
                    'success': False,
                    'error': 'MiniMax API key not configured'
                }
            
            # Generate output path if not provided
            if not output_path:
                temp_folder = os.path.abspath(current_app.config['TEMP_FOLDER'])
                os.makedirs(temp_folder, exist_ok=True)
                output_path = os.path.join(temp_folder, f"cloned_speech_{os.urandom(8).hex()}.mp3")
            
            # MiniMax T2A API - Try both sync endpoints
            # /t2a_v2 returns base64 (might be incomplete)
            # /t2a returns streaming (better for reliability)
            
            # Try with stream=True to get complete audio
            payload = {
                "model": "speech-2.5-hd-preview",
                "text": text,
                "voice_setting": {
                    "voice_id": voice_id,
                    "speed": 1.0,
                    "vol": 1.0,
                    "pitch": 0
                },
                "audio_setting": {
                    "sample_rate": 32000,
                    "bitrate": 128000,
                    "format": "mp3",
                    "channel": 1
                },
                "stream": True  # Request streaming to get complete audio
            }
            
            # Add group_id if available
            if group_id and group_id.strip():
                payload["group_id"] = group_id
            
            url = f"{self.base_url}/t2a_v2"
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            print(f"🔊 Calling MiniMax T2A: {url}")
            print(f"📦 Payload: {payload}")
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60, stream=True)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('Content-Type', '')
                print(f"📦 Response Content-Type: {content_type}")
                
                # If Server-Sent Events (SSE)
                if 'text/event-stream' in content_type:
                    print("📦 Receiving SSE stream...")
                    audio_data = b""
                    
                    for line in response.iter_lines(decode_unicode=True):
                        if line:
                            print(f"📦 SSE Line: {line[:100]}...")
                            
                            # SSE format: "data: {...}"
                            if line.startswith('data: '):
                                json_str = line[6:]  # Remove "data: "
                                try:
                                    event_data = json.loads(json_str)
                                    
                                    # Look for audio data in SSE events
                                    if 'data' in event_data and 'audio' in event_data['data']:
                                        audio_chunk = event_data['data']['audio']
                                        # Convert hex to bytes
                                        audio_bytes = bytes.fromhex(audio_chunk)
                                        audio_data += audio_bytes
                                        print(f"📦 Got audio chunk: {len(audio_bytes)} bytes")
                                    
                                    # Check if final
                                    if event_data.get('is_final'):
                                        print(f"✅ Final SSE event received")
                                        break
                                        
                                except json.JSONDecodeError:
                                    continue
                    
                    if audio_data:
                        print(f"✅ Total audio: {len(audio_data)} bytes")
                        with open(output_path, 'wb') as f:
                            f.write(audio_data)
                        
                        # Fix duplicated audio by cutting in half
                        fixed_path = self.fix_duplicated_audio(output_path)
                        
                        return {'success': True, 'audio_path': fixed_path}
                    else:
                        return {'success': False, 'error': 'No audio data in SSE stream'}
                
                # If streaming audio (binary)
                elif 'audio' in content_type or 'octet-stream' in content_type:
                    print("📦 Receiving binary audio stream...")
                    audio_data = b""
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            audio_data += chunk
                    
                    print(f"✅ Downloaded {len(audio_data)} bytes from binary stream")
                    
                    # Save directly
                    with open(output_path, 'wb') as f:
                        f.write(audio_data)
                    
                    # Fix duplicated audio by cutting in half
                    fixed_path = self.fix_duplicated_audio(output_path)
                    
                    return {
                        'success': True,
                        'audio_path': fixed_path
                    }
                
                # Otherwise JSON response
                result = response.json()
                
                # Check MiniMax base_resp
                if 'base_resp' in result:
                    base_resp = result['base_resp']
                    if base_resp.get('status_code') != 0:
                        error_msg = base_resp.get('status_msg', 'Unknown error')
                        
                        # User-friendly error messages
                        if 'rate limit' in error_msg.lower():
                            error_msg = 'API rate limit aşıldı. Lütfen birkaç saniye bekleyip tekrar deneyin.'
                        elif 'token limit' in error_msg.lower():
                            error_msg = 'Token limiti aşıldı. Daha kısa bir metin deneyin.'
                        
                        return {
                            'success': False,
                            'error': error_msg
                        }
                
                print(f"✅ TTS Success!")
                print(f"📦 Full Response Keys: {result.keys()}")
                if 'data' in result:
                    print(f"📦 Data Keys: {result['data'].keys()}")
                    if 'audio' in result['data']:
                        audio_len = len(result['data']['audio'])
                        print(f"📦 Base64 audio length: {audio_len} characters")
                    if 'audio_url' in result['data']:
                        print(f"📦 Audio URL found: {result['data']['audio_url']}")
                if 'extra_info' in result:
                    print(f"📦 Extra Info Keys: {result['extra_info'].keys()}")
                    if 'audio_url' in result['extra_info']:
                        print(f"📦 Audio URL in extra_info: {result['extra_info']['audio_url']}")
                    else:
                        print(f"📦 No audio_url in extra_info")
                    print(f"📦 Expected audio size: {result['extra_info'].get('audio_size', 'unknown')} bytes")
                
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                try:
                    if hasattr(e.response, 'text'):
                        error_msg = f"{e.response.status_code}: {e.response.text}"
                except:
                    pass
                return {
                    'success': False,
                    'error': f'Speech generation failed: {error_msg}'
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Speech generation failed: {str(e)}'
                }
            
            # MiniMax T2A returns audio data in various formats
            # Priority: audio_url > base64 audio
            audio_data = None

            # Format 1: Audio URL in data (PREFERRED - always works)
            if 'data' in result and 'audio_url' in result['data']:
                print("📦 Using audio_url from data")
                audio_url = result['data']['audio_url']
                audio_response = requests.get(audio_url, timeout=30)
                audio_response.raise_for_status()
                audio_data = audio_response.content
                print(f"✅ Downloaded {len(audio_data)} bytes from URL")
            # Format 2: Audio URL in extra_info
            elif 'extra_info' in result and 'audio_url' in result['extra_info']:
                print("📦 Using audio_url from extra_info")
                audio_url = result['extra_info']['audio_url']
                audio_response = requests.get(audio_url, timeout=30)
                audio_response.raise_for_status()
                audio_data = audio_response.content
                print(f"✅ Downloaded {len(audio_data)} bytes from URL")
            # Format 3: Base64 audio in data.audio
            elif 'data' in result and 'audio' in result['data']:
                print("📦 Using base64 audio from data.audio")
                try:
                    audio_b64 = result['data']['audio']
                    # Add padding if needed
                    missing_padding = len(audio_b64) % 4
                    if missing_padding:
                        audio_b64 += '=' * (4 - missing_padding)
                    audio_data = base64.b64decode(audio_b64)
                    print(f"✅ Decoded {len(audio_data)} bytes from base64")
                except Exception as e:
                    print(f"❌ Base64 decode failed: {e}")
                    return {
                        'success': False,
                        'error': f'Failed to decode audio: {str(e)}'
                    }
            # Format 4: Direct base64 audio
            elif 'audio' in result:
                print("📦 Using direct base64 audio")
                try:
                    audio_b64 = result['audio']
                    missing_padding = len(audio_b64) % 4
                    if missing_padding:
                        audio_b64 += '=' * (4 - missing_padding)
                    audio_data = base64.b64decode(audio_b64)
                    print(f"✅ Decoded {len(audio_data)} bytes from base64")
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Failed to decode audio: {str(e)}'
                    }
            # Format 5: Base64 string directly in data
            elif 'data' in result and isinstance(result['data'], str):
                print("📦 Using base64 string from data")
                try:
                    audio_b64 = result['data']
                    missing_padding = len(audio_b64) % 4
                    if missing_padding:
                        audio_b64 += '=' * (4 - missing_padding)
                    audio_data = base64.b64decode(audio_b64)
                    print(f"✅ Decoded {len(audio_data)} bytes from base64")
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Failed to decode audio: {str(e)}'
                    }
            else:
                return {
                    'success': False,
                    'error': f'No audio found in response. Keys: {list(result.keys())}'
                }
            
            # Verify we have audio data
            if not audio_data or len(audio_data) < 100:
                return {
                    'success': False,
                    'error': f'Audio data too short or empty: {len(audio_data) if audio_data else 0} bytes'
                }
            
            # Write audio to file
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            
            # Fix duplicated audio by cutting in half
            fixed_path = self.fix_duplicated_audio(output_path)
            
            return {
                'success': True,
                'audio_path': fixed_path
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            try:
                if hasattr(e.response, 'text'):
                    error_msg = f"{e.response.status_code}: {e.response.text}"
            except:
                pass
            return {
                'success': False,
                'error': f'Speech generation failed: {error_msg}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Speech generation failed: {str(e)}'
            }
    
    def get_cloned_voices(self):
        """
        Get list of all cloned voices from MiniMax
        
        Returns:
            dict: Result with list of voices
        """
        try:
            api_key = current_app.config.get('MINIMAX_API_KEY')
            group_id = current_app.config.get('MINIMAX_GROUP_ID', '')
            
            if not api_key:
                return {
                    'success': False,
                    'error': 'MiniMax API key not configured'
                }
            
            # MiniMax voices list endpoint
            url = f"{self.base_url}/voices"
            params = {'group_id': group_id} if group_id else {}
            
            response = requests.get(url, headers=self.get_headers(), params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract voices from response
            voices_data = result.get('voices', []) or result.get('data', {}).get('voices', [])
            
            cloned_voices = []
            for voice in voices_data:
                cloned_voices.append({
                    'voice_id': voice.get('voice_id', ''),
                    'name': voice.get('name', ''),
                    'description': voice.get('description', ''),
                    'preview_url': voice.get('preview_url')
                })
            
            return {
                'success': True,
                'voices': cloned_voices
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get voices: {str(e)}'
            }
    
    def delete_cloned_voice(self, voice_id):
        """
        Delete a cloned voice (session-based, MiniMax may not support API delete)
        
        Args:
            voice_id: ID of the voice to delete
        
        Returns:
            dict: Result with success status
        """
        try:
            # MiniMax may not support voice deletion via API
            # We'll just return success and handle deletion in session
            # The voice will be removed from session in the route handler
            
            print(f"🗑️ Deleting voice from session: {voice_id}")
            
            # Note: If MiniMax adds a delete endpoint later, it would be:
            # DELETE /v1/voice_clone/{voice_id} or similar
            # For now, we only delete from session
            
            return {
                'success': True,
                'message': 'Voice removed from session (MiniMax voices persist on server)'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to delete voice: {str(e)}'
            }

# Global service instance
voice_clone_service = VoiceCloneService()


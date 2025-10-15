"""
Video Dubbing Service
Handles video dubbing by extracting audio, transcribing, translating, 
generating new speech and merging with video
"""
import os
import subprocess
import imageio_ffmpeg
from flask import current_app
from app.services.whisper_service import whisper_service
from app.services.voice_clone_service import voice_clone_service
from app.services.tts_service import tts_service
import logging


class DubbingService:
    """Service for video dubbing operations"""
    
    def __init__(self):
        pass
    
    def extract_audio_from_video(self, video_path):
        """
        Extract audio from video file using FFmpeg
        
        Args:
            video_path: Path to video file
            
        Returns:
            str: Path to extracted audio file, or None if failed
        """
        try:
            logging.info(f"🎬 Extracting audio from: {os.path.basename(video_path)}")
            
            # Create output path for audio
            video_dir = os.path.dirname(video_path)
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            audio_path = os.path.join(video_dir, f"{video_name}_audio.mp3")
            
            # Get FFmpeg executable
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            # Extract audio
            cmd = [
                ffmpeg_exe,
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'libmp3lame',
                '-b:a', '192k',
                '-ar', '44100',
                '-y',  # Overwrite output
                audio_path
            ]
            
            logging.info(f"🏃 Running: {' '.join(cmd[:3])} ... {os.path.basename(audio_path)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logging.error(f"❌ FFmpeg audio extraction failed: {result.stderr}")
                return None
            
            # Check if audio file was created
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                logging.info(f"✅ Audio extracted: {os.path.getsize(audio_path)} bytes")
                return audio_path
            else:
                logging.error("❌ Audio file was not created or is empty")
                return None
                
        except Exception as e:
            logging.error(f"❌ Audio extraction error: {str(e)}")
            return None
    
    def get_media_duration(self, file_path):
        """
        Get duration of video or audio file using FFmpeg
        
        Args:
            file_path: Path to media file
            
        Returns:
            float: Duration in seconds, or None if failed
        """
        try:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            # Try FFprobe first
            ffprobe_exe = ffmpeg_exe.replace('ffmpeg', 'ffprobe')
            if os.path.exists(ffprobe_exe):
                cmd = [
                    ffprobe_exe,
                    '-v', 'quiet',
                    '-show_entries', 'format=duration',
                    '-of', 'csv=p=0',
                    file_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    duration = float(result.stdout.strip())
                    logging.info(f"📏 Duration (FFprobe): {duration:.2f}s")
                    return duration
            
            # Fallback: Use FFmpeg with null output to get duration
            logging.info("⚠️ FFprobe not found, using FFmpeg fallback...")
            
            cmd = [
                ffmpeg_exe,
                '-i', file_path,
                '-f', 'null',
                '-'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Parse duration from FFmpeg output
            if result.stderr:
                # Look for "Duration: HH:MM:SS.ms" in stderr
                import re
                duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', result.stderr)
                if duration_match:
                    hours = int(duration_match.group(1))
                    minutes = int(duration_match.group(2))
                    seconds = int(duration_match.group(3))
                    centiseconds = int(duration_match.group(4))
                    
                    total_seconds = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
                    logging.info(f"📏 Duration (FFmpeg): {total_seconds:.2f}s")
                    return total_seconds
            
            logging.error(f"❌ Could not parse duration from FFmpeg output")
            return None
                
        except Exception as e:
            logging.error(f"❌ Duration detection error: {str(e)}")
            return None
    
    def adjust_audio_speed(self, audio_path, speed_factor):
        """
        Adjust audio speed using FFmpeg
        
        Args:
            audio_path: Path to audio file
            speed_factor: Speed factor (1.0 = normal, 1.5 = 50% faster, 0.8 = 20% slower)
            
        Returns:
            str: Path to adjusted audio file
        """
        try:
            if speed_factor == 1.0:
                return audio_path  # No adjustment needed
            
            logging.info(f"⚡ Adjusting audio speed by {speed_factor:.2f}x")
            
            # Create output path
            temp_folder = current_app.config['TEMP_FOLDER']
            output_path = os.path.join(temp_folder, f"speed_adjusted_{os.urandom(8).hex()}.mp3")
            
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            # Use atempo filter (range: 0.5 to 2.0)
            if speed_factor > 2.0:
                # For speeds > 2.0, chain multiple atempo filters
                atempo_chain = []
                remaining_speed = speed_factor
                while remaining_speed > 2.0:
                    atempo_chain.append("atempo=2.0")
                    remaining_speed /= 2.0
                if remaining_speed > 1.0:
                    atempo_chain.append(f"atempo={remaining_speed:.2f}")
                atempo_filter = ",".join(atempo_chain)
            elif speed_factor < 0.5:
                # For speeds < 0.5, chain multiple atempo filters
                atempo_chain = []
                remaining_speed = speed_factor
                while remaining_speed < 0.5:
                    atempo_chain.append("atempo=0.5")
                    remaining_speed /= 0.5
                if remaining_speed < 1.0:
                    atempo_chain.append(f"atempo={remaining_speed:.2f}")
                atempo_filter = ",".join(atempo_chain)
            else:
                atempo_filter = f"atempo={speed_factor:.2f}"
            
            cmd = [
                ffmpeg_exe,
                '-i', audio_path,
                '-filter:a', atempo_filter,
                '-c:a', 'libmp3lame',
                '-b:a', '192k',
                '-y',
                output_path
            ]
            
            logging.info(f"🏃 Running: ffmpeg with speed adjustment...")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                final_duration = self.get_media_duration(output_path)
                logging.info(f"✅ Audio speed adjusted: {final_duration:.2f}s")
                return output_path
            else:
                logging.error(f"❌ Speed adjustment failed: {result.stderr}")
                return audio_path
                
        except Exception as e:
            logging.error(f"❌ Speed adjustment error: {str(e)}")
            return audio_path
    
    def add_silence_to_audio(self, audio_path, silence_duration):
        """
        Add silence to the end of audio file
        
        Args:
            audio_path: Path to audio file
            silence_duration: Duration of silence to add in seconds
            
        Returns:
            str: Path to extended audio file
        """
        try:
            if silence_duration <= 0:
                return audio_path  # No silence needed
            
            logging.info(f"🔇 Adding {silence_duration:.1f}s of silence to audio...")
            
            temp_folder = current_app.config['TEMP_FOLDER']
            output_path = os.path.join(temp_folder, f"extended_{os.urandom(8).hex()}.mp3")
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            cmd = [
                ffmpeg_exe,
                '-i', audio_path,
                '-af', f'apad=pad_dur={silence_duration}',
                '-c:a', 'libmp3lame',
                '-b:a', '192k',
                '-y',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                final_duration = self.get_media_duration(output_path)
                logging.info(f"✅ Silence added successfully: {final_duration:.2f}s total")
                return output_path
            else:
                logging.error(f"❌ Failed to add silence: {result.stderr}")
                return audio_path
                
        except Exception as e:
            logging.error(f"❌ Silence addition error: {str(e)}")
            return audio_path
    
    def merge_audio_with_video(self, video_path, audio_path, output_path=None, match_audio_duration=True):
        """
        Merge new audio with video using FFmpeg
        
        Args:
            video_path: Path to original video
            audio_path: Path to new audio file
            output_path: Optional output path
            match_audio_duration: If True, extend video to match audio duration
            
        Returns:
            str: Path to output video, or None if failed
        """
        try:
            logging.info(f"🎬 Merging audio with video...")
            logging.info(f"  📹 Video: {os.path.basename(video_path)}")
            logging.info(f"  🔊 Audio: {os.path.basename(audio_path)}")
            
            # Get durations
            video_duration = self.get_media_duration(video_path)
            audio_duration = self.get_media_duration(audio_path)
            
            if video_duration and audio_duration:
                logging.info(f"📏 Duration analysis:")
                logging.info(f"  📹 Video: {video_duration:.2f}s")
                logging.info(f"  🔊 Audio: {audio_duration:.2f}s")
                logging.info(f"  ⚖️ Difference: {abs(audio_duration - video_duration):.2f}s")
            
            # Create output path if not provided
            if not output_path:
                video_dir = os.path.dirname(video_path)
                video_name = os.path.splitext(os.path.basename(video_path))[0]
                output_path = os.path.join(video_dir, f"{video_name}_dubbed.mp4")
            
            # Get FFmpeg executable
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            
            if match_audio_duration and audio_duration and video_duration:
                if audio_duration > video_duration:
                    # Audio is longer than video - extend video to match audio
                    logging.info(f"⏰ Extending video to match audio duration ({audio_duration:.2f}s)")
                    
                    cmd = [
                        ffmpeg_exe,
                        '-i', video_path,      # Input video
                        '-i', audio_path,      # Input audio
                        '-c:v', 'libx264',     # Re-encode video to extend
                        '-c:a', 'aac',         # AAC audio codec
                        '-b:a', '192k',        # Audio bitrate
                        '-map', '0:v:0',       # Map video from first input
                        '-map', '1:a:0',       # Map audio from second input
                        '-t', str(audio_duration),  # Set duration to audio length
                        '-y',                  # Overwrite output
                        output_path
                    ]
                else:
                    # Audio is shorter than video - extend audio with silence to match video
                    logging.info(f"🔇 Extending audio to match video duration ({video_duration:.2f}s)")
                    
                    # First extend audio with silence
                    extended_audio_path = self.add_silence_to_audio(audio_path, video_duration - audio_duration)
                    if extended_audio_path != audio_path:
                        temp_files.append(extended_audio_path)
                        audio_path = extended_audio_path
                    
                    cmd = [
                        ffmpeg_exe,
                        '-i', video_path,      # Input video
                        '-i', audio_path,      # Input audio (now extended)
                        '-c:v', 'copy',        # Copy video codec (faster)
                        '-c:a', 'aac',         # AAC audio codec
                        '-b:a', '192k',        # Audio bitrate
                        '-map', '0:v:0',       # Map video from first input
                        '-map', '1:a:0',       # Map audio from second input
                        '-shortest',           # Finish encoding when shortest input ends
                        '-y',                  # Overwrite output
                        output_path
                    ]
            else:
                # Fallback: Standard merge - use shortest duration
                logging.info(f"⚠️ Using standard merge (shortest duration)")
                cmd = [
                    ffmpeg_exe,
                    '-i', video_path,      # Input video
                    '-i', audio_path,      # Input audio
                    '-c:v', 'copy',        # Copy video codec (faster)
                    '-c:a', 'aac',         # AAC audio codec
                    '-b:a', '192k',        # Audio bitrate
                    '-map', '0:v:0',       # Map video from first input
                    '-map', '1:a:0',       # Map audio from second input
                    '-shortest',           # Finish encoding when shortest input ends
                    '-y',                  # Overwrite output
                    output_path
                ]
            
            logging.info(f"🏃 Running: {' '.join(cmd[:5])} ... {os.path.basename(output_path)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logging.error(f"❌ FFmpeg merge failed: {result.stderr}")
                return None
            
            # Check if output file was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                final_duration = self.get_media_duration(output_path)
                logging.info(f"✅ Video merged: {os.path.getsize(output_path)} bytes, duration: {final_duration:.2f}s")
                return output_path
            else:
                logging.error("❌ Output video was not created or is empty")
                return None
                
        except Exception as e:
            logging.error(f"❌ Video merge error: {str(e)}")
            return None
    
    def dub_video(self, video_path, target_language='en', voice='alloy', voice_type='standard', source_language=None, speed_factor=1.0):
        """
        Complete video dubbing workflow with intelligent duration matching
        
        Args:
            video_path: Path to input video file
            target_language: Target language code (e.g., 'en', 'tr', 'es')
            voice: Voice to use (standard voice name or cloned voice_id)
            voice_type: 'standard' for OpenAI voices, 'cloned' for MiniMax cloned voices
            source_language: Optional source language hint
            speed_factor: Audio speed adjustment (1.0 = normal, 1.5 = 50% faster, 0.8 = 20% slower)
            
        Returns:
            dict: Result with output video path and info
        """
        temp_files = []  # Track temporary files for cleanup
        
        try:
            logging.info(f"🎬 Starting video dubbing workflow...")
            logging.info(f"  📹 Video: {os.path.basename(video_path)}")
            logging.info(f"  🌐 Target Language: {target_language}")
            logging.info(f"  🗣️ Voice: {voice} ({voice_type})")
            logging.info(f"  ⚡ Speed Factor: {speed_factor:.2f}x")
            
            # Get original video duration
            original_video_duration = self.get_media_duration(video_path)
            if original_video_duration:
                logging.info(f"📏 Original video duration: {original_video_duration:.2f}s")
            
            # Step 1: Extract audio from video
            logging.info("📝 Step 1/6: Extracting audio from video...")
            audio_path = self.extract_audio_from_video(video_path)
            if not audio_path:
                return {
                    'success': False,
                    'error': 'Failed to extract audio from video'
                }
            temp_files.append(audio_path)
            
            # Step 2: Transcribe audio
            logging.info("📝 Step 2/6: Transcribing audio...")
            transcription_result = whisper_service.transcribe_audio(
                audio_path, 
                language=source_language
            )
            
            if not transcription_result['success']:
                return {
                    'success': False,
                    'error': f"Transcription failed: {transcription_result['error']}"
                }
            
            original_text = transcription_result['text']
            detected_language = source_language or 'auto'
            
            logging.info(f"✅ Transcribed: {len(original_text)} characters")
            logging.info(f"  📄 Text preview: {original_text[:100]}...")
            
            # Step 3: Translate text to target language (if needed)
            translated_text = original_text
            if target_language and target_language != source_language:
                logging.info(f"📝 Step 3/6: Translating to {target_language}...")
                translation_result = tts_service.translate_text(original_text, target_language)
                
                if translation_result['success']:
                    translated_text = translation_result['translated_text']
                    logging.info(f"✅ Translated: {len(translated_text)} characters")
                    logging.info(f"  📄 Translation preview: {translated_text[:100]}...")
                else:
                    logging.warning(f"⚠️ Translation failed, using original text: {translation_result['error']}")
            else:
                logging.info(f"📝 Step 3/6: Skipping translation (same language)")
            
            # Step 4: Generate new speech
            logging.info(f"📝 Step 4/6: Generating speech with {voice_type} voice...")
            
            if voice_type == 'cloned':
                # Use MiniMax cloned voice
                speech_result = voice_clone_service.generate_speech_with_cloned_voice(
                    translated_text,
                    voice
                )
            else:
                # Use OpenAI standard voice
                speech_result = tts_service.generate_speech(
                    translated_text,
                    voice=voice
                )
            
            if not speech_result['success']:
                return {
                    'success': False,
                    'error': f"Speech generation failed: {speech_result['error']}"
                }
            
            new_audio_path = speech_result['audio_path']
            temp_files.append(new_audio_path)
            
            logging.info(f"✅ Speech generated: {os.path.getsize(new_audio_path)} bytes")
            
            # Step 5: Apply manual speed adjustment only (if user specified)
            logging.info(f"📝 Step 5/6: Applying speed adjustment...")
            
            # Get generated audio duration
            generated_audio_duration = self.get_media_duration(new_audio_path)
            if generated_audio_duration:
                logging.info(f"🔊 Generated audio duration: {generated_audio_duration:.2f}s")
            
            # Only apply speed adjustment if user manually changed it from default (1.0)
            if speed_factor != 1.0:
                logging.info(f"🎯 User specified speed factor: {speed_factor:.2f}x")
                adjusted_audio_path = self.adjust_audio_speed(new_audio_path, speed_factor)
                if adjusted_audio_path != new_audio_path:
                    temp_files.append(adjusted_audio_path)
                    new_audio_path = adjusted_audio_path
                    logging.info(f"✅ Audio speed adjusted to {speed_factor:.2f}x")
            else:
                logging.info(f"✅ Using normal speech speed (1.0x) - no speed adjustment")
            
            # Step 6: Merge new audio with video (extend video if needed)
            logging.info(f"📝 Step 6/6: Merging new audio with video...")
            
            # Create output path in temp folder
            temp_folder = current_app.config['TEMP_FOLDER']
            output_filename = f"dubbed_{os.urandom(8).hex()}.mp4"
            output_path = os.path.join(temp_folder, output_filename)
            
            merged_video_path = self.merge_audio_with_video(
                video_path,
                new_audio_path,
                output_path,
                match_audio_duration=True  # Extend video to match audio
            )
            
            if not merged_video_path:
                return {
                    'success': False,
                    'error': 'Failed to merge audio with video'
                }
            
            # Get final video duration
            final_duration = self.get_media_duration(merged_video_path)
            
            logging.info(f"✅ Video dubbing completed!")
            logging.info(f"  📹 Output: {os.path.basename(merged_video_path)}")
            logging.info(f"  📏 Size: {os.path.getsize(merged_video_path)} bytes")
            logging.info(f"  ⏱️ Final duration: {final_duration:.2f}s")
            logging.info(f"  ⚡ Speed factor used: {speed_factor:.2f}x")
            
            # Cleanup temporary files (but keep the final output)
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        logging.info(f"🧹 Cleaned up: {os.path.basename(temp_file)}")
                except:
                    pass
            
            return {
                'success': True,
                'output_path': merged_video_path,
                'original_text': original_text,
                'translated_text': translated_text,
                'detected_language': detected_language,
                'target_language': target_language,
                'voice': voice,
                'voice_type': voice_type,
                'speed_factor': speed_factor,
                'original_duration': original_video_duration,
                'final_duration': final_duration
            }
            
        except Exception as e:
            logging.error(f"❌ Dubbing error: {str(e)}")
            
            # Cleanup on error
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass
            
            return {
                'success': False,
                'error': f'Dubbing failed: {str(e)}'
            }


# Global service instance
dubbing_service = DubbingService()


#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "elevenlabs",
#     "python-dotenv",
# ]
# ///

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Import config and text utilities
sys.path.append(str(Path(__file__).parent.parent))

# Constants for fallback values
DEFAULT_VOICE_ID = "FNMROvc7ZdHldafWFMqC"
DEFAULT_MODEL_ID = "eleven_turbo_v2_5"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"

try:
    from config import get_active_tts_provider, get_elevenlabs_config, get_macos_config, get_tts_timeout
    from text_utils import clean_text_for_speech
except ImportError as e:
    if "config" in str(e):
        print(f"❌ Config module import error: {e}", file=sys.stderr)
        print("Using fallback configuration", file=sys.stderr)
        # Define fallback functions
        def get_active_tts_provider():
            return 'macos'
        def get_elevenlabs_config():
            return {
                'voice_id': DEFAULT_VOICE_ID,
                'model': DEFAULT_MODEL_ID,
                'output_format': DEFAULT_OUTPUT_FORMAT
            }
        def get_macos_config():
            try:
                import json
                from pathlib import Path
                config_path = Path.cwd() / ".claude" / "config.json"
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        macos_config = config.get('tts', {}).get('voices', {}).get('macos', {})
                        return {
                            'voice': macos_config.get('voice', 'Alex'),
                            'rate': macos_config.get('rate', 190),
                            'quality': macos_config.get('quality', 127)
                        }
            except Exception:
                pass
            return {'voice': 'Alex', 'rate': 190, 'quality': 127}
        def get_tts_timeout():
            try:
                import json
                from pathlib import Path
                config_path = Path.cwd() / ".claude" / "config.json"
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        return config.get('tts', {}).get('timeout', 120)
            except Exception:
                pass
            return 120
        def clean_text_for_speech(text):
            # Try to get limit from a basic config system fallback
            try:
                import json
                from pathlib import Path
                config_path = Path.cwd() / ".claude" / "config.json"
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        limit = config.get('tts', {}).get('text_length_limit', 2000)
                else:
                    limit = 2000  # Default if no config file
            except Exception:
                limit = 2000  # Default if any error
            return text[:limit] if len(text) > limit else text
    else:
        raise

def speak_with_native_macos(text):
    """Speak text using native macOS TTS with enhanced quality settings."""
    try:
        # Get macOS config with quality settings
        macos_config = get_macos_config()
        voice = macos_config['voice']
        rate = macos_config['rate']
        quality = macos_config['quality']
        timeout = get_tts_timeout()
        
        # Clean text for speech
        clean_text = clean_text_for_speech(text)
        
        if not clean_text:
            return False
        
        print(f"🎙️  {voice} speaking (rate:{rate}, quality:{quality}): {clean_text[:100]}...")
        
        # Use macOS say command with quality settings
        result = subprocess.run([
            "say", 
            "-v", voice,
            "-r", str(rate),
            "--quality", str(quality),
            clean_text
        ], 
        capture_output=True,
        text=True,
        timeout=timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {voice} has spoken!")
            return True
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown subprocess error"
            print(f"❌ macOS TTS subprocess error: {error_msg}", file=sys.stderr)
            return False
        
    except subprocess.TimeoutExpired:
        print(f"❌ macOS TTS timeout after {timeout} seconds", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("❌ macOS 'say' command not found", file=sys.stderr)
        return False
    except OSError as e:
        print(f"❌ macOS TTS OS error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Unexpected macOS TTS error: {e}", file=sys.stderr)
        return False

def speak_response(text):
    """Speak text using configured TTS provider with consolidated logic."""
    load_dotenv()
    
    # Determine active TTS provider based on configuration and environment
    provider = get_active_tts_provider()
    
    if provider == 'macos':
        return speak_with_native_macos(text)
    
    # Handle ElevenLabs provider (get_active_tts_provider already checked API key availability)
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import play
        
        # Initialize client
        api_key = os.getenv('ELEVENLABS_API_KEY')
        elevenlabs = ElevenLabs(api_key=api_key)
        
        # Clean text for speech
        clean_text = clean_text_for_speech(text)
        
        if not clean_text:
            print("❌ No speakable content found", file=sys.stderr)
            return False
        
        # Get ElevenLabs settings from config
        elevenlabs_config = get_elevenlabs_config()
        
        print(f"🎙️  ElevenLabs speaking: {clean_text[:100]}...")
        
        # Generate and play audio using config settings
        audio = elevenlabs.text_to_speech.convert(
            text=clean_text,
            voice_id=elevenlabs_config['voice_id'],
            model_id=elevenlabs_config['model'],
            output_format=elevenlabs_config['output_format'],
        )
        
        play(audio)
        print("✅ ElevenLabs TTS completed!")
        return True
        
    except ImportError as e:
        if "elevenlabs" in str(e):
            print(f"❌ ElevenLabs package not available: {e}", file=sys.stderr)
            print("🔄 Falling back to macOS TTS", file=sys.stderr)
            return speak_with_native_macos(text)
        else:
            # Re-raise if it's not an ElevenLabs import issue
            raise
    except Exception as e:
        print(f"❌ ElevenLabs TTS error: {e}", file=sys.stderr)
        print("🔄 Falling back to macOS TTS", file=sys.stderr)
        return speak_with_native_macos(text)

def main():
    """Command line interface for response TTS."""
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        success = speak_response(text)
        sys.exit(0 if success else 1)
    else:
        print("Usage: ./response_tts.py 'text to speak'")
        sys.exit(1)

if __name__ == "__main__":
    main()
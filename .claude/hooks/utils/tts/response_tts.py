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
import re
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Import config utility
sys.path.append(str(Path(__file__).parent.parent))
from config import get_tts_config, get_voice_for_provider, is_tts_enabled, get_elevenlabs_config, get_macos_config

def clean_text_for_speech(text):
    """
    Clean text to make it suitable for TTS.
    Remove code blocks, excessive formatting, and keep conversational parts.
    """
    # Remove code blocks (```...```)
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Remove inline code (`...`)
    text = re.sub(r'`[^`]+`', '', text)
    
    # Remove markdown links [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove markdown headers (#, ##, ###)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove bullet points and list markers
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Remove tool call indicators and XML-like tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove all emojis for better speech
    # This regex matches most Unicode emoji ranges
    text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)  # emoticons
    text = re.sub(r'[\U0001F300-\U0001F5FF]', '', text)  # symbols & pictographs
    text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)  # transport & map
    text = re.sub(r'[\U0001F1E0-\U0001F1FF]', '', text)  # flags
    text = re.sub(r'[\U00002600-\U000027BF]', '', text)  # misc symbols
    text = re.sub(r'[\U0001F900-\U0001F9FF]', '', text)  # supplemental symbols
    
    # Clean up and limit length
    text = text.strip()
    
    # Limit to reasonable TTS length (about 2 minutes of speech)
    if len(text) > 2000:
        text = text[:2000] + "..."
    
    return text

def speak_with_native_macos(text):
    """Speak text using native macOS TTS with enhanced quality settings."""
    try:
        # Get macOS config with quality settings
        macos_config = get_macos_config()
        voice = macos_config['voice']
        rate = macos_config['rate']
        quality = macos_config['quality']
        
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
        text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {voice} has spoken!")
            return True
        else:
            print(f"❌ Error: {result.stderr}", file=sys.stderr)
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False

def speak_with_marvin(text):
    """Speak text using Marvin's voice via ElevenLabs."""
    load_dotenv()
    
    # Check config for TTS provider preference
    tts_config = get_tts_config()
    provider = tts_config.get('provider', 'macos')
    
    # If config says use macOS, skip ElevenLabs entirely
    if provider == 'macos':
        return speak_with_native_macos(text)
    
    # Only use ElevenLabs if explicitly configured AND API key available
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("🔄 No ElevenLabs API key, using native macOS TTS", file=sys.stderr)
        return speak_with_native_macos(text)
    
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import play
        
        # Initialize client
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
        print("✅ Marvin has spoken!")
        return True
        
    except ImportError:
        print("❌ Error: elevenlabs package not available", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False

def main():
    """Command line interface for response TTS."""
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        success = speak_with_marvin(text)
        sys.exit(0 if success else 1)
    else:
        print("Usage: ./response_tts.py 'text to speak'")
        sys.exit(1)

if __name__ == "__main__":
    main()
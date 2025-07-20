#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import os
import sys
import re
import subprocess
from pathlib import Path

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

def speak_with_macos(text, voice="Lee (Premium)"):
    """Speak text using native macOS TTS with specified voice."""
    
    try:
        # Clean text for speech
        clean_text = clean_text_for_speech(text)
        
        if not clean_text:
            print("❌ No speakable content found", file=sys.stderr)
            return False
        
        print(f"🎙️  {voice} speaking: {clean_text[:100]}...")
        
        # Use macOS say command
        result = subprocess.run([
            "say", "-v", voice, clean_text
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

def get_available_voices():
    """Get list of available macOS voices."""
    try:
        result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
        if result.returncode == 0:
            voices = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    # Extract voice name (first part before spaces)
                    voice_name = line.split()[0]
                    voices.append(voice_name)
            return voices
        return []
    except Exception:
        return []

def main():
    """Command line interface for macOS TTS."""
    if len(sys.argv) > 1:
        # Check if first arg is a voice name
        available_voices = get_available_voices()
        
        if sys.argv[1] in available_voices and len(sys.argv) > 2:
            # First arg is voice, rest is text
            voice = sys.argv[1]
            text = " ".join(sys.argv[2:])
        else:
            # All args are text, use default voice
            voice = "Lee (Premium)"
            text = " ".join(sys.argv[1:])
        
        success = speak_with_macos(text, voice)
        sys.exit(0 if success else 1)
    else:
        print("Usage: ./macos_tts.py 'text to speak'")
        print("   or: ./macos_tts.py 'VoiceName' 'text to speak'")
        print(f"Available voices: {', '.join(get_available_voices()[:5])}...")
        sys.exit(1)

if __name__ == "__main__":
    main()
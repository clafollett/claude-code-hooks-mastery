#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import re
import sys
from pathlib import Path

# Import config for text length limit
sys.path.append(str(Path(__file__).parent))
from config import get_text_length_limit

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
    text = remove_emojis(text)
    
    # Clean up and limit length
    text = text.strip()
    
    # Limit to configured TTS length with fallback
    try:
        text_limit = get_text_length_limit()
    except Exception:
        text_limit = 2000  # Fallback if config unavailable
        
    if len(text) > text_limit:
        text = text[:text_limit] + "..."
    
    return text

def remove_emojis(text):
    """
    Remove all Unicode emoji ranges from text for clean TTS speech.
    This regex matches most Unicode emoji ranges.
    """
    # Remove various Unicode emoji ranges
    text = re.sub(r'[\U0001F600-\U0001F64F]', '', text)  # emoticons
    text = re.sub(r'[\U0001F300-\U0001F5FF]', '', text)  # symbols & pictographs
    text = re.sub(r'[\U0001F680-\U0001F6FF]', '', text)  # transport & map
    text = re.sub(r'[\U0001F1E0-\U0001F1FF]', '', text)  # flags
    text = re.sub(r'[\U00002600-\U000027BF]', '', text)  # misc symbols
    text = re.sub(r'[\U0001F900-\U0001F9FF]', '', text)  # supplemental symbols
    
    return text
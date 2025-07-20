#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import os
import sys
import subprocess
from pathlib import Path

def trigger_response_tts(input_data):
    """
    Trigger TTS for assistant responses if enabled.
    Only speaks if CLAUDE_RESPONSE_TTS=true environment variable is set.
    """
    # Check if response TTS is enabled
    if not os.getenv('CLAUDE_RESPONSE_TTS', '').lower() == 'true':
        return
    
    # Extract tool response if available
    tool_response = input_data.get('tool_response', {})
    
    # Look for text content that might be assistant responses
    response_text = None
    
    # Check various fields where responses might be
    if isinstance(tool_response, dict):
        if 'content' in tool_response:
            response_text = tool_response['content']
        elif 'output' in tool_response:
            response_text = tool_response['output']
        elif 'result' in tool_response:
            response_text = tool_response['result']
    elif isinstance(tool_response, str):
        response_text = tool_response
    
    # Only proceed if we have meaningful text
    if not response_text or len(response_text.strip()) < 20:
        return
    
    # Skip if it looks like code output or tool output
    if any(indicator in response_text.lower() for indicator in [
        'error:', '404', '500', 'traceback', 'exception',
        'usage:', 'command not found', 'permission denied'
    ]):
        return
    
    try:
        # Get script directory and construct path to response TTS
        script_dir = Path(__file__).parent
        tts_script = script_dir / "utils" / "tts" / "response_tts.py"
        
        if not tts_script.exists():
            return
        
        # Trigger TTS in background (don't wait)
        subprocess.Popen([
            "uv", "run", str(tts_script), response_text
        ], 
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
        )
        
    except Exception:
        # Fail silently
        pass

def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        
        # Ensure log directory exists
        log_dir = Path.cwd() / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / 'post_tool_use.json'
        
        # Read existing log data or initialize empty list
        if log_path.exists():
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []
        
        # Append new data
        log_data.append(input_data)
        
        # Write back to file with formatting
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        # Check if we should trigger response TTS
        trigger_response_tts(input_data)
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Exit cleanly on any other error
        sys.exit(0)

if __name__ == '__main__':
    main()
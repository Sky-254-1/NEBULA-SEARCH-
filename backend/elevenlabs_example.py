"""
ElevenLabs Text-to-Speech Example
This demonstrates basic text-to-speech functionality with ElevenLabs.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Load environment variables
load_dotenv()

def text_to_speech_example():
    """
    Simple example: Convert text to speech and save as an audio file.
    """
    # Initialize the ElevenLabs client
    # The API key is automatically loaded from ELEVENLABS_API_KEY env variable
    client = ElevenLabs()
    
    # Text to convert to speech
    text = "Hello! Welcome to Nebula Search Engine. This is a demonstration of ElevenLabs text-to-speech capabilities."
    
    # Generate speech
    print("Generating speech...")
    audio = client.generate(
        text=text,
        voice="Rachel",  # You can also use "Adam", "Domi", "Bella", etc.
        model="eleven_monolingual_v1"
    )
    
    # Save the audio to a file
    output_path = Path("output_speech.mp3")
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    
    print(f"✓ Speech generated successfully and saved to: {output_path}")
    return output_path


def list_available_voices():
    """
    List all available voices from your ElevenLabs account.
    """
    client = ElevenLabs()
    
    print("\nAvailable voices:")
    voices = client.voices.get_all()
    
    for voice in voices.voices:
        print(f"  - {voice.name} (ID: {voice.voice_id})")


def text_to_speech_with_settings():
    """
    Advanced example: Generate speech with custom voice settings.
    """
    client = ElevenLabs()
    
    text = "This is an advanced example with customized voice settings for more expressive speech."
    
    # Generate with custom settings
    audio = client.generate(
        text=text,
        voice="Rachel",
        model="eleven_monolingual_v1",
        voice_settings={
            "stability": 0.5,        # 0-1: Lower = more variable, Higher = more stable
            "similarity_boost": 0.75, # 0-1: How closely to match the original voice
            "style": 0.0,             # 0-1: Exaggeration of speaking style
            "use_speaker_boost": True # Enhance clarity
        }
    )
    
    output_path = Path("output_speech_custom.mp3")
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    
    print(f"✓ Custom speech generated and saved to: {output_path}")


if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("❌ Error: ELEVENLABS_API_KEY not found in environment variables.")
        print("Please add your API key to the .env file.")
        exit(1)
    
    print("ElevenLabs Text-to-Speech Demo\n" + "="*40)
    
    try:
        # Run the basic example
        text_to_speech_example()
        
        # List available voices
        list_available_voices()
        
        # Run advanced example with custom settings
        print("\nGenerating speech with custom settings...")
        text_to_speech_with_settings()
        
        print("\n✨ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Added your ELEVENLABS_API_KEY to the .env file")
        print("2. Installed the elevenlabs package: pip install elevenlabs")

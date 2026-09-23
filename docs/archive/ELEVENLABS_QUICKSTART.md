# ElevenLabs Quick Start Guide

## What is ElevenLabs?

ElevenLabs provides AI-powered audio capabilities including:
- 🎤 **Text-to-Speech** - Convert text to natural-sounding voices
- 🎧 **Speech-to-Text** - Transcribe audio files or real-time streams
- 🤖 **AI Agents** - Create voice-enabled conversational agents
- 🔊 **Sound Effects** - Generate custom sound effects from descriptions
- 🎵 **Music Generation** - Compose AI music (paid plans only)

## Setup Steps

### 1. Get Your API Key
1. Visit [https://elevenlabs.io](https://elevenlabs.io)
2. Sign up or log in
3. Go to your profile settings
4. Copy your API key

### 2. Add API Key to .env
Open the `.env` file in the root directory and replace `your-api-key-here` with your actual key:

```env
ELEVENLABS_API_KEY=your_actual_api_key_here
```

### 3. Install the Python SDK
```bash
cd backend
pip install elevenlabs
```

## Running the Example

Once you've completed the setup:

```bash
cd backend
python elevenlabs_example.py
```

This will:
- Generate a simple text-to-speech audio file
- List all available voices in your account
- Generate another audio file with custom voice settings
- Save both as `output_speech.mp3` and `output_speech_custom.mp3`

## Basic Usage

### Text-to-Speech (Python)

```python
from elevenlabs.client import ElevenLabs

client = ElevenLabs()  # Uses ELEVENLABS_API_KEY from environment

# Generate speech
audio = client.generate(
    text="Hello, world!",
    voice="Rachel",
    model="eleven_monolingual_v1"
)

# Save to file
with open("output.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)
```

### Available Pre-built Voices
- Rachel (Female, American)
- Adam (Male, American)
- Domi (Female, American)
- Bella (Female, American)
- Antoni (Male, American)
- Elli (Female, American)
- Josh (Male, American)
- Arnold (Male, American)
- Callum (Male, American)
- Charlie (Male, Australian)

You can also clone your own voice or create custom voices!

## Voice Settings Parameters

Fine-tune the output:

```python
audio = client.generate(
    text="Your text here",
    voice="Rachel",
    voice_settings={
        "stability": 0.5,         # 0-1: Lower = more expressive, Higher = more stable
        "similarity_boost": 0.75, # 0-1: How similar to the original voice
        "style": 0.0,             # 0-1: Exaggeration of speaking style
        "use_speaker_boost": True # Enhance clarity
    }
)
```

## Next Steps

### For More Advanced Features:

1. **Streaming TTS** - For low-latency, real-time speech generation
2. **Speech-to-Text** - Transcribe audio files or real-time audio
3. **AI Agents** - Build conversational voice agents
4. **Sound Effects** - Generate custom audio effects
5. **Music Generation** - Compose AI music (requires paid plan)

### Need Help with Specific Features?

Just ask! For example:
- "How do I stream text-to-speech for real-time playback?"
- "Show me how to transcribe an audio file"
- "Help me create a voice agent"
- "How do I generate sound effects?"

## Troubleshooting

### Error: API Key Not Found
Make sure `ELEVENLABS_API_KEY` is in your `.env` file and you've loaded it with `python-dotenv`.

### Error: Module Not Found
Install the SDK: `pip install elevenlabs`

### Audio Quality Issues
Try adjusting voice settings:
- Increase `stability` for more consistent output
- Increase `similarity_boost` for closer voice matching
- Enable `use_speaker_boost` for better clarity

## Resources

- [ElevenLabs Documentation](https://elevenlabs.io/docs)
- [Python SDK Reference](https://github.com/elevenlabs/elevenlabs-python)
- [API Reference](https://elevenlabs.io/docs/api-reference)

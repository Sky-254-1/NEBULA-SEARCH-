# 🔊 Nebula Search - Audio Features

## Overview

Nebula Search now includes comprehensive audio features powered by **ElevenLabs**, making search accessible, hands-free, and more engaging.

---

## ✨ Features

### 1. 🔊 Voice Narration for Search Results
- **Listen to search results** instead of reading them
- Perfect for multitasking or accessibility needs
- Natural-sounding AI voices
- Narrates top results with titles, snippets, and sources

**Use Cases:**
- Hands-free search while driving
- Accessibility for visually impaired users
- Reviewing results while doing other tasks

---

### 2. ♿ Audio Accessibility Features
- **Screen reader alternative** using natural voices
- Individual result narration with one-click playback
- Toggle audio controls on any text content
- Full keyboard navigation support

**Benefits:**
- Better than traditional screen readers for natural speech
- Improves content accessibility
- Reduces eye strain for long reading sessions

---

### 3. 🎤 Voice Search Capabilities
- **Search by speaking** instead of typing
- Fast, accurate speech-to-text transcription
- Supports multiple languages
- Works in real-time

**How It Works:**
1. Click the microphone button
2. Speak your search query
3. Results appear automatically
4. Audio confirmation of your search

---

### 4. 🔔 Audio Notifications & Alerts
- **Spoken notifications** for search events
- Success, error, info, and warning alerts
- Customizable voice and message types
- Can be toggled on/off by user preference

**Examples:**
- "Search completed successfully"
- "Found 10 results for machine learning"
- "No results found for your query"

---

### 5. 🎙️ Podcast/Audio Content Generation
- **Convert articles to podcast episodes**
- Generate downloadable MP3 files
- Add custom intros and outros
- Perfect for consuming content on-the-go

**Features:**
- Automatic intro generation
- Multiple voice options
- Download or stream audio
- Custom title and content formatting

---

## 🚀 Quick Start

### Prerequisites

1. **Get ElevenLabs API Key:**
   - Visit [elevenlabs.io](https://elevenlabs.io)
   - Sign up for free account (10,000 characters/month)
   - Copy your API key from dashboard

2. **Add to Environment:**
   ```bash
   # Add to .env file in project root
   ELEVENLABS_API_KEY=your_api_key_here
   ```

3. **Install Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Start Using

```bash
# Start backend
cd backend
python -m uvicorn app.main:app --reload

# Start frontend (in new terminal)
cd frontend
npm run dev
```

Visit `http://localhost:5173` and try:
- 🎤 Click microphone for voice search
- 🔊 Click speaker icons to hear results
- 🎧 Click "Listen to Results" for full narration

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [ELEVENLABS_QUICKSTART.md](ELEVENLABS_QUICKSTART.md) | Basic ElevenLabs setup and examples |
| [docs/AUDIO_FEATURES.md](docs/AUDIO_FEATURES.md) | Complete API documentation and usage |
| [AUDIO_INTEGRATION_EXAMPLE.md](AUDIO_INTEGRATION_EXAMPLE.md) | Step-by-step integration guide |
| [backend/elevenlabs_example.py](backend/elevenlabs_example.py) | Python code examples |

---

## 🎯 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/audio/health` | GET | Check service availability |
| `/api/v1/audio/voices` | GET | List available voices |
| `/api/v1/audio/tts` | POST | Text-to-speech conversion |
| `/api/v1/audio/stt` | POST | Speech-to-text transcription |
| `/api/v1/audio/narrate/search` | POST | Narrate search results |
| `/api/v1/audio/notification` | POST | Generate audio notification |
| `/api/v1/audio/podcast/generate` | POST | Create podcast from content |

Full API documentation: [docs/AUDIO_FEATURES.md](docs/AUDIO_FEATURES.md)

---

## 🎨 Frontend Components

### AudioControls
Add text-to-speech to any content:

```jsx
import AudioControls from './components/AudioControls';

<AudioControls text="Your content here" voice="Rachel" />
```

### VoiceSearch
Voice-activated search input:

```jsx
import VoiceSearch from './components/VoiceSearch';

<VoiceSearch onTranscript={(text) => performSearch(text)} />
```

### SearchResultsNarrator
Narrate all search results:

```jsx
import SearchResultsNarrator from './components/SearchResultsNarrator';

<SearchResultsNarrator query={query} results={results} />
```

---

## 🎭 Available Voices

| Voice | Gender | Accent | Best For |
|-------|--------|--------|----------|
| Rachel | Female | American | General purpose, clear |
| Adam | Male | American | Professional, authoritative |
| Bella | Female | American | Warm, friendly |
| Antoni | Male | American | Clear, conversational |
| Domi | Female | American | Energetic, youthful |

*More voices available - see `/api/v1/audio/voices`*

---

## 🔧 Configuration

### Voice Settings

Customize voice characteristics:

```python
{
  "stability": 0.5,         # 0-1: Lower = expressive, Higher = stable
  "similarity_boost": 0.75, # 0-1: Voice similarity
  "style": 0.0,             # 0-1: Style exaggeration
  "use_speaker_boost": True # Enhance clarity
}
```

### Audio Notifications

Enable/disable in frontend:

```javascript
import { useAudioNotifications } from './hooks/useAudio';

const { toggle, isEnabled } = useAudioNotifications();

<button onClick={toggle}>
  {isEnabled ? 'Disable' : 'Enable'} Audio Notifications
</button>
```

---

## 💡 Usage Examples

### Example 1: Voice-Powered Search

```javascript
// User speaks: "machine learning tutorials"
// → Transcribed to text
// → Search performed automatically
// → Results narrated back to user
// → Audio notification: "Found 10 results"
```

### Example 2: Accessibility Mode

```javascript
// User enables audio narration
// → All search results get speaker icons
// → Click any result to hear it
// → Full results narration available
// → Hands-free browsing experience
```

### Example 3: Content to Podcast

```javascript
// User finds interesting article
// → Clicks "Convert to Podcast"
// → AI generates audio version
// → Downloads as MP3 file
// → Listen while commuting
```

---

## 🎓 Use Cases

### Education
- Listen to research papers while exercising
- Voice-activate searches during study sessions
- Convert articles to podcast episodes

### Accessibility
- Screen reader alternative for visually impaired
- Hands-free search for motor disabilities
- Audio confirmations for hearing-capable users

### Productivity
- Search while driving (hands-free)
- Listen to results while multitasking
- Convert work documents to audio

### Content Consumption
- Turn articles into podcasts
- Listen to search results compilation
- Generate audio summaries

---

## 📊 Pricing & Limits

### ElevenLabs Tiers

| Tier | Characters/Month | Price | Best For |
|------|-----------------|-------|----------|
| Free | 10,000 | $0 | Testing, personal use |
| Starter | 30,000 | $5 | Small projects |
| Creator | 100,000 | $22 | Regular use |
| Pro | 500,000 | $99 | Heavy use |

**Tip:** Monitor usage at [elevenlabs.io/app/usage](https://elevenlabs.io/app/usage)

---

## 🔒 Security & Privacy

- ✅ API key stored in environment variables (never in code)
- ✅ All audio endpoints require authentication
- ✅ Rate limiting prevents abuse
- ✅ No audio data stored on servers
- ✅ Audio generated on-demand only

---

## 🐛 Troubleshooting

### Audio Not Working?

1. **Check API Key:**
   ```bash
   # Verify in .env file
   cat .env | grep ELEVENLABS_API_KEY
   ```

2. **Check Service Health:**
   ```bash
   curl http://localhost:8000/api/v1/audio/health
   ```

3. **Browser Console:**
   - Open DevTools (F12)
   - Check for JavaScript errors
   - Verify API requests are successful

### Voice Search Not Recording?

1. Grant microphone permissions in browser
2. Ensure HTTPS (required for microphone access)
3. Check microphone not used by another app

### Slow Performance?

1. Enable streaming: `optimize_streaming: true`
2. Reduce text length for narration
3. Cache frequently used audio
4. Check API rate limits

More troubleshooting: [docs/AUDIO_FEATURES.md#troubleshooting](docs/AUDIO_FEATURES.md#troubleshooting)

---

## 🌟 Feature Comparison

| Feature | Without Audio | With Audio |
|---------|---------------|------------|
| Search | Type only | Type OR speak |
| Results | Read manually | Hear narration |
| Accessibility | Basic | Enhanced |
| Multitasking | Limited | Full support |
| Content | Text only | Text + Audio |
| Notifications | Visual only | Visual + Audio |

---

## 🚦 Getting Started Checklist

- [ ] Get ElevenLabs API key
- [ ] Add key to `.env` file
- [ ] Install backend dependencies (`pip install -r requirements.txt`)
- [ ] Start backend server
- [ ] Start frontend server
- [ ] Test voice search (click mic icon)
- [ ] Test result narration (click speaker icon)
- [ ] Enable audio notifications (toggle button)
- [ ] Try generating a podcast

---

## 📚 Learn More

### Documentation
- [Full Audio Features Documentation](docs/AUDIO_FEATURES.md)
- [Integration Guide](AUDIO_INTEGRATION_EXAMPLE.md)
- [ElevenLabs Quick Start](ELEVENLABS_QUICKSTART.md)

### External Resources
- [ElevenLabs Documentation](https://elevenlabs.io/docs)
- [ElevenLabs Python SDK](https://github.com/elevenlabs/elevenlabs-python)
- [Voice Samples](https://elevenlabs.io/voices)

---

## 🤝 Contributing

Have ideas for audio features? Open an issue or submit a PR!

**Feature Requests:**
- Real-time conversation agents
- Custom voice cloning
- Multi-language support
- Audio playlists
- Background audio controls

---

## 📄 License

Audio features powered by ElevenLabs. See their [Terms of Service](https://elevenlabs.io/terms).

---

## 🎉 Try It Now!

1. **Install:**
   ```bash
   # Add to .env
   ELEVENLABS_API_KEY=your_key_here
   
   # Install and run
   cd backend && pip install -r requirements.txt
   python -m uvicorn app.main:app --reload
   ```

2. **Test:**
   - Open http://localhost:8000/docs
   - Try `/api/v1/audio/health` endpoint
   - Test text-to-speech with sample text

3. **Integrate:**
   - Follow [AUDIO_INTEGRATION_EXAMPLE.md](AUDIO_INTEGRATION_EXAMPLE.md)
   - Add components to your search page
   - Customize voices and settings

---

**Made with 🔊 by Nebula Search Team**

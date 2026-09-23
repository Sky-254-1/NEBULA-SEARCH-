# 🎵 Audio Features Quick Reference Card

## 🚀 Quick Setup (5 Minutes)

```bash
# 1. Add API Key to .env
echo "ELEVENLABS_API_KEY=your_key_here" >> .env

# 2. Install Backend Dependencies
cd backend && pip install -r requirements.txt

# 3. Test Installation
python elevenlabs_example.py

# 4. Start Services
python -m uvicorn app.main:app --reload
# In new terminal: cd ../frontend && npm run dev
```

---

## 📋 API Endpoints Cheat Sheet

| Endpoint | Method | Quick Example |
|----------|--------|---------------|
| Health | GET | `curl http://localhost:8000/api/v1/audio/health` |
| Voices | GET | `curl -H "Authorization: Bearer $TOKEN" /api/v1/audio/voices` |
| TTS | POST | `{"text": "Hello", "voice": "Rachel"}` |
| STT | POST | Upload audio file as multipart/form-data |
| Narrate | POST | `{"query": "...", "results": [...]}` |
| Notify | POST | `{"message": "...", "notification_type": "success"}` |
| Podcast | POST | `{"title": "...", "content": "..."}` |

---

## ⚡ Component Usage

### AudioControls
```jsx
import AudioControls from './components/AudioControls';

<AudioControls text="Your text here" voice="Rachel" />
```

### VoiceSearch
```jsx
import VoiceSearch from './components/VoiceSearch';

<VoiceSearch onTranscript={(text) => performSearch(text)} />
```

### SearchResultsNarrator
```jsx
import SearchResultsNarrator from './components/SearchResultsNarrator';

<SearchResultsNarrator query={query} results={results} maxResults={5} />
```

---

## 🎣 Hook Usage

### useTextToSpeech
```jsx
const { speak, stop, isPlaying } = useTextToSpeech();
speak('Hello world', 'Rachel');
```

### useSpeechToText
```jsx
const { startRecording, stopRecording, transcript } = useSpeechToText();
```

### useSearchNarration
```jsx
const { narrateResults, isPlaying } = useSearchNarration();
narrateResults(query, results);
```

### useAudioNotifications
```jsx
const { notify, toggle, isEnabled } = useAudioNotifications();
notify('Success!', 'success');
```

---

## 🎤 Available Voices

| Voice | Gender | Accent | Best For |
|-------|--------|--------|----------|
| Rachel | F | American | Default, clear |
| Adam | M | American | Professional |
| Bella | F | American | Friendly |
| Antoni | M | American | Conversational |
| Domi | F | American | Energetic |

Full list: `GET /api/v1/audio/voices`

---

## 🔧 Common Tasks

### Play Text
```javascript
import { textToSpeech, playAudio } from './api/audio';

const audio = await textToSpeech('Hello world', 'Rachel');
playAudio(audio);
```

### Voice Search
```javascript
const { startRecording, stopRecording, transcript } = useSpeechToText();

// Start recording
startRecording();

// Stop and get transcript
stopRecording();
console.log(transcript); // User's speech as text
```

### Narrate Results
```javascript
import { narrateSearchResults } from './api/audio';

const audio = await narrateSearchResults(query, results, 5, 'Rachel');
playAudio(audio);
```

### Download Podcast
```javascript
import { generatePodcast, downloadAudio } from './api/audio';

const audio = await generatePodcast('Title', 'Long content...', 'Rachel');
downloadAudio(audio, 'podcast.mp3');
```

---

## 🐛 Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| "API key not configured" | Check `.env` file and restart server |
| Audio not playing | Check browser console, verify API key |
| Mic not working | Grant permission, use HTTPS |
| Slow response | Enable `optimize_streaming: true` |
| 401 Unauthorized | Check authentication token |
| Rate limit error | Wait or upgrade ElevenLabs plan |

---

## 📊 Response Time Expectations

| Operation | Expected | Max |
|-----------|----------|-----|
| Health check | < 50ms | 200ms |
| Voice list | < 500ms | 2s |
| Short TTS | < 2s | 5s |
| Long TTS | < 5s | 15s |
| STT | < 3s | 10s |
| Narration | < 4s | 12s |

---

## 🎨 CSS Classes Reference

### AudioControls
- `.audio-controls` - Container
- `.audio-btn` - Button base
- `.audio-btn-play` - Play button
- `.audio-btn-stop` - Stop button

### VoiceSearch
- `.voice-search` - Container
- `.voice-search-btn` - Mic button
- `.voice-search-btn.recording` - Active state

### SearchResultsNarrator
- `.search-narrator` - Container
- `.narrator-btn` - Main button
- `.narrator-btn.playing` - Playing state

---

## 🔑 Environment Variables

```bash
# Required
ELEVENLABS_API_KEY=your_api_key_here

# Optional (defaults shown)
VITE_API_URL=http://localhost:8000
```

---

## 📦 Import Paths

```javascript
// API Client
import * as audioApi from '../api/audio';

// Hooks
import { 
  useTextToSpeech,
  useSpeechToText,
  useSearchNarration,
  useAudioNotifications
} from '../hooks/useAudio';

// Components
import AudioControls from '../components/AudioControls';
import VoiceSearch from '../components/VoiceSearch';
import SearchResultsNarrator from '../components/SearchResultsNarrator';
```

---

## 🧪 Test Commands

```bash
# Backend health check
curl http://localhost:8000/api/v1/audio/health

# Run example script
cd backend && python elevenlabs_example.py

# Test TTS endpoint
curl -X POST http://localhost:8000/api/v1/audio/tts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Test","voice":"Rachel"}' \
  --output test.mp3
```

---

## 💾 File Locations

```
backend/
├── app/
│   ├── services/audio.py          # Audio service
│   └── routes/audio.py            # API endpoints
├── elevenlabs_example.py          # Test script
└── requirements.txt               # Dependencies

frontend/
├── src/
│   ├── api/audio.js               # API client
│   ├── hooks/useAudio.js          # React hooks
│   └── components/
│       ├── AudioControls.jsx      # Audio controls
│       ├── VoiceSearch.jsx        # Voice search
│       └── SearchResultsNarrator.jsx  # Narrator

docs/
├── AUDIO_FEATURES.md              # Full docs
├── AUDIO_INTEGRATION_EXAMPLE.md   # Integration guide
├── AUDIO_TESTING_GUIDE.md         # Testing guide
└── AUDIO_QUICK_REFERENCE.md       # This file
```

---

## 🎯 Common Patterns

### Pattern 1: Add Audio to Existing Content
```jsx
function Article({ title, content }) {
  return (
    <div>
      <h1>{title}</h1>
      <AudioControls text={content} />
      <p>{content}</p>
    </div>
  );
}
```

### Pattern 2: Voice-Enabled Search
```jsx
function SearchBar() {
  const [query, setQuery] = useState('');
  
  return (
    <div>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      <VoiceSearch onTranscript={setQuery} />
      <button>Search</button>
    </div>
  );
}
```

### Pattern 3: Results with Narration
```jsx
function Results({ query, results }) {
  return (
    <div>
      <SearchResultsNarrator query={query} results={results} />
      {results.map(r => <ResultCard key={r.id} result={r} />)}
    </div>
  );
}
```

---

## 📱 Browser Requirements

- ✅ Modern browser (Chrome, Firefox, Safari, Edge)
- ✅ HTTPS for microphone access
- ✅ Audio playback enabled
- ✅ JavaScript enabled

---

## 💰 ElevenLabs Pricing Quick Ref

| Tier | Chars/Month | Price |
|------|-------------|-------|
| Free | 10,000 | $0 |
| Starter | 30,000 | $5 |
| Creator | 100,000 | $22 |
| Pro | 500,000 | $99 |

Monitor: [elevenlabs.io/app/usage](https://elevenlabs.io/app/usage)

---

## 🔐 Security Checklist

- [ ] API key in `.env` (never in code)
- [ ] Authentication required for all endpoints
- [ ] Rate limiting enabled
- [ ] Input validation active
- [ ] HTTPS in production
- [ ] CORS configured

---

## 📖 Documentation Quick Links

| Topic | File |
|-------|------|
| Getting Started | `ELEVENLABS_QUICKSTART.md` |
| Feature Overview | `AUDIO_FEATURES_README.md` |
| API Reference | `docs/AUDIO_FEATURES.md` |
| Integration | `AUDIO_INTEGRATION_EXAMPLE.md` |
| Testing | `AUDIO_TESTING_GUIDE.md` |
| Summary | `AUDIO_IMPLEMENTATION_SUMMARY.md` |

---

## ⚡ Performance Tips

1. **Enable streaming for long text:**
   ```javascript
   textToSpeech(text, voice, true) // optimize_streaming: true
   ```

2. **Cache frequently used audio:**
   ```javascript
   const cache = new Map();
   if (cache.has(text)) return cache.get(text);
   ```

3. **Debounce voice search:**
   ```javascript
   const debouncedSearch = debounce(performSearch, 500);
   ```

4. **Lazy load components:**
   ```javascript
   const AudioControls = lazy(() => import('./AudioControls'));
   ```

---

## 🎬 Getting Started Workflow

1. **Setup** (5 min)
   - Get API key
   - Add to `.env`
   - Install dependencies

2. **Test** (2 min)
   - Run `elevenlabs_example.py`
   - Check API health
   - Verify voices list

3. **Integrate** (10 min)
   - Add components to search page
   - Import hooks
   - Test in browser

4. **Customize** (5 min)
   - Select preferred voice
   - Adjust settings
   - Style components

**Total: ~22 minutes to full audio-enabled search!**

---

## 🆘 Emergency Debug

```bash
# Check if API key is set
echo $ELEVENLABS_API_KEY

# Test health endpoint
curl http://localhost:8000/api/v1/audio/health

# Check backend logs
# Look for errors in terminal running uvicorn

# Check frontend logs
# Open browser DevTools (F12) → Console

# Verify authentication
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/audio/voices
```

---

## 📞 Support

- 📖 Docs: See files listed above
- 🐛 Issues: Check `AUDIO_TESTING_GUIDE.md`
- 💡 Examples: See `elevenlabs_example.py`
- 🔗 ElevenLabs: [docs.elevenlabs.io](https://docs.elevenlabs.io)

---

**🎉 Happy Building!**

*Keep this card handy for quick reference during development.*

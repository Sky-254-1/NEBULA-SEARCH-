# Audio Features Documentation

## Overview

Nebula Search Engine now includes comprehensive audio features powered by ElevenLabs, providing:

1. **🔊 Voice Narration** - Text-to-speech for search results and content
2. **♿ Audio Accessibility** - Screen reader alternatives for visually impaired users
3. **🎤 Voice Search** - Speech-to-text search capabilities
4. **🔔 Audio Notifications** - Spoken alerts and notifications
5. **🎙️ Podcast Generation** - Convert articles and content to audio

---

## Table of Contents

1. [Setup & Installation](#setup--installation)
2. [Backend API Endpoints](#backend-api-endpoints)
3. [Frontend Components](#frontend-components)
4. [Usage Examples](#usage-examples)
5. [Accessibility Features](#accessibility-features)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Setup & Installation

### 1. Prerequisites

- ElevenLabs API key (get from [elevenlabs.io](https://elevenlabs.io))
- Python 3.8+ (backend)
- Node.js 16+ (frontend)

### 2. Backend Setup

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Add API key to .env
echo "ELEVENLABS_API_KEY=your_api_key_here" >> ../.env
```

### 3. Frontend Setup

No additional dependencies needed - audio features use browser APIs and the backend.

### 4. Start Services

```bash
# Start backend
cd backend
python -m uvicorn app.main:app --reload

# Start frontend (in separate terminal)
cd frontend
npm run dev
```

### 5. Verify Installation

Check audio service health:
```bash
curl http://localhost:8000/api/v1/audio/health
```

---

## Backend API Endpoints

### Health Check

**GET** `/api/v1/audio/health`

Check if audio service is available.

**Response:**
```json
{
  "available": true,
  "service": "ElevenLabs",
  "features": ["text-to-speech", "speech-to-text", "sound-effects", "search-narration", "notifications"]
}
```

---

### List Voices

**GET** `/api/v1/audio/voices`

Get available voices for text-to-speech.

**Headers:**
- `Authorization: Bearer <token>`

**Response:**
```json
{
  "voices": [
    {
      "voice_id": "21m00Tcm4TlvDq8ikWAM",
      "name": "Rachel",
      "category": "premade",
      "description": "American female voice",
      "preview_url": "https://..."
    }
  ],
  "total": 10
}
```

---

### Text-to-Speech

**POST** `/api/v1/audio/tts`

Convert text to speech audio.

**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Body:**
```json
{
  "text": "Hello, this is a test",
  "voice": "Rachel",
  "optimize_streaming": false
}
```

**Response:** Audio file (MP3)

---

### Streaming Text-to-Speech

**POST** `/api/v1/audio/tts/stream`

Stream text-to-speech for real-time playback.

**Body:**
```json
{
  "text": "Long content to narrate...",
  "voice": "Rachel"
}
```

**Response:** Streaming audio (MP3)

---

### Speech-to-Text

**POST** `/api/v1/audio/stt`

Transcribe audio to text (voice search).

**Headers:**
- `Authorization: Bearer <token>`

**Form Data:**
- `audio`: Audio file (MP3, WAV, etc.)
- `language`: Language code (default: "en")

**Response:**
```json
{
  "text": "search for machine learning",
  "language": "en",
  "success": true
}
```

---

### Narrate Search Results

**POST** `/api/v1/audio/narrate/search`

Generate audio narration of search results.

**Body:**
```json
{
  "query": "machine learning",
  "results": [
    {
      "title": "Introduction to ML",
      "snippet": "Machine learning is...",
      "url": "https://example.com",
      "source": "Wikipedia"
    }
  ],
  "max_results": 5,
  "voice": "Rachel"
}
```

**Response:** Audio file (MP3)

---

### Audio Notification

**POST** `/api/v1/audio/notification`

Generate spoken notification.

**Body:**
```json
{
  "message": "Search completed successfully",
  "notification_type": "success",
  "voice": "Rachel"
}
```

**Types:** `info`, `success`, `warning`, `error`

**Response:** Audio file (MP3)

---

### Generate Sound Effect

**POST** `/api/v1/audio/sound-effect`

Create custom sound effect.

**Body:**
```json
{
  "description": "notification bell",
  "duration": 2.0
}
```

**Response:** Audio file (MP3)

---

### Generate Podcast

**POST** `/api/v1/audio/podcast/generate`

Convert long-form content to podcast.

**Body:**
```json
{
  "title": "Machine Learning Guide",
  "content": "In this episode...",
  "voice": "Rachel",
  "add_intro": true
}
```

**Response:** Audio file (MP3, downloadable)

---

## Frontend Components

### AudioControls

Add text-to-speech to any text content.

```jsx
import AudioControls from './components/AudioControls';

function Article({ content }) {
  return (
    <div>
      <AudioControls text={content} voice="Rachel" />
      <p>{content}</p>
    </div>
  );
}
```

**Props:**
- `text` (string, required) - Text to narrate
- `voice` (string, optional) - Voice name (default: "Rachel")
- `className` (string, optional) - Additional CSS classes

---

### VoiceSearch

Voice-activated search input.

```jsx
import VoiceSearch from './components/VoiceSearch';

function SearchBar() {
  const handleTranscript = (text) => {
    console.log('Voice search:', text);
    // Perform search with transcript
  };

  return (
    <div>
      <input type="text" placeholder="Search..." />
      <VoiceSearch onTranscript={handleTranscript} />
    </div>
  );
}
```

**Props:**
- `onTranscript` (function, required) - Callback with transcribed text
- `className` (string, optional) - Additional CSS classes

---

### SearchResultsNarrator

Narrate search results for accessibility.

```jsx
import SearchResultsNarrator from './components/SearchResultsNarrator';

function SearchResults({ query, results }) {
  return (
    <div>
      <SearchResultsNarrator 
        query={query}
        results={results}
        maxResults={5}
        voice="Rachel"
      />
      {/* Display results */}
    </div>
  );
}
```

**Props:**
- `query` (string, required) - Search query
- `results` (array, required) - Search results array
- `maxResults` (number, optional) - Max results to narrate (default: 5)
- `voice` (string, optional) - Voice name (default: "Rachel")
- `className` (string, optional) - Additional CSS classes

---

## React Hooks

### useTextToSpeech

```jsx
import { useTextToSpeech } from '../hooks/useAudio';

function Component() {
  const { speak, stop, pause, resume, isLoading, isPlaying, error } = useTextToSpeech();

  const handleSpeak = () => {
    speak('Hello world!', 'Rachel', true);
  };

  return (
    <button onClick={handleSpeak} disabled={isLoading}>
      {isPlaying ? 'Pause' : 'Speak'}
    </button>
  );
}
```

---

### useSpeechToText

```jsx
import { useSpeechToText } from '../hooks/useAudio';

function VoiceInput() {
  const { 
    startRecording, 
    stopRecording, 
    isRecording, 
    transcript 
  } = useSpeechToText();

  return (
    <div>
      <button onClick={isRecording ? stopRecording : startRecording}>
        {isRecording ? 'Stop' : 'Record'}
      </button>
      {transcript && <p>You said: {transcript}</p>}
    </div>
  );
}
```

---

### useSearchNarration

```jsx
import { useSearchNarration } from '../hooks/useAudio';

function Results({ query, results }) {
  const { narrateResults, isPlaying } = useSearchNarration();

  return (
    <button onClick={() => narrateResults(query, results)}>
      {isPlaying ? 'Stop' : 'Listen'}
    </button>
  );
}
```

---

### useAudioNotifications

```jsx
import { useAudioNotifications } from '../hooks/useAudio';

function App() {
  const { notify, toggle, isEnabled } = useAudioNotifications();

  const handleSuccess = () => {
    notify('Operation completed successfully!', 'success');
  };

  return (
    <div>
      <button onClick={toggle}>
        Audio Notifications: {isEnabled ? 'ON' : 'OFF'}
      </button>
      <button onClick={handleSuccess}>Test Notification</button>
    </div>
  );
}
```

---

## Usage Examples

### Example 1: Search Results with Voice Narration

```jsx
import { useState } from 'react';
import SearchResultsNarrator from './components/SearchResultsNarrator';
import VoiceSearch from './components/VoiceSearch';

function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const handleVoiceSearch = (transcript) => {
    setQuery(transcript);
    performSearch(transcript);
  };

  const performSearch = async (searchQuery) => {
    const response = await fetch(`/api/v1/search/web?q=${searchQuery}`);
    const data = await response.json();
    setResults(data);
  };

  return (
    <div>
      <div className="search-bar">
        <input 
          type="text" 
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search..."
        />
        <VoiceSearch onTranscript={handleVoiceSearch} />
      </div>

      {results.length > 0 && (
        <>
          <SearchResultsNarrator 
            query={query}
            results={results}
            maxResults={5}
          />
          
          {results.map((result, i) => (
            <div key={i} className="result">
              <h3>{result.title}</h3>
              <p>{result.snippet}</p>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
```

---

### Example 2: Accessible Article Reader

```jsx
import AudioControls from './components/AudioControls';

function Article({ title, content }) {
  return (
    <article>
      <header>
        <h1>{title}</h1>
        <AudioControls 
          text={`${title}. ${content}`}
          voice="Rachel"
        />
      </header>
      <div className="content">
        {content}
      </div>
    </article>
  );
}
```

---

### Example 3: Voice-Controlled Search

```jsx
import { useState, useEffect } from 'react';
import { useSpeechToText } from '../hooks/useAudio';
import { useAudioNotifications } from '../hooks/useAudio';

function VoiceControlledSearch() {
  const { startRecording, stopRecording, isRecording, transcript } = useSpeechToText();
  const { notify } = useAudioNotifications();
  const [results, setResults] = useState([]);

  useEffect(() => {
    if (transcript) {
      performSearch(transcript);
      notify(`Searching for: ${transcript}`, 'info');
    }
  }, [transcript]);

  const performSearch = async (query) => {
    const response = await fetch(`/api/v1/search/web?q=${query}`);
    const data = await response.json();
    setResults(data);
    notify(`Found ${data.length} results`, 'success');
  };

  return (
    <div>
      <button onClick={isRecording ? stopRecording : startRecording}>
        {isRecording ? '🔴 Stop' : '🎤 Voice Search'}
      </button>
      {/* Display results */}
    </div>
  );
}
```

---

## Accessibility Features

### Screen Reader Support

All audio components include proper ARIA labels:

```jsx
<button 
  onClick={handlePlay}
  aria-label="Play narration"
  role="button"
>
  🔊
</button>
```

### Keyboard Navigation

- All buttons are keyboard accessible
- Focus indicators are clearly visible
- Tab order follows logical flow

### Visual Feedback

- Loading states with spinners
- Playing states with animations
- Error messages with clear text

### Audio Alternatives

- All audio features are optional
- Text alternatives always available
- Users can enable/disable audio notifications

---

## Best Practices

### 1. Voice Selection

Choose appropriate voices for your content:

- **Rachel** - Clear, professional female voice (default)
- **Adam** - Professional male voice
- **Bella** - Warm, friendly female voice
- **Antoni** - Clear male voice

### 2. Content Optimization

Format text for better narration:

```javascript
// Good: Clear, conversational
const text = "Welcome to Nebula Search. Here are your results.";

// Avoid: Special characters, markdown
const badText = "## Welcome to *Nebula* Search! Here are [your results]";
```

### 3. Performance

- Cache audio for frequently used content
- Use streaming for long content (>1000 characters)
- Implement rate limiting for API calls

### 4. User Preferences

Store user audio preferences:

```javascript
localStorage.setItem('preferredVoice', 'Rachel');
localStorage.setItem('audioNotifications', 'true');
```

### 5. Error Handling

Always handle audio errors gracefully:

```javascript
try {
  await speak(text);
} catch (error) {
  console.error('Audio error:', error);
  // Show text alternative
}
```

---

## Troubleshooting

### Audio Not Playing

**Issue:** No sound when clicking play button

**Solutions:**
1. Check browser console for errors
2. Verify ELEVENLABS_API_KEY is set
3. Check audio service health: `/api/v1/audio/health`
4. Ensure browser allows audio playback (user interaction required)

---

### Voice Search Not Working

**Issue:** Microphone not recording

**Solutions:**
1. Grant microphone permissions in browser
2. Check if HTTPS is enabled (required for microphone access)
3. Verify microphone is not used by another app
4. Test with `navigator.mediaDevices.getUserMedia()`

---

### API Key Errors

**Issue:** "Audio service unavailable"

**Solutions:**
1. Verify API key in `.env` file
2. Check API key is valid at elevenlabs.io
3. Restart backend server
4. Check for API rate limits

---

### Slow Response Times

**Issue:** Audio generation takes too long

**Solutions:**
1. Use `optimize_streaming: true` for faster response
2. Reduce text length for narration
3. Cache frequently requested audio
4. Consider using streaming endpoint for long content

---

## API Rate Limits

ElevenLabs API has the following limits:

- **Free Tier**: 10,000 characters/month
- **Starter**: 30,000 characters/month
- **Creator**: 100,000 characters/month
- **Pro**: 500,000 characters/month

Monitor usage in your ElevenLabs dashboard.

---

## Security Considerations

1. **API Key Protection**
   - Never expose API key in frontend code
   - Store in environment variables only
   - Rotate keys regularly

2. **User Authentication**
   - All audio endpoints require authentication
   - Use JWT tokens for API access
   - Implement rate limiting per user

3. **Content Validation**
   - Sanitize user input before TTS
   - Limit text length (5000 chars max)
   - Validate file types for STT

---

## Future Enhancements

- [ ] Voice cloning for personalized voices
- [ ] Multi-language support
- [ ] Real-time conversation agents
- [ ] Audio search history
- [ ] Playlist generation for multiple articles
- [ ] Background audio controls
- [ ] Audio speed controls
- [ ] Audio bookmarks

---

## Support

For issues or questions:
1. Check [ElevenLabs Documentation](https://elevenlabs.io/docs)
2. Review API logs in backend console
3. Test endpoints with curl or Postman
4. Check browser console for frontend errors

---

## License

Audio features are powered by ElevenLabs. Review their [terms of service](https://elevenlabs.io/terms) for usage guidelines.

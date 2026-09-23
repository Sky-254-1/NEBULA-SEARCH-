# Audio Features Testing Guide

Complete guide to test all audio features in Nebula Search.

---

## Prerequisites

✅ ElevenLabs API key added to `.env`  
✅ Backend dependencies installed  
✅ Frontend running  
✅ Valid authentication token  

---

## Test 1: Backend Health Check

### Using cURL

```bash
curl http://localhost:8000/api/v1/audio/health
```

**Expected Response:**
```json
{
  "available": true,
  "service": "ElevenLabs",
  "features": [
    "text-to-speech",
    "speech-to-text",
    "sound-effects",
    "search-narration",
    "notifications"
  ]
}
```

### Using Python

```python
import requests

response = requests.get('http://localhost:8000/api/v1/audio/health')
print(response.json())
```

**✅ Pass:** `available: true`  
**❌ Fail:** Check API key in `.env` file

---

## Test 2: List Available Voices

### Using cURL

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/audio/voices
```

**Expected Response:**
```json
{
  "voices": [
    {
      "voice_id": "21m00Tcm4TlvDq8ikWAM",
      "name": "Rachel",
      "category": "premade",
      "description": "Calm, articulate",
      "preview_url": "https://..."
    }
  ],
  "total": 10
}
```

**✅ Pass:** List of voices returned  
**❌ Fail:** Check authentication token

---

## Test 3: Text-to-Speech

### Using cURL

```bash
curl -X POST http://localhost:8000/api/v1/audio/tts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from Nebula Search!", "voice": "Rachel"}' \
  --output test_speech.mp3
```

**Verification:**
1. File `test_speech.mp3` is created
2. File size > 0 bytes
3. Play the file - should hear clear speech

**✅ Pass:** Audio file plays correctly  
**❌ Fail:** Check API rate limits or text content

---

## Test 4: Speech-to-Text

### Using Python

```python
import requests

# Record or use a test audio file
audio_file = open('test_audio.mp3', 'rb')

response = requests.post(
    'http://localhost:8000/api/v1/audio/stt',
    headers={'Authorization': f'Bearer {token}'},
    files={'audio': audio_file},
    data={'language': 'en'}
)

print(response.json())
```

**Expected Response:**
```json
{
  "text": "transcribed text here",
  "language": "en",
  "success": true
}
```

**✅ Pass:** Text transcription matches audio  
**❌ Fail:** Check audio file format and quality

---

## Test 5: Search Results Narration

### Using cURL

```bash
curl -X POST http://localhost:8000/api/v1/audio/narrate/search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "results": [
      {
        "title": "Introduction to ML",
        "snippet": "Machine learning is a subset of AI...",
        "url": "https://example.com",
        "source": "Wikipedia"
      }
    ],
    "max_results": 3,
    "voice": "Rachel"
  }' \
  --output search_narration.mp3
```

**Verification:**
1. Audio file created
2. Narration includes query, titles, and snippets
3. Clear and natural sounding

**✅ Pass:** Narration flows naturally  
**❌ Fail:** Check results format

---

## Test 6: Audio Notifications

### Using Python

```python
import requests

for notification_type in ['info', 'success', 'warning', 'error']:
    response = requests.post(
        'http://localhost:8000/api/v1/audio/notification',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'message': f'Test {notification_type} notification',
            'notification_type': notification_type,
            'voice': 'Rachel'
        }
    )
    
    with open(f'notification_{notification_type}.mp3', 'wb') as f:
        f.write(response.content)
    
    print(f'✅ {notification_type} notification generated')
```

**Verification:**
1. Four audio files created
2. Each has appropriate prefix (Info, Success, Warning, Error)
3. Message is clear

**✅ Pass:** All notification types work  
**❌ Fail:** Check notification type parameter

---

## Test 7: Podcast Generation

### Using cURL

```bash
curl -X POST http://localhost:8000/api/v1/audio/podcast/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Podcast",
    "content": "This is a test podcast episode with some longer content to test the audio generation quality and duration handling.",
    "voice": "Rachel",
    "add_intro": true
  }' \
  --output test_podcast.mp3
```

**Verification:**
1. MP3 file created
2. Includes intro: "Welcome to Nebula Search Podcast..."
3. Content is narrated clearly
4. File duration matches content length

**✅ Pass:** Podcast sounds professional  
**❌ Fail:** Check content length (min 100 chars)

---

## Test 8: Frontend Voice Search

### Manual Testing

1. **Open frontend:** http://localhost:5173
2. **Click microphone icon** in search bar
3. **Grant microphone permission** if prompted
4. **Speak clearly:** "machine learning tutorials"
5. **Stop recording** (click mic again or auto-stop)
6. **Verify:** Search query appears in input field
7. **Verify:** Search is performed automatically

**Expected Behavior:**
- Mic icon turns red while recording
- "Recording..." status appears
- "Processing..." appears after stopping
- Search query populates input
- Results appear automatically

**✅ Pass:** Voice search works smoothly  
**❌ Fail:** Check microphone permissions and HTTPS

---

## Test 9: Frontend Result Narration

### Manual Testing

1. **Perform a search** (any query)
2. **Wait for results** to load
3. **Click "Listen to Results"** button
4. **Verify:** Audio plays automatically
5. **Check:** Status shows "Narrating X results..."
6. **Listen:** Narration includes query and results
7. **Click stop** to end playback

**Expected Behavior:**
- Button shows loading spinner
- Audio plays immediately
- Can stop at any time
- Clear narration of titles and snippets

**✅ Pass:** Narration is clear and complete  
**❌ Fail:** Check browser audio settings

---

## Test 10: Frontend Audio Controls

### Manual Testing

1. **Navigate to search results**
2. **Find speaker icon** on individual result
3. **Click speaker icon**
4. **Verify:** Result title + snippet plays
5. **Click again** to pause
6. **Click stop** to reset

**Expected Behavior:**
- Play/pause toggle works
- Stop button appears when playing
- Audio quality is clear
- Visual feedback (icon changes)

**✅ Pass:** Controls work as expected  
**❌ Fail:** Check component props

---

## Test 11: Audio Notification Toggle

### Manual Testing

1. **Locate notification toggle** button
2. **Initial state:** Check if enabled/disabled
3. **Perform search** and observe notifications
4. **Toggle off**
5. **Perform another search**
6. **Verify:** No audio notifications
7. **Toggle on**
8. **Verify:** Notifications resume

**Expected Behavior:**
- Toggle persists after page reload
- Stored in localStorage
- Other audio features still work

**✅ Pass:** Toggle affects only notifications  
**❌ Fail:** Check localStorage access

---

## Test 12: Example Script

Run the comprehensive test example:

```bash
cd backend
python elevenlabs_example.py
```

**Expected Output:**
```
ElevenLabs Text-to-Speech Demo
========================================
Generating speech...
✓ Speech generated successfully and saved to: output_speech.mp3

Available voices:
  - Rachel (ID: ...)
  - Adam (ID: ...)
  - Bella (ID: ...)

Generating speech with custom settings...
✓ Custom speech generated and saved to: output_speech_custom.mp3

✨ All examples completed successfully!
```

**✅ Pass:** All examples run without errors  
**❌ Fail:** Check API key and dependencies

---

## Performance Benchmarks

### Expected Response Times

| Endpoint | Expected Time | Max Acceptable |
|----------|--------------|----------------|
| `/audio/health` | < 50ms | 200ms |
| `/audio/voices` | < 500ms | 2s |
| `/audio/tts` (short) | < 2s | 5s |
| `/audio/tts` (long) | < 5s | 15s |
| `/audio/stt` | < 3s | 10s |
| `/audio/narrate/search` | < 4s | 12s |

**Test Performance:**
```bash
time curl -X POST http://localhost:8000/api/v1/audio/tts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Quick test", "voice": "Rachel"}' \
  --output /dev/null
```

---

## Load Testing

### Test Concurrent Requests

```python
import concurrent.futures
import requests

def test_tts():
    response = requests.post(
        'http://localhost:8000/api/v1/audio/tts',
        headers={'Authorization': f'Bearer {token}'},
        json={'text': 'Test', 'voice': 'Rachel'}
    )
    return response.status_code == 200

# Test 10 concurrent requests
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(test_tts) for _ in range(10)]
    results = [f.result() for f in futures]
    
print(f'Success rate: {sum(results)}/10')
```

**✅ Pass:** 80%+ success rate  
**❌ Fail:** Check rate limits and server capacity

---

## Error Handling Tests

### Test 1: Missing API Key

```bash
# Temporarily rename .env file
mv .env .env.backup

# Start server and test
curl http://localhost:8000/api/v1/audio/health

# Should return: "available": false

# Restore .env
mv .env.backup .env
```

### Test 2: Invalid Voice

```bash
curl -X POST http://localhost:8000/api/v1/audio/tts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test", "voice": "InvalidVoice"}' \
  --output /dev/null
```

**Expected:** Error message with available voices

### Test 3: Text Too Long

```bash
# Generate 10,000 character text
python -c "print('a' * 10000)" > long_text.txt

curl -X POST http://localhost:8000/api/v1/audio/tts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$(cat long_text.txt)\", \"voice\": \"Rachel\"}" \
  --output /dev/null
```

**Expected:** Error or truncation with max length

### Test 4: Unauthorized Access

```bash
curl -X POST http://localhost:8000/api/v1/audio/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Test", "voice": "Rachel"}'
```

**Expected:** 401 Unauthorized

---

## Browser Compatibility

Test in multiple browsers:

- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari
- [ ] Mobile Chrome
- [ ] Mobile Safari

**Features to verify:**
- Voice search (microphone access)
- Audio playback
- Notification sounds
- Download functionality

---

## Accessibility Testing

### Keyboard Navigation

1. Tab through all audio controls
2. Verify focus indicators are visible
3. Test Enter/Space to activate buttons
4. Ensure all features accessible without mouse

### Screen Reader Testing

1. Enable screen reader (NVDA, JAWS, VoiceOver)
2. Navigate to audio controls
3. Verify ARIA labels are announced
4. Test with audio features enabled

### High Contrast Mode

1. Enable high contrast mode
2. Verify all controls are visible
3. Check icon clarity
4. Test color contrast ratios

---

## Troubleshooting Common Issues

### Issue: "API key not configured"

**Solution:**
```bash
# Check .env file
cat .env | grep ELEVENLABS_API_KEY

# Restart backend server
python -m uvicorn app.main:app --reload
```

### Issue: "Microphone access denied"

**Solution:**
1. Check browser permissions
2. Use HTTPS (required for microphone)
3. Grant permission when prompted

### Issue: Audio not playing

**Solution:**
1. Check browser console for errors
2. Verify audio file is downloaded
3. Test browser audio with other sites
4. Check volume settings

### Issue: Slow response times

**Solution:**
1. Enable `optimize_streaming: true`
2. Reduce text length
3. Check API rate limits
4. Monitor network speed

---

## Test Checklist

### Backend Tests
- [ ] Health check returns available: true
- [ ] Voices endpoint lists voices
- [ ] Text-to-speech generates audio
- [ ] Speech-to-text transcribes correctly
- [ ] Search narration works
- [ ] Notifications generate audio
- [ ] Podcast generation works
- [ ] Error handling functions properly

### Frontend Tests
- [ ] Voice search captures audio
- [ ] Search results narrate correctly
- [ ] Individual result audio works
- [ ] Audio controls respond
- [ ] Notification toggle works
- [ ] Loading states display
- [ ] Error messages show
- [ ] Keyboard navigation works

### Integration Tests
- [ ] Voice search triggers real search
- [ ] Search results play correctly
- [ ] Notifications fire on events
- [ ] Podcast downloads work
- [ ] Components integrate smoothly

### Performance Tests
- [ ] Response times acceptable
- [ ] Concurrent requests handled
- [ ] No memory leaks
- [ ] Audio cache works

### Accessibility Tests
- [ ] Keyboard accessible
- [ ] Screen reader compatible
- [ ] ARIA labels present
- [ ] High contrast support

---

## Success Criteria

**All tests pass if:**

✅ Backend health check shows available  
✅ At least 5 voices are listed  
✅ Text-to-speech generates clear audio  
✅ Voice search transcribes accurately  
✅ Search narration is natural-sounding  
✅ All notification types work  
✅ Podcasts download successfully  
✅ Frontend components render correctly  
✅ Audio controls respond to clicks  
✅ Keyboard navigation works  
✅ No console errors during normal use  
✅ Performance meets benchmarks  

---

## Report Issues

If tests fail:

1. Note the specific test that failed
2. Copy error messages
3. Check logs in backend console
4. Verify prerequisites are met
5. Review documentation
6. Open issue with details

---

**Happy Testing! 🎉**

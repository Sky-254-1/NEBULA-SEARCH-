# Audio Features Integration Example

## Quick Start: Add Audio to Your Search Page

This guide shows how to integrate all audio features into your existing Nebula Search interface.

---

## Step 1: Import Components

```jsx
// In your SearchPage component file
import AudioControls from '../components/AudioControls';
import VoiceSearch from '../components/VoiceSearch';
import SearchResultsNarrator from '../components/SearchResultsNarrator';
import { useAudioNotifications } from '../hooks/useAudio';
```

---

## Step 2: Enhanced Search Page Example

```jsx
import { useState, useEffect } from 'react';
import AudioControls from '../components/AudioControls';
import VoiceSearch from '../components/VoiceSearch';
import SearchResultsNarrator from '../components/SearchResultsNarrator';
import { useAudioNotifications } from '../hooks/useAudio';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const { notify, isEnabled, toggle } = useAudioNotifications();

  // Handle regular text search
  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    
    try {
      const response = await fetch(
        `/api/v1/search/web?q=${encodeURIComponent(query)}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );
      
      const data = await response.json();
      setResults(data);
      
      // Audio notification for search completion
      notify(`Found ${data.length} results for ${query}`, 'success');
      
    } catch (error) {
      console.error('Search error:', error);
      notify('Search failed. Please try again.', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle voice search transcript
  const handleVoiceTranscript = (transcript) => {
    setQuery(transcript);
    notify(`Searching for: ${transcript}`, 'info');
    
    // Trigger search with voice transcript
    setTimeout(() => {
      handleSearch({ preventDefault: () => {} });
    }, 100);
  };

  return (
    <div className="search-page">
      {/* Header with audio notification toggle */}
      <header className="search-header">
        <h1>Nebula Search</h1>
        <button 
          onClick={toggle}
          className="audio-toggle"
          title={`Audio notifications ${isEnabled ? 'enabled' : 'disabled'}`}
        >
          {isEnabled ? '🔊' : '🔇'} Audio Notifications
        </button>
      </header>

      {/* Search Bar with Voice Search */}
      <form onSubmit={handleSearch} className="search-form">
        <div className="search-input-group">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search the web..."
            className="search-input"
            aria-label="Search query"
          />
          
          {/* Voice Search Button */}
          <VoiceSearch 
            onTranscript={handleVoiceTranscript}
            className="voice-search-btn"
          />
          
          <button 
            type="submit" 
            disabled={isLoading}
            className="search-button"
          >
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {/* Search Results with Audio Narration */}
      {results.length > 0 && (
        <div className="search-results">
          {/* Audio Narration Controls */}
          <div className="results-header">
            <h2>
              Results for "{query}" ({results.length})
            </h2>
            <SearchResultsNarrator
              query={query}
              results={results}
              maxResults={5}
              voice="Rachel"
            />
          </div>

          {/* Individual Results */}
          <div className="results-list">
            {results.map((result, index) => (
              <article key={index} className="result-card">
                <div className="result-header">
                  <h3>
                    <a href={result.url} target="_blank" rel="noopener noreferrer">
                      {result.title}
                    </a>
                  </h3>
                  
                  {/* Audio controls for each result */}
                  <AudioControls 
                    text={`${result.title}. ${result.snippet}`}
                    voice="Rachel"
                    className="result-audio"
                  />
                </div>
                
                <p className="result-snippet">{result.snippet}</p>
                
                <div className="result-footer">
                  <span className="result-source">{result.source}</span>
                  <a href={result.url} className="result-link">
                    Visit →
                  </a>
                </div>
              </article>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && results.length === 0 && query && (
        <div className="empty-state">
          <p>No results found for "{query}"</p>
          <AudioControls 
            text={`No results found for ${query}. Try a different search term.`}
            voice="Rachel"
          />
        </div>
      )}
    </div>
  );
}
```

---

## Step 3: Add Basic Styles

```css
/* search-page.css */

.search-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.search-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.audio-toggle {
  background: rgba(139, 92, 246, 0.2);
  border: 1px solid rgba(139, 92, 246, 0.4);
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.audio-toggle:hover {
  background: rgba(139, 92, 246, 0.3);
}

.search-form {
  margin-bottom: 2rem;
}

.search-input-group {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.search-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 0.5rem;
  background: rgba(0, 0, 0, 0.2);
  color: inherit;
  font-size: 1rem;
}

.search-button {
  padding: 0.75rem 1.5rem;
  background: #3b82f6;
  border: none;
  border-radius: 0.5rem;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.search-button:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
}

.search-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.result-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.75rem;
  padding: 1.5rem;
  transition: all 0.2s;
}

.result-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.result-header h3 {
  flex: 1;
  margin: 0;
  font-size: 1.25rem;
}

.result-header a {
  color: #3b82f6;
  text-decoration: none;
}

.result-header a:hover {
  text-decoration: underline;
}

.result-snippet {
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
  margin-bottom: 1rem;
}

.result-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
}

.result-link {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: rgba(255, 255, 255, 0.6);
}

@media (max-width: 768px) {
  .search-page {
    padding: 1rem;
  }

  .search-input-group {
    flex-wrap: wrap;
  }

  .search-input {
    width: 100%;
  }

  .results-header {
    flex-direction: column;
    align-items: start;
    gap: 1rem;
  }

  .result-header {
    flex-direction: column;
  }
}
```

---

## Step 4: API Configuration

Make sure your frontend can reach the backend API:

```javascript
// src/config/api.js
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Add to .env file in frontend directory
// VITE_API_URL=http://localhost:8000
```

---

## Step 5: Test the Features

1. **Start the backend:**
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test each feature:**
   - ✅ Type a search query and click "Search"
   - ✅ Click the microphone icon for voice search
   - ✅ Click "Listen to Results" to hear narration
   - ✅ Click speaker icons on individual results
   - ✅ Toggle audio notifications on/off

---

## Advanced: Podcast Generation

Add a "Convert to Podcast" button for long articles:

```jsx
import { useState } from 'react';
import * as audioApi from '../api/audio';

function ArticleView({ title, content }) {
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGeneratePodcast = async () => {
    setIsGenerating(true);
    
    try {
      const audioBlob = await audioApi.generatePodcast(
        title,
        content,
        'Rachel',
        true // add intro
      );
      
      // Download the podcast
      audioApi.downloadAudio(audioBlob, `podcast-${title}.mp3`);
      
      alert('Podcast generated and downloaded!');
    } catch (error) {
      alert('Failed to generate podcast');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <article>
      <h1>{title}</h1>
      
      <button 
        onClick={handleGeneratePodcast}
        disabled={isGenerating}
        className="podcast-btn"
      >
        {isGenerating ? '⏳ Generating...' : '🎙️ Convert to Podcast'}
      </button>
      
      <div className="content">
        {content}
      </div>
    </article>
  );
}
```

---

## Accessibility Checklist

- [ ] All audio controls have ARIA labels
- [ ] Keyboard navigation works for all buttons
- [ ] Visual feedback for loading/playing states
- [ ] Text alternatives always available
- [ ] Audio notifications can be toggled
- [ ] Screen reader compatible
- [ ] High contrast mode supported

---

## Performance Tips

1. **Cache audio for common phrases:**
   ```javascript
   const audioCache = new Map();
   
   async function getCachedAudio(text) {
     if (audioCache.has(text)) {
       return audioCache.get(text);
     }
     
     const audio = await audioApi.textToSpeech(text);
     audioCache.set(text, audio);
     return audio;
   }
   ```

2. **Debounce voice search:**
   ```javascript
   import { useCallback } from 'react';
   import debounce from 'lodash/debounce';
   
   const debouncedSearch = useCallback(
     debounce((query) => performSearch(query), 500),
     []
   );
   ```

3. **Lazy load audio components:**
   ```javascript
   import { lazy, Suspense } from 'react';
   
   const AudioControls = lazy(() => import('./components/AudioControls'));
   
   function Component() {
     return (
       <Suspense fallback={<div>Loading audio...</div>}>
         <AudioControls text="..." />
       </Suspense>
     );
   }
   ```

---

## Troubleshooting

**Issue:** Voice search button doesn't respond
- **Fix:** Ensure you're using HTTPS (microphone requires secure context)

**Issue:** Audio doesn't play
- **Fix:** Check browser console for errors, verify API key is set

**Issue:** Slow audio generation
- **Fix:** Use `optimize_streaming: true` parameter

**Issue:** Narration is robotic
- **Fix:** Try different voices or adjust voice settings

---

## Next Steps

1. Customize voice settings for your brand
2. Add more languages for international users
3. Implement audio playlists for multiple articles
4. Create custom notification sounds
5. Add audio speed controls
6. Integrate with browser's media session API

For complete documentation, see `docs/AUDIO_FEATURES.md`

/**
 * SearchResultsNarrator Component
 * Narrates search results for accessibility
 */

import { useSearchNarration } from '../hooks/useAudio';
import './SearchResultsNarrator.css';

export default function SearchResultsNarrator({ 
  query, 
  results, 
  maxResults = 5,
  voice = 'Rachel',
  className = '' 
}) {
  const { narrateResults, stop, isLoading, isPlaying, error } = useSearchNarration();

  const handleNarrate = () => {
    if (isPlaying) {
      stop();
    } else {
      narrateResults(query, results, maxResults, voice);
    }
  };

  if (!results || results.length === 0) return null;

  return (
    <div className={`search-narrator ${className}`}>
      <button
        onClick={handleNarrate}
        disabled={isLoading}
        className={`narrator-btn ${isPlaying ? 'playing' : ''}`}
        title={isPlaying ? 'Stop narration' : 'Listen to search results'}
        aria-label={isPlaying ? 'Stop search results narration' : 'Play search results narration'}
      >
        {isLoading ? (
          <>
            <span className="narrator-spinner">⏳</span>
            <span className="narrator-text">Loading...</span>
          </>
        ) : isPlaying ? (
          <>
            <span>⏹</span>
            <span className="narrator-text">Stop Narration</span>
          </>
        ) : (
          <>
            <span>🔊</span>
            <span className="narrator-text">Listen to Results</span>
          </>
        )}
      </button>

      {error && (
        <div className="narrator-error" role="alert">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {isPlaying && (
        <div className="narrator-status">
          <span className="status-indicator"></span>
          <span>Narrating {Math.min(results.length, maxResults)} results...</span>
        </div>
      )}
    </div>
  );
}

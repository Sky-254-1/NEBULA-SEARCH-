/**
 * VoiceSearch Component
 * Speech-to-text voice search functionality
 */

import { useEffect } from 'react';
import { useSpeechToText } from '../hooks/useAudio';
import './VoiceSearch.css';

export default function VoiceSearch({ onTranscript, className = '' }) {
  const {
    startRecording,
    stopRecording,
    clearTranscript,
    isRecording,
    isProcessing,
    transcript,
    error
  } = useSpeechToText();

  // Call onTranscript when transcript is ready
  useEffect(() => {
    if (transcript && onTranscript) {
      onTranscript(transcript);
      // Clear after a delay
      setTimeout(clearTranscript, 1000);
    }
  }, [transcript, onTranscript, clearTranscript]);

  const handleToggle = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className={`voice-search ${className}`}>
      <button
        onClick={handleToggle}
        disabled={isProcessing}
        className={`voice-search-btn ${isRecording ? 'recording' : ''}`}
        title={isRecording ? 'Stop recording' : 'Start voice search'}
        aria-label={isRecording ? 'Stop voice recording' : 'Start voice search'}
      >
        {isProcessing ? (
          <span className="voice-spinner">⏳</span>
        ) : isRecording ? (
          <span className="voice-icon-recording">🎤</span>
        ) : (
          <span className="voice-icon">🎤</span>
        )}
      </button>

      {isRecording && (
        <span className="voice-status">Recording...</span>
      )}

      {isProcessing && (
        <span className="voice-status">Processing...</span>
      )}

      {error && (
        <span className="voice-error" role="alert">
          {error}
        </span>
      )}
    </div>
  );
}

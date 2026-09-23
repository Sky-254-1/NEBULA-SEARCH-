/**
 * AudioControls Component
 * Provides text-to-speech controls for any text content
 */

import { useState } from 'react';
import { useTextToSpeech } from '../hooks/useAudio';
import './AudioControls.css';

export default function AudioControls({ text, voice = 'Rachel', className = '' }) {
  const { speak, stop, pause, resume, isLoading, isPlaying, error } = useTextToSpeech();

  const handleSpeak = () => {
    if (isPlaying) {
      pause();
    } else if (text) {
      speak(text, voice);
    }
  };

  const handleStop = () => {
    stop();
  };

  if (!text) return null;

  return (
    <div className={`audio-controls ${className}`}>
      <button
        onClick={handleSpeak}
        disabled={isLoading || !text}
        className="audio-btn audio-btn-play"
        title={isPlaying ? 'Pause' : 'Play audio'}
        aria-label={isPlaying ? 'Pause narration' : 'Play narration'}
      >
        {isLoading ? (
          <span className="audio-spinner">⏳</span>
        ) : isPlaying ? (
          <span>⏸</span>
        ) : (
          <span>🔊</span>
        )}
      </button>

      {isPlaying && (
        <button
          onClick={handleStop}
          className="audio-btn audio-btn-stop"
          title="Stop audio"
          aria-label="Stop narration"
        >
          ⏹
        </button>
      )}

      {error && (
        <span className="audio-error" role="alert">
          {error}
        </span>
      )}
    </div>
  );
}

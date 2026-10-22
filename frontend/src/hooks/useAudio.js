/**
 * Audio React Hooks
 * Custom hooks for audio features
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import * as audioApi from '../api/audio';

/**
 * Hook for text-to-speech functionality
 */
export function useTextToSpeech() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);

  const speak = useCallback(async (text, voice = 'Rachel', autoPlay = true) => {
    setIsLoading(true);
    setError(null);

    try {
      const audioBlob = await audioApi.textToSpeech(text, voice, true);
      
      if (autoPlay) {
        const audio = audioApi.playAudio(audioBlob);
        audioRef.current = audio;
        setIsPlaying(true);

        audio.addEventListener('ended', () => {
          setIsPlaying(false);
        });

        audio.addEventListener('error', (e) => {
          setError('Playback error');
          setIsPlaying(false);
        });
      }

      return audioBlob;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  }, []);

  const pause = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  }, []);

  const resume = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.play();
      setIsPlaying(true);
    }
  }, []);

  return {
    speak,
    stop,
    pause,
    resume,
    isLoading,
    isPlaying,
    error
  };
}

/**
 * Hook for speech-to-text (voice recording)
 */
export function useSpeechToText() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [transcript, setTranscript] = useState('');
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setIsProcessing(true);

        try {
          const result = await audioApi.speechToText(audioBlob);
          setTranscript(result.text);
        } catch (err) {
          setError(err.message);
        } finally {
          setIsProcessing(false);
        }

        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setError(null);
    } catch (err) {
      setError('Microphone access denied');
      console.error('Recording error:', err);
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, [isRecording]);

  const clearTranscript = useCallback(() => {
    setTranscript('');
  }, []);

  return {
    startRecording,
    stopRecording,
    clearTranscript,
    isRecording,
    isProcessing,
    transcript,
    error
  };
}

/**
 * Hook for search results narration
 */
export function useSearchNarration() {
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState(null);
  const audioRef = useRef(null);

  const narrateResults = useCallback(async (query, results, maxResults = 5, voice = 'Rachel') => {
    setIsLoading(true);
    setError(null);

    try {
      const audioBlob = await audioApi.narrateSearchResults(query, results, maxResults, voice);
      const audio = audioApi.playAudio(audioBlob);
      audioRef.current = audio;
      setIsPlaying(true);

      audio.addEventListener('ended', () => {
        setIsPlaying(false);
      });

      audio.addEventListener('error', () => {
        setError('Playback error');
        setIsPlaying(false);
      });

      return audioBlob;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  }, []);

  return {
    narrateResults,
    stop,
    isLoading,
    isPlaying,
    error
  };
}

/**
 * Hook for audio notifications
 */
export function useAudioNotifications() {
  const [isEnabled, setIsEnabled] = useState(() => {
    return localStorage.getItem('audioNotifications') === 'true';
  });

  const notify = useCallback(async (message, type = 'info', voice = 'Rachel') => {
    if (!isEnabled) return;

    try {
      const audioBlob = await audioApi.audioNotification(message, type, voice);
      audioApi.playAudio(audioBlob);
    } catch (err) {
      console.error('Audio notification error:', err);
    }
  }, [isEnabled]);

  const toggle = useCallback(() => {
    setIsEnabled(prev => {
      const newValue = !prev;
      localStorage.setItem('audioNotifications', newValue.toString());
      return newValue;
    });
  }, []);

  return {
    notify,
    toggle,
    isEnabled
  };
}

/**
 * Hook for checking audio service availability
 */
export function useAudioHealth() {
  const [isAvailable, setIsAvailable] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function checkHealth() {
      try {
        const health = await audioApi.checkAudioHealth();
        setIsAvailable(health.available);
      } catch (err) {
        setError(err.message);
        setIsAvailable(false);
      } finally {
        setIsLoading(false);
      }
    }

    checkHealth();
  }, []);

  return { isAvailable, isLoading, error };
}

/**
 * Hook for managing available voices
 */
export function useVoices() {
  const [voices, setVoices] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchVoices() {
      try {
        const data = await audioApi.listVoices();
        setVoices(data.voices || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    }

    fetchVoices();
  }, []);

  return { voices, isLoading, error };
}

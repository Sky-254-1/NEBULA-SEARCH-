/**
 * Audio API Client
 * Interface for ElevenLabs audio features
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Get authentication token from localStorage
 */
function getAuthToken() {
  return localStorage.getItem('token');
}

/**
 * Common fetch with auth headers
 */
async function authFetch(url, options = {}) {
  const token = getAuthToken();
  const headers = {
    ...options.headers,
    'Authorization': token ? `Bearer ${token}` : '',
  };

  const response = await fetch(url, { ...options, headers });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response;
}

/**
 * Check if audio service is available
 */
export async function checkAudioHealth() {
  const response = await authFetch(`${API_BASE}/api/v1/audio/health`);
  return response.json();
}

/**
 * Get list of available voices
 */
export async function listVoices() {
  const response = await authFetch(`${API_BASE}/api/v1/audio/voices`);
  return response.json();
}

/**
 * Convert text to speech
 * @param {string} text - Text to convert
 * @param {string} voice - Voice name (default: "Rachel")
 * @param {boolean} optimizeStreaming - Enable streaming optimization
 * @returns {Promise<Blob>} Audio blob
 */
export async function textToSpeech(text, voice = 'Rachel', optimizeStreaming = false) {
  const response = await authFetch(`${API_BASE}/api/v1/audio/tts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text, voice, optimize_streaming: optimizeStreaming }),
  });
  
  return response.blob();
}

/**
 * Convert text to speech with streaming
 * @param {string} text - Text to convert
 * @param {string} voice - Voice name
 * @returns {Promise<Blob>} Audio blob
 */
export async function textToSpeechStream(text, voice = 'Rachel') {
  const response = await authFetch(`${API_BASE}/api/v1/audio/tts/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text, voice }),
  });
  
  return response.blob();
}

/**
 * Convert speech to text (transcribe audio)
 * @param {File|Blob} audioFile - Audio file to transcribe
 * @param {string} language - Language code (default: "en")
 * @returns {Promise<Object>} Transcription result
 */
export async function speechToText(audioFile, language = 'en') {
  const formData = new FormData();
  formData.append('audio', audioFile);
  formData.append('language', language);
  
  const token = getAuthToken();
  const response = await fetch(`${API_BASE}/api/v1/audio/stt`, {
    method: 'POST',
    headers: {
      'Authorization': token ? `Bearer ${token}` : '',
    },
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Transcription failed' }));
    throw new Error(error.detail);
  }
  
  return response.json();
}

/**
 * Generate audio narration of search results
 * @param {string} query - Search query
 * @param {Array} results - Search results array
 * @param {number} maxResults - Max results to narrate (default: 5)
 * @param {string} voice - Voice name
 * @returns {Promise<Blob>} Audio blob
 */
export async function narrateSearchResults(query, results, maxResults = 5, voice = 'Rachel') {
  const response = await authFetch(`${API_BASE}/api/v1/audio/narrate/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, results, max_results: maxResults, voice }),
  });
  
  return response.blob();
}

/**
 * Generate audio notification
 * @param {string} message - Notification message
 * @param {string} type - Notification type (info, success, warning, error)
 * @param {string} voice - Voice name
 * @returns {Promise<Blob>} Audio blob
 */
export async function audioNotification(message, type = 'info', voice = 'Rachel') {
  const response = await authFetch(`${API_BASE}/api/v1/audio/notification`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, notification_type: type, voice }),
  });
  
  return response.blob();
}

/**
 * Generate custom sound effect
 * @param {string} description - Sound description
 * @param {number} duration - Duration in seconds (0.5-10.0)
 * @returns {Promise<Blob>} Audio blob
 */
export async function generateSoundEffect(description, duration = 2.0) {
  const response = await authFetch(`${API_BASE}/api/v1/audio/sound-effect`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ description, duration }),
  });
  
  return response.blob();
}

/**
 * Generate podcast from content
 * @param {string} title - Podcast title
 * @param {string} content - Podcast content
 * @param {string} voice - Voice name
 * @param {boolean} addIntro - Add intro (default: true)
 * @returns {Promise<Blob>} Audio blob
 */
export async function generatePodcast(title, content, voice = 'Rachel', addIntro = true) {
  const response = await authFetch(`${API_BASE}/api/v1/audio/podcast/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title, content, voice, add_intro: addIntro }),
  });
  
  return response.blob();
}

/**
 * Play audio blob
 * @param {Blob} audioBlob - Audio blob to play
 * @returns {HTMLAudioElement} Audio element
 */
export function playAudio(audioBlob) {
  const audioUrl = URL.createObjectURL(audioBlob);
  const audio = new Audio(audioUrl);
  
  // Clean up URL when audio finishes
  audio.addEventListener('ended', () => {
    URL.revokeObjectURL(audioUrl);
  });
  
  audio.play();
  return audio;
}

/**
 * Download audio blob as file
 * @param {Blob} audioBlob - Audio blob to download
 * @param {string} filename - Filename for download
 */
export function downloadAudio(audioBlob, filename = 'audio.mp3') {
  const url = URL.createObjectURL(audioBlob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

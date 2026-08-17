import { SpeechRecognition } from '@capacitor-community/speech-recognition';

const SUPPORTED_LANGUAGES = [
  'en-US', 'en-GB', 'es-ES', 'fr-FR', 'de-DE', 'it-IT',
  'pt-BR', 'ru-RU', 'zh-CN', 'ja-JP', 'ko-KR', 'hi-IN'
];

/**
 * Start voice search with enhanced error handling and language support.
 * @param language - Optional language code (defaults to 'en-US')
 * @returns Transcribed text or null if failed
 */
export async function startVoiceSearch(language: string = 'en-US'): Promise<string | null> {
  try {
    const available = await SpeechRecognition.available();
    if (!available.available) {
      console.warn('Speech recognition not available on this device');
      return null;
    }

    // Request permissions
    const permissionResult = await SpeechRecognition.requestPermissions();
    if (permissionResult.speechRecognition !== 'granted') {
      console.error('Speech recognition permission denied');
      return null;
    }

    // Start recognition with optimized settings
    const result = await SpeechRecognition.start({
      language: SUPPORTED_LANGUAGES.includes(language) ? language : 'en-US',
      maxResults: 1,
      partialResults: false,
      popup: false,
    });

    if (result.matches && result.matches.length > 0) {
      return result.matches[0].trim();
    }

    console.warn('No speech detected');
    return null;
  } catch (error) {
    console.error('Voice search failed:', error);
    return null;
  }
}

/**
 * Stop voice search listening.
 */
export async function stopVoiceSearch() {
  try {
    await SpeechRecognition.stop();
  } catch (error) {
    console.error('Failed to stop voice search:', error);
  }
}

/**
 * Check if voice search is supported on the device.
 */
export async function isVoiceSearchAvailable(): Promise<boolean> {
  try {
    const available = await SpeechRecognition.available();
    return available.available;
  } catch {
    return false;
  }
}

/**
 * Get list of supported languages for voice search.
 */
export function getSupportedLanguages(): string[] {
  return [...SUPPORTED_LANGUAGES];
}

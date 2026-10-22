import { Preferences } from '@capacitor/preferences';
import { BiometricAuth } from '@capacitor-community/biometric';
import { config } from './config';

const TOKEN_KEY = 'nebula_tokens';
const BIOMETRIC_ENABLED_KEY = 'nebula_biometric_enabled';

export async function saveTokens(tokens: { access_token: string; refresh_token?: string }) {
  await Preferences.set({ key: TOKEN_KEY, value: JSON.stringify(tokens) });
}

export async function loadTokens() {
  const { value } = await Preferences.get({ key: TOKEN_KEY });
  return value ? JSON.parse(value) : null;
}

export async function clearTokens() {
  await Preferences.remove({ key: TOKEN_KEY });
}

export async function restoreSession(apiBase: string) {
  const tokens = await loadTokens();
  if (!tokens?.access_token) return null;
  const res = await fetch(`${apiBase}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${tokens.access_token}` },
  });
  if (!res.ok) {
    await clearTokens();
    return null;
  }
  return await res.json();
}

/**
 * Check if biometric authentication is available on the device.
 */
export async function isBiometricAvailable(): Promise<boolean> {
  try {
    const result = await BiometricAuth.checkBiometric();
    return result.isAvailable && result.biometryType !== 'none';
  } catch {
    return false;
  }
}

/**
 * Check if user has enabled biometric login.
 */
export async function isBiometricEnabled(): Promise<boolean> {
  const { value } = await Preferences.get({ key: BIOMETRIC_ENABLED_KEY });
  return value === 'true';
}

/**
 * Enable biometric authentication for the app.
 */
export async function enableBiometric(): Promise<void> {
  await Preferences.set({ key: BIOMETRIC_ENABLED_KEY, value: 'true' });
}

/**
 * Disable biometric authentication.
 */
export async function disableBiometric(): Promise<void> {
  await Preferences.remove({ key: BIOMETRIC_ENABLED_KEY });
}

/**
 * Authenticate with biometrics and return stored tokens.
 */
export async function authenticateWithBiometric(): Promise<{ access_token: string; refresh_token?: string } | null> {
  try {
    // Trigger biometric prompt
    const result = await BiometricAuth.authenticate({
      reason: 'Authenticate to access Nebula Search',
      title: 'Biometric Login',
      subtitle: 'Use your fingerprint or face to login',
    });

    if (result.success) {
      const tokens = await loadTokens();
      if (tokens?.access_token) {
        return tokens;
      }
    }
    return null;
  } catch (error) {
    console.error('Biometric authentication failed:', error);
    return null;
  }
}

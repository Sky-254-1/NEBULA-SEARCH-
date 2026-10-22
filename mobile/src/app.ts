import { App } from '@capacitor/app';
import { PushNotifications } from '@capacitor/push-notifications';
import { config, isNative } from './config';
import { restoreSession } from './auth';
import { flushQueue } from '../sync/queue';
import { isOnline } from '../plugins/native';

export async function initMobileShell() {
  if (!isNative) return;

  const user = await restoreSession(config.apiBase);
  if (user && (await isOnline())) {
    const { loadTokens } = await import('./auth');
    const tokens = await loadTokens();
    if (tokens?.access_token) {
      await flushQueue(config.apiBase, tokens.access_token);
    }
  }

  await PushNotifications.requestPermissions();
  await PushNotifications.register();

  App.addListener('appStateChange', async ({ isActive }) => {
    if (isActive && (await isOnline())) {
      const { loadTokens } = await import('./auth');
      const tokens = await loadTokens();
      if (tokens?.access_token) {
        await flushQueue(config.apiBase, tokens.access_token);
      }
    }
  });
}

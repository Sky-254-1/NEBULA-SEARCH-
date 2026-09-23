import { useEffect, useState } from 'react';

export function useInstallPrompt() {
  const [prompt, setPrompt] = useState(null);
  const [installed, setInstalled] = useState(false);

  useEffect(() => {
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setInstalled(true);
      return;
    }

    function handleBeforeInstall(e) {
      e.preventDefault();
      setPrompt(e);
    }

    function handleInstalled() {
      setInstalled(true);
      setPrompt(null);
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstall);
    window.addEventListener('appinstalled', handleInstalled);
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
      window.removeEventListener('appinstalled', handleInstalled);
    };
  }, []);

  async function install() {
    if (!prompt) return false;
    prompt.prompt();
    const { outcome } = await prompt.userChoice;
    setPrompt(null);
    return outcome === 'accepted';
  }

  return { canInstall: Boolean(prompt), installed, install };
}

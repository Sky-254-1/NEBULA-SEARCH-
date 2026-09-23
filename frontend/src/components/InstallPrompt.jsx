export function InstallPrompt({ canInstall, onInstall, onDismiss }) {
  if (!canInstall) return null;

  return (
    <div className="install-banner" role="region" aria-label="Install app">
      <p>Install Nebula Search for offline access and a native app experience.</p>
      <div className="install-actions">
        <button type="button" className="btn primary" onClick={onInstall}>
          Install
        </button>
        <button type="button" className="btn ghost" onClick={onDismiss}>
          Not now
        </button>
      </div>
    </div>
  );
}

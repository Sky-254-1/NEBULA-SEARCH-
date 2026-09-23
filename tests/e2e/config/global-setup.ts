async function globalSetup() {
  const apiURL = process.env.E2E_API_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${apiURL}/health`);
    if (!res.ok) {
      console.warn(`API health check failed: ${res.status}`);
    }
  } catch {
    console.warn('API not reachable during global setup — tests may fail if servers are not running');
  }
}

export default globalSetup;

export const env = {
  baseURL: process.env.E2E_BASE_URL || 'http://localhost:5173',
  apiURL: process.env.E2E_API_URL || 'http://localhost:8000',
  defaultPassword: 'e2e_secret123',
  timeout: 30000,
};

import { createAuthedFetch } from './base';
import { createAuthApi } from './auth';
import { createSearchApi } from './search';
import { createAiApi } from './ai';

export { ApiError } from './base';

export function buildClient(getTokens, setTokens, clearTokens) {
  const authedFetch = createAuthedFetch(getTokens, setTokens, clearTokens);
  return {
    ...createAuthApi(authedFetch, setTokens, getTokens, clearTokens),
    ...createSearchApi(authedFetch),
    ...createAiApi(authedFetch, getTokens, setTokens),
    health: () => fetch('/health').then((r) => r.json()),
  };
}

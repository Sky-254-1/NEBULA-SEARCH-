import { describe, expect, it } from 'vitest';
import { normalizeApiPath } from '../src/api/client.ts';

describe('API path compatibility', () => {
  it('adds the v1 prefix for shorthand paths used by the client', () => {
    expect(normalizeApiPath('/auth/login')).toBe('/api/v1/auth/login');
    expect(normalizeApiPath('/documents')).toBe('/api/v1/documents');
  });

  it('preserves explicit v1 paths without duplicating the base prefix', () => {
    expect(normalizeApiPath('/api/v1/search/history')).toBe('/api/v1/search/history');
  });

  it('maps v2 shorthand and preserves fully qualified versioned paths', () => {
    expect(normalizeApiPath('/v2/search/')).toBe('/api/v2/search/');
    expect(normalizeApiPath('/api/v2/search/')).toBe('/api/v2/search/');
  });
});

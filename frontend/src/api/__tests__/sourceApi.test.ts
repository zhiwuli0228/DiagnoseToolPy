import { describe, it, expect, afterEach } from 'vitest';
import { server } from '../../mocks/server';
import { http, HttpResponse } from 'msw';
import { checkSourceDirectory, scanSourceDirectory } from '../sourceApi';

describe('sourceApi', () => {
  afterEach(() => server.resetHandlers());

  describe('checkSourceDirectory', () => {
    it('returns allowed=true for valid path', async () => {
      const result = await checkSourceDirectory('/data/logs');
      expect(result.allowed).toBe(true);
      expect(result.path).toBe('/data/logs');
      expect(result.name).toBe('mylogs');
    });

    it('returns allowed=false for forbidden path', async () => {
      server.use(
        http.post('/api/source/check', () => HttpResponse.json({ allowed: false, path: '/etc', name: '' }))
      );
      const result = await checkSourceDirectory('/etc');
      expect(result.allowed).toBe(false);
    });
  });

  describe('scanSourceDirectory', () => {
    it('returns scan result with file counts', async () => {
      const result = await scanSourceDirectory('/data/logs');
      expect(result.total_files).toBe(42);
      expect(result.total_bytes).toBe(1234567);
      expect(result.file_types).toHaveProperty('.log');
      expect(result.error_count).toBe(3);
      expect(result.warn_count).toBe(7);
    });

    it('throws error on scan failure', async () => {
      server.use(
        http.post('/api/source/scan', () => HttpResponse.json({ detail: 'Access denied' }, { status: 403 }))
      );
      await expect(scanSourceDirectory('/restricted')).rejects.toThrow();
    });
  });
});

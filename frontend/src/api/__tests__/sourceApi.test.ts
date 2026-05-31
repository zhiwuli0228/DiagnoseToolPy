import { describe, it, expect, afterEach } from 'vitest';
import { server } from '../../mocks/server';
import { http, HttpResponse } from 'msw';
import { checkSourceDirectory, scanSourceDirectory, deleteTempDir } from '../sourceApi';

describe('sourceApi', () => {
  afterEach(() => server.resetHandlers());

  describe('checkSourceDirectory', () => {
    it('returns allowed=true for valid path', async () => {
      const result = await checkSourceDirectory('/data/logs');
      expect(result.allowed).toBe(true);
      expect(result.path).toBe('/data/logs');
      expect(result.name).toBe('mylogs');
      expect(result.is_zip).toBe(false);
    });

    it('returns allowed=false for forbidden path', async () => {
      server.use(
        http.post('/api/source/check', () => HttpResponse.json({ allowed: false, path: '/etc', name: '' }))
      );
      const result = await checkSourceDirectory('/etc');
      expect(result.allowed).toBe(false);
    });

    it('detects ZIP file and returns is_zip=true', async () => {
      const result = await checkSourceDirectory('/data/logs.zip');
      expect(result.allowed).toBe(true);
      expect(result.is_zip).toBe(true);
      expect(result.name).toBe('logs.zip');
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

    it('returns extracted_path and zip_task_id for ZIP files', async () => {
      const result = await scanSourceDirectory('/data/logs.zip');
      expect(result.total_files).toBe(2);
      expect(result.extracted_path).toBe('/data/temp/zip-abc123/logs');
      expect(result.zip_task_id).toBe('abc123');
    });
  });

  describe('deleteTempDir', () => {
    it('deletes temp directory and returns success', async () => {
      const result = await deleteTempDir('abc123');
      expect(result.status).toBe('cleaned');
      expect(result.task_id).toBe('abc123');
    });

    it('throws error when temp directory not found', async () => {
      server.use(
        http.delete('/api/source/temp/:taskId', () => HttpResponse.json({ detail: 'Temp directory not found' }, { status: 404 }))
      );
      await expect(deleteTempDir('nonexistent')).rejects.toThrow();
    });
  });
});

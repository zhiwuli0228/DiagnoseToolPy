import { describe, it, expect, afterEach } from 'vitest';
import { server } from '../../mocks/server';
import { http, HttpResponse } from 'msw';
import { listCases, getCase, getHealth } from '../caseApi';

describe('caseApi', () => {
  afterEach(() => {
    server.resetHandlers();
  });

  describe('getHealth', () => {
    it('returns health response', async () => {
      const result = await getHealth();
      expect(result.status).toBe('ok');
      expect(result.app).toBe('DiagnoseToolPy');
    });
  });

  describe('listCases', () => {
    it('returns list of cases', async () => {
      const result = await listCases();
      expect(Array.isArray(result)).toBe(true);
    });
  });

  describe('getCase', () => {
    it('returns null for any caseId (stub)', async () => {
      const result = await getCase('CASE-001');
      expect(result).toBeNull();
    });
  });
});

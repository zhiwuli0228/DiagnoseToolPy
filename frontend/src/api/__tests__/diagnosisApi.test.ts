import { describe, it, expect, afterEach } from 'vitest';
import { server } from '../../mocks/server';
import { http, HttpResponse } from 'msw';
import { diagnose } from '../diagnosisApi';

describe('diagnosisApi', () => {
  afterEach(() => server.resetHandlers());

  it('returns diagnosis result for valid taskId', async () => {
    const result = await diagnose('task-001');
    expect(result.case_id).toBe('task-001');
    expect(typeof result.diagnosis).toBe('string');
    expect(result.diagnosis.length).toBeGreaterThan(0);
  });

  it('throws error on HTTP error response', async () => {
    server.use(
      http.post('/api/diagnosis', () => HttpResponse.json({ detail: 'Task not found' }, { status: 404 }))
    );
    await expect(diagnose('nonexistent')).rejects.toThrow('Task not found');
  });
});

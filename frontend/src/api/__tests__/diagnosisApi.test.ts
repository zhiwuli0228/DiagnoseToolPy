import { describe, it, expect, afterEach } from 'vitest';
import { server } from '../../mocks/server';
import { http, HttpResponse } from 'msw';
import { diagnose, exportBugfixPrompt } from '../diagnosisApi';

describe('diagnosisApi', () => {
  afterEach(() => server.resetHandlers());

  it('returns diagnosis result for valid taskId', async () => {
    const result = await diagnose('task-001') as { case_id: string; diagnosis: string };
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

  it('exports bugfix prompt for valid taskId', async () => {
    server.use(
      http.post('/api/diagnosis/export-bugfix-prompt', async ({ request }) => {
        const body = await request.json() as { task_id: string };
        return HttpResponse.json({
          success: true,
          task_id: body.task_id,
          output_path: `data/output/${body.task_id}/bugfix-prompt.md`,
          prompt: '# Bugfix Prompt\n\nTask summary',
        });
      })
    );

    const result = await exportBugfixPrompt({ task_id: 'task-001' });
    expect(result.success).toBe(true);
    expect(result.task_id).toBe('task-001');
    expect(result.output_path).toBe('data/output/task-001/bugfix-prompt.md');
    expect(result.prompt).toContain('Bugfix Prompt');
  });
});

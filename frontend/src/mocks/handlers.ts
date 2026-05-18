import { http, HttpResponse } from 'msw';

export const handlers = [
  // health
  http.get('/api/health', () =>
    HttpResponse.json({ status: 'ok', app: 'DiagnoseToolPy' })
  ),

  // case APIs
  http.get('/api/cases', () =>
    HttpResponse.json([
      { case_id: 'CASE-001', title: 'DB Connection Timeout' },
      { case_id: 'CASE-002', title: 'NullPointer at OrderService' },
    ])
  ),
  http.get('/api/cases/:caseId', ({ params }) =>
    HttpResponse.json({ case_id: params.caseId, title: 'Test Case' })
  ),

  // diagnosis API
  http.post('/api/diagnosis', async ({ request }) => {
    const body = await request.json() as { task_id: string };
    if (!body.task_id) {
      return HttpResponse.json({ detail: 'task_id required' }, { status: 400 });
    }
    return HttpResponse.json({
      case_id: body.task_id,
      diagnosis: 'Database connection pool exhausted.',
    });
  }),

  // source APIs
  http.post('/api/source/check', async ({ request }) => {
    const body = await request.json() as { path: string };
    return HttpResponse.json({ allowed: true, path: body.path, name: 'mylogs' });
  }),
  http.post('/api/source/scan', async ({ request }) => {
    const body = await request.json() as { path: string };
    return HttpResponse.json({
      total_files: 42,
      total_bytes: 1234567,
      file_types: { '.log': 30, '.txt': 10, '.gz': 2 },
      error_count: 3,
      warn_count: 7,
    });
  }),
];

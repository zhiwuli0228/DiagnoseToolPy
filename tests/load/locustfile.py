"""Locust scenario for DiagnoseToolPy.

Mixes frontend HTML hits with backend API hits to mimic a real user
browsing cases and config while the dashboard pings /health.

Endpoint notes:
- /health is the real health probe (FastAPI root scope, not /api/...)
- /api/config is a GET-only list-style endpoint
- / serves the SPA HTML root
- Other read-only list endpoints (e.g. /api/diagnosis/check-result)
  require query params, so they are excluded to keep the run clean.
"""

from locust import HttpUser, task, between


class DiagnoseUser(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def get_health(self) -> None:
        self.client.get("/health", name="GET /health")

    @task(3)
    def get_config(self) -> None:
        self.client.get("/api/config", name="GET /api/config")

    @task(2)
    def get_index(self) -> None:
        # Frontend HTML root (after dev server is up at :5173 in dev;
        # in standalone test, hit the FastAPI server's /)
        self.client.get("/", name="GET /")

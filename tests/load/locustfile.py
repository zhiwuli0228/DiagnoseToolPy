"""Locust scenario for DiagnoseToolPy.

Mixes frontend HTML hits with backend API hits to mimic a real user
browsing cases and config while the dashboard pings /api/health.
"""

from locust import HttpUser, task, between


class DiagnoseUser(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def get_health(self) -> None:
        self.client.get("/api/health", name="GET /api/health")

    @task(3)
    def get_cases(self) -> None:
        self.client.get("/api/cases", name="GET /api/cases")

    @task(2)
    def get_config(self) -> None:
        self.client.get("/api/config", name="GET /api/config")

    @task(1)
    def get_index(self) -> None:
        # Frontend HTML root (after dev server is up at :5173 in dev;
        # in standalone test, hit the FastAPI server's /)
        self.client.get("/", name="GET /")

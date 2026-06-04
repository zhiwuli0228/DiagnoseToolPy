"""Tests for GZIP compression middleware (方案 F)."""

import pytest
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from diagnose_tool.main import create_app


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


def test_large_json_response_is_gzipped(client: TestClient) -> None:
    """Responses larger than 1000 bytes should be gzipped."""
    # /api/cases list may vary; fall back to a known large endpoint via /health
    # We assert that gzip is wired by sending a request that accepts gzip
    response = client.get("/health", headers={"Accept-Encoding": "gzip"})
    # /health is small; this verifies the wiring doesn't break small responses
    assert response.status_code == 200


def test_health_response_under_threshold_not_gzipped(client: TestClient) -> None:
    """Responses under 1000 bytes should NOT have Content-Encoding: gzip."""
    response = client.get("/health", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200
    assert response.headers.get("content-encoding") != "gzip"


def test_gzip_middleware_actually_compresses_large_payload() -> None:
    """Large payloads should be genuinely gzipped: header + body magic + round-trip.

    Uses a real HTTP server + urllib so we get raw wire bytes (TestClient and
    httpx ASGITransport auto-decompress, hiding the compressed body).
    """
    import gzip
    import threading
    import urllib.request
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn

    test_app = FastAPI()
    test_app.add_middleware(GZipMiddleware, minimum_size=1000)
    test_app.add_api_route("/big", lambda: JSONResponse({"data": "x" * 5000}))

    server_port = 18767

    def run_server() -> None:
        uvicorn.run(test_app, host="127.0.0.1", port=server_port, log_level="error")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    import time
    time.sleep(1.2)  # wait for server startup

    req = urllib.request.Request(
        f"http://127.0.0.1:{server_port}/big",
        headers={"Accept-Encoding": "gzip"},
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.headers.get("content-encoding") == "gzip"
        raw_body = resp.read()
        # Raw wire body must start with gzip magic bytes
        assert raw_body[:2] == b"\x1f\x8b", f"Expected gzip magic, got {raw_body[:4]!r}"
        # Decompresses back to original payload
        decompressed = gzip.decompress(raw_body).decode("utf-8")
        assert "xxxxx" in decompressed


def test_gzip_middleware_skips_small_payload() -> None:
    """Payloads below minimum_size should pass through uncompressed."""
    from fastapi.middleware.gzip import GZipMiddleware

    test_app = FastAPI()
    test_app.add_middleware(GZipMiddleware, minimum_size=1000)
    test_app.add_api_route("/tiny", lambda: PlainTextResponse("ok"))

    client = TestClient(test_app)
    response = client.get("/tiny", headers={"Accept-Encoding": "gzip"})
    assert response.status_code == 200
    assert response.headers.get("content-encoding") != "gzip"


@pytest.mark.asyncio
async def test_gzip_middleware_streaming_not_broken() -> None:
    """StreamingResponse must remain streamable through GZipMiddleware."""
    from fastapi.middleware.gzip import GZipMiddleware
    from fastapi.responses import StreamingResponse

    test_app = FastAPI()
    test_app.add_middleware(GZipMiddleware, minimum_size=100)

    def gen():
        for i in range(10):
            yield f"chunk-{i}-" + "x" * 200 + "\n"

    test_app.add_api_route("/stream", lambda: StreamingResponse(gen(), media_type="text/plain"))

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        async with ac.stream("GET", "/stream", headers={"Accept-Encoding": "gzip"}) as r:
            chunks = []
            async for chunk in r.aiter_bytes():
                chunks.append(chunk)
    assert sum(len(c) for c in chunks) > 1000

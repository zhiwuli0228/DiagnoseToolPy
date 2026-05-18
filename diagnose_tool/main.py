"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from diagnose_tool.api.routes_case import router as case_router
from diagnose_tool.api.routes_diagnosis import router as diagnosis_router
from diagnose_tool.api.routes_source import router as source_router
from diagnose_tool.core.config import load_config


def create_app() -> FastAPI:
    """Create the DiagnoseToolPy FastAPI application."""

    config = load_config()
    app = FastAPI(title=config.name, version=config.version)
    app.include_router(source_router)
    app.include_router(case_router)
    app.include_router(diagnosis_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "app": config.name}

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>DiagnoseToolPy</title>
  </head>
  <body>
    <main>
      <h1>DiagnoseToolPy</h1>
      <p>Lightweight Web-based diagnostic assistant for system stability work.</p>
    </main>
  </body>
</html>
""".strip()

    return app


app = create_app()

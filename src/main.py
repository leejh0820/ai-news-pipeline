from __future__ import annotations

import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException, status

from .models import PreprocessRequest, PreprocessResponse
from .preprocessing import preprocess_items

app = FastAPI(
    title="AI News Preprocessing Service",
    version="0.1.0",
    description="Deterministic preprocessing layer for the Daily Tech Radar pipeline.",
)


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("PIPELINE_API_KEY")
    if not expected:
        return

    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/preprocess",
    response_model=PreprocessResponse,
    dependencies=[Depends(verify_api_key)],
)
def preprocess(request: PreprocessRequest) -> PreprocessResponse:
    return preprocess_items(request.items, request.config)

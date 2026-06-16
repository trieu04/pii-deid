import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from typing import Any

from src.config import Config, get_config
from src.processing.json_processor import deidentify_json
from src.pseudonym.mapper import cache_size


router = APIRouter(prefix="/deidentify", tags=["deidentify"])


class DeidentifyRequest(BaseModel):
    data: Any
    options: dict = {}


class DeidentifyResponse(BaseModel):
    success: bool
    data: Any
    meta: dict = {}


@router.post("", response_model=DeidentifyResponse)
def deidentify(req: DeidentifyRequest, config: Config = Depends(get_config)) -> DeidentifyResponse:
    result, stats = deidentify_json(req.data, config)
    return DeidentifyResponse(
        success=True,
        data=result,
        meta={
            "entities_found": stats.entities_found,
            "processing_ms": round(stats.processing_ms, 2),
        },
    )


@router.post("/proxy", response_model=DeidentifyResponse)
async def deidentify_proxy(
    req: DeidentifyRequest,
    x_api_key: str = Header(..., alias="x-api-key"),
    config: Config = Depends(get_config),
) -> DeidentifyResponse:
    if not config.upstream_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Proxy not configured: upstream_url is empty",
        )

    headers = {
        "accept": "*/*",
        "Content-Type": "application/json",
        "x-api-key": x_api_key,
    }

    try:
        async with httpx.AsyncClient(timeout=config.upstream_timeout) as client:
            resp = await client.post(config.upstream_url, headers=headers, json=req.data)
            resp.raise_for_status()
            upstream_data = resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Upstream returned an error")
    except httpx.RequestError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Upstream request failed")

    result, stats = deidentify_json(upstream_data, config)
    return DeidentifyResponse(
        success=True,
        data=result,
        meta={
            "entities_found": stats.entities_found,
            "processing_ms": round(stats.processing_ms, 2),
        },
    )


@router.get("/stats")
def stats() -> dict:
    return {"cache_size": cache_size()}

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx

from ..config import settings


class TargetAPIError(RuntimeError):
    """Raised when the ticket target API call fails."""


def _build_url() -> str:
    base = settings.target_api_base_url
    if base is None:
        raise TargetAPIError("Target API base URL is not configured")
    base_with_slash = base if base.endswith("/") else f"{base}/"
    return urljoin(base_with_slash, settings.target_api_tickets_path.lstrip("/"))


async def submit_ticket(payload: dict[str, Any]) -> dict[str, Any] | Any:
    url = _build_url()

    headers = {"Content-Type": "application/json"}
    if settings.target_api_token:
        headers["Authorization"] = f"Bearer {settings.target_api_token}"

    async with httpx.AsyncClient(timeout=settings.target_timeout_seconds) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:  # noqa: BLE001
            raise TargetAPIError(f"Target API request failed: {exc}") from exc

    if response.headers.get("content-type", "").startswith("application/json"):
        try:
            return response.json()
        except ValueError as exc:  # noqa: B904
            raise TargetAPIError("Target API responded mit invalidem JSON") from exc

    return {"status_code": response.status_code, "content": response.text}

"""HTTP client for the Skills Catalog API."""
from __future__ import annotations

import click
import httpx


class CatalogClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(base_url=self.base_url, timeout=30.0)

    def _get(self, path: str, **params: str) -> httpx.Response:
        try:
            resp = self._http.get(path, params=params)
        except httpx.ConnectError:
            raise click.ClickException(
                f"Cannot connect to catalog at {self.base_url}. "
                "Is the server running?"
            )
        if resp.status_code == 404:
            return resp  # let caller handle
        if resp.status_code >= 400:
            raise click.ClickException(
                f"API error {resp.status_code}: {resp.text[:200]}"
            )
        return resp

    def get_item(self, name: str) -> dict | None:
        resp = self._get(f"/api/v1/items/{name}")
        if resp.status_code == 404:
            return None
        return resp.json()

    def get_raw(self, name: str) -> str | None:
        resp = self._get(f"/api/v1/items/{name}/raw")
        if resp.status_code == 404:
            return None
        return resp.text

    def get_bundle(self, names: list[str]) -> dict:
        resp = self._get("/api/v1/items/bundle", items=",".join(names))
        try:
            data = resp.json()
        except Exception:
            raise click.ClickException(
                f"Unexpected response from {self.base_url}/api/v1/items/bundle — "
                "is the catalog server up-to-date?"
            )
        return data

    def search(self, query: str, **kwargs: str) -> dict:
        resp = self._get("/api/v1/items/search", q=query, **kwargs)
        return resp.json()

    def list_items(self, **kwargs: str) -> dict:
        resp = self._get("/api/v1/items", **kwargs)
        return resp.json()

    def close(self) -> None:
        self._http.close()

from typing import Any, cast

import httpx

from .types import Body, Headers, Query, Timeout
from .utils.logging import setup_logging

logger = setup_logging(__name__)


class SyncAPIClient:
    _client: httpx.Client

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        timeout: Timeout = 30.0,
        http_client: httpx.Client | None = None,
        custom_headers: Headers | None = None,
    ) -> None:
        if http_client is not None:
            self._client = http_client
        else:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            if api_key:
                headers["x-api-key"] = api_key
            if custom_headers:
                headers.update(custom_headers)

            self._client = httpx.Client(
                base_url=base_url,
                headers=headers,
                timeout=timeout,
            )

    def request(
        self,
        method: str,
        path: str,
        *,
        content: Any = None,
        data: Any = None,
        files: Any = None,
        json: Body | None = None,
        params: Query | None = None,
        headers: Headers | None = None,
        timeout: Timeout = None,
    ) -> httpx.Response:
        kwargs = {
            "json": json,
            "params": params,
        }
        if content is not None:
            kwargs["content"] = content
        if data is not None:
            kwargs["data"] = data
        if files is not None:
            kwargs["files"] = files
        if headers is not None:
            kwargs["headers"] = headers
        if timeout is not None:
            kwargs["timeout"] = timeout

        return self._client.request(
            method=method,
            url=path,
            **cast(Any, kwargs),
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if hasattr(self, "_client"):
            try:
                self._client.close()
                logger.info("HTTP client closed.")
            except Exception as e:
                logger.error(f"Error closing HTTP client: {e}", exc_info=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class AsyncAPIClient:
    _client: httpx.AsyncClient

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        timeout: Timeout = 30.0,
        http_client: httpx.AsyncClient | None = None,
        custom_headers: Headers | None = None,
    ) -> None:
        if http_client is not None:
            self._client = http_client
        else:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            if api_key:
                headers["x-api-key"] = api_key
            if custom_headers:
                headers.update(custom_headers)

            self._client = httpx.AsyncClient(
                base_url=base_url,
                headers=headers,
                timeout=timeout,
            )

    async def request(
        self,
        method: str,
        path: str,
        *,
        content: Any = None,
        data: Any = None,
        files: Any = None,
        json: Body | None = None,
        params: Query | None = None,
        headers: Headers | None = None,
        timeout: Timeout = None,
    ) -> httpx.Response:
        kwargs = {
            "json": json,
            "params": params,
        }
        if content is not None:
            kwargs["content"] = content
        if data is not None:
            kwargs["data"] = data
        if files is not None:
            kwargs["files"] = files
        if headers is not None:
            kwargs["headers"] = headers
        if timeout is not None:
            kwargs["timeout"] = timeout

        return await self._client.request(
            method=method,
            url=path,
            **cast(Any, kwargs),
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if hasattr(self, "_client"):
            try:
                await self._client.aclose()
                logger.info("Async HTTP client closed.")
            except Exception as e:
                logger.error(f"Error closing Async HTTP client: {e}", exc_info=True)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

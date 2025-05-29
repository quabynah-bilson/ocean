from typing import AsyncGenerator, Any, Optional

from httpx import HTTPError, HTTPStatusError
from loguru import logger

from port_ocean.context.ocean import ocean
from port_ocean.exceptions.base import BaseOceanException
from port_ocean.utils import http_async_client
from port_ocean.utils.cache import cache_iterator_result
from .constants import DEFAULT_PAGE_SIZE
from .rate_limiter import (
    RollingWindowLimiter,
    GitHubRateLimiter,
)

RATE_LIMITER: RollingWindowLimiter = RollingWindowLimiter(
    limit=GitHubRateLimiter.LIMIT,
    window=GitHubRateLimiter.WINDOW_TTL,
)


class IntegrationClient:
    def __init__(self):
        logger.info("Initializing integration client")

        # http client setup
        self._client = http_async_client

        # config setup
        self.base_url = ocean.integration_config["base_url"]
        self._access_token = ocean.integration_config.get("personal_access_token", None)
        self._user_agent = ocean.integration_config.get("user_agent", None)

        if self._access_token is None:
            raise BaseOceanException("Provide valid GitHub personal access token")

        if self._user_agent is None:
            raise BaseOceanException("Provide valid GitHub username as User-Agent")

        # configure headers for an http client
        self._headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._access_token}",
            "User-Agent": f"{self._user_agent}",
        }
        self._client.headers.update(self._headers)

    async def _send_api_request(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        method: str = "GET",
    ) -> list[dict[str, Any]]:
        """Send a request to Bitbucket v2 API with error handling."""
        logger.info(f"Sending request to {url}")

        try:
            response = await self._client.request(
                method=method, url=url, params=params, json=json_data
            )
            logger.info(f"Response from API: {response}")
            response.raise_for_status()
            return response.json()

        except HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(
                    f"Requested resource not found: {url}; message: {str(e)}"
                )
                return []
            logger.error(f"API error: {str(e)}")
            raise e

        except HTTPError as e:
            logger.error(f"Failed to send {method} request to url {url}: {str(e)}")
            raise e

    async def _fetch_data(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        method: str = "GET",
    ) -> AsyncGenerator[list[dict[str, Any]], None]:
        """handles HTTP calls to the API server"""
        page = 1

        if params is None:
            params = {
                "per_page": DEFAULT_PAGE_SIZE,
                "page": page,
                "sort": "asc",
            }

        while True:
            async with RATE_LIMITER:
                try:
                    logger.info(f"Fetching page {params.get("page")}")
                    response = await self._send_api_request(
                        method=method, url=url, params=params
                    )
                    logger.info(f"Fetched {len(response)} data from {url}")
                    yield response

                    if len(response) < DEFAULT_PAGE_SIZE:
                        logger.info(f"No more data from {url}")
                        break  # end of page reached

                    # update the params to fetch from the next page, if available
                    params = {
                        "per_page": DEFAULT_PAGE_SIZE,
                        "page": page + 1,
                        "sort": "asc",
                    }
                except BaseException as e:
                    logger.error(f"An error occurred while fetching {url}: {e}")
                    yield []
                    break

    @cache_iterator_result()
    async def get_repositories(self) -> AsyncGenerator[list[dict[str, Any]], None]:
        async for repos in self._fetch_data(f"{self.base_url}/user/repos"):
            yield repos

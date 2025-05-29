from typing import AsyncGenerator, Any, Optional

from httpx import HTTPError, HTTPStatusError
from loguru import logger

from port_ocean.context.ocean import ocean
from port_ocean.utils import http_async_client
from port_ocean.utils.cache import cache_iterator_result
from .auth import AuthClient
from .rate_limiter import (
    RollingWindowLimiter,
    GitHubRateLimiter,
)

# constants
DEFAULT_PAGE_SIZE = 100

# rate limiter
RATE_LIMITER: RollingWindowLimiter = RollingWindowLimiter(
    limit=GitHubRateLimiter.LIMIT,
    window=GitHubRateLimiter.WINDOW_TTL,
)


class IntegrationClient:
    def __init__(self, auth_client: AuthClient):
        logger.info("Initializing integration client")

        # configure base url
        self.base_url = ocean.integration_config["base_url"]

        # http client setup
        self._client = http_async_client
        self._auth_client = auth_client

        # configure headers for an http client
        self._client.headers.update(self._auth_client.get_headers())

    async def _send_api_request(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        method: str = "GET",
        values_key: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Send a request to Bitbucket v2 API with error handling."""
        logger.info(f"Sending request to {url}")

        try:
            response = await self._client.request(
                method=method, url=url, params=params, json=json_data
            )
            logger.info(f"Response from API: {response}")
            response.raise_for_status()
            if values_key is not None:
                return response.json().get(values_key, [])
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
        values_key: Optional[str] = None,
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
                        method=method, url=url, params=params, values_key=values_key
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
        """get all repos for the current user"""
        async for repos in self._fetch_data(f"{self.base_url}/user/repos"):
            yield repos

    @cache_iterator_result()
    async def get_issues(
        self,
        repo_slug: str,
    ) -> AsyncGenerator[list[dict[str, Any]], None]:
        """get all issues for a repo"""
        params = {
            "per_page": DEFAULT_PAGE_SIZE,
            "page": 1,
            "sort": "updated",
        }
        async for issues in self._fetch_data(
            f"{self.base_url}/repos/{self._auth_client.get_user_agent()}/{repo_slug}/issues",
            params=params,
        ):
            yield issues

    @cache_iterator_result()
    async def get_workflows(
        self,
        repo_slug: str,
    ) -> AsyncGenerator[list[dict[str, Any]], None]:
        """get all workflows for a repo"""
        async for workflows in self._fetch_data(
            f"{self.base_url}/repos/{self._auth_client.get_user_agent()}/{repo_slug}/actions/workflows",
            values_key="workflows",
        ):
            logger.info(f"Found {len(workflows)} workflows for {repo_slug}")
            yield workflows

    @cache_iterator_result()
    async def get_teams(self) -> AsyncGenerator[list[dict[str, Any]], None]:
        """get all teams for the current user"""
        async for teams in self._fetch_data(f"{self.base_url}/user/teams"):
            logger.info(f"Found {len(teams)} teams for current user")
            yield teams

    @cache_iterator_result()
    async def get_pull_requests(
        self,
        repo_slug: str,
    ) -> AsyncGenerator[list[dict[str, Any]], None]:
        """get pull requests for a repo"""
        async for prs in self._fetch_data(
            f"{self.base_url}/repos/{self._auth_client.get_user_agent()}/{repo_slug}/pulls"
        ):
            logger.info(f"Found {len(prs)} prs for {repo_slug}")
            yield prs

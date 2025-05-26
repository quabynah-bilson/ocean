import base64
from typing import AsyncGenerator, Any, Optional, cast

from httpx import HTTPError, HTTPStatusError
from loguru import logger
from typing_extensions import Buffer

from port_ocean.context.ocean import ocean
from port_ocean.exceptions.base import BaseOceanException
from port_ocean.utils import http_async_client
from port_ocean.utils.cache import cache_iterator_result
from .utils.rate_limiter import RollingWindowLimiter, BitbucketRateLimiter

# API constants
PREFERRED_PR_STATE = "OPEN"
DEFAULT_PAGE_SIZE = 10

RATE_LIMITER: RollingWindowLimiter = RollingWindowLimiter(
    limit=BitbucketRateLimiter.LIMIT,
    window=BitbucketRateLimiter.WINDOW_TTL,
)


class BitbucketIntegrationClient:
    """
    BitBucket integration client
    Handles authentication and API calls to BitBucket
    """

    def __init__(self):
        logger.info("Initializing BitBucket Client")

        # http client
        self.client = http_async_client

        # get credentials
        self.base_url = ocean.integration_config["bitbucket_host_url"]
        self.username = ocean.integration_config.get("bitbucket_username", None)
        self.password = ocean.integration_config.get("bitbucket_app_password", None)
        self.workspace = ocean.integration_config.get("bitbucket_workspace", None)
        self.workspace_token = ocean.integration_config.get(
            "bitbucket_workspace_token", None
        )

        if self.workspace is None:
            raise BaseOceanException("Provide a valid BitBucket workspace URL")

        # set up auth headers
        if (not self.username is None) and (not self.password is None):
            self.encoded_credentials = base64.b64encode(
                cast(Buffer, f"{self.username}:{self.password}".encode())
            ).decode()
            self.headers = {
                "Authorization": f"Basic {self.encoded_credentials}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        elif not self.workspace_token is None:
            self.headers = {
                "Authorization": f"Bearer {self.workspace_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        else:
            raise BaseOceanException(
                "Provide either workspace token or both username and password to authenticate"
            )
        self.client.headers.update(self.headers)

    # @cache_iterator_result()
    async def get_projects(self) -> AsyncGenerator[list[dict[str, Any]], None]:
        """get all projects under the current workspace"""
        async for projects in self._fetch_data(
            f"{self.base_url}/workspaces/{self.workspace}/projects"
        ):
            logger.info(
                f"Fetched {len(projects)} projects from BitBucket workspace {self.workspace}"
            )
            yield projects

    @cache_iterator_result()
    async def get_repositories(self) -> AsyncGenerator[list[dict[str, Any]], None]:
        """get all repos under the current workspace"""
        async for repos in self._fetch_data(
            f"{self.base_url}/repositories/{self.workspace}"
        ):
            logger.info(
                f"Fetched batch of {len(repos)} repositories from workspace {self.workspace}"
            )
            yield repos

    @cache_iterator_result()
    async def get_pull_requests(
        self, slug: str
    ) -> AsyncGenerator[list[dict[str, Any]], None]:
        params = {
            "state": PREFERRED_PR_STATE,
            "pagelen": DEFAULT_PAGE_SIZE,
        }
        async for pull_requests in self._fetch_data(
            f"{self.base_url}/repositories/{self.workspace}/{slug}/pullrequests",
            params=params,
        ):
            logger.info(
                f"Fetched batch of {len(pull_requests)} pull requests from repository {slug} in workspace {self.workspace}"
            )
            yield pull_requests

    async def _send_api_request(
        self,
        url: str,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        method: str = "GET",
        return_full_response: bool = False,
    ) -> Any:
        """Send a request to Bitbucket v2 API with error handling."""
        logger.info(f"Sending request to {url}")
        response = await self.client.request(
            method=method, url=url, params=params, json=json_data
        )
        logger.info(f"Response from BitBucket API: {response}")
        try:
            response.raise_for_status()
            return response if return_full_response else response.json()
        except HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(
                    f"Requested resource not found: {url}; message: {str(e)}"
                )
                return {}
            logger.error(f"Bitbucket API error: {str(e)}")
            raise e
        except HTTPError as e:
            logger.error(f"Failed to send {method} request to url {url}: {str(e)}")
            raise e

    async def _fetch_data(
        self,
        url: str,
        method: str = "GET",
        data_key: str = "values",
        params: Optional[dict[str, Any]] = None,
    ) -> AsyncGenerator[list[dict[str, Any]], None]:
        if params is None:
            params = (
                {
                    "pagelen": DEFAULT_PAGE_SIZE,
                },
            )
        while True:
            async with RATE_LIMITER:
                try:
                    response = await self._send_api_request(
                        url, params=params, method=method
                    )
                    if response.status_code == 429:
                        break  # too many requests
                    response_data = response.json()
                    if values := response_data.get(data_key, []):
                        yield values
                    # get the `next` page
                    url = response_data.get("next")
                    if not url:
                        break  # end of page reached
                except BaseException as e:
                    logger.error(f"Bitbucket API error: {str(e)}")
                    yield []
                    break

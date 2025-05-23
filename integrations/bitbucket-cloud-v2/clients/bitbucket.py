import base64
from typing import AsyncGenerator, Any

from loguru import logger

from port_ocean.context.ocean import ocean
from port_ocean.utils.cache import cache_iterator_result


class BitbucketIntegrationClient:
    """
    BitBucket integration client
    Handles authentication and API calls to BitBucket
    """

    def __init__(self):
        logger.info("Initializing BitBucket Client")

        # get credentials
        self.base_url = ocean.integration_config["bitbucket_host_url"]
        self.username = ocean.integration_config["bitbucket_username"]
        self.password = ocean.integration_config["bitbucket_app_password"]
        self.workspace = ocean.integration_config["bitbucket_workspace"]

        # set up auth headers
        if self.username and self.password:
            self.encoded_credentials = base64.b64encode(
                f"{self.username}:{self.password}".encode()
            ).decode()
            self.headers = {"Authorization": f"Basic {self.encoded_credentials}"}
        elif self.workspace:
            self.headers = {"Authorization": f"Bearer {self.workspace}"}
        else:
            raise RuntimeError(
                "Provide both username and password or workspace to authenticate"
            )

    @cache_iterator_result()
    async def get_projects(self) -> AsyncGenerator[list[dict[str, Any]], None]:
        headers = self.headers
        for x in range(5):
            yield [
                {
                    "uuid": f"project-{x}",
                    "name": f"project-{x}",
                    "url": f"https://bitbucket.org/project-{x}",
                }
            ]

    @cache_iterator_result()
    async def get_repositories(self) -> AsyncGenerator[list[dict[str, Any]], None]:
        headers = self.headers
        for x in range(5):
            yield [
                {
                    "uuid": f"repository-{x}",
                    "name": f"repository-{x}",
                    "url": f"https://bitbucket.org/project-{x}/repository-{x}",
                    "scm": "git",
                    "slug": f"repository-{x}",
                    "language": "python",
                    "description": f"some description {x}",
                }
            ]

    @cache_iterator_result()
    async def get_pull_requests(
        self, slug: str
    ) -> AsyncGenerator[list[dict[str, Any]], None]:
        headers = self.headers
        for x in range(5):
            yield [
                {
                    "uuid": f"pull-request-{x}",
                    "url": f"https://bitbucket.org/project-{x}/{slug}/pull-requests/{x}",
                    "state": "OPEN",
                    "author": f"user-{x % 3}",
                }
            ]

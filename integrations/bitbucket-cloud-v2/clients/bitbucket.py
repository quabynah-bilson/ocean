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
            raise BaseOceanException(
                "Workspace is not yet configured. Provide a valid BitBucket workspace URL"
            )

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

    @cache_iterator_result()
    async def get_projects(self) -> AsyncGenerator[list[dict[str, Any]], None]:
        """get all projects under the current workspace"""
        # async for projects in self._fetch_data(
        #     f"{self.base_url}/workspaces/{self.workspace}/projects"
        # ):
        #     logger.info(
        #         f"Fetched {len(projects)} projects from BitBucket workspace {self.workspace}"
        #     )
        #     # todo - convert to data classes
        #     yield projects
        yield [
            {
                "type": "project",
                "owner": {
                    "display_name": "Dennis",
                    "links": {
                        "self": {
                            "href": "https://api.bitbucket.org/2.0/users/%7B6d599fd8-ee97-4686-8cda-1daf9aa5badd%7D"
                        },
                        "avatar": {
                            "href": "https://secure.gravatar.com/avatar/4f27b2b01d47adb1f27860d7410f4465?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FD-3.png"
                        },
                        "html": {
                            "href": "https://bitbucket.org/%7B6d599fd8-ee97-4686-8cda-1daf9aa5badd%7D/"
                        },
                    },
                    "type": "user",
                    "uuid": "{6d599fd8-ee97-4686-8cda-1daf9aa5badd}",
                    "account_id": "557058:3ec526d0-97ff-49f0-a687-37029415897d",
                    "nickname": "Quabynah_1993",
                },
                "workspace": {
                    "type": "workspace",
                    "uuid": "{6d599fd8-ee97-4686-8cda-1daf9aa5badd}",
                    "name": "quabynah-bilson",
                    "slug": "quabynah-bilson",
                    "links": {
                        "avatar": {
                            "href": "https://bitbucket.org/workspaces/quabynah-bilson/avatar/?ts=1748008563"
                        },
                        "html": {"href": "https://bitbucket.org/quabynah-bilson/"},
                        "self": {
                            "href": "https://api.bitbucket.org/2.0/workspaces/quabynah-bilson"
                        },
                    },
                },
                "key": "CLOUD_INTEGRATION_1",
                "uuid": "{cfb0022f-f093-43ae-812c-a0bb5e41b277}",
                "is_private": False,
                "name": "cloud-integration-1",
                "description": "Cloud integration demo",
                "links": {
                    "self": {
                        "href": "https://api.bitbucket.org/2.0/workspaces/quabynah-bilson/projects/CLOUD_INTEGRATION_1"
                    },
                    "html": {
                        "href": "https://bitbucket.org/quabynah-bilson/workspace/projects/CLOUD_INTEGRATION_1"
                    },
                    "repositories": {
                        "href": 'https://api.bitbucket.org/2.0/repositories/quabynah-bilson?q=project.key="CLOUD_INTEGRATION_1"'
                    },
                    "avatar": {
                        "href": "https://bitbucket.org/quabynah-bilson/workspace/projects/CLOUD_INTEGRATION_1/avatar/32?ts=1748008827"
                    },
                },
                "created_on": "2018-12-01T18:00:31.701578+00:00",
                "updated_on": "2025-05-23T14:00:27.134638+00:00",
                "has_publicly_visible_repos": False,
            }
        ]

    @cache_iterator_result()
    async def get_repositories(self) -> AsyncGenerator[list[dict[str, Any]], None]:
        """get all repos under the current workspace"""
        # async for repos in self._fetch_data(
        #     f"{self.base_url}/repositories/{self.workspace}"
        # ):
        #     logger.info(
        #         f"Fetched batch of {len(repos)} repositories from workspace {self.workspace}"
        #     )
        #     yield repos
        yield [
            {
                "type": "repository",
                "full_name": "quabynah-bilson/survival-games",
                "links": {
                    "self": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games"
                    },
                    "html": {
                        "href": "https://bitbucket.org/quabynah-bilson/survival-games"
                    },
                    "avatar": {
                        "href": "https://bytebucket.org/ravatar/%7B545d507d-65cc-4930-9da0-0b645e0b0c02%7D?ts=c_plus_plus"
                    },
                    "pullrequests": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/pullrequests"
                    },
                    "commits": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/commits"
                    },
                    "forks": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/forks"
                    },
                    "watchers": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/watchers"
                    },
                    "branches": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/refs/branches"
                    },
                    "tags": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/refs/tags"
                    },
                    "downloads": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/downloads"
                    },
                    "source": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/src"
                    },
                    "clone": [
                        {
                            "name": "https",
                            "href": "https://quabynah-bilson@bitbucket.org/quabynah-bilson/survival-games.git",
                        },
                        {
                            "name": "ssh",
                            "href": "git@bitbucket.org:quabynah-bilson/survival-games.git",
                        },
                    ],
                    "hooks": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/hooks"
                    },
                },
                "name": "Survival Games",
                "slug": "survival-games",
                "description": "This is a fake repository",
                "scm": "git",
                "website": None,
                "owner": {
                    "display_name": "Dennis",
                    "links": {
                        "self": {
                            "href": "https://api.bitbucket.org/2.0/users/%7B6d599fd8-ee97-4686-8cda-1daf9aa5badd%7D"
                        },
                        "avatar": {
                            "href": "https://secure.gravatar.com/avatar/4f27b2b01d47adb1f27860d7410f4465?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FD-3.png"
                        },
                        "html": {
                            "href": "https://bitbucket.org/%7B6d599fd8-ee97-4686-8cda-1daf9aa5badd%7D/"
                        },
                    },
                    "type": "user",
                    "uuid": "{6d599fd8-ee97-4686-8cda-1daf9aa5badd}",
                    "account_id": "557058:3ec526d0-97ff-49f0-a687-37029415897d",
                    "nickname": "Quabynah_1993",
                },
                "workspace": {
                    "type": "workspace",
                    "uuid": "{6d599fd8-ee97-4686-8cda-1daf9aa5badd}",
                    "name": "quabynah-bilson",
                    "slug": "quabynah-bilson",
                    "links": {
                        "avatar": {
                            "href": "https://bitbucket.org/workspaces/quabynah-bilson/avatar/?ts=1748008563"
                        },
                        "html": {"href": "https://bitbucket.org/quabynah-bilson/"},
                        "self": {
                            "href": "https://api.bitbucket.org/2.0/workspaces/quabynah-bilson"
                        },
                    },
                },
                "is_private": True,
                "project": {
                    "type": "project",
                    "key": "CLOUD_INTEGRATION_1",
                    "uuid": "{cfb0022f-f093-43ae-812c-a0bb5e41b277}",
                    "name": "cloud-integration-1",
                    "links": {
                        "self": {
                            "href": "https://api.bitbucket.org/2.0/workspaces/quabynah-bilson/projects/CLOUD_INTEGRATION_1"
                        },
                        "html": {
                            "href": "https://bitbucket.org/quabynah-bilson/workspace/projects/CLOUD_INTEGRATION_1"
                        },
                        "avatar": {
                            "href": "https://bitbucket.org/quabynah-bilson/workspace/projects/CLOUD_INTEGRATION_1/avatar/32?ts=1748008827"
                        },
                    },
                },
                "fork_policy": "no_public_forks",
                "created_on": "2016-10-22T16:10:44.203928+00:00",
                "updated_on": "2025-05-23T14:32:02.648174+00:00",
                "size": 54545,
                "language": "c++",
                "uuid": "{545d507d-65cc-4930-9da0-0b645e0b0c02}",
                "mainbranch": {"name": "master", "type": "branch"},
                "override_settings": {
                    "default_merge_strategy": False,
                    "branching_model": False,
                },
                "parent": None,
                "enforced_signed_commits": None,
                "has_issues": False,
                "has_wiki": False,
            }
        ]

    @cache_iterator_result()
    async def get_pull_requests(
        self, slug: str
    ) -> AsyncGenerator[list[dict[str, Any]], None]:

        yield [
            {
                "comment_count": 0,
                "task_count": 0,
                "type": "pullrequest",
                "id": 1,
                "title": ".gitignore edited online with Bitbucket",
                "description": ".gitignore edited online with Bitbucket",
                "state": "OPEN",
                "draft": False,
                "merge_commit": None,
                "close_source_branch": True,
                "closed_by": None,
                "author": {
                    "display_name": "Dennis",
                    "links": {
                        "self": {
                            "href": "https://api.bitbucket.org/2.0/users/%7B6d599fd8-ee97-4686-8cda-1daf9aa5badd%7D"
                        },
                        "avatar": {
                            "href": "https://secure.gravatar.com/avatar/4f27b2b01d47adb1f27860d7410f4465?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FD-3.png"
                        },
                        "html": {
                            "href": "https://bitbucket.org/%7B6d599fd8-ee97-4686-8cda-1daf9aa5badd%7D/"
                        },
                    },
                    "type": "user",
                    "uuid": "{6d599fd8-ee97-4686-8cda-1daf9aa5badd}",
                    "account_id": "557058:3ec526d0-97ff-49f0-a687-37029415897d",
                    "nickname": "Quabynah_1993",
                },
                "reason": "",
                "created_on": "2025-05-23T14:50:23.687424+00:00",
                "updated_on": "2025-05-23T14:50:24.695983+00:00",
                "destination": {
                    "branch": {"name": "master"},
                    "commit": {
                        "hash": "ff1c5865ea3a",
                        "links": {
                            "self": {
                                "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/commit/ff1c5865ea3a"
                            },
                            "html": {
                                "href": "https://bitbucket.org/quabynah-bilson/survival-games/commits/ff1c5865ea3a"
                            },
                        },
                        "type": "commit",
                    },
                    "repository": {
                        "type": "repository",
                        "full_name": "quabynah-bilson/survival-games",
                        "links": {
                            "self": {
                                "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games"
                            },
                            "html": {
                                "href": "https://bitbucket.org/quabynah-bilson/survival-games"
                            },
                            "avatar": {
                                "href": "https://bytebucket.org/ravatar/%7B545d507d-65cc-4930-9da0-0b645e0b0c02%7D?ts=c_plus_plus"
                            },
                        },
                        "name": "Survival Games",
                        "uuid": "{545d507d-65cc-4930-9da0-0b645e0b0c02}",
                    },
                },
                "source": {
                    "branch": {"name": "dennis/update-gitignore", "links": {}},
                    "commit": {
                        "hash": "fb11710da8bd",
                        "links": {
                            "self": {
                                "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/commit/fb11710da8bd"
                            },
                            "html": {
                                "href": "https://bitbucket.org/quabynah-bilson/survival-games/commits/fb11710da8bd"
                            },
                        },
                        "type": "commit",
                    },
                    "repository": {
                        "type": "repository",
                        "full_name": "quabynah-bilson/survival-games",
                        "links": {
                            "self": {
                                "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games"
                            },
                            "html": {
                                "href": "https://bitbucket.org/quabynah-bilson/survival-games"
                            },
                            "avatar": {
                                "href": "https://bytebucket.org/ravatar/%7B545d507d-65cc-4930-9da0-0b645e0b0c02%7D?ts=c_plus_plus"
                            },
                        },
                        "name": "Survival Games",
                        "uuid": "{545d507d-65cc-4930-9da0-0b645e0b0c02}",
                    },
                },
                "links": {
                    "self": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/pullrequests/1"
                    },
                    "html": {
                        "href": "https://bitbucket.org/quabynah-bilson/survival-games/pull-requests/1"
                    },
                    "commits": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/pullrequests/1/commits"
                    },
                    "approve": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/pullrequests/1/approve"
                    },
                    "request-changes": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/pullrequests/1/request-changes"
                    },
                    "diff": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/diff/quabynah-bilson/survival-games:fb11710da8bd%0Dff1c5865ea3a?from_pullrequest_id=1&topic=true"
                    },
                    "diffstat": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/diffstat/quabynah-bilson/survival-games:fb11710da8bd%0Dff1c5865ea3a?from_pullrequest_id=1&topic=true"
                    },
                    "comments": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/pullrequests/1/comments"
                    },
                    "activity": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/pullrequests/1/activity"
                    },
                    "merge": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/pullrequests/1/merge"
                    },
                    "decline": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/pullrequests/1/decline"
                    },
                    "statuses": {
                        "href": "https://api.bitbucket.org/2.0/repositories/quabynah-bilson/survival-games/pullrequests/1/statuses"
                    },
                },
                "summary": {
                    "type": "rendered",
                    "raw": ".gitignore edited online with Bitbucket",
                    "markup": "markdown",
                    "html": "<p>.gitignore edited online with Bitbucket</p>",
                },
            }
        ]

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
                        url=url, params=params, method=method
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

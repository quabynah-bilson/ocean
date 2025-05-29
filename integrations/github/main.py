from enum import StrEnum
from typing import Any

from clients.github import IntegrationClient
from port_ocean.context.ocean import ocean
from port_ocean.core.ocean_types import ASYNC_GENERATOR_RESYNC_TYPE


class ObjectKind(StrEnum):
    REPOSITORY = "repository"
    PULL_REQUEST = "pull-request"
    ISSUE = "issue"
    TEAM = "team"
    WORKFLOW = "workflow"


@ocean.on_resync()
async def on_resync(kind: str) -> list[dict[Any, Any]]:
    if kind == ObjectKind.REPOSITORY:
        resync_repositories(kind)

    return []


@ocean.on_resync(ObjectKind.REPOSITORY)
async def resync_repositories(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    if kind == ObjectKind.REPOSITORY:
        client = IntegrationClient()
        async for repository in client.get_repositories():
            yield repository

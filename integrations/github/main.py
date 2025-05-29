from typing import Any

from integration.clients.github import IntegrationClient
from integration.utils.kind import ObjectKind
from port_ocean.context.ocean import ocean
from port_ocean.core.ocean_types import ASYNC_GENERATOR_RESYNC_TYPE


def init_client() -> IntegrationClient:
    return IntegrationClient()


# resync all object kinds
@ocean.on_resync()
async def on_resync(kind: str) -> list[dict[Any, Any]]:
    if kind == ObjectKind.REPOSITORY:
        resync_repositories(kind)

    return []


# resync repository
@ocean.on_resync(ObjectKind.REPOSITORY)
async def resync_repositories(kind: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    if kind == ObjectKind.REPOSITORY:
        client = init_client()
        async for repository in client.get_repositories():
            yield repository

from typing import Any

from clients.bitbucket import BitbucketIntegrationClient
from port_ocean.context.ocean import ocean
from port_ocean.core.ocean_types import ASYNC_GENERATOR_RESYNC_TYPE
from port_ocean.utils.async_iterators import stream_async_iterators_tasks
from utils.enums import ObjectKind


def init_bitbucket_client() -> BitbucketIntegrationClient:
    return BitbucketIntegrationClient()


# Required
# Listen to the resync event of all the kinds specified in the mapping inside port.
# Called each time with a different kind that should be returned from the source system.
@ocean.on_resync()
async def on_resync(kind: str) -> list[dict[Any, Any]]:
    # get all projects
    if kind == ObjectKind.PROJECT:
        resync_project(kind)

    # get all repositories
    if kind == ObjectKind.REPOSITORY:
        resync_repository(kind)

    # get all pull requests
    if kind == ObjectKind.PULL_REQUEST:
        resync_pull_requests(kind)

    # todo - add components
    if kind == "component":
        return []

    return []


@ocean.on_resync(ObjectKind.PROJECT)
async def resync_project(_: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = init_bitbucket_client()
    async for projects in client.get_projects():
        yield projects


@ocean.on_resync(ObjectKind.REPOSITORY)
async def resync_repository(_: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = init_bitbucket_client()
    async for repositories in client.get_repositories():
        yield repositories


@ocean.on_resync(ObjectKind.PULL_REQUEST)
async def resync_pull_requests(_: str) -> ASYNC_GENERATOR_RESYNC_TYPE:
    client = init_bitbucket_client()
    async for repositories in client.get_repositories():
        tasks = [
            client.get_pull_requests(
                repository.get("slug", repository["name"].lower().replace(" ", "-"))
            )
            for repository in repositories
        ]
        async for prs in stream_async_iterators_tasks(*tasks):
            yield prs


# Listen to the `start` event of the integration. Called once when the integration starts.
@ocean.on_start()
async def on_start() -> None:
    # todo - register webhooks here
    print("Starting bitbucket-cloud-v2 integration")

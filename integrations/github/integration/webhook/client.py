from integrations.github.integration.github.client import IntegrationClient, AuthClient
from integrations.github.integration.webhook.processor.repository import (
    RepositoryWebhookProcessor,
)
from port_ocean.utils.async_iterators import stream_async_iterators_tasks


class WebhookClient:
    def __init__(
        self,
        client: "IntegrationClient",
        auth_client: "AuthClient",
    ) -> None:
        self.client = client
        self.auth_client = auth_client

    async def setup_webhooks(self) -> None:
        """set up processors and subscribe to webhooks"""

        # repository webhook processor config
        repo_processor = (
            RepositoryWebhookProcessor.create_from_ocean_config_and_integration(
                self.client, self.auth_client
            )
        )

        # tasks to perform for webhook subscriptions
        tasks = [repo_processor.subscribe_to_webhooks()]

        # subscribe to all webhooks asynchronously
        async for task in stream_async_iterators_tasks(*tasks):
            await task

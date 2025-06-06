from abc import abstractmethod, ABC

from loguru import logger

from integrations.github.integration.utils.auth import AuthClient
from port_ocean.context.ocean import ocean
from port_ocean.utils import http_async_client
from .events import GitHubWebhookEventType


class BaseWebhookProcessor(ABC):
    retry_threshold: int = 10
    initial_delay: float = 1.0

    def __init__(self, auth_client: AuthClient) -> None:
        self.base_url = ocean.integration_config["base_url"]
        self.retry_threshold = 10
        self._client = http_async_client
        self._client.headers.update(auth_client.get_headers())

    async def on_failed(self, exception: Exception) -> None:
        """handle failed webhook"""
        logger.error(
            f"Webhook failed with exception: {str(exception)}",
            exc_info=exception
        )

    async def create_webhook(self, webhook_url: str) -> None:
        """subscribe to webhook"""
        # @todo - implement this
        pass

    @abstractmethod
    def get_event_type(self) -> GitHubWebhookEventType:
        """return the type of event of the webhook"""
        pass

    async def validate_webhook(self, repo_slug: str, target_url: str) -> bool:
        """checks if a webhook already exists"""
        # @todo - implement this
        await self._client.get(f"{self.base_url}/repos/{repo_slug}/hooks")
        return False

from .base import BaseWebhookProcessor
from .events import GitHubWebhookEventType


class RepositoryWebhookProcessor(BaseWebhookProcessor):
    """processor for repository webhooks"""

    def get_event_type(self) -> GitHubWebhookEventType:
        return GitHubWebhookEventType.REPOSITORY

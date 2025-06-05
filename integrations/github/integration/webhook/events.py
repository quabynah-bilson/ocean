from abc import ABC
from enum import StrEnum


class GitHubWebhookEvent(StrEnum):
    """events for GitHub webhooks"""
    PUSH = "push"
    PR = "pull_request"


class GitHubWebhookEventType(StrEnum):
    """event types for GitHub webhooks"""
    REPOSITORY = "Repository"


class WebhookEvent(ABC):
    """base class for webhook events"""

    def __init__(self, event: GitHubWebhookEventType) -> None:
        self.event = event

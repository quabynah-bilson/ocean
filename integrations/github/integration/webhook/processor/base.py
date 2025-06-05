from loguru import logger


class BaseWebhookProcessor():
    retry_threshold: int = 10
    initial_delay: float = 1.0

    def __init__(self) -> None:
        self.retry_threshold = 10

    async def on_failed(self, exception: Exception) -> None:
        """handle failed webhook"""
        logger.error(
            f"Webhook failed with exception: {str(exception)}",
            exc_info=exception
        )

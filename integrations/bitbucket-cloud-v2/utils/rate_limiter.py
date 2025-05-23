from dataclasses import dataclass


@dataclass
class BitbucketRateLimiter:
    """Config for BitBucket v2 API rate limiter"""

    TTL: int = 3600  # rate limit timespan in seconds
    LIMIT: int = 980  # request limit allowed per second

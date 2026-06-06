# Shared in-process request counter. Single source of truth — imported by middleware and routes.
_request_count: int = 0


def increment_request_count() -> None:
    global _request_count
    _request_count += 1


def get_request_count() -> int:
    return _request_count
"""Settings for task hard limit module."""

import os
from typing import Optional


def get_max_active_task_count() -> int:
    """
    Get the maximum active task count from environment variable or default.

    Returns:
        Maximum active task count (default: 5)
    """
    env_value = os.getenv("MAX_ACTIVE_TASK_COUNT")
    if env_value is not None:
        try:
            return int(env_value)
        except ValueError:
            # If env var is set but invalid, fall back to default
            pass
    return 5

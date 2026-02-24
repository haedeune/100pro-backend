"""Policy logic for task hard limit."""

import logging
from typing import Optional

from app.domains.TaskHardLimit.task_hard_limit.exceptions import MaxActiveTasksExceededError
from app.domains.TaskHardLimit.task_hard_limit.settings import get_max_active_task_count

logger = logging.getLogger(__name__)


def check_hard_limit(active_task_count: int, user_id: Optional[int] = None) -> None:
    """
    Check if adding a new task would exceed the hard limit.

    Args:
        active_task_count: Current active task count for today (YYYY-MM-DD)
        user_id: Optional user ID for logging purposes

    Raises:
        MaxActiveTasksExceededError: If NextTaskCount > MaxActiveTaskCount
    """
    max_active_task_count = get_max_active_task_count()
    next_task_count = active_task_count + 1

    if next_task_count > max_active_task_count:
        # Log the limit_blocked event
        logger.warning(
            "limit_blocked",
            extra={
                "active": active_task_count,
                "next": next_task_count,
                "max": max_active_task_count,
                "user_id": user_id,
            },
        )
        raise MaxActiveTasksExceededError(
            max_active_task_count=max_active_task_count,
            active_task_count=active_task_count,
            next_task_count=next_task_count,
        )

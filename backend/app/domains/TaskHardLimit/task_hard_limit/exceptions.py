"""Exceptions for task hard limit module."""


class MaxActiveTasksExceededError(Exception):
    """Raised when the maximum active task count is exceeded."""

    ERROR_CODE = "MAX_ACTIVE_TASKS_EXCEEDED"

    def __init__(self, max_active_task_count: int, active_task_count: int, next_task_count: int):
        """
        Initialize the exception.

        Args:
            max_active_task_count: Maximum allowed active task count
            active_task_count: Current active task count
            next_task_count: Next task count that would exceed the limit
        """
        self.max_active_task_count = max_active_task_count
        self.active_task_count = active_task_count
        self.next_task_count = next_task_count
        message = f"오늘의 목표는 최대 {max_active_task_count}개까지 설정할 수 있습니다."
        super().__init__(message)

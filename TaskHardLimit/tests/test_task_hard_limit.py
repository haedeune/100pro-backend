"""Unit tests for task hard limit module."""

import pytest

from task_hard_limit.exceptions import MaxActiveTasksExceededError
from task_hard_limit.policy import check_hard_limit


def test_check_hard_limit_allow_when_active_is_4():
    """Test that check_hard_limit allows when active_task_count is 4 (next=5, max=5)."""
    # Given: active_task_count = 4, max = 5 (default)
    # When: check_hard_limit is called
    # Then: No exception should be raised
    check_hard_limit(active_task_count=4)


def test_check_hard_limit_block_when_active_is_5():
    """Test that check_hard_limit blocks when active_task_count is 5 (next=6, max=5)."""
    # Given: active_task_count = 5, max = 5 (default)
    # When: check_hard_limit is called
    # Then: MaxActiveTasksExceededError should be raised
    with pytest.raises(MaxActiveTasksExceededError) as exc_info:
        check_hard_limit(active_task_count=5)

    # Verify exception attributes
    assert exc_info.value.max_active_task_count == 5
    assert exc_info.value.active_task_count == 5
    assert exc_info.value.next_task_count == 6
    assert exc_info.value.ERROR_CODE == "MAX_ACTIVE_TASKS_EXCEEDED"
    assert "오늘의 목표는 최대 5개까지 설정할 수 있습니다." in str(exc_info.value)

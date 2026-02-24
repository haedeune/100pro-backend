"""
task_archive 인프라 패키지 [PRO-B-23].
전략 선택에 따른 상태 전환, 보관함 테이블 격리, 상태 변경 히스토리 관리.
"""
from app.infrastructure.task_archive.router import router

__all__ = ["router"]

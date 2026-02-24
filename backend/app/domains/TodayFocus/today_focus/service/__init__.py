"""TodayFocus Service."""
from app.domains.TodayFocus.today_focus.service.impl import TodayFocusServiceImpl
from app.domains.TodayFocus.today_focus.service.interface import TodayFocusServiceProtocol

__all__ = ["TodayFocusServiceImpl", "TodayFocusServiceProtocol"]

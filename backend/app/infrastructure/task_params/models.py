"""
시스템 파라미터 모델 [PRO-B-16].
모든 실험·임계치·정책 변수를 key-value 형태로 DB에 저장하여 실시간 제어한다.
"""
from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.core.database import Base


class SystemParameter(Base):
    """
    시스템 파라미터 테이블 [PRO-B-16].
    코드 배포 없이 대시보드/API를 통해 값을 변경할 수 있다.
    """

    __tablename__ = "system_parameters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(128), nullable=False, unique=True, index=True)
    value = Column(String(512), nullable=False)
    value_type = Column(String(16), nullable=False, default="str")
    category = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

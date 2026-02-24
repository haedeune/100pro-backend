"""
환경 변수 로딩 책임을 갖는 모듈.
애플리케이션 시작 시 .env 파일을 1회 로드한다.
"""
from dotenv import load_dotenv


def load_env() -> None:
    """`.env` 파일을 로드하여 환경 변수에 반영한다. 1회 호출을 권장한다."""
    load_dotenv()

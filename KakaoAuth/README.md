# Backend (FastAPI)

PM-JSH Kakao OAuth 인증 API.

## 폴더 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 앱 진입점
│   ├── core/                # 공통 설정·유틸
│   │   ├── __init__.py
│   │   └── env.py           # 환경 변수 로딩
│   └── domains/              # 도메인별 모듈
│       ├── __init__.py
│       └── kakao_authentication/
│           ├── __init__.py
│           ├── router.py     # API 라우터
│           ├── schemas.py    # 요청/응답 스키마
│           ├── exceptions.py
│           └── service/
│               ├── __init__.py
│               ├── interface.py
│               └── impl.py
├── main.py                  # 실행 진입점 (python -m main)
├── requirements.txt
├── .env.example
├── .gitignore
└── strategy/                # 전략 YAML (PM-JSH-1 ~ 4)
```

- **app/core**: 환경 변수 등 앱 전역 설정
- **app/domains**: 도메인 단위 (인증, 추후 확장 시 도메인 추가)
- **router** → **service** → **외부 API** 구조 유지

## 실행

```bash
# 가상환경 활성화 후
python -m main
# 또는
uvicorn app.main:app --reload
```

## 환경 변수

`.env.example`을 참고해 `.env`를 생성하고 `KAKAO_CLIENT_ID`, `KAKAO_REDIRECT_URI`를 설정한다.

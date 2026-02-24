# 100pro-backend

`100pro-backend`는 **'5늘할일'** 서비스의 백엔드 페이지(서버) 프로젝트입니다.  
사용자의 할 일 데이터를 안정적으로 저장하고, 조회/수정/삭제할 수 있도록 API를 제공하는 것을 목표로 합니다.

## 프로젝트 소개

'5늘할일'은 일상적인 할 일을 가볍게 기록하고 관리할 수 있는 서비스입니다.  
이 저장소는 해당 서비스의 백엔드 로직, 데이터 처리, API 제공 영역을 담당합니다.

## 백엔드 역할

- 할 일(Task) 데이터 생성/조회/수정/삭제(CRUD)
- 사용자 요청 처리 및 응답 포맷 관리
- 데이터 저장소 연동 및 기본 검증 로직 처리
- 프론트엔드와의 안정적인 통신을 위한 API 제공

## 핵심 기능 (도메인)

1. **사용자 및 로그인 (Auth)**
   - 메일/패스워드 기반 회원가입 및 JWT 로그인
   - **카카오 소셜 로그인(SSO)** 연동 (`/auth/kakao`)
2. **할 일 관리 (Task)**
   - CRUD 및 상태 관리 (진행 전/완료/보관/삭제)
   - **하루 5개 제한**, **미래 날짜 생성 차단** 검증 로직
   - 미완료 할 일들의 일괄 보관함 처리 (Batch Action)
   - 퍼센트 형태의 오늘자 생산성(달성률) 통계 API 제공

## 실행 방법 및 환경 설정 (Kakao Auth 포함)

본 프로젝트는 `python-dotenv`를 사용하여 환경 변수를 관리합니다. 
GitHub에 공유할 때 민감한 키가 노출되지 않도록, 로컬 PC에서만 `.env` 파일을 생성해 사용하세요.

### 1) 패키지 설치
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2) `.env` 파일 구성
루트 디렉토리(`backend/`)에 `.env` 파일을 만들고 아래 양식을 채워주세요. (`.env.example` 참고)

```env
# JWT 암호화를 위한 시크릿 키 (임의의 무작위 문자열 긴 것)
JWT_SECRET_KEY=your_super_secret_jwt_key_here

# [선택] 카카오 로그인을 위함 - Kakao Developers > 내 애플리케이션 > 앱 키 > REST API 키
KAKAO_CLIENT_ID=your_kakao_rest_api_key

# [선택] 프론트엔드로 리다이렉트될 주소
KAKAO_REDIRECT_URI=http://localhost:5173/auth/kakao/callback
```
> **주의**: `JWT_SECRET_KEY`가 설정되지 않으면 보안 상 서버 애플리케이션이 실행되지(startup) 않습니다.

### 3) 서버 실행
```bash
uvicorn app.main:app --port 8000 --reload
```
서버 구동 후 `http://localhost:8000/docs` 에 접속하여 Swagger API 문서를 확인하고 테스트할 수 있습니다.

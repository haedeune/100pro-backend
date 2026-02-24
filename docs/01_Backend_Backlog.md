# 백엔드 백로그 통합 문서

---

## 목차

| # | 티켓 | 제목 |
|---|------|------|
| 01 | PRO-B-11 | 환경 변수 로딩 및 초기화 구조 개선 |
| 02 | PRO-B-33 | 사용자 인증 및 계정 관리 API |
| 03 | PRO-B-34 | 일일 할 일 생성 5개 제한 검증 |
| 04 | PRO-B-35 | 할 일 생성 시 미래 날짜 지정 차단 |
| 05 | PRO-B-36 | 할 일 기본 CRUD 및 완료 상태 토글 |
| 06 | PRO-B-37 | 미완료 할 일 보관(Archive) 및 삭제 |
| 07 | PRO-B-38 | 카카오 소셜 로그인(SSO) 연동 |
| 08 | PRO-B-39 | 과거 미완료 항목 조회 및 일괄 처리 |
| 09 | PRO-B-40 | 사용자 대시보드 및 일일 달성률 통계 |

---

## [PRO-B-11] 환경 변수 로딩 및 초기화 구조 개선

### Success Criteria
- 환경 변수 로딩 책임은 config 패키지에 명시적으로 위치한다.
- Service 및 Controller에서는 `.env` 파일을 직접 로드하지 않는다.
- 환경 변수 로딩 여부는 애플리케이션 전역에서 일관되게 보장된다.

### Todo
- [x] python-dotenv 의존성 추가
- [x] config/env.py 생성 및 load_env 함수 구현
- [x] 애플리케이션 엔트리포인트에서 load_env 호출

### 작업 이력

**Date:** 2026-02-24

#### 배경 (Background)
기존 프로젝트 구조에서는 백엔드의 환경 변수(`.env`) 로딩과 관련된 책임이 명확히 분리되지 않았고, FastAPI 엔트리포인트(`main.py`) 내부에서 모듈 경로가 꼬여 데이터베이스 모델의 중복 등록 문제가 발생하고 있었습니다. 이를 개선하여 안정적인 백엔드 시작 경험을 보장하기 위해 환경 변수 로딩 로직을 개선했습니다.

#### 작업 내용 (What was done)

1. **환경 변수 로딩 책임 분리 (`config/env.py`)**
   - 백엔드의 환경 변수 로딩을 전담하는 `config` 패키지를 신설하고 `env.py` 파일을 생성했습니다.
   - `python-dotenv`의 `load_dotenv`를 활용하여 `.env` 파일 존재 여부를 확인하고 환경 변수를 시스템에 로드하는 `load_env()` 함수를 구현했습니다.
   - 파일 누락 시 경고 로그를 남기며 시스템 환경 변수를 폴백(fallback)으로 사용할 수 있도록 조치했습니다.

2. **애플리케이션 진입점 변경 (`main.py`)**
   - FastAPI를 구동하는 엔트리포인트인 `main.py`의 `lifespan` 시작 지점에서 가장 먼저 `load_env()`가 명시적으로 호출되도록 수정했습니다.
   - 이를 통해 애플리케이션의 나머지 부분(Controller, Service 등)에서는 파일 파싱을 신경 쓰지 않고 안정적으로 `os.getenv` 등을 사용할 수 있게 되었습니다.

3. **중복 임포트 버그 수정 (`core/database.py` 및 `main.py`)**
   - `core/database.py`의 `init_db()`에서 모델 테이블을 로딩할 때, 기존에는 `backend.app...` 과 `app...` 처럼 절대 경로명이 혼재되어 호출되었습니다.
   - 이로 인해 SQLAlchemy의 `MetaData`가 동일한 테이블(`tasks` 등)을 두 번 인식하여 부팅에 실패(`InvalidRequestError: Table 'tasks' is already defined...`)하는 문제가 발견되었습니다.
   - 내부 모듈 임포트 경로를 모두 `app...` 으로 일관되게 통일하여 테이블 중복 생성 문제를 고치고 데이터베이스 초기화 로직을 안정화했습니다.
   - 또한, 모델이 아닌 `config.py`나 `settings.py`를 참조해야 하는 파라미터성 모듈의 경로도 정상적으로 바로잡았습니다.

#### 결과 및 기대 효과
- **관심사의 분리**: 설정 전담 패키지가 생성되어 코드가 깔끔해졌습니다.
- **안정성 입증**: SQLite 데이터베이스 충돌 및 서버 구동 실패 버그를 해결하여, `uvicorn` 실행 시 서버가 에러 없이 정상적으로 구동(`http://127.0.0.1:8000`)되는 상태를 확보했습니다.

---

## [PRO-B-33] 사용자 인증 및 계정 관리 API 구현

### Success Criteria
- 이메일, 비밀번호, 이름을 통한 회원가입 API가 정상 동작해야 한다.
- 이메일, 비밀번호를 통한 로그인 API가 세션 또는 토큰(JWT)을 발급해야 한다.
- 로그아웃 및 회원탈퇴 API가 구현되어 데이터베이스에서 사용자를 처리(삭제 또는 비활성화)해야 한다.
- 모든 비밀번호는 암호화(해싱)되어 데이터베이스에 안전하게 저장되어야 한다.

### Todo
- [ ] 사용자(User) 도메인 모델 설계 및 테이블 스키마 작성
- [ ] 회원가입 로직 및 비밀번호 해싱 유틸리티 구현
- [ ] JWT / 세션 방식의 로그인 로직 작성 및 인증 미들웨어 추가
- [ ] 로그아웃 및 회원정보 삭제(탈퇴) 엔드포인트 구현

---

## [PRO-B-34] 일일 할 일 생성 5개 제한 검증 로직 구현

### Success Criteria
- 사용자가 당일(Today) 기준으로 이미 5개의 할 일을 생성했다면, 추가 생성 API 호출 시 400 Bad Request 혹은 명시적인 에러를 반환해야 한다.
- 예외 메시지는 프론트엔드가 인지할 수 있도록 명확히 전달되어야 한다.

### Todo
- [ ] Todo 생성 API에 당일 생성된 본인의 할 일 개수 조회 로직 추가
- [ ] 당일 개수가 5개 이상일 경우 예외를 발생시키는 Validation 로직 구현
- [ ] 5개 초과 생성 방지 로직에 대한 백엔드 단위 테스트(Unit Test) 작성

---

## [PRO-B-35] 할 일 생성 시 미래 날짜 지정 차단 로직 구현

### Success Criteria
- 할 일(Todo) 생성 API 호출 시 요청된 식별 날짜(`createdAt` 또는 `targetDate`)가 서버 기준 '내일' 이후라면 예외를 반환해야 한다.
- 서버 기준 날짜와 클라이언트 기준 날짜의 타임존(Timezone) 시차를 고려하여 유연하게 검증해야 한다.

### Todo
- [ ] Todo 생성 API 파라미터에서 날짜 데이터 추출 및 밸리데이션 데코레이터/로직 추가
- [ ] 요청일이 미래인지 판별하는 유틸리티 함수(Timezone 고려) 구현
- [ ] 미래 날짜일 경우 400 Bad Request와 명확한 에러 코드로 응답하도록 예외 처리

---

## [PRO-B-36] 할 일(Todo) 기본 CRUD 및 완료 상태 토글 API 구현

### Success Criteria
- 사용자가 자신의 할 일 목록을 생성, 조회, 내용 수정, 완료(토글) 상태 업데이트를 수행할 수 있어야 한다.
- 모든 할 일 조회 및 수정은 인증된 본인의 데이터에만 접근할 수 있어야 한다. (인가/Authorization 로직)
- `isDone` 상태를 빠르고 안전하게 변경할 수 있는 별도 엔드포인트(혹은 부분 업데이트 PATCH)가 제공되어야 한다.

### Todo
- [ ] Todo 엔티티(모델) 및 테이블 스키마/마이그레이션 생성
- [ ] 내 할 일 목록 조회(List), 생성(Create) API 개발
- [ ] 할 일 내용 수정(Update) 및 완료 상태(`isDone`) 변경 토글 API 개발
- [ ] 본인 소유의 데이터만 수정 및 조회 가능한지 검증하는 권한 로직 적용

---

## [PRO-B-37] 미완료 할 일 보관(Archive) 및 삭제 API 구현

### Success Criteria
- 할 일을 영구 삭제(Delete)하는 API가 정상적으로 개별 아이템을 제거해야 한다.
- 할 일을 보관함으로 이동(Archived 상태로 변경)하는 상태 업데이트 API가 동작해야 한다.
- 보관함 조회 전용 API는 사용자의 할 일 중 `archived == true` 인 데이터만 필터링하여 반환해야 한다.

### Todo
- [ ] 기존 Todo 모델에 `archived` (boolean) 플래그 필드 추가 및 기본값 False 적용
- [ ] 특정 할 일을 영구 삭제하는 DELETE 엔드포인트 개발
- [ ] 특정 할 일을 보관 상태로 지정하는 변경(PATCH) 엔드포인트 개발
- [ ] 보관 상태의 할 일만 모아서 조회하는 Archive List 뷰 리턴 API 개발

---

## [PRO-B-38] 카카오 소셜 로그인(SSO) API 연동

### Success Criteria
- 프론트엔드에서 전달받은 카카오 인가 코드(또는 액세스 토큰)를 검증하여 백엔드에서 자체 사용자 세션/JWT를 발급해야 한다.
- 카카오 로그인으로 최초 접근한 사용자는 데이터베이스에 자동으로 회원가입 처리(Social User) 되어야 한다.
- 기존 이메일 가입자가 카카오 연동을 시도할 경우, 계정 통합 처리가 이루어져야 한다.

### Todo
- [ ] 카카오 OAuth REST API 통신 로직 및 토큰 검증 유틸리티 구현
- [ ] 소셜 로그인 회원가입/로그인 통합 엔드포인트 개발
- [ ] User 모델에 `provider` (email, kakao 등) 및 `social_id` 필드 추가

---

## [PRO-B-39] 과거 미완료 항목 조회 및 상태 일괄 처리 API

### Success Criteria
- 사용자가 접속했을 때, '오늘'을 기준으로 과거에 작성되었으나 완료되지 않은(`isDone == false`) 할 일 목록을 반환하는 전용 API가 있어야 한다.
- 사용자가 과거 미완료 항목들을 한 번에 삭제하거나 보관함으로 넘길 수 있도록, 다건의 ID를 배열로 받아 일괄 상태를 업데이트(Batch Update)하는 API가 동작해야 한다.

### Todo
- [ ] 오늘 날짜 기준으로 과거의 미완료 Todo만 필터링해서 리턴하는 API 구현
- [ ] Todo ID 리스트와 변경할 상태(Archive 또는 Delete)를 받아 일괄 처리하는 Endpoint 개발
- [ ] 대량 데이터 업데이트 시 동시성 및 트랜잭션 안전성 테스트 적용

---

## [PRO-B-40] 사용자 대시보드 및 일일 달성률 통계 API

### Success Criteria
- 클라이언트가 마이페이지 등에서 사용자 경험(Productivity Tracker)을 그릴 수 있도록, '오늘 작성한 5개의 할 일 중 완료된 개수/비율'을 반환해야 한다.
- 누적 완료 개수, 전체 보관함 개수 등 마이페이지 프로필 영역에 필요한 요약 데이터를 한 번의 API 호출로 제공해야 한다.

### Todo
- [ ] 특정 사용자의 오늘치 달성률(Total vs Done) 계산 로직 구현
- [ ] 총 누적 완료 수 등 마이페이지용 통계 DTO 및 전용 엔드포인트 개발
- [ ] Aggregate Query(집계 쿼리)를 이용해 데이터베이스 조회 성능 최적화



# 백엔드 작업 이력 — 인증 시스템 완성 (PRO-B-33, PRO-B-38)

## 작업 일시
- **Date:** 2026-02-24

---

## 배경 (Background)

백엔드에는 이메일 인증 및 카카오 SSO 관련 엔드포인트가 존재했으나 아래 문제가 있었습니다.

1. **이메일 로그인**: 백엔드 구현은 완성되어 있었으나 프론트엔드가 mock 전용으로 연결되지 않은 상태
2. **카카오 로그인**: `/auth/kakao` 엔드포인트가 인가 코드(Authorization Code)가 아닌 액세스 토큰을 직접 받는 방식으로 잘못 구현됨 → 프론트엔드 S2S 흐름과 불일치
3. **CORS 미설정**: 프론트엔드(`localhost:5173`)에서 백엔드(`localhost:8000`) API 호출 불가
4. **응답 스키마 불일치**: 로그인 성공 시 토큰만 반환, 유저 정보 미포함 → 프론트엔드에서 유저 정보를 별도 요청해야 하는 구조

---

## 변경 파일 목록

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/main.py` | CORSMiddleware 추가, import 경로 통일 |
| `backend/app/domains/auth/schemas.py` | `TokenWithUser` 스키마 추가 |
| `backend/app/domains/auth/router.py` | `/auth/login` 응답 수정, `/auth/kakao` S2S 구현 |
| `backend/.env.example` | `KAKAO_REDIRECT_URI` 프론트 URL로 수정, `JWT_SECRET_KEY` 추가 |
| `backend/.env` | 실제 키값 설정 (gitignore 대상) |

---

## 주요 변경 내용

### 1. `main.py` — CORS 및 import 경로 수정

**CORS 추가:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**import 경로 통일 (버그 수정):**
```python
# Before (main.py 내에서만 외부 경로 사용 → ModuleNotFoundError 발생)
from backend.app.config.env import load_env

# After (모든 import를 app. 기준으로 통일)
from app.config.env import load_env
```

> **실행 방법 변경:** `100pro-backend/backend/` 폴더 안에서 실행해야 함
> ```bash
> cd 100pro-backend/backend
> python -m uvicorn app.main:app --reload
> ```

---

### 2. `schemas.py` — `TokenWithUser` 추가

로그인 성공 시 토큰과 유저 정보를 한 번에 반환하는 통합 스키마 추가.

```python
class TokenWithUser(BaseModel):
    access_token: str
    token_type: str
    user: UserOut  # id, name, email, provider 포함
```

---

### 3. `router.py` — `/auth/login` 응답 수정

```python
# Before
return {"access_token": access_token, "token_type": "bearer"}

# After
return {"access_token": access_token, "token_type": "bearer", "user": user}
```

---

### 4. `router.py` — `/auth/kakao` S2S OAuth 완전 구현

**Before (잘못된 구현):**
- 프론트엔드가 액세스 토큰을 `code` 필드로 직접 전달한다고 가정
- 카카오 서버와의 토큰 교환 없이 `code` 값을 바로 Bearer 토큰으로 사용

**After (올바른 S2S 흐름):**
```
프론트엔드 → 인가 코드(code) → 백엔드
백엔드 → POST kauth.kakao.com/oauth/token → 카카오 액세스 토큰 획득
백엔드 → GET kapi.kakao.com/v2/user/me → 유저 정보 획득
백엔드 → DB에서 유저 조회/생성/연동
백엔드 → 자체 JWT 발급 → 프론트엔드
```

**계정 처리 로직:**
| 케이스 | 처리 |
|--------|------|
| 신규 카카오 유저 | 새 계정 생성 (`provider=kakao`) |
| 동일 `social_id` 기존 유저 | 기존 계정으로 로그인 |
| 동일 이메일 기존 이메일 유저 | `social_id` 연동 후 로그인 |

---

## 환경 변수 설정

### `backend/.env` (gitignore, 직접 생성 필요)
```
KAKAO_CLIENT_ID=<Kakao Developers REST API 키>
KAKAO_REDIRECT_URI=http://localhost:5173/auth/kakao/callback
JWT_SECRET_KEY=<강력한 랜덤 문자열>
```

> `KAKAO_REDIRECT_URI`는 카카오 개발자 콘솔에 등록된 값과 반드시 일치해야 함.

---

## 인증 아키텍처 요약 (Unified Session)

```
[이메일] 비밀번호 검증 ─┐
                        ├─→ create_access_token(user.id) → JWT 반환
[카카오] OAuth 토큰 검증 ─┘

이후 모든 인증: JWT만 검사 (로그인 방식 무관)
```

- `User` 테이블 단일화: `provider` (email/kakao), `social_id`, `password_hash` (nullable)
- 향후 구글/애플 로그인 추가 시 DB 수정 없이 `AuthService` 로직만 확장 가능

---

## 결과
- 이메일 로그인/회원가입/탈퇴: 정상 동작
- 카카오 S2S 로그인: 인가 코드 → 카카오 토큰 교환 → 유저 생성 → JWT 발급 완성
- 백엔드 서버 정상 구동 확인 (`Loaded environment variables from .../backend/.env`)

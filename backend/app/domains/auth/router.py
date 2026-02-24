from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session_factory
from app.domains.auth import models, schemas, security

router = APIRouter()

def get_db():
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = security.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        password_hash=hashed_password,
        name=user.name,
        provider="email"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.TokenWithUser)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials"
        )

    if not user.password_hash or not security.verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials"
        )

    access_token = security.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.post("/logout")
def logout():
    # Stateless JWT removes capability of explicit logout on server.
    # We rely on client to delete the token, but we return a success response.
    return {"message": "Successfully logged out. Please remove token from client headers."}

@router.delete("/withdraw")
def withdraw(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    db.delete(current_user)
    db.commit()
    return {"message": "User account successfully deleted."}

import httpx
import os

@router.post("/kakao", response_model=schemas.TokenWithUser)
async def kakao_login(kakao_data: schemas.KakaoLogin, db: Session = Depends(get_db)):
    kakao_client_id = os.getenv("KAKAO_CLIENT_ID")
    kakao_redirect_uri = os.getenv("KAKAO_REDIRECT_URI")
    kakao_client_secret = os.getenv("KAKAO_CLIENT_SECRET", "")

    if not kakao_client_id or not kakao_redirect_uri:
        raise HTTPException(status_code=500, detail="Kakao OAuth is not configured on the server")

    # 1. S2S: authorization code → Kakao access token
    token_payload = {
        "grant_type": "authorization_code",
        "client_id": kakao_client_id,
        "redirect_uri": kakao_redirect_uri,
        "code": kakao_data.code,
    }
    if kakao_client_secret:
        token_payload["client_secret"] = kakao_client_secret

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://kauth.kakao.com/oauth/token",
            data=token_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code with Kakao")

    kakao_access_token = token_res.json().get("access_token")

    # 2. S2S: Kakao access token → user info
    async with httpx.AsyncClient() as client:
        user_res = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {kakao_access_token}"},
        )

    if user_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve user info from Kakao")

    kakao_user = user_res.json()
    social_id = str(kakao_user.get("id"))
    email = kakao_user.get("kakao_account", {}).get("email", f"{social_id}@kakao.com")
    name = kakao_user.get("properties", {}).get("nickname", "KakaoUser")

    # 3. Find or create user (unified account)
    user = db.query(models.User).filter(
        (models.User.social_id == social_id) | (models.User.email == email)
    ).first()

    if not user:
        user = models.User(email=email, name=name, provider="kakao", social_id=social_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not user.social_id:
        # Existing email account → Collision found. Require password validation.
        temp_token = security.create_temp_token(data={"sub": str(user.id), "social_id": social_id})
        raise HTTPException(
            status_code=409,
            detail={
                "code": "ACCOUNT_COLLISION_REQUIRE_PASSWORD",
                "message": "이미 이메일로 가입된 계정이 있습니다. 본인 확인을 위해 기존 비밀번호를 입력해 주세요.",
                "data": {
                    "email": email,
                    "oauth_provider": "KAKAO",
                    "temp_token": temp_token
                }
            }
        )
    elif user.social_id != social_id:
        # Rare case: email already linked to a DIFFERENT kakao account
        raise HTTPException(status_code=400, detail="이메일이 다른 소셜 계정에 이미 연동되어 있습니다.")

    access_token = security.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.post("/link-account", response_model=schemas.TokenWithUser)
def link_account(data: schemas.LinkAccountRequest, db: Session = Depends(get_db)):
    payload = security.verify_temp_token(data.temp_token)
    if not payload:
        raise HTTPException(status_code=401, detail="임시 토큰이 만료되었거나 유효하지 않습니다.")
    
    user_id_str = payload.get("sub")
    social_id = payload.get("social_id")
    
    user = db.query(models.User).filter(models.User.id == int(user_id_str)).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
    if not user.password_hash or not security.verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다.")
        
    # Link account
    user.social_id = social_id
    user.provider = "kakao"
    db.commit()
    db.refresh(user)
    
    access_token = security.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

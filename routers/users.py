from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
from database import get_db
from schemas.user import UserCreate, UserResponse
from services.password_service import hash_password


router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    # 1. 동일한 이메일이 이미 존재하는지 확인
    existing_user = (
        db.query(models.User)
        .filter(models.User.email == user.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 등록된 이메일입니다."
        )

    # 2. 비밀번호 해싱
    hashed_password = hash_password(user.password)

    # 3. 사용자 객체 생성
    db_user = models.User(
        name=user.name,
        email=user.email,
        password=hashed_password
    )

    # 4. DB에 저장
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
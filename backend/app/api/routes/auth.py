from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import authenticate_user, get_user_by_email
from app.core.security import create_access_token, get_password_hash
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserRead


router = APIRouter()


@router.post("/login", response_model=Token)
async def login(form_data: LoginRequest, session: AsyncSession = Depends(get_db)) -> Token:
    user = await authenticate_user(session, form_data.email, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    token = create_access_token(user.id)
    return Token(access_token=token)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, session: AsyncSession = Depends(get_db)) -> User:
    existing = await get_user_by_email(session, user_in.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(
        name=user_in.name,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_active=user_in.is_active,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

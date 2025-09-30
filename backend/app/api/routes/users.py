from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter()


@router.get("/", response_model=list[UserRead])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[User]:
    result = await session.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> User:
    result = await session.execute(select(User).where(User.email == user_in.email))
    if result.scalars().first():
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


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        user.hashed_password = get_password_hash(update_data.pop("password"))
    for field, value in update_data.items():
        setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> None:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await session.delete(user)
    await session.commit()
    return None

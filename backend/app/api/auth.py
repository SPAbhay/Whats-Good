from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import jwt
from sqlalchemy.sql import Select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.base_class import get_async_session
from app.models.brand import BrandResponse, Brand
from app.models.user import User, UserCreate, UserResponse
from app.services.brand_processor import BrandProcessor
from core.config import Settings

settings = Settings()
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(days=1)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_session)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    query = select(User).where(and_(User.email == email))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    return user

@router.post("/signup", response_model=dict)
async def signup(
    user_create: UserCreate,
    db: AsyncSession = Depends(get_async_session)
):
    # Check if user exists
    query = select(User).where(and_(User.email == user_create.email))
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    hashed_password = get_password_hash(user_create.password)
    new_user = User(
        name=user_create.name,
        email=user_create.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Create access token
    access_token = create_access_token(
        data={"sub": new_user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(new_user)
    }


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login(
        request: LoginRequest,
        db: AsyncSession = Depends(get_async_session)
):
    # Find user
    query = select(User).where(and_(User.email == request.email))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }


# Separate endpoint for form-based login
@router.post("/login/token")
async def login_form(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_async_session)
):
    # Find user
    query = select(User).where(and_(User.email == form_data.username))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return current_user


# Add these Pydantic models if not already present
class BrandQuestionnaireResponse(BaseModel):
    raw_brand_name: str
    raw_industry_focus: str
    raw_target_audience: str
    raw_unique_value: str
    raw_social_platforms: Optional[str]
    raw_successful_content: Optional[str]


# Update the brand endpoints with proper paths
@router.post("/brand/questionnaire", response_model=BrandResponse)
async def submit_brand_questionnaire(
        questionnaire: BrandQuestionnaireResponse,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    stmt: Select = select(Brand).where(
        and_(Brand.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    existing_brand = result.scalar_one_or_none()

    if existing_brand:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brand profile already exists for this user"
        )

    try:
        new_brand = Brand(
            user_id=current_user.id,
            raw_brand_name=questionnaire.raw_brand_name,
            raw_industry_focus=questionnaire.raw_industry_focus,
            raw_target_audience=questionnaire.raw_target_audience,
            raw_unique_value=questionnaire.raw_unique_value,
            raw_social_platforms=questionnaire.raw_social_platforms,
            raw_successful_content=questionnaire.raw_successful_content
        )

        db.add(new_brand)
        await db.commit()
        await db.refresh(new_brand)

        return new_brand

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/brand/{brand_id}/process", response_model=BrandResponse)
async def process_brand_responses(
    brand_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    # Verify ownership
    brand = await get_brand_by_id_and_user(brand_id, current_user.id, db)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found or access denied"
        )

    processor = BrandProcessor()
    processed_brand = await processor.process_brand_responses(brand_id, db)

    if not processed_brand:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process brand responses"
        )

    return processed_brand

@router.get("/brand/profile", response_model=BrandResponse)
async def get_brand_profile(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    stmt: Select = select(Brand).where(
        and_(Brand.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    brand = result.scalar_one_or_none()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand profile not found"
        )

    return brand


@router.put("/brand/profile", response_model=BrandResponse)
async def update_brand_profile(
        questionnaire: BrandQuestionnaireResponse,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_session)
):
    stmt: Select = select(Brand).where(
        and_(Brand.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    existing_brand = result.scalar_one_or_none()

    if not existing_brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand profile not found"
        )

    try:
        for field, value in questionnaire.model_dump().items():
            setattr(existing_brand, field, value)

        await db.commit()
        await db.refresh(existing_brand)
        return existing_brand

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
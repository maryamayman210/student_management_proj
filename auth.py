from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.schemas.token import Token
from app.services.auth_service import AuthService
from app.utils.logger import log_auth_event, log_error
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = AuthService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    new_user = AuthService.create_user(db, user_data)
    return new_user

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db), request: Request = None):
    try:
        user = AuthService.authenticate_user(db, user_data.email, user_data.password)
        if not user:
            log_auth_event(user_data.email, success=False, error="Wrong credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        log_auth_event(user_data.email, success=True)
        token_data = AuthService.create_user_token(user)
        return token_data
    except Exception as e:
        log_error(e, "Login endpoint")
        raise

@router.post("/logout")
def logout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """تسجيل الخروج"""
    return AuthService.logout(db, current_user.id, request)
@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """الحصول على معلومات المستخدم الحالي"""
    # تحديث آخر نشاط (اختياري)
    return current_user
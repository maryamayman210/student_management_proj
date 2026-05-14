from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from app.models.models import UserRole, Department


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.student


class UserLoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Student Schemas ──────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    student_id: str = Field(..., min_length=3, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    department: Department
    gpa: float = Field(default=0.0, ge=0.0, le=4.0)
    year: int = Field(..., ge=1, le=6)
    address: Optional[str] = None
    user_id: Optional[int] = None

    @field_validator("gpa")
    @classmethod
    def validate_gpa(cls, v):
        return round(v, 2)


class StudentUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = None
    department: Optional[Department] = None
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    year: Optional[int] = Field(None, ge=1, le=6)
    address: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("gpa")
    @classmethod
    def validate_gpa(cls, v):
        if v is not None:
            return round(v, 2)
        return v


class StudentAdminUpdate(StudentUpdate):
    """Admin can also update email and student_id"""
    email: Optional[EmailStr] = None
    student_id: Optional[str] = Field(None, min_length=3, max_length=20)


class StudentResponse(BaseModel):
    id: int
    student_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    department: Department
    gpa: float
    year: int
    is_active: bool
    address: Optional[str]
    user_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaginatedStudentResponse(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    students: List[StudentResponse]


# ─── Audit Log Schemas ────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: int
    student_id: Optional[int]
    performed_by: int
    action: str
    details: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


# ─── General ─────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    database: str
    cache: str
    version: str

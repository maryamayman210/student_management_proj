from fastapi import Depends, HTTPException, status
from app.auth import get_current_user
from app.utils.roles import UserRole

def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only: you do not have permission"
        )
    return current_user


def require_student_or_admin(current_user=Depends(get_current_user)):
    if current_user.role not in [UserRole.ADMIN.value, UserRole.STUDENT.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    return current_user


def check_student_access(student_id: int, current_user):
    """
    Admin can access any student.
    Student can access only own profile.
    """
    if current_user.role == UserRole.ADMIN.value:
        return True

    if current_user.role == UserRole.STUDENT.value:
        if current_user.student_id == student_id:
            return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: you can only access your own profile"
    )
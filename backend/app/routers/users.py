"""Routes for the signed-in user's own profile."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import verify_password
from app.database.database import get_db
from app.models.user import User
from app.schemas.user import DeleteAccountRequest, UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=UserRead)
def get_my_profile(current_user: User = Depends(get_current_user)) -> UserRead:
    """Return the profile attached to the valid bearer token."""
    return current_user


@router.patch("/me", response_model=UserRead)
def update_my_profile(
    updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRead:
    """Change the signed-in user's name or email address."""
    return UserService(db).update_profile(current_user, updates)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    request: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Delete the signed-in account after confirming its current password."""
    if not verify_password(request.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password is incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    UserService(db).delete_account(current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

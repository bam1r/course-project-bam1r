from fastapi import Header, HTTPException
from pydantic import BaseModel

from app.models.user import UserRole


class CurrentUser(BaseModel):
    id: int
    role: UserRole


def get_current_user(
    x_user_id: int = Header(default=None, alias="X-User-Id"),
    x_user_role: UserRole = Header(default=None, alias="X-User-Role"),
) -> CurrentUser:
    return CurrentUser(id=x_user_id, role=x_user_role)


def require_admin(current_user: CurrentUser) -> None:
    if current_user.role != UserRole.admin:
        raise HTTPException(403, "This operation requires administrator privileges")


def ensure_owner_or_admin(owner_id: int, current_user: CurrentUser) -> None:
    if current_user.role == UserRole.admin:
        return
    if current_user.id != owner_id:
        raise HTTPException(403, "You can only access your own resources")

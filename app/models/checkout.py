from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class CheckoutStatus(str, Enum):
    active = "active"
    returned = "returned"
    overdue = "overdue"


class Checkout(BaseModel):
    id: int
    asset_id: int
    due_at: datetime
    status: CheckoutStatus
    owner_id: int


class CheckoutCreate(BaseModel):
    asset_id: int = Field(..., gt=0, description="Asset ID (must be positive)")
    due_at: datetime = Field(..., description="Due date and time (UTC)")
    status: CheckoutStatus = CheckoutStatus.active

    @field_validator("asset_id")
    @classmethod
    def validate_asset_id(cls, v: int) -> int:
        """Validate asset ID is positive."""
        if v <= 0:
            raise ValueError("Asset ID must be a positive integer")
        return v


    @field_validator("due_at")
    @classmethod
    def normalize_datetime(cls, v: datetime) -> datetime:
        """Normalize datetime to UTC and ensure it's timezone-aware."""
        if v.tzinfo is None:
            # Assume naive datetime is UTC
            v = v.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC
            v = v.astimezone(timezone.utc)
        return v

    @model_validator(mode="after")
    def validate_due_date(self) -> CheckoutCreate:
        """Validate due date is in the future for new checkouts."""
        if self.status == CheckoutStatus.active:
            now = datetime.now(timezone.utc)
            if self.due_at <= now:
                raise ValueError("Due date must be in the future for active checkouts")
        return self


class CheckoutOut(BaseModel):
    id: int
    asset_id: int
    due_at: datetime
    status: CheckoutStatus
    owner_id: int


ALLOWED_STATUS_TRANSITIONS = {
    CheckoutStatus.active: {CheckoutStatus.returned, CheckoutStatus.overdue},
    CheckoutStatus.overdue: {CheckoutStatus.returned},
    CheckoutStatus.returned: set(),
}


def can_transition(
    current_status: Optional[CheckoutStatus], next_status: CheckoutStatus
) -> bool:
    if current_status is None:
        # Fresh checkout must always start as active per business rules.
        return next_status == CheckoutStatus.active
    return next_status in ALLOWED_STATUS_TRANSITIONS.get(current_status, set())


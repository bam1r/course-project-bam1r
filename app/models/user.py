from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class UserRole(str, Enum):
    student = "student"
    admin = "admin"


class User(BaseModel):
    id: int
    name: str
    email: EmailStr
    password: str
    role: UserRole


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="User full name")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    role: UserRole

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Normalize and validate name."""
        if not v:
            raise ValueError("Name cannot be empty")
        # Trim and normalize whitespace
        v = " ".join(v.strip().split())
        if not v:
            raise ValueError("Name cannot be only whitespace")
        # Reject names with only special characters
        if not re.match(r"^[\w\s\-'\.]+$", v):
            raise ValueError("Name contains invalid characters")
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email (lowercase, trim)."""
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 128:
            raise ValueError("Password must be at most 128 characters long")
        # Check for at least one letter and one digit (basic strength)
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v

    @model_validator(mode="after")
    def validate_model(self) -> UserCreate:
        """Additional model-level validation."""
        # Ensure name is not empty after normalization
        if not self.name.strip():
            raise ValueError("Name cannot be empty")
        return self


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
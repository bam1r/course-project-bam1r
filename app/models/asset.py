from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator


class Asset(BaseModel):
    id: int
    title: str
    inv_id: str


class AssetCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Asset title/name")
    inv_id: str = Field(..., min_length=1, max_length=50, description="Inventory ID")

    @field_validator("title")
    @classmethod
    def normalize_title(cls, v: str) -> str:
        """Normalize title (trim, collapse whitespace)."""
        if not v:
            raise ValueError("Title cannot be empty")
        # Trim and normalize whitespace
        v = " ".join(v.strip().split())
        if not v:
            raise ValueError("Title cannot be only whitespace")
        return v

    @field_validator("inv_id")
    @classmethod
    def validate_inv_id(cls, v: str) -> str:
        """Validate and normalize inventory ID format."""
        if not v:
            raise ValueError("Inventory ID cannot be empty")
        # Trim and convert to uppercase
        v = v.strip().upper()
        # Validate format: alphanumeric with optional dashes/underscores
        # Example: INV-001, ASSET_123, ABC-123-XYZ
        if not re.match(r"^[A-Z0-9\-_]+$", v):
            raise ValueError("Inventory ID must contain only uppercase letters, numbers, dashes, and underscores")
        if len(v) < 3:
            raise ValueError("Inventory ID must be at least 3 characters long")
        return v


class AssetOut(BaseModel):
    id: int
    title: str
    inv_id: str


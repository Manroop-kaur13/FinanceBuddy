"""Shared API schema behavior."""

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    """Base schema that trims user-entered strings before validation."""

    model_config = ConfigDict(str_strip_whitespace=True)

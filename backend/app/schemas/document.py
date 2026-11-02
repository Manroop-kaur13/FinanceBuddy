from app.schemas.base import APIModel
"""Document metadata request and response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field


class DocumentCreate(APIModel):
    document_name: str = Field(min_length=1, max_length=160)
    file_name: str = Field(min_length=1, max_length=255)
    document_type: str = Field(min_length=1, max_length=60)
    storage_key: str = Field(min_length=1, max_length=512)


class DocumentRead(APIModel):
    id: UUID
    user_id: UUID
    document_name: str
    file_name: str
    document_type: str
    storage_key: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

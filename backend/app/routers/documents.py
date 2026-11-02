"""Document metadata endpoints. File upload is a separate storage concern."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentRead
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.get("", response_model=list[DocumentRead])
def list_documents(
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    return DocumentService(db, user.id).get_documents(limit=limit, offset=offset)


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def create_document_metadata(
    data: DocumentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentRead:
    return DocumentService(db, user.id).create_document(data)


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentRead:
    return DocumentService(db, user.id).get_owned(document_id)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    DocumentService(db, user.id).delete_document(document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

"""User-scoped document metadata operations."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.document import DocumentCreate
from app.services.base import OwnedService


class DocumentService(OwnedService):
    """Store metadata only; file bytes belong in a private object-storage service."""

    model = Document

    def __init__(self, db: Session, user_id: UUID) -> None:
        super().__init__(db, user_id)

    def create_document(self, data: DocumentCreate) -> Document:
        document = Document(user_id=self.user_id, **data.model_dump())
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_documents(self, *, limit: int = 100, offset: int = 0) -> list[Document]:
        return self.list_owned(limit=limit, offset=offset)

    def delete_document(self, document_id: UUID) -> None:
        self.db.delete(self.get_owned(document_id))
        self.db.commit()

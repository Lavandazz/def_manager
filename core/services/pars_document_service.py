from config.db.models import ParsDocument
from core.repository.pars_documents_repository import ParsDocumentAlchemyRepository


class ParsDocumentService:
    """
    Сервис-прослойка между API и репозиторием документов.
    Делегирует все операции репозиторию.
    """

    def __init__(self, repository: ParsDocumentAlchemyRepository):
        self.repository = repository

    async def add_document(self, document: ParsDocument) -> ParsDocument | None:
        return await self.repository.add_document(document)

    async def get_document(self, document_id: int) -> ParsDocument | None:
        return await self.repository.get_document(document_id)

    async def get_documents_by_case(
        self, case_id: int, page: int = 1, size: int = 10
    ) -> tuple[list[ParsDocument], int]:
        return await self.repository.get_documents_by_case(case_id, page, size)

    async def get_documents_by_status(self, status: str) -> list[ParsDocument]:
        return await self.repository.get_documents_by_status(status)

    async def update_document(self, document_id: int, **kwargs) -> ParsDocument | None:
        return await self.repository.update_document(document_id, **kwargs)

    async def delete_document(self, document_id: int) -> bool:
        return await self.repository.delete_document(document_id)
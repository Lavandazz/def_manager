from datetime import date

from sqlalchemy import desc, func, select
from sqlalchemy.orm import selectinload
from config.db.models import ParsDocument
from config.logger_config import db_logger


class ParsDocumentAlchemyRepository:
    """
    Репозиторий для работы с таблицей pars_documents через SQLAlchemy.
    Предоставляет методы CRUD, фильтрацию по делу и статусу, пагинацию.
    """

    def __init__(self, session):
        self.session = session

    async def add_document(self, document: ParsDocument) -> ParsDocument | None:
        """
        Сохраняет новый документ в БД.
        """
        try:
            db_logger.info(f"Сохраняю документ {document.document}")
            self.session.add(document)
            await self.session.commit()   
            db_logger.info(f"Сохранен документ {document.document}")
            return document
        except Exception as e:
            db_logger.exception("Не удалось сохранить документ в БД: %s", e)
            await self.session.rollback()

    async def exists_document(self, case_id: int, date: date, declarer: str, document_name: str) -> bool:
        try:
            db_logger.info("Начинается проверка документа перед сохранением")
            stmt = select(ParsDocument).where(
                ParsDocument.id_case == case_id,
                ParsDocument.date == date,
                ParsDocument.declarer == declarer,
                ParsDocument.document == document_name)
            result = await self.session.execute(stmt.limit(1))
            db_logger.info(f"Окончена проверка документа перед сохранением")
            return result.scalar() is not None
        
        except Exception as e:
            db_logger.error(f"Ошибка при проверке документа: {e}")
            return False


    async def get_document(self, document_id: int) -> ParsDocument | None:
        """
        Возвращает документ по его id.
        """
        stmt = select(ParsDocument).where(ParsDocument.id == document_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_documents_by_case(
        self, case_id: int, page: int = 1, size: int = 10
    ) -> tuple[list[ParsDocument], int]:
        """
        Возвращает документы, привязанные к конкретному делу, с пагинацией.
        Сортировка по дате (новые сверху).
        Возвращает кортеж (список документов, общее количество).
        """
        # Общее количество документов по делу
        total_query = select(func.count()).select_from(ParsDocument).where(
            ParsDocument.id_case == case_id
        )
        total_result = await self.session.execute(total_query)
        total = total_result.scalar_one()

        # Документы для текущей страницы
        stmt = (
            select(ParsDocument)
            .where(ParsDocument.id_case == case_id)
            .order_by(desc(ParsDocument.date))
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.session.execute(stmt)
        documents = result.scalars().all()
        return documents, total

    async def get_documents_by_status(self, status: str) -> list[ParsDocument]:
        """
        Возвращает все документы с указанным статусом.
        """
        stmt = select(ParsDocument).where(ParsDocument.status == status)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_document(self, document_id: int, **kwargs) -> ParsDocument | None:
        """
        Обновляет поля документа, переданные в kwargs.
        Возвращает обновлённый объект или None, если документ не найден.
        """
        try:
            stmt = select(ParsDocument).where(ParsDocument.id == document_id)
            result = await self.session.execute(stmt)
            document = result.scalars().first()
            if not document:
                return None

            for key, value in kwargs.items():
                if hasattr(document, key):
                    setattr(document, key, value)

            await self.session.commit()
            return document
        except Exception as e:
            await self.session.rollback()
            db_logger.exception("Не удалось обновить документ (id=%s): %s", document_id, e)

    async def delete_document(self, document_id: int) -> bool:
        """
        Удаляет документ по id. Возвращает True, если удаление выполнено.
        """
        try:
            stmt = select(ParsDocument).where(ParsDocument.id == document_id)
            result = await self.session.execute(stmt)
            document = result.scalars().first()
            if not document:
                return False

            await self.session.delete(document)
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            db_logger.exception("Не удалось удалить документ (id=%s): %s", document_id, e)
            return False

        
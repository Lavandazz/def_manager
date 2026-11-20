"""
Сервис для генерации документов в формате Word.
Запросы генерируются в банки и инстанции
"""

import asyncio
import io
import zipfile
from pathlib import Path
from docxtpl import DocxTemplate

from shared.utils.exceptions import DocumentsDirNotFound
from shared.config.logger_config import gen_logger 


BASE_DIR = Path.cwd() / "shared"
TEMPLATES_DIR = BASE_DIR / "documents" / "templates"
OUTPUT_DIR = BASE_DIR / "documents" / "ready_documents"


class DocumentGenerator:
    """Синхронный движок для одного шаблона. Не хранит состояние между вызовами."""

    def __init__(self, template_path: Path):
        self.template_path = template_path

    def _render_sync( self, context: dict, output_path: Path) -> Path:
        docx = DocxTemplate(self.template_path)
        docx.render(context)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        docx.save(output_path)
        return output_path

    async def generate(
        self,
        context: dict,
        output_filename: str,
        subdir: str | None = None,
    ) -> Path:
        out_dir = OUTPUT_DIR / subdir if subdir else OUTPUT_DIR
        output_path = out_dir / output_filename
        # имя файла  проверяем - не должно содержать ../..
        if output_path.resolve().parent != out_dir:
            raise ValueError(f"Некорректное имя файла: {output_filename}")
        return await asyncio.to_thread(self._render_sync, context, output_path)


class DocumentService:
    """Оркестратор: запускает несколько генераций параллельно."""

    def __init__(self):
        self.bank_template = DocumentGenerator(TEMPLATES_DIR / "bank_mo.docx")
        self.requests_template = DocumentGenerator(TEMPLATES_DIR / "requests_mo.docx")

    async def generate_request_doc(self, user_id: int, context: dict, short_name: str) -> Path:
        """Возвращаем ссылку на документ"""
        try:
            subdir = f"user_{user_id}/{short_name}"
            return await self.requests_template.generate(
                context=context,
                output_filename=f"{short_name}.docx",
                subdir=f"{subdir}/requests",
            )
        except Exception as e:
            gen_logger.error(f"Ошибка генерации запросов в госорганы: {e}")

    async def _generate_bank_doc(self, user_id: int, context: dict, short_name: str, bank_name: str) -> Path:
        """Возвращаем ссылку на документ"""
        subdir = f"user_{user_id}/{short_name}"
        try:
            return await self.bank_template.generate(
                context=context,
                output_filename=f"{short_name}_{bank_name}.docx",
                subdir=f"{subdir}/banks",
            )
        except Exception as e:
            gen_logger.error(f"Ошибка генерации запросов в банки: {e}")

    async def generate_banks_docs(self, user_id, contexts: list[dict], short_name: str,) -> list[Path]:
        """Запустить несколько генераций параллельно."""
        tasks = [
            self._generate_bank_doc(user_id,
                context=ctx,
                short_name=short_name,
                bank_name=ctx["debtor_bank"]
            )
            for ctx in contexts
        ]
        return await asyncio.gather(*tasks)

    async def get_documents_path(self, user_id: int, debtor_short_name: str) -> Path:
        """Получение пути для выгрузки документов"""
        dir_path: Path = (OUTPUT_DIR / f"user_{user_id}" / debtor_short_name).resolve()
        # is_relative_to — защита от traversal (../../..)
        #  лежит ли путь внутри OUTPUT_DIR ( не трогает диск, не проверяет существование файла, сравнивает строку пути)
        if not dir_path.is_relative_to(OUTPUT_DIR.resolve()): 
            gen_logger.warning(f"Попытка загрузки документов {dir_path} не валидный")
            raise DocumentsDirNotFound(dir_path)   
        
        if not dir_path.is_dir():
            gen_logger.warning(f"Загрузка пути к документам {dir_path} - путь не существует")
            raise DocumentsDirNotFound(dir_path)
        
        return dir_path

    @staticmethod
    def zip_folder(folder: Path) -> io.BytesIO:
        """Собирает все файлы из folder (включая подпапки) в zip-архив в памяти."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in folder.rglob("*"):        # rglob = рекурсивно, включая подпапки
                if f.is_file():
                    # arcname — путь относительно folder, чтобы сохранить структуру подпапок
                    zf.write(f, arcname=f.relative_to(folder))
        buffer.seek(0)                          # перемотать в начало, чтобы читать с нуля
        return buffer
        
        
    
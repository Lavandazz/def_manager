"""
Сервис для генерации документов в формате Word.
Запросы генерируются в банки и инстанции
"""

import asyncio
from pathlib import Path

from docxtpl import DocxTemplate


BASE_DIR = Path.cwd() / "documents"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "ready_documents"


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

    # async def generate( self, context: dict, output_filename: str, subdir: str | None = None) -> Path:
    #     out_dir = OUTPUT_DIR / subdir if subdir else OUTPUT_DIR
    #     output_path = out_dir / output_filename

    #     loop = asyncio.get_running_loop()
    #     return await loop.run_in_executor(
    #         None,
    #         self._render_sync,
    #         context,
    #         output_path,
    #     )
    async def generate(
        self,
        context: dict,
        output_filename: str,
        subdir: str | None = None,
    ) -> Path:
        out_dir = OUTPUT_DIR / subdir if subdir else OUTPUT_DIR
        output_path = out_dir / output_filename
        return await asyncio.to_thread(self._render_sync, context, output_path)


class DocumentService:
    """Оркестратор: запускает несколько генераций параллельно."""

    def __init__(self):
        self.bank_template = DocumentGenerator(TEMPLATES_DIR / "bank_mo.docx")
        self.requests_template = DocumentGenerator(TEMPLATES_DIR / "requests_mo.docx")

    async def generate_bank_doc(self, context: dict, short_name: str, bank_name: str) -> Path:
        return await self.bank_template.generate(
            context=context,
            output_filename=f"{short_name}_{bank_name}.docx",
            subdir="banks",
        )

    async def generate_request_doc(self, context: dict, short_name: str) -> Path:
        return await self.requests_template.generate(
            context=context,
            output_filename=f"{short_name}.docx",
            subdir="requests",
        )

    async def generate_many(self, tasks_spec: list[dict]) -> list[Path]:
        """Запустить несколько генераций параллельно."""
        tasks = [
            self.generate_request_doc(spec["context"], spec["short_name"])
            for spec in tasks_spec
        ]
        return await asyncio.gather(*tasks)
    
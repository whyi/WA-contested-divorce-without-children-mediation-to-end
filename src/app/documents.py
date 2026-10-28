import io
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from zipfile import BadZipFile

import fitz
from docx import Document as WordDocument
from docx.opc.exceptions import PackageNotFoundError
from docxtpl import DocxTemplate
from jinja2.exceptions import TemplateError
from jinja2.sandbox import SandboxedEnvironment
from lxml.etree import XMLSyntaxError
from pdf2docx import Converter
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.config import Settings, get_settings
from app.validation import validate_upload

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PDF_MEDIA_TYPE = "application/pdf"


@dataclass(frozen=True)
class ExtractedDocument:
    text: str
    page_count: int


def render_template(template_bytes: bytes, context: dict) -> bytes:
    try:
        template = DocxTemplate(io.BytesIO(template_bytes))
        template.render(context, jinja_env=SandboxedEnvironment(autoescape=True))
        output = io.BytesIO()
        template.save(output)
    except (BadZipFile, PackageNotFoundError, TemplateError, XMLSyntaxError) as error:
        raise ValueError("The uploaded DOCX template could not be rendered.") from error
    result = output.getvalue()
    validate_upload("rendered.docx", result, "docx", get_settings().max_upload_bytes)
    return result


def convert_docx_to_pdf(docx_bytes: bytes, settings: Settings | None = None) -> bytes:
    settings = settings or get_settings()
    validate_upload("source.docx", docx_bytes, "docx", settings.max_upload_bytes)

    with tempfile.TemporaryDirectory(prefix="mediation-docx-") as directory:
        source = Path(directory) / "source.docx"
        source.write_bytes(docx_bytes)
        destination = Path(directory) / "source.pdf"

        if os.name == "nt" or (os.name == "posix" and os.uname().sysname == "Darwin"):
            from docx2pdf import convert

            convert(str(source), str(destination))
        else:
            office = shutil.which("libreoffice") or shutil.which("soffice")
            if not office:
                raise RuntimeError("DOCX-to-PDF rendering requires LibreOffice on this platform.")
            try:
                subprocess.run(
                    [
                        office,
                        "--headless",
                        f"-env:UserInstallation=file://{directory}/lo-profile",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        directory,
                        str(source),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=settings.conversion_timeout_seconds,
                )
            except subprocess.TimeoutExpired as error:
                raise TimeoutError("DOCX-to-PDF rendering exceeded its time limit.") from error
            except subprocess.CalledProcessError as error:
                raise RuntimeError("LibreOffice could not render the DOCX file.") from error

        if not destination.is_file():
            raise RuntimeError("The DOCX-to-PDF renderer did not produce a PDF.")
        pdf_bytes = destination.read_bytes()
        validate_upload("rendered.pdf", pdf_bytes, "pdf", settings.max_upload_bytes)
        return pdf_bytes


def convert_pdf_to_docx(pdf_bytes: bytes, settings: Settings | None = None) -> bytes:
    settings = settings or get_settings()
    validate_upload("source.pdf", pdf_bytes, "pdf", settings.max_upload_bytes)
    page_count = _pdf_page_count(pdf_bytes, settings.max_pdf_pages)

    with tempfile.TemporaryDirectory(prefix="mediation-pdf-") as directory:
        source = Path(directory) / "source.pdf"
        destination = Path(directory) / "editable.docx"
        source.write_bytes(pdf_bytes)

        converter = Converter(str(source))
        try:
            converter.convert(str(destination), start=0, end=page_count)
        finally:
            converter.close()

        if not destination.is_file():
            raise RuntimeError("The PDF-to-DOCX converter did not produce a DOCX.")
        docx_bytes = destination.read_bytes()
        validate_upload("converted.docx", docx_bytes, "docx", settings.max_upload_bytes)
        return docx_bytes


def extract_document(
    content: bytes, document_type: str, settings: Settings | None = None
) -> ExtractedDocument:
    settings = settings or get_settings()
    validate_upload(
        f"source.{document_type}",
        content,
        document_type,
        settings.max_upload_bytes,
    )

    if document_type == "docx":
        try:
            document = WordDocument(io.BytesIO(content))
        except (BadZipFile, PackageNotFoundError, XMLSyntaxError) as error:
            raise ValueError("The uploaded DOCX file is not readable.") from error
        text_parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        for table in document.tables:
            for row in table.rows:
                text_parts.append(" | ".join(cell.text for cell in row.cells))
        return ExtractedDocument("\n".join(text_parts), 1)

    if document_type == "pdf":
        page_count = _pdf_page_count(content, settings.max_pdf_pages)
        try:
            reader = PdfReader(io.BytesIO(content), strict=True)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except PdfReadError as error:
            raise ValueError("The uploaded PDF could not be parsed.") from error
        return ExtractedDocument(text, page_count)

    raise ValueError(f"Unsupported document type: {document_type}")


def _pdf_page_count(content: bytes, max_pages: int) -> int:
    try:
        with fitz.open(stream=content, filetype="pdf") as document:
            page_count = document.page_count
    except fitz.FileDataError as error:
        raise ValueError("The uploaded file is not a readable PDF.") from error
    if page_count == 0:
        raise ValueError("The PDF contains no pages.")
    if page_count > max_pages:
        raise ValueError(f"The PDF exceeds the {max_pages}-page limit.")
    return page_count

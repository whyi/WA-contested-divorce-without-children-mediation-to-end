import io
import unittest
from zipfile import ZipFile

import fitz
from docx import Document as WordDocument

from app.config import Settings
from app.documents import DocumentExtractionError, extract_document


def create_pdf(page_texts: list[str], password: str | None = None) -> bytes:
    document = fitz.open()
    for text in page_texts:
        page = document.new_page()
        if text:
            page.insert_text((72, 72), text)
    options = {}
    if password is not None:
        options = {
            "encryption": fitz.PDF_ENCRYPT_AES_256,
            "owner_pw": "owner-password",
            "user_pw": password,
        }
    return document.tobytes(**options)


def create_docx() -> bytes:
    document = WordDocument()
    document.add_paragraph("Settlement proposal")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Asset"
    table.cell(0, 1).text = "Value"
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def create_malformed_docx() -> bytes:
    output = io.BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document")
    return output.getvalue()


class DocumentExtractionTests(unittest.TestCase):
    def test_pdf_text_preserves_one_based_page_boundaries(self) -> None:
        result = extract_document(create_pdf(["First page", "Second page"]), "pdf")

        self.assertEqual(result.text, "First page\nSecond page")
        self.assertEqual(result.page_count, 2)
        self.assertEqual(
            [(page.page_number, page.text) for page in result.pages],
            [(1, "First page"), (2, "Second page")],
        )
        self.assertFalse(result.needs_attention)

    def test_pdf_with_a_page_without_selectable_text_needs_ocr(self) -> None:
        result = extract_document(create_pdf(["First page", ""]), "pdf")

        self.assertEqual(result.pages[0].text, "First page")
        self.assertEqual(result.pages[1].page_number, 2)
        self.assertTrue(result.needs_attention)
        self.assertEqual(result.error_code, "ocr_required")

    def test_password_protected_pdf_is_actionable_without_decryption(self) -> None:
        result = extract_document(create_pdf(["Private page"], "secret"), "pdf")

        self.assertTrue(result.needs_attention)
        self.assertEqual(result.error_code, "password_protected")
        self.assertEqual(result.pages, ())

    def test_default_page_limit_accepts_200_and_rejects_201_pages(self) -> None:
        accepted = extract_document(create_pdf(["page"] * 200), "pdf")
        self.assertEqual(accepted.page_count, 200)
        self.assertFalse(accepted.needs_attention)

        with self.assertRaises(DocumentExtractionError) as raised:
            extract_document(create_pdf(["page"] * 201), "pdf")
        self.assertEqual(raised.exception.error_code, "page_limit_exceeded")

    def test_pdf_page_limit_is_enforced_during_extraction(self) -> None:
        with self.assertRaisesRegex(DocumentExtractionError, "page limit"):
            extract_document(
                create_pdf(["First page", "Second page"]),
                "pdf",
                Settings(max_pdf_pages=1),
            )

    def test_docx_extraction_does_not_claim_physical_page_numbers(self) -> None:
        result = extract_document(create_docx(), "docx")

        self.assertIn("Settlement proposal", result.text)
        self.assertIn("Asset | Value", result.text)
        self.assertIsNone(result.pages[0].page_number)
        self.assertEqual(result.page_count, 1)

    def test_malformed_docx_is_actionable(self) -> None:
        with self.assertRaises(DocumentExtractionError) as raised:
            extract_document(create_malformed_docx(), "docx")

        self.assertEqual(raised.exception.error_code, "unreadable_file")


if __name__ == "__main__":
    unittest.main()

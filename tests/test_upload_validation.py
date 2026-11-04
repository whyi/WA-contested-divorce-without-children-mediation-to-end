import io
import unittest
from zipfile import ZipFile

from app.validation import UploadValidationError, validate_upload


def make_docx_container() -> bytes:
    output = io.BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    return output.getvalue()


def make_xlsx_container() -> bytes:
    output = io.BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("xl/workbook.xml", "<workbook/>")
    return output.getvalue()


class UploadValidationTests(unittest.TestCase):
    def test_accepts_docx_container_with_required_parts(self) -> None:
        validate_upload("draft.docx", make_docx_container(), "docx", 1024)

    def test_accepts_xlsx_container_with_required_parts(self) -> None:
        validate_upload("final.xlsx", make_xlsx_container(), "xlsx", 1024)

    def test_rejects_malformed_xlsx(self) -> None:
        with self.assertRaisesRegex(UploadValidationError, "valid Office workbook"):
            validate_upload("final.xlsx", b"not a zip file", "xlsx", 1024)

    def test_rejects_xlsx_missing_workbook(self) -> None:
        output = io.BytesIO()
        with ZipFile(output, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
        with self.assertRaisesRegex(UploadValidationError, "required workbook parts"):
            validate_upload("final.xlsx", output.getvalue(), "xlsx", 1024)

    def test_rejects_empty_file(self) -> None:
        with self.assertRaisesRegex(UploadValidationError, "empty"):
            validate_upload("draft.docx", b"", "docx", 1024)

    def test_rejects_oversized_file(self) -> None:
        with self.assertRaisesRegex(UploadValidationError, "exceeds"):
            validate_upload("draft.pdf", b"%PDF-1.7" + b"x" * 10, "pdf", 8)

    def test_oversized_file_has_a_safe_status_code(self) -> None:
        with self.assertRaises(UploadValidationError) as raised:
            validate_upload("draft.pdf", b"%PDF-1.7" + b"x" * 10, "pdf", 8)

        self.assertEqual(raised.exception.error_code, "file_too_large")

    def test_rejects_mismatched_extension(self) -> None:
        with self.assertRaisesRegex(UploadValidationError, "valid .pdf"):
            validate_upload("draft.pdf", make_docx_container(), "pdf", 1024)

    def test_rejects_malformed_docx(self) -> None:
        with self.assertRaisesRegex(UploadValidationError, "valid Office"):
            validate_upload("draft.docx", b"not a zip file", "docx", 1024)

    def test_rejects_zip_missing_word_document(self) -> None:
        output = io.BytesIO()
        with ZipFile(output, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
        with self.assertRaisesRegex(UploadValidationError, "required document parts"):
            validate_upload("draft.docx", output.getvalue(), "docx", 1024)

    def test_accepts_pdf_signature(self) -> None:
        validate_upload("draft.PDF", b"%PDF-1.7\nbody", "pdf", 1024)

    def test_accepts_pdf_header_with_leading_bytes(self) -> None:
        validate_upload("draft.pdf", b" " * 20 + b"%PDF-1.7\nbody", "pdf", 1024)

    def test_rejects_unknown_document_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported document type"):
            validate_upload("draft.txt", b"body", "txt", 1024)


if __name__ == "__main__":
    unittest.main()

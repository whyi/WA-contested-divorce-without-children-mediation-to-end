import unittest

from app.validation import UploadValidationError, validate_upload


class UploadValidationErrorTests(unittest.TestCase):
    def test_invalid_uploads_have_stable_safe_error_codes(self) -> None:
        cases = (
            ("empty.pdf", b"", "pdf", 1024, "empty_file"),
            ("large.pdf", b"%PDF-1.7", "pdf", 1, "file_too_large"),
            ("wrong.docx", b"%PDF-1.7", "pdf", 1024, "unsupported_file"),
            ("broken.docx", b"not a zip file", "docx", 1024, "unreadable_file"),
        )

        for filename, content, expected_type, max_bytes, error_code in cases:
            with self.subTest(error_code=error_code):
                with self.assertRaises(UploadValidationError) as raised:
                    validate_upload(filename, content, expected_type, max_bytes)

                self.assertEqual(raised.exception.error_code, error_code)


if __name__ == "__main__":
    unittest.main()

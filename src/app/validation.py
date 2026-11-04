from io import BytesIO
from zipfile import BadZipFile, ZipFile


class UploadValidationError(ValueError):
    """An uploaded document is empty, oversized, malformed, or the wrong type."""

    def __init__(self, message: str, error_code: str = "invalid_file") -> None:
        super().__init__(message)
        self.error_code = error_code


def validate_upload(
    filename: str,
    content: bytes,
    expected_type: str,
    max_bytes: int,
) -> None:
    if not content:
        raise UploadValidationError("The uploaded file is empty.", "empty_file")
    if len(content) > max_bytes:
        raise UploadValidationError(
            f"The uploaded file exceeds the {max_bytes}-byte limit.",
            "file_too_large",
        )

    extension = filename.rpartition(".")[2].lower()
    if expected_type == "docx":
        if extension != "docx":
            raise UploadValidationError("Expected a .docx file.", "unsupported_file")
        try:
            with ZipFile(BytesIO(content)) as archive:
                names = set(archive.namelist())
        except BadZipFile as error:
            raise UploadValidationError(
                "The uploaded DOCX file is not a valid Office document.",
                "unreadable_file",
            ) from error
        if "[Content_Types].xml" not in names or "word/document.xml" not in names:
            raise UploadValidationError(
                "The uploaded DOCX file is missing required document parts.",
                "unreadable_file",
            )
        return

    if expected_type == "xlsx":
        if extension != "xlsx":
            raise UploadValidationError("Expected an .xlsx file.", "unsupported_file")
        try:
            with ZipFile(BytesIO(content)) as archive:
                names = set(archive.namelist())
        except BadZipFile as error:
            raise UploadValidationError(
                "The uploaded XLSX file is not a valid Office workbook.",
                "unreadable_file",
            ) from error
        if "[Content_Types].xml" not in names or "xl/workbook.xml" not in names:
            raise UploadValidationError(
                "The uploaded XLSX file is missing required workbook parts.",
                "unreadable_file",
            )
        return

    if expected_type == "pdf":
        if extension != "pdf" or b"%PDF-" not in content[:1024]:
            raise UploadValidationError("Expected a valid .pdf file.", "unsupported_file")
        return

    raise ValueError(f"Unsupported document type: {expected_type}")

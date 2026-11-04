from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import BytesIO
import re
from zipfile import BadZipFile

from docx import Document as WordDocument
from docx.opc.exceptions import PackageNotFoundError
from lxml.etree import XMLSyntaxError
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException


class ModifiedOfferParseError(ValueError):
    """The uploaded offer documents cannot be parsed safely."""


def _normalized(value: object) -> str:
    return " ".join(str(value or "").split()).casefold()


def _docx_text(document) -> list[str]:
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                paragraphs.extend(paragraph.strip() for paragraph in cell.text.splitlines())
    return [value for value in paragraphs if value]


def _parse_docx(content: bytes) -> tuple[dict, list[str]]:
    try:
        document = WordDocument(BytesIO(content))
    except (BadZipFile, PackageNotFoundError, KeyError, ValueError, XMLSyntaxError, OSError) as error:
        raise ModifiedOfferParseError("The modified DOCX could not be read.") from error

    text = _docx_text(document)
    searchable_text = "\n".join(text)
    fields: dict[str, object] = {}
    warnings: list[str] = []

    patterns = (
        ("offer_from", r"Proposing party:\s*(.+)"),
        ("offer_to", r"Other party:\s*(.+)"),
        ("cause_number", r"\bNO\.\s*(\S+)"),
        ("proposed_effective_date", r"Proposed effective date:\s*(\d{4}-\d{2}-\d{2})"),
        ("proposed_response_date", r"Proposed response deadline:\s*(\d{4}-\d{2}-\d{2})"),
    )
    for field, pattern in patterns:
        match = re.search(pattern, searchable_text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            if field == "cause_number" and not value.strip("_"):
                continue
            if field.endswith("_date"):
                try:
                    value = date.fromisoformat(value).isoformat()
                except ValueError:
                    warnings.append(f"Could not recognize the date for {field.replace('_', ' ')}.")
                    continue
            fields[field] = value
        elif field in {"offer_from", "offer_to"}:
            warnings.append(f"Could not recognize {field.replace('_', ' ')} in the DOCX.")
        elif field == "cause_number" and re.search(r"\bNO\.\s*_+", searchable_text, re.IGNORECASE):
            continue

    county = re.search(r"\bFOR\s+(.+?)\s+COUNTY\b", searchable_text, re.IGNORECASE)
    if county and county.group(1).strip().casefold() != "[county]":
        fields["county"] = county.group(1).strip()

    terms_started = False
    terms_finished = False
    terms: list[str] = []
    for paragraph in document.paragraphs:
        value = paragraph.text.strip()
        if re.match(r"4\.5\b", value):
            terms_started = True
            continue
        if terms_started and re.match(r"V\.\s+ALLOCATION OF DEBTS", value, re.IGNORECASE):
            terms_finished = True
            break
        if terms_started and value and paragraph.style.name.startswith("List"):
            terms.append(value)
    if terms:
        fields["proposal_terms"] = terms
    elif not terms_finished:
        warnings.append("Could not recognize proposal terms in the DOCX; existing terms were not imported.")
    return fields, warnings


def _parse_xlsx(
    content: bytes,
    known_assets: list[dict],
) -> tuple[dict[str, str], list[dict], list[str]]:
    try:
        workbook = load_workbook(
            BytesIO(content),
            read_only=True,
            data_only=False,
            keep_links=False,
        )
    except (BadZipFile, InvalidFileException, KeyError, ValueError, OSError, XMLSyntaxError) as error:
        raise ModifiedOfferParseError("The modified XLSX could not be read.") from error

    warnings: list[str] = []
    try:
        if "Property Division" not in workbook.sheetnames:
            raise ModifiedOfferParseError(
                'The XLSX is missing the required "Property Division" sheet.'
            )
        sheet = workbook["Property Division"]
        rows = sheet.iter_rows(values_only=False)
        header_row = None
        header_columns: dict[str, int] = {}
        for row in rows:
            labels = {_normalized(cell.value): cell.column for cell in row if cell.value is not None}
            if {"property or debt", "proposed to user", "proposed to other party"}.issubset(labels):
                header_row = row[0].row
                header_columns = labels
                break
        if header_row is None:
            raise ModifiedOfferParseError("The XLSX property-allocation table is not recognizable.")

        party_fields: dict[str, str] = {}
        party_line = str(sheet["A3"].value or "")
        parties = re.search(
            r"Proposing party:\s*(.*?)\s+Other party:\s*(.+)",
            party_line,
            re.IGNORECASE,
        )
        if parties:
            party_fields = {
                "offer_from": parties.group(1).strip(),
                "offer_to": parties.group(2).strip(),
            }
        elif party_line.strip():
            warnings.append("Could not recognize the party names in the XLSX.")

        assets_by_name = {
            _normalized(item.get("asset_name")): str(item["asset_id"])
            for item in known_assets
            if item.get("asset_name") and item.get("asset_id")
        }
        allocation_values: list[dict] = []
        seen_assets: set[str] = set()
        for row in sheet.iter_rows(min_row=header_row + 1):
            name_cell = row[header_columns["property or debt"] - 1]
            asset_name = str(name_cell.value or "").strip()
            if not asset_name or _normalized(asset_name) == "total":
                continue
            if _normalized(asset_name).startswith("net to "):
                continue
            asset_id = assets_by_name.get(_normalized(asset_name))
            if asset_id is None:
                warnings.append(f'XLSX row "{asset_name}" did not match a known asset and was not imported.')
                continue
            if asset_id in seen_assets:
                raise ModifiedOfferParseError(
                    f'The XLSX contains more than one allocation row for "{asset_name}".'
                )
            seen_assets.add(asset_id)

            user_cell = row[header_columns["proposed to user"] - 1]
            other_cell = row[header_columns["proposed to other party"] - 1]
            if user_cell.data_type == "f" or other_cell.data_type == "f":
                warnings.append(
                    f'XLSX formulas for "{asset_name}" were not evaluated; formula-based allocations were not imported.'
                )
                continue
            if isinstance(user_cell.value, (int, float, Decimal)) and not isinstance(user_cell.value, bool):
                try:
                    cents = int(
                        (Decimal(str(user_cell.value)) * 100).quantize(
                            Decimal("1"),
                            rounding=ROUND_HALF_UP,
                        )
                    )
                except InvalidOperation as error:
                    raise ModifiedOfferParseError(
                        f'The proposed user allocation for "{asset_name}" is invalid.'
                    ) from error
                if abs(cents) > 1_000_000_000_000:
                    raise ModifiedOfferParseError(
                        f'The proposed user allocation for "{asset_name}" is outside the supported range.'
                    )
                allocation_values.append(
                    {"asset_id": asset_id, "proposed_amount_cents": cents}
                )
            elif user_cell.value is not None:
                warnings.append(
                    f'The proposed user allocation for "{asset_name}" was not numeric and was not imported.'
                )
            if other_cell.value is not None:
                warnings.append(
                    f'The proposed allocation to the other party for "{asset_name}" is shown for review but is not an editable imported field.'
                )
        return party_fields, allocation_values, warnings
    except ModifiedOfferParseError:
        raise
    except (
        BadZipFile,
        InvalidFileException,
        KeyError,
        ValueError,
        OSError,
        XMLSyntaxError,
        IndexError,
        TypeError,
    ) as error:
        raise ModifiedOfferParseError("The modified XLSX could not be read completely.") from error
    finally:
        workbook.close()


def parse_modified_offer(
    docx_content: bytes,
    xlsx_content: bytes,
    known_assets: list[dict],
) -> dict:
    docx_fields, warnings = _parse_docx(docx_content)
    xlsx_parties, proposed_values, xlsx_warnings = _parse_xlsx(xlsx_content, known_assets)
    warnings.extend(xlsx_warnings)

    for field in ("offer_from", "offer_to"):
        docx_party = docx_fields.get(field)
        xlsx_party = xlsx_parties.get(field)
        if docx_party and xlsx_party and _normalized(docx_party) != _normalized(xlsx_party):
            raise ModifiedOfferParseError(
                f"The DOCX and XLSX disagree about {field.replace('_', ' ')}. Correct the documents and upload both again."
            )
        if not docx_party and xlsx_party:
            docx_fields[field] = xlsx_party

    docx_fields["proposed_values"] = proposed_values
    for field, default in (
        ("offer_from", ""),
        ("offer_to", ""),
        ("county", ""),
        ("cause_number", ""),
        ("proposed_effective_date", None),
        ("proposed_response_date", None),
        ("proposal_terms", []),
    ):
        docx_fields.setdefault(field, default)
    maximum_lengths = {
        "offer_from": 160,
        "offer_to": 160,
        "county": 100,
        "cause_number": 100,
    }
    for field, maximum in maximum_lengths.items():
        value = docx_fields[field]
        if not isinstance(value, str) or len(value) > maximum:
            raise ModifiedOfferParseError(
                f"The imported {field.replace('_', ' ')} exceeds the supported length."
            )
    terms = docx_fields["proposal_terms"]
    if (
        not isinstance(terms, list)
        or len(terms) > 80
        or any(not isinstance(term, str) or not term.strip() or len(term) > 2_000 for term in terms)
    ):
        raise ModifiedOfferParseError("The imported proposal terms exceed supported limits.")
    if len(proposed_values) > 500:
        raise ModifiedOfferParseError("The XLSX contains more allocations than can be reviewed.")
    return {"editable_state": docx_fields, "warnings": warnings}

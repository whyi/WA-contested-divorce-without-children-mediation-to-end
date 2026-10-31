
## Prompt - 2026-10-31T07:06:28Z

### Exact user prompt

````text
implement the latest spec
````

### Execution - 2026-10-31T07:06:28Z

- Invocation: `INTERACTION_CAPTURE=1 INTERACTION_LOG=interactions/08-consent-based-document-analysis/response-08-consent-based-document-analysis.md bash harness/validate.sh -- python3 -m unittest discover -s tests -p test_analysis_worker.py -v`
- Exit status: `1`

### Output

```text
PASS: directory exists: specs
PASS: directory exists: harness
PASS: directory exists: interactions
PASS: directory exists: src/app
PASS: directory exists: tests
PASS: file exists: .cursorrules
PASS: file exists: harness/validate.sh
PASS: file exists: specs/00-initialization/spec-00-init.md
PASS: file exists: specs/01-tech-stack-override/01-tech-stack-override.md
PASS: file exists: pyproject.toml
PASS: file exists: Dockerfile
PASS: file exists: docker-compose.yml
PASS: file exists: alembic.ini
PASS: file exists: migrations/versions/0001_initial_schema.py
PASS: file exists: src/app/main.py
PASS: file exists: src/app/documents.py
PASS: file exists: src/app/storage.py
PASS: validation harness shell syntax.
PASS: Python source compiles.
test_0002_authentication (unittest.loader._FailedTest.test_0002_authentication) ... ERROR
test_0003_material_imports (unittest.loader._FailedTest.test_0003_material_imports) ... ERROR
test_0004_document_extraction_jobs (unittest.loader._FailedTest.test_0004_document_extraction_jobs) ... ERROR
test_0005_document_analysis (unittest.loader._FailedTest.test_0005_document_analysis) ... ERROR
test_ai (unittest.loader._FailedTest.test_ai) ... ERROR
test_analysis (unittest.loader._FailedTest.test_analysis) ... ERROR
test_analysis_worker (unittest.loader._FailedTest.test_analysis_worker) ... ERROR
test_auth (unittest.loader._FailedTest.test_auth) ... ERROR
test_auth_routes (unittest.loader._FailedTest.test_auth_routes) ... ERROR
test_config (unittest.loader._FailedTest.test_config) ... ERROR
test_dashboard (unittest.loader._FailedTest.test_dashboard) ... ERROR
test_demo (unittest.loader._FailedTest.test_demo) ... ERROR
test_documents (unittest.loader._FailedTest.test_documents) ... ERROR
test_extraction (unittest.loader._FailedTest.test_extraction) ... ERROR
test_extraction_worker (unittest.loader._FailedTest.test_extraction_worker) ... ERROR
test_main (unittest.loader._FailedTest.test_main) ... ERROR
test_materials (unittest.loader._FailedTest.test_materials) ... ERROR
test_models (unittest.loader._FailedTest.test_models) ... ERROR
test_compose_demo_login_is_explicit_and_case_data_remains_disabled (test_project_configuration.ProjectConfigurationTests.test_compose_demo_login_is_explicit_and_case_data_remains_disabled) ... ok
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
test_package_includes_the_landing_page_asset (test_project_configuration.ProjectConfigurationTests.test_package_includes_the_landing_page_asset) ... ok
test_project_declares_specified_stack (test_project_configuration.ProjectConfigurationTests.test_project_declares_specified_stack) ... ok
test_storage (unittest.loader._FailedTest.test_storage) ... ERROR
test_accepts_docx_container_with_required_parts (test_upload_validation.UploadValidationTests.test_accepts_docx_container_with_required_parts) ... ok
test_accepts_pdf_header_with_leading_bytes (test_upload_validation.UploadValidationTests.test_accepts_pdf_header_with_leading_bytes) ... ok
test_accepts_pdf_signature (test_upload_validation.UploadValidationTests.test_accepts_pdf_signature) ... ok
test_oversized_file_has_a_safe_status_code (test_upload_validation.UploadValidationTests.test_oversized_file_has_a_safe_status_code) ... ok
test_rejects_empty_file (test_upload_validation.UploadValidationTests.test_rejects_empty_file) ... ok
test_rejects_malformed_docx (test_upload_validation.UploadValidationTests.test_rejects_malformed_docx) ... ok
test_rejects_mismatched_extension (test_upload_validation.UploadValidationTests.test_rejects_mismatched_extension) ... ok
test_rejects_oversized_file (test_upload_validation.UploadValidationTests.test_rejects_oversized_file) ... ok
test_rejects_unknown_document_type (test_upload_validation.UploadValidationTests.test_rejects_unknown_document_type) ... ok
test_rejects_zip_missing_word_document (test_upload_validation.UploadValidationTests.test_rejects_zip_missing_word_document) ... ok
test_invalid_uploads_have_stable_safe_error_codes (test_validation.UploadValidationErrorTests.test_invalid_uploads_have_stable_safe_error_codes) ... ok

======================================================================
ERROR: test_0002_authentication (unittest.loader._FailedTest.test_0002_authentication)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_0002_authentication
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_0002_authentication.py", line 6, in <module>
    import sqlalchemy as sa
ModuleNotFoundError: No module named 'sqlalchemy'


======================================================================
ERROR: test_0003_material_imports (unittest.loader._FailedTest.test_0003_material_imports)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_0003_material_imports
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_0003_material_imports.py", line 17, in <module>
    MIGRATION_SPEC.loader.exec_module(migration)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/migrations/versions/0003_material_imports.py", line 3, in <module>
    from alembic import op
ModuleNotFoundError: No module named 'alembic'


======================================================================
ERROR: test_0004_document_extraction_jobs (unittest.loader._FailedTest.test_0004_document_extraction_jobs)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_0004_document_extraction_jobs
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_0004_document_extraction_jobs.py", line 21, in <module>
    MIGRATION_SPEC.loader.exec_module(migration)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/migrations/versions/0004_document_extraction_jobs.py", line 3, in <module>
    from alembic import op
ModuleNotFoundError: No module named 'alembic'


======================================================================
ERROR: test_0005_document_analysis (unittest.loader._FailedTest.test_0005_document_analysis)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_0005_document_analysis
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_0005_document_analysis.py", line 21, in <module>
    MIGRATION_SPEC.loader.exec_module(migration)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/migrations/versions/0005_document_analysis.py", line 3, in <module>
    from alembic import op
ModuleNotFoundError: No module named 'alembic'


======================================================================
ERROR: test_ai (unittest.loader._FailedTest.test_ai)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_ai
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_ai.py", line 4, in <module>
    from app.ai import analyze_case_materials
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/src/app/ai.py", line 7, in <module>
    import boto3
ModuleNotFoundError: No module named 'boto3'


======================================================================
ERROR: test_analysis (unittest.loader._FailedTest.test_analysis)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_analysis
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_analysis.py", line 7, in <module>
    from fastapi import HTTPException
ModuleNotFoundError: No module named 'fastapi'


======================================================================
ERROR: test_analysis_worker (unittest.loader._FailedTest.test_analysis_worker)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_analysis_worker
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_analysis_worker.py", line 8, in <module>
    from app.analysis_worker import (
    ...<3 lines>...
    )
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/src/app/analysis_worker.py", line 8, in <module>
    from botocore.exceptions import BotoCoreError
ModuleNotFoundError: No module named 'botocore'


======================================================================
ERROR: test_auth (unittest.loader._FailedTest.test_auth)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_auth
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_auth.py", line 7, in <module>
    from app.auth import (
    ...<9 lines>...
    )
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/src/app/auth.py", line 8, in <module>
    from email_validator import EmailNotValidError, validate_email
ModuleNotFoundError: No module named 'email_validator'


======================================================================
ERROR: test_auth_routes (unittest.loader._FailedTest.test_auth_routes)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_auth_routes
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_auth_routes.py", line 4, in <module>
    from fastapi import HTTPException, Response
ModuleNotFoundError: No module named 'fastapi'


======================================================================
ERROR: test_config (unittest.loader._FailedTest.test_config)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_config
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_config.py", line 3, in <module>
    from app.config import Settings
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/src/app/config.py", line 4, in <module>
    from pydantic import Field, model_validator
ModuleNotFoundError: No module named 'pydantic'


======================================================================
ERROR: test_dashboard (unittest.loader._FailedTest.test_dashboard)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_dashboard
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_dashboard.py", line 6, in <module>
    from fastapi.testclient import TestClient
ModuleNotFoundError: No module named 'fastapi'


======================================================================
ERROR: test_demo (unittest.loader._FailedTest.test_demo)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_demo
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_demo.py", line 4, in <module>
    from app.demo import (
    ...<6 lines>...
    )
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/src/app/demo.py", line 4, in <module>
    from pwdlib import PasswordHash
ModuleNotFoundError: No module named 'pwdlib'


======================================================================
ERROR: test_documents (unittest.loader._FailedTest.test_documents)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_documents
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_documents.py", line 5, in <module>
    import fitz
ModuleNotFoundError: No module named 'fitz'


======================================================================
ERROR: test_extraction (unittest.loader._FailedTest.test_extraction)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_extraction
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_extraction.py", line 8, in <module>
    from botocore.exceptions import BotoCoreError
ModuleNotFoundError: No module named 'botocore'


======================================================================
ERROR: test_extraction_worker (unittest.loader._FailedTest.test_extraction_worker)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_extraction_worker
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_extraction_worker.py", line 5, in <module>
    from app.extraction import ExtractionLease
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/src/app/extraction.py", line 7, in <module>
    from botocore.exceptions import BotoCoreError
ModuleNotFoundError: No module named 'botocore'


======================================================================
ERROR: test_main (unittest.loader._FailedTest.test_main)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_main
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_main.py", line 8, in <module>
    from botocore.exceptions import BotoCoreError
ModuleNotFoundError: No module named 'botocore'


======================================================================
ERROR: test_materials (unittest.loader._FailedTest.test_materials)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_materials
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_materials.py", line 6, in <module>
    from fastapi.testclient import TestClient
ModuleNotFoundError: No module named 'fastapi'


======================================================================
ERROR: test_models (unittest.loader._FailedTest.test_models)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_models
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_models.py", line 3, in <module>
    from app.models import (
    ...<18 lines>...
    )
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/src/app/models.py", line 4, in <module>
    from sqlalchemy import (
    ...<11 lines>...
    )
ModuleNotFoundError: No module named 'sqlalchemy'


======================================================================
ERROR: test_storage (unittest.loader._FailedTest.test_storage)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_storage
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_storage.py", line 4, in <module>
    from app.config import Settings
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/src/app/config.py", line 4, in <module>
    from pydantic import Field, model_validator
ModuleNotFoundError: No module named 'pydantic'


----------------------------------------------------------------------
Ran 35 tests in 0.006s

FAILED (errors=19)
FAIL: Python unit tests failed.
Validation failed with 1 missing requirement(s).
```

## Prompt - 2026-10-31T07:11:52Z

### Exact user prompt

````text
implement the latest spec
````

### Execution - 2026-10-31T07:11:52Z

- Invocation: `INTERACTION_CAPTURE=1 INTERACTION_LOG=interactions/08-consent-based-document-analysis/response-08-consent-based-document-analysis.md bash harness/validate.sh`
- Exit status: `0`

### Output

```text
PASS: directory exists: specs
PASS: directory exists: harness
PASS: directory exists: interactions
PASS: directory exists: src/app
PASS: directory exists: tests
PASS: file exists: .cursorrules
PASS: file exists: harness/validate.sh
PASS: file exists: specs/00-initialization/spec-00-init.md
PASS: file exists: specs/01-tech-stack-override/01-tech-stack-override.md
PASS: file exists: pyproject.toml
PASS: file exists: Dockerfile
PASS: file exists: docker-compose.yml
PASS: file exists: alembic.ini
PASS: file exists: migrations/versions/0001_initial_schema.py
PASS: file exists: src/app/main.py
PASS: file exists: src/app/documents.py
PASS: file exists: src/app/storage.py
PASS: validation harness shell syntax.
PASS: Python source compiles.
/usr/local/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  from starlette.testclient import TestClient as TestClient  # noqa
warning: The `fitz` API is deprecated and will be removed in future. Use `import pymupdf` instead.
test_upgrade_creates_authentication_schema_and_downgrade_removes_it (test_0002_authentication.AuthenticationMigrationTests.test_upgrade_creates_authentication_schema_and_downgrade_removes_it) ... ok
test_upgrade_creates_import_batch_and_idempotency_tables (test_0003_material_imports.MaterialImportsMigrationTests.test_upgrade_creates_import_batch_and_idempotency_tables) ... ok
test_downgrade_removes_jobs_and_page_provenance (test_0004_document_extraction_jobs.DocumentExtractionJobMigrationTests.test_downgrade_removes_jobs_and_page_provenance) ... ok
test_upgrade_adds_page_provenance_and_durable_jobs (test_0004_document_extraction_jobs.DocumentExtractionJobMigrationTests.test_upgrade_adds_page_provenance_and_durable_jobs) ... ok
test_downgrade_removes_analysis_tables_in_dependency_order (test_0005_document_analysis.DocumentAnalysisMigrationTests.test_downgrade_removes_analysis_tables_in_dependency_order) ... ok
test_upgrade_creates_consent_request_job_and_proposal_tables (test_0005_document_analysis.DocumentAnalysisMigrationTests.test_upgrade_creates_consent_request_job_and_proposal_tables) ... ok
test_document_analysis_discards_unverifiable_proposals_individually (test_ai.BedrockExtractionTests.test_document_analysis_discards_unverifiable_proposals_individually) ... ok
test_document_analysis_verifies_page_citations_and_uses_no_tools (test_ai.BedrockExtractionTests.test_document_analysis_verifies_page_citations_and_uses_no_tools) ... ok
test_docx_analysis_requires_document_level_quotes_without_fake_pages (test_ai.BedrockExtractionTests.test_docx_analysis_requires_document_level_quotes_without_fake_pages) ... ok
test_rejects_unverifiable_source_quotes (test_ai.BedrockExtractionTests.test_rejects_unverifiable_source_quotes) ... ok
test_requires_a_configured_model (test_ai.BedrockExtractionTests.test_requires_a_configured_model) ... ok
test_returns_only_fields_with_verifiable_source_quotes (test_ai.BedrockExtractionTests.test_returns_only_fields_with_verifiable_source_quotes) ... ok
test_surfaces_invalid_model_output (test_ai.BedrockExtractionTests.test_surfaces_invalid_model_output) ... [WARNING] Bedrock returned non-JSON case analysis output.
ok
test_analysis_is_unavailable_by_default (test_analysis.AnalysisConfigurationTests.test_analysis_is_unavailable_by_default) ... ok
test_analysis_request_persists_consent_and_one_job_per_eligible_file (test_analysis.AnalysisConfigurationTests.test_analysis_request_persists_consent_and_one_job_per_eligible_file) ... ok
test_analysis_request_rejects_unprocessed_documents_without_queueing (test_analysis.AnalysisConfigurationTests.test_analysis_request_rejects_unprocessed_documents_without_queueing) ... ok
test_analysis_requires_provider_region_and_deployment_notice (test_analysis.AnalysisConfigurationTests.test_analysis_requires_provider_region_and_deployment_notice) ... ok
test_disclosure_names_provider_model_purpose_and_data_handling (test_analysis.AnalysisConfigurationTests.test_disclosure_names_provider_model_purpose_and_data_handling) ... ok
test_retry_only_requeues_a_failed_job_with_active_consent_and_same_source (test_analysis.AnalysisConfigurationTests.test_retry_only_requeues_a_failed_job_with_active_consent_and_same_source) ... ok
test_revocation_cancels_queued_jobs_for_the_request (test_analysis.AnalysisConfigurationTests.test_revocation_cancels_queued_jobs_for_the_request) ... ok
test_request_requires_explicit_consent_and_unique_documents (test_analysis.AnalysisRequestValidationTests.test_request_requires_explicit_consent_and_unique_documents) ... ok
test_request_status_reflects_work_and_mixed_terminal_outcomes (test_analysis.AnalysisRequestValidationTests.test_request_status_reflects_work_and_mixed_terminal_outcomes) ... ok
test_provider_is_not_called_when_analysis_is_disabled (test_analysis_worker.AnalysisWorkerTests.test_provider_is_not_called_when_analysis_is_disabled) ... ok
test_revoked_consent_cancels_job_without_calling_bedrock (test_analysis_worker.AnalysisWorkerTests.test_revoked_consent_cancels_job_without_calling_bedrock) ... ok
test_worker_claims_a_queued_job (test_analysis_worker.AnalysisWorkerTests.test_worker_claims_a_queued_job) ... ok
test_worker_persists_only_a_verified_proposal (test_analysis_worker.AnalysisWorkerTests.test_worker_persists_only_a_verified_proposal) ... ok
test_access_token_has_required_claims_and_validates_audience (test_auth.AuthenticationServiceTests.test_access_token_has_required_claims_and_validates_audience) ... ok
test_authentication_fails_closed_without_a_signing_secret (test_auth.AuthenticationServiceTests.test_authentication_fails_closed_without_a_signing_secret) ... ok
test_normalizes_email_without_provider_specific_rewriting (test_auth.AuthenticationServiceTests.test_normalizes_email_without_provider_specific_rewriting) ... ok
test_password_hash_verifies_without_storing_plaintext (test_auth.AuthenticationServiceTests.test_password_hash_verifies_without_storing_plaintext) ... ok
test_password_size_limit_counts_utf8_bytes (test_auth.AuthenticationServiceTests.test_password_size_limit_counts_utf8_bytes) ... ok
test_refresh_token_has_a_distinct_token_type_and_session_claim (test_auth.AuthenticationServiceTests.test_refresh_token_has_a_distinct_token_type_and_session_claim) ... ok
test_rejects_short_and_common_passwords (test_auth.AuthenticationServiceTests.test_rejects_short_and_common_passwords) ... ok
test_rejects_wrong_token_type_and_invalid_signature (test_auth.AuthenticationServiceTests.test_rejects_wrong_token_type_and_invalid_signature) ... ok
test_token_hash_is_stable_and_one_way (test_auth.AuthenticationServiceTests.test_token_hash_is_stable_and_one_way) ... ok
test_authentication_contract_routes_are_registered (test_auth_routes.AuthenticationRouteTests.test_authentication_contract_routes_are_registered) ... ok
test_authentication_routes_fail_closed_when_disabled (test_auth_routes.AuthenticationRouteTests.test_authentication_routes_fail_closed_when_disabled) ... [INFO] HTTP Request: POST http://testserver/api/auth/passkeys/authenticate/options "HTTP/1.1 503 Service Unavailable"
ok
test_browser_auth_cookies_are_http_only_and_csrf_cookie_is_accessible (test_auth_routes.AuthenticationRouteTests.test_browser_auth_cookies_are_http_only_and_csrf_cookie_is_accessible) ... ok
test_demo_login_accepts_demo_credentials_only_when_demo_mode_is_enabled (test_auth_routes.AuthenticationRouteTests.test_demo_login_accepts_demo_credentials_only_when_demo_mode_is_enabled) ... ok
test_demo_login_rejects_an_incorrect_password (test_auth_routes.AuthenticationRouteTests.test_demo_login_rejects_an_incorrect_password) ... ok
test_google_provider_is_reported_available_when_fully_configured (test_auth_routes.AuthenticationRouteTests.test_google_provider_is_reported_available_when_fully_configured) ... [INFO] HTTP Request: GET http://testserver/api/auth/providers "HTTP/1.1 200 OK"
ok
test_google_provider_is_reported_unavailable_when_auth_is_disabled (test_auth_routes.AuthenticationRouteTests.test_google_provider_is_reported_unavailable_when_auth_is_disabled) ... [INFO] HTTP Request: GET http://testserver/api/auth/providers "HTTP/1.1 200 OK"
ok
test_mfa_challenge_is_sent_in_the_request_body_not_the_url (test_auth_routes.AuthenticationRouteTests.test_mfa_challenge_is_sent_in_the_request_body_not_the_url) ... ok
test_passkey_verification_handlers_are_not_duplicated (test_auth_routes.AuthenticationRouteTests.test_passkey_verification_handlers_are_not_duplicated) ... ok
test_totp_secrets_are_encrypted_and_codes_are_time_bounded (test_auth_routes.AuthenticationRouteTests.test_totp_secrets_are_encrypted_and_codes_are_time_bounded) ... ok
test_auth_cannot_be_enabled_without_a_strong_secret (test_config.SettingsTests.test_auth_cannot_be_enabled_without_a_strong_secret) ... ok
test_authentication_configuration_rejects_invalid_session_lifetimes (test_config.SettingsTests.test_authentication_configuration_rejects_invalid_session_lifetimes) ... ok
test_authentication_configuration_rejects_mismatched_provider_secrets (test_config.SettingsTests.test_authentication_configuration_rejects_mismatched_provider_secrets) ... ok
test_authentication_is_disabled_without_explicit_secrets (test_config.SettingsTests.test_authentication_is_disabled_without_explicit_secrets) ... ok
test_bedrock_configuration_is_optional (test_config.SettingsTests.test_bedrock_configuration_is_optional) ... ok
test_bedrock_model_and_region_can_be_configured (test_config.SettingsTests.test_bedrock_model_and_region_can_be_configured) ... ok
test_case_data_cannot_be_enabled_without_authentication (test_config.SettingsTests.test_case_data_cannot_be_enabled_without_authentication) ... ok
test_case_materials_require_auth_and_case_data (test_config.SettingsTests.test_case_materials_require_auth_and_case_data) ... ok
test_demo_mode_is_local_only_and_cannot_enable_case_data (test_config.SettingsTests.test_demo_mode_is_local_only_and_cannot_enable_case_data) ... ok
test_local_loopback_storage_can_be_explicitly_enabled_without_kms (test_config.SettingsTests.test_local_loopback_storage_can_be_explicitly_enabled_without_kms) ... ok
test_non_local_auth_origins_require_https (test_config.SettingsTests.test_non_local_auth_origins_require_https) ... ok
test_production_case_data_requires_kms_even_before_materials_toggle (test_config.SettingsTests.test_production_case_data_requires_kms_even_before_materials_toggle) ... ok
test_production_case_materials_require_a_kms_key (test_config.SettingsTests.test_production_case_materials_require_a_kms_key) ... ok
test_remote_http_s3_endpoint_is_rejected (test_config.SettingsTests.test_remote_http_s3_endpoint_is_rejected) ... ok
test_s3_endpoint_cannot_embed_credentials (test_config.SettingsTests.test_s3_endpoint_cannot_embed_credentials) ... ok
test_samesite_none_requires_secure_cookies (test_config.SettingsTests.test_samesite_none_requires_secure_cookies) ... ok
test_status_reports_database_failure_as_retryable_service_error (test_dashboard.DashboardStatusTests.test_status_reports_database_failure_as_retryable_service_error) ... [ERROR] Dashboard case-status lookup failed.
Traceback (most recent call last):
  File "/workspace/src/app/main.py", line 332, in dashboard_status
    rows = db.execute(
           ^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/mock.py", line 1198, in _execute_mock_call
    raise effect
sqlalchemy.exc.SQLAlchemyError: database unavailable
[INFO] HTTP Request: GET http://testserver/api/v1/dashboard/status "HTTP/1.1 503 Service Unavailable"
ok
test_status_requires_an_authenticated_user (test_dashboard.DashboardStatusTests.test_status_requires_an_authenticated_user) ... [INFO] HTTP Request: GET http://testserver/api/v1/dashboard/status "HTTP/1.1 401 Unauthorized"
ok
test_status_returns_empty_case_list_for_new_account (test_dashboard.DashboardStatusTests.test_status_returns_empty_case_list_for_new_account) ... [INFO] HTTP Request: GET http://testserver/api/v1/dashboard/status "HTTP/1.1 200 OK"
ok
test_status_returns_only_the_current_users_case_summaries (test_dashboard.DashboardStatusTests.test_status_returns_only_the_current_users_case_summaries) ... [INFO] HTTP Request: GET http://testserver/api/v1/dashboard/status "HTTP/1.1 200 OK"
ok
test_demo_credentials_are_fixed_for_the_local_demo (test_demo.DemoAccountTests.test_demo_credentials_are_fixed_for_the_local_demo) ... ok
test_rejects_wrong_demo_password (test_demo.DemoAccountTests.test_rejects_wrong_demo_password) ... ok
test_seeds_an_active_email_verified_demo_user (test_demo.DemoAccountTests.test_seeds_an_active_email_verified_demo_user) ... ok
test_docx_extraction_does_not_claim_physical_page_numbers (test_documents.DocumentExtractionTests.test_docx_extraction_does_not_claim_physical_page_numbers) ... ok
test_malformed_docx_is_actionable (test_documents.DocumentExtractionTests.test_malformed_docx_is_actionable) ... ok
test_password_protected_pdf_is_actionable_without_decryption (test_documents.DocumentExtractionTests.test_password_protected_pdf_is_actionable_without_decryption) ... ok
test_pdf_page_limit_is_enforced_during_extraction (test_documents.DocumentExtractionTests.test_pdf_page_limit_is_enforced_during_extraction) ... ok
test_pdf_text_preserves_one_based_page_boundaries (test_documents.DocumentExtractionTests.test_pdf_text_preserves_one_based_page_boundaries) ... ok
test_pdf_with_a_page_without_selectable_text_needs_ocr (test_documents.DocumentExtractionTests.test_pdf_with_a_page_without_selectable_text_needs_ocr) ... ok
test_claim_uses_skip_locked_and_reclaims_expired_work (test_extraction.ExtractionQueueTests.test_claim_uses_skip_locked_and_reclaims_expired_work) ... ok
test_concurrent_enqueue_recovers_the_existing_unique_job (test_extraction.ExtractionQueueTests.test_concurrent_enqueue_recovers_the_existing_unique_job) ... ok
test_enqueue_persists_a_queued_job_without_processing_it (test_extraction.ExtractionQueueTests.test_enqueue_persists_a_queued_job_without_processing_it) ... ok
test_enqueue_returns_existing_job_for_repeated_request (test_extraction.ExtractionQueueTests.test_enqueue_returns_existing_job_for_repeated_request) ... ok
test_expired_job_at_attempt_limit_is_marked_failed (test_extraction.ExtractionQueueTests.test_expired_job_at_attempt_limit_is_marked_failed) ... ok
test_ocr_needed_file_is_persisted_as_needs_attention (test_extraction.ExtractionQueueTests.test_ocr_needed_file_is_persisted_as_needs_attention) ... ok
test_retry_does_not_repeat_completed_extraction (test_extraction.ExtractionQueueTests.test_retry_does_not_repeat_completed_extraction) ... ok
test_retry_resets_only_failed_jobs_for_the_same_request (test_extraction.ExtractionQueueTests.test_retry_resets_only_failed_jobs_for_the_same_request) ... ok
test_status_does_not_disclose_a_document_from_another_case (test_extraction.ExtractionQueueTests.test_status_does_not_disclose_a_document_from_another_case) ... ok
test_status_is_stored_until_a_consent_request_enqueues_work (test_extraction.ExtractionQueueTests.test_status_is_stored_until_a_consent_request_enqueues_work) ... ok
test_storage_failure_is_reported_without_exposing_storage_details (test_extraction.ExtractionQueueTests.test_storage_failure_is_reported_without_exposing_storage_details) ... [ERROR] Extraction storage read failed (BotoCoreError).
ok
test_successful_processing_persists_page_provenance (test_extraction.ExtractionQueueTests.test_successful_processing_persists_page_provenance) ... ok
test_worker_processes_one_claimed_job_in_a_separate_session (test_extraction_worker.ExtractionWorkerTests.test_worker_processes_one_claimed_job_in_a_separate_session) ... ok
test_worker_waits_when_no_jobs_are_queued (test_extraction_worker.ExtractionWorkerTests.test_worker_waits_when_no_jobs_are_queued) ... ok
test_case_data_endpoints_fail_closed_until_authentication_is_configured (test_main.MainWorkflowTests.test_case_data_endpoints_fail_closed_until_authentication_is_configured) ... ok
test_document_deletion_keeps_metadata_when_object_removal_fails (test_main.MainWorkflowTests.test_document_deletion_keeps_metadata_when_object_removal_fails) ... [ERROR] Document deletion from object storage failed (BotoCoreError).
ok
test_document_deletion_removes_the_object_and_metadata (test_main.MainWorkflowTests.test_document_deletion_removes_the_object_and_metadata) ... ok
test_document_deletion_reports_incomplete_metadata_cleanup (test_main.MainWorkflowTests.test_document_deletion_reports_incomplete_metadata_cleanup) ... [ERROR] Document metadata deletion failed after object removal.
Traceback (most recent call last):
  File "/workspace/src/app/main.py", line 625, in delete_document
    db.commit()
  File "/usr/local/lib/python3.12/unittest/mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/mock.py", line 1198, in _execute_mock_call
    raise effect
sqlalchemy.exc.SQLAlchemyError: database unavailable
ok
test_document_deletion_requires_case_membership_and_non_viewer_role (test_main.MainWorkflowTests.test_document_deletion_requires_case_membership_and_non_viewer_role) ... ok
test_onboarding_paths_serve_the_authenticated_preview_page (test_main.MainWorkflowTests.test_onboarding_paths_serve_the_authenticated_preview_page) ... ok
test_root_displays_mode_choices_and_authentication_gate (test_main.MainWorkflowTests.test_root_displays_mode_choices_and_authentication_gate) ... ok
test_cleanup_failure_logs_no_object_key (test_materials.MaterialsImportTests.test_cleanup_failure_logs_no_object_key) ... ok
test_config_reports_runtime_upload_limit_and_unconfigured_providers (test_materials.MaterialsImportTests.test_config_reports_runtime_upload_limit_and_unconfigured_providers) ... [INFO] HTTP Request: GET http://testserver/api/v1/materials/config "HTTP/1.1 200 OK"
ok
test_database_failure_cleans_up_the_uploaded_object (test_materials.MaterialsImportTests.test_database_failure_cleans_up_the_uploaded_object) ... [ERROR] Material import database transaction failed (SQLAlchemyError).
[INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/b5e3e2d3-b594-45c7-baf0-2fd7c94ab482/files/d99096fc-511c-4214-b993-0c50f3b36efc "HTTP/1.1 503 Service Unavailable"
ok
test_import_fails_closed_when_case_data_is_disabled (test_materials.MaterialsImportTests.test_import_fails_closed_when_case_data_is_disabled) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/59c09af7-e1be-49a1-91d0-d10c64b1c6d8/files/6944378d-b782-4967-876e-846dd09f72d1 "HTTP/1.1 503 Service Unavailable"
ok
test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/23ad0ce9-1b3c-4b05-b36f-71253c960873/files/d8a7ac90-fd07-41d6-8e00-e49b8db8b439 "HTTP/1.1 415 Unsupported Media Type"
ok
test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/d4137925-ceb8-43e9-b258-01d82d7f6809/files/7756dd64-d2d6-47f3-9ceb-c4b629442c18 "HTTP/1.1 201 Created"
ok
test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/b0f8197d-5810-4128-971e-f142c99fe338/files/cf89d7fb-2d15-4fea-99c9-6204af2fc4be "HTTP/1.1 201 Created"
ok
test_analysis_jobs_and_proposals_keep_source_provenance (test_models.AuthenticationModelTests.test_analysis_jobs_and_proposals_keep_source_provenance) ... ok
test_authentication_tables_are_registered (test_models.AuthenticationModelTests.test_authentication_tables_are_registered) ... ok
test_provider_and_case_access_constraints_are_explicit (test_models.AuthenticationModelTests.test_provider_and_case_access_constraints_are_explicit) ... ok
test_compose_demo_login_is_explicit_and_case_data_remains_disabled (test_project_configuration.ProjectConfigurationTests.test_compose_demo_login_is_explicit_and_case_data_remains_disabled) ... ok
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
test_package_includes_the_landing_page_asset (test_project_configuration.ProjectConfigurationTests.test_package_includes_the_landing_page_asset) ... ok
test_project_declares_specified_stack (test_project_configuration.ProjectConfigurationTests.test_project_declares_specified_stack) ... ok
test_delete_uses_only_the_configured_bucket_and_object_key (test_storage.ObjectStorageTests.test_delete_uses_only_the_configured_bucket_and_object_key) ... ok
test_local_loopback_upload_does_not_require_or_send_kms (test_storage.ObjectStorageTests.test_local_loopback_upload_does_not_require_or_send_kms) ... ok
test_production_upload_requests_kms_encryption (test_storage.ObjectStorageTests.test_production_upload_requests_kms_encryption) ... ok
test_read_closes_the_storage_response_body (test_storage.ObjectStorageTests.test_read_closes_the_storage_response_body) ... ok
test_upload_fails_closed_without_a_kms_key (test_storage.ObjectStorageTests.test_upload_fails_closed_without_a_kms_key) ... ok
test_accepts_docx_container_with_required_parts (test_upload_validation.UploadValidationTests.test_accepts_docx_container_with_required_parts) ... ok
test_accepts_pdf_header_with_leading_bytes (test_upload_validation.UploadValidationTests.test_accepts_pdf_header_with_leading_bytes) ... ok
test_accepts_pdf_signature (test_upload_validation.UploadValidationTests.test_accepts_pdf_signature) ... ok
test_oversized_file_has_a_safe_status_code (test_upload_validation.UploadValidationTests.test_oversized_file_has_a_safe_status_code) ... ok
test_rejects_empty_file (test_upload_validation.UploadValidationTests.test_rejects_empty_file) ... ok
test_rejects_malformed_docx (test_upload_validation.UploadValidationTests.test_rejects_malformed_docx) ... ok
test_rejects_mismatched_extension (test_upload_validation.UploadValidationTests.test_rejects_mismatched_extension) ... ok
test_rejects_oversized_file (test_upload_validation.UploadValidationTests.test_rejects_oversized_file) ... ok
test_rejects_unknown_document_type (test_upload_validation.UploadValidationTests.test_rejects_unknown_document_type) ... ok
test_rejects_zip_missing_word_document (test_upload_validation.UploadValidationTests.test_rejects_zip_missing_word_document) ... ok
test_invalid_uploads_have_stable_safe_error_codes (test_validation.UploadValidationErrorTests.test_invalid_uploads_have_stable_safe_error_codes) ... ok

----------------------------------------------------------------------
Ran 126 tests in 0.998s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
```

### Supplemental verification

- The first host-side harness attempt could not import project dependencies because the selected host Python environment lacks them. The full harness was rerun in the project API image as the workspace owner and passed.
- `git diff --check`: exit status `0`.
- `docker compose build api extraction-worker analysis-worker`: exit status `0`; all three images built.
- `docker compose config --quiet`: exit status `0`.
- Alembic SQL was generated offline and confirmed to include `0005_document_analysis`; the migration was not applied to the running database.
- No live AWS Bedrock request was made.

### Commit verification

- The TDD pairing hook passed. The commit hook ran the full unittest suite: 126 tests, `OK`.
- Implementation commit: `60e37948c852359899bd34ba53548952e374b44c` (`Implement consent-based document analysis`).

### Pull request follow-up

- Created [PR #36](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/pull/36) against `feature/async-document-extraction`; its body ends with `Resolves #32`.
- GitHub rejected `gh pr review 36 --approve` because the author cannot approve their own pull request.
- PR #36 is open and `CLEAN`, with no review requests and an empty review decision. Parent PR #35 has the same review state, so work on dependent issue #33 continued without waiting for approval.


## Prompt - 2026-10-31T16:11:41Z

### Exact user prompt

````text
implement the latest spec
````

### Execution - 2026-10-31T16:11:41Z

- Invocation: `INTERACTION_CAPTURE=1 INTERACTION_LOG=interactions/09-ai-suggestion-review/response-09-ai-suggestion-review.md bash harness/validate.sh -- python -m unittest discover -s tests -p test_review.py -v`
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
/usr/local/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  from starlette.testclient import TestClient as TestClient  # noqa
warning: The `fitz` API is deprecated and will be removed in future. Use `import pymupdf` instead.
test_upgrade_creates_authentication_schema_and_downgrade_removes_it (test_0002_authentication.AuthenticationMigrationTests.test_upgrade_creates_authentication_schema_and_downgrade_removes_it) ... ok
test_upgrade_creates_import_batch_and_idempotency_tables (test_0003_material_imports.MaterialImportsMigrationTests.test_upgrade_creates_import_batch_and_idempotency_tables) ... ok
test_downgrade_removes_jobs_and_page_provenance (test_0004_document_extraction_jobs.DocumentExtractionJobMigrationTests.test_downgrade_removes_jobs_and_page_provenance) ... ok
test_upgrade_adds_page_provenance_and_durable_jobs (test_0004_document_extraction_jobs.DocumentExtractionJobMigrationTests.test_upgrade_adds_page_provenance_and_durable_jobs) ... ok
test_downgrade_removes_analysis_tables_in_dependency_order (test_0005_document_analysis.DocumentAnalysisMigrationTests.test_downgrade_removes_analysis_tables_in_dependency_order) ... ok
test_upgrade_creates_consent_request_job_and_proposal_tables (test_0005_document_analysis.DocumentAnalysisMigrationTests.test_upgrade_creates_consent_request_job_and_proposal_tables) ... ok
test_0006_proposal_review_and_adoption (unittest.loader._FailedTest.test_0006_proposal_review_and_adoption) ... ERROR
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
[INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/56f311e6-1eb8-4f24-adb9-f4ce500bd7cf/files/9f2c23b8-ddbf-4aff-ac8b-553e1eb55a40 "HTTP/1.1 503 Service Unavailable"
ok
test_import_fails_closed_when_case_data_is_disabled (test_materials.MaterialsImportTests.test_import_fails_closed_when_case_data_is_disabled) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/3d9e9d9e-04ff-4205-b52c-0ce774b74f97/files/5552af2a-edab-4d30-aa67-59feb2cf63ab "HTTP/1.1 503 Service Unavailable"
ok
test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/66c78426-9b50-4973-9ed2-88e8bf819654/files/efdb2ec3-4891-45ae-86da-1e3c234bee94 "HTTP/1.1 415 Unsupported Media Type"
ok
test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/fddfd638-b7cd-4c6c-8d2c-0bdd5b14ded4/files/34684ca5-49a8-4a43-872e-01a6f3150c45 "HTTP/1.1 201 Created"
ok
test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/75285715-8655-41c7-86a9-4e1c7d0a9da1/files/d34912e7-96ef-4886-86f3-2d428ab44634 "HTTP/1.1 201 Created"
ok
test_models (unittest.loader._FailedTest.test_models) ... ERROR
test_compose_demo_login_is_explicit_and_case_data_remains_disabled (test_project_configuration.ProjectConfigurationTests.test_compose_demo_login_is_explicit_and_case_data_remains_disabled) ... ok
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
test_package_includes_the_landing_page_asset (test_project_configuration.ProjectConfigurationTests.test_package_includes_the_landing_page_asset) ... ok
test_project_declares_specified_stack (test_project_configuration.ProjectConfigurationTests.test_project_declares_specified_stack) ... ok
test_review (unittest.loader._FailedTest.test_review) ... ERROR
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

======================================================================
ERROR: test_0006_proposal_review_and_adoption (unittest.loader._FailedTest.test_0006_proposal_review_and_adoption)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_0006_proposal_review_and_adoption
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/unittest/loader.py", line 396, in _find_test_path
    module = self._get_module_from_name(name)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/loader.py", line 339, in _get_module_from_name
    __import__(name)
  File "/workspace/tests/test_0006_proposal_review_and_adoption.py", line 21, in <module>
    MIGRATION_SPEC.loader.exec_module(migration)
  File "<frozen importlib._bootstrap_external>", line 995, in exec_module
  File "<frozen importlib._bootstrap_external>", line 1132, in get_code
  File "<frozen importlib._bootstrap_external>", line 1190, in get_data
FileNotFoundError: [Errno 2] No such file or directory: '/workspace/migrations/versions/0006_proposal_review_and_adoption.py'


======================================================================
ERROR: test_models (unittest.loader._FailedTest.test_models)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_models
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/unittest/loader.py", line 396, in _find_test_path
    module = self._get_module_from_name(name)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/loader.py", line 339, in _get_module_from_name
    __import__(name)
  File "/workspace/tests/test_models.py", line 3, in <module>
    from app.models import (
ImportError: cannot import name 'CaseProfileAdoption' from 'app.models' (/workspace/src/app/models.py)


======================================================================
ERROR: test_review (unittest.loader._FailedTest.test_review)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_review
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/unittest/loader.py", line 396, in _find_test_path
    module = self._get_module_from_name(name)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/loader.py", line 339, in _get_module_from_name
    __import__(name)
  File "/workspace/tests/test_review.py", line 6, in <module>
    from app.review import (
ModuleNotFoundError: No module named 'app.review'


----------------------------------------------------------------------
Ran 126 tests in 0.923s

FAILED (errors=3)
FAIL: Python unit tests failed.
Validation failed with 1 missing requirement(s).
```

## Prompt - 2026-10-31T16:12:38Z

### Exact user prompt

````text
implement the latest spec
````

### Execution - 2026-10-31T16:12:38Z

- Invocation: `INTERACTION_CAPTURE=1 INTERACTION_LOG=interactions/09-ai-suggestion-review/response-09-ai-suggestion-review.md bash harness/validate.sh -- python -m unittest discover -s tests -p test_review.py -v`
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
/usr/local/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  from starlette.testclient import TestClient as TestClient  # noqa
warning: The `fitz` API is deprecated and will be removed in future. Use `import pymupdf` instead.
test_upgrade_creates_authentication_schema_and_downgrade_removes_it (test_0002_authentication.AuthenticationMigrationTests.test_upgrade_creates_authentication_schema_and_downgrade_removes_it) ... ok
test_upgrade_creates_import_batch_and_idempotency_tables (test_0003_material_imports.MaterialImportsMigrationTests.test_upgrade_creates_import_batch_and_idempotency_tables) ... ok
test_downgrade_removes_jobs_and_page_provenance (test_0004_document_extraction_jobs.DocumentExtractionJobMigrationTests.test_downgrade_removes_jobs_and_page_provenance) ... ok
test_upgrade_adds_page_provenance_and_durable_jobs (test_0004_document_extraction_jobs.DocumentExtractionJobMigrationTests.test_upgrade_adds_page_provenance_and_durable_jobs) ... ok
test_downgrade_removes_analysis_tables_in_dependency_order (test_0005_document_analysis.DocumentAnalysisMigrationTests.test_downgrade_removes_analysis_tables_in_dependency_order) ... ok
test_upgrade_creates_consent_request_job_and_proposal_tables (test_0005_document_analysis.DocumentAnalysisMigrationTests.test_upgrade_creates_consent_request_job_and_proposal_tables) ... ok
test_0006_proposal_review_and_adoption (unittest.loader._FailedTest.test_0006_proposal_review_and_adoption) ... ERROR
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
test_main (unittest.loader._FailedTest.test_main) ... ERROR
test_cleanup_failure_logs_no_object_key (test_materials.MaterialsImportTests.test_cleanup_failure_logs_no_object_key) ... ok
test_config_reports_runtime_upload_limit_and_unconfigured_providers (test_materials.MaterialsImportTests.test_config_reports_runtime_upload_limit_and_unconfigured_providers) ... [INFO] HTTP Request: GET http://testserver/api/v1/materials/config "HTTP/1.1 200 OK"
ok
test_database_failure_cleans_up_the_uploaded_object (test_materials.MaterialsImportTests.test_database_failure_cleans_up_the_uploaded_object) ... [ERROR] Material import database transaction failed (SQLAlchemyError).
[INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/1ea3b1bc-c6d2-4060-b54a-5c45b549336b/files/f5e8d744-8291-4925-bce2-41379b18e3ff "HTTP/1.1 503 Service Unavailable"
ok
test_import_fails_closed_when_case_data_is_disabled (test_materials.MaterialsImportTests.test_import_fails_closed_when_case_data_is_disabled) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/8892efb4-76f2-4ce2-bf9b-f69561ff707b/files/4540807e-ee0e-46fa-b0e8-77dfb19a15be "HTTP/1.1 503 Service Unavailable"
ok
test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/fee30aa0-c50c-4654-8411-935a561eb01d/files/48004eb9-32ed-4521-a810-4add60342fcf "HTTP/1.1 415 Unsupported Media Type"
ok
test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/7d31ec77-0b9a-420c-b5e7-9aaca11b76fd/files/4d5feeef-dd8d-416f-8239-9446f391bc4f "HTTP/1.1 201 Created"
ok
test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/c9d9127d-bd1b-4133-9760-c6d0bfb47067/files/213ddc77-ce29-4fba-8c00-5e9318d44840 "HTTP/1.1 201 Created"
ok
test_models (unittest.loader._FailedTest.test_models) ... ERROR
test_compose_demo_login_is_explicit_and_case_data_remains_disabled (test_project_configuration.ProjectConfigurationTests.test_compose_demo_login_is_explicit_and_case_data_remains_disabled) ... ok
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
test_package_includes_the_landing_page_asset (test_project_configuration.ProjectConfigurationTests.test_package_includes_the_landing_page_asset) ... ok
test_project_declares_specified_stack (test_project_configuration.ProjectConfigurationTests.test_project_declares_specified_stack) ... ok
test_review (unittest.loader._FailedTest.test_review) ... ERROR
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

======================================================================
ERROR: test_0006_proposal_review_and_adoption (unittest.loader._FailedTest.test_0006_proposal_review_and_adoption)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_0006_proposal_review_and_adoption
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/unittest/loader.py", line 396, in _find_test_path
    module = self._get_module_from_name(name)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/loader.py", line 339, in _get_module_from_name
    __import__(name)
  File "/workspace/tests/test_0006_proposal_review_and_adoption.py", line 21, in <module>
    MIGRATION_SPEC.loader.exec_module(migration)
  File "<frozen importlib._bootstrap_external>", line 995, in exec_module
  File "<frozen importlib._bootstrap_external>", line 1132, in get_code
  File "<frozen importlib._bootstrap_external>", line 1190, in get_data
FileNotFoundError: [Errno 2] No such file or directory: '/workspace/migrations/versions/0006_proposal_review_and_adoption.py'


======================================================================
ERROR: test_main (unittest.loader._FailedTest.test_main)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_main
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/unittest/loader.py", line 396, in _find_test_path
    module = self._get_module_from_name(name)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/loader.py", line 339, in _get_module_from_name
    __import__(name)
  File "/workspace/tests/test_main.py", line 14, in <module>
    from app.main import app, delete_document, preview_document
ImportError: cannot import name 'preview_document' from 'app.main' (/workspace/src/app/main.py)


======================================================================
ERROR: test_models (unittest.loader._FailedTest.test_models)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_models
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/unittest/loader.py", line 396, in _find_test_path
    module = self._get_module_from_name(name)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/loader.py", line 339, in _get_module_from_name
    __import__(name)
  File "/workspace/tests/test_models.py", line 3, in <module>
    from app.models import (
ImportError: cannot import name 'CaseProfileAdoption' from 'app.models' (/workspace/src/app/models.py)


======================================================================
ERROR: test_review (unittest.loader._FailedTest.test_review)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_review
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/unittest/loader.py", line 396, in _find_test_path
    module = self._get_module_from_name(name)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/loader.py", line 339, in _get_module_from_name
    __import__(name)
  File "/workspace/tests/test_review.py", line 9, in <module>
    from app.models import CaseProfileFact
ImportError: cannot import name 'CaseProfileFact' from 'app.models' (/workspace/src/app/models.py)


----------------------------------------------------------------------
Ran 120 tests in 0.952s

FAILED (errors=4)
FAIL: Python unit tests failed.
Validation failed with 1 missing requirement(s).
```

## Prompt - 2026-10-31T16:24:32Z

### Exact user prompt

````text
implement the latest spec
````

### Execution - 2026-10-31T16:24:32Z

- Invocation: `INTERACTION_CAPTURE=1 INTERACTION_LOG=interactions/09-ai-suggestion-review/response-09-ai-suggestion-review.md bash harness/validate.sh -- python -m unittest discover -s tests -p test_review.py -v`
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
/usr/local/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  from starlette.testclient import TestClient as TestClient  # noqa
warning: The `fitz` API is deprecated and will be removed in future. Use `import pymupdf` instead.
test_upgrade_creates_authentication_schema_and_downgrade_removes_it (test_0002_authentication.AuthenticationMigrationTests.test_upgrade_creates_authentication_schema_and_downgrade_removes_it) ... ok
test_upgrade_creates_import_batch_and_idempotency_tables (test_0003_material_imports.MaterialImportsMigrationTests.test_upgrade_creates_import_batch_and_idempotency_tables) ... ok
test_downgrade_removes_jobs_and_page_provenance (test_0004_document_extraction_jobs.DocumentExtractionJobMigrationTests.test_downgrade_removes_jobs_and_page_provenance) ... ok
test_upgrade_adds_page_provenance_and_durable_jobs (test_0004_document_extraction_jobs.DocumentExtractionJobMigrationTests.test_upgrade_adds_page_provenance_and_durable_jobs) ... ok
test_downgrade_removes_analysis_tables_in_dependency_order (test_0005_document_analysis.DocumentAnalysisMigrationTests.test_downgrade_removes_analysis_tables_in_dependency_order) ... ok
test_upgrade_creates_consent_request_job_and_proposal_tables (test_0005_document_analysis.DocumentAnalysisMigrationTests.test_upgrade_creates_consent_request_job_and_proposal_tables) ... ok
test_downgrade_removes_tables_before_profile_revision (test_0006_proposal_review_and_adoption.ProposalReviewMigrationTests.test_downgrade_removes_tables_before_profile_revision) ... ok
test_upgrade_adds_profile_revision_and_review_adoption_tables (test_0006_proposal_review_and_adoption.ProposalReviewMigrationTests.test_upgrade_adds_profile_revision_and_review_adoption_tables) ... ok
test_document_analysis_discards_unverifiable_proposals_individually (test_ai.BedrockExtractionTests.test_document_analysis_discards_unverifiable_proposals_individually) ... ok
test_document_analysis_verifies_page_citations_and_uses_no_tools (test_ai.BedrockExtractionTests.test_document_analysis_verifies_page_citations_and_uses_no_tools) ... ok
test_docx_analysis_requires_document_level_quotes_without_fake_pages (test_ai.BedrockExtractionTests.test_docx_analysis_requires_document_level_quotes_without_fake_pages) ... ok
test_rejects_unverifiable_source_quotes (test_ai.BedrockExtractionTests.test_rejects_unverifiable_source_quotes) ... ok
test_requires_a_configured_model (test_ai.BedrockExtractionTests.test_requires_a_configured_model) ... ok
test_returns_only_fields_with_verifiable_source_quotes (test_ai.BedrockExtractionTests.test_returns_only_fields_with_verifiable_source_quotes) ... ok
test_surfaces_invalid_model_output (test_ai.BedrockExtractionTests.test_surfaces_invalid_model_output) ... [WARNING] Bedrock returned non-JSON case analysis output.
ok
test_analysis_is_unavailable_by_default (test_analysis.AnalysisConfigurationTests.test_analysis_is_unavailable_by_default) ... ok
test_analysis_request_persists_consent_and_one_job_per_eligible_file (test_analysis.AnalysisConfigurationTests.test_analysis_request_persists_consent_and_one_job_per_eligible_file) ... ERROR
test_analysis_request_rejects_unprocessed_documents_without_queueing (test_analysis.AnalysisConfigurationTests.test_analysis_request_rejects_unprocessed_documents_without_queueing) ... ERROR
test_analysis_requires_provider_region_and_deployment_notice (test_analysis.AnalysisConfigurationTests.test_analysis_requires_provider_region_and_deployment_notice) ... ERROR
test_disclosure_names_provider_model_purpose_and_data_handling (test_analysis.AnalysisConfigurationTests.test_disclosure_names_provider_model_purpose_and_data_handling) ... ok
test_retry_only_requeues_a_failed_job_with_active_consent_and_same_source (test_analysis.AnalysisConfigurationTests.test_retry_only_requeues_a_failed_job_with_active_consent_and_same_source) ... ERROR
test_revocation_cancels_queued_jobs_for_the_request (test_analysis.AnalysisConfigurationTests.test_revocation_cancels_queued_jobs_for_the_request) ... ok
test_request_requires_explicit_consent_and_unique_documents (test_analysis.AnalysisRequestValidationTests.test_request_requires_explicit_consent_and_unique_documents) ... ok
test_request_status_reflects_work_and_mixed_terminal_outcomes (test_analysis.AnalysisRequestValidationTests.test_request_status_reflects_work_and_mixed_terminal_outcomes) ... ok
test_provider_is_not_called_when_analysis_is_disabled (test_analysis_worker.AnalysisWorkerTests.test_provider_is_not_called_when_analysis_is_disabled) ... ok
test_revoked_consent_cancels_job_without_calling_bedrock (test_analysis_worker.AnalysisWorkerTests.test_revoked_consent_cancels_job_without_calling_bedrock) ... ERROR
test_worker_claims_a_queued_job (test_analysis_worker.AnalysisWorkerTests.test_worker_claims_a_queued_job) ... ok
test_worker_persists_only_a_verified_proposal (test_analysis_worker.AnalysisWorkerTests.test_worker_persists_only_a_verified_proposal) ... ERROR
test_access_token_has_required_claims_and_validates_audience (test_auth.AuthenticationServiceTests.test_access_token_has_required_claims_and_validates_audience) ... ok
test_authentication_fails_closed_without_a_signing_secret (test_auth.AuthenticationServiceTests.test_authentication_fails_closed_without_a_signing_secret) ... ERROR
test_normalizes_email_without_provider_specific_rewriting (test_auth.AuthenticationServiceTests.test_normalizes_email_without_provider_specific_rewriting) ... ok
test_password_hash_verifies_without_storing_plaintext (test_auth.AuthenticationServiceTests.test_password_hash_verifies_without_storing_plaintext) ... ok
test_password_size_limit_counts_utf8_bytes (test_auth.AuthenticationServiceTests.test_password_size_limit_counts_utf8_bytes) ... ok
test_refresh_token_has_a_distinct_token_type_and_session_claim (test_auth.AuthenticationServiceTests.test_refresh_token_has_a_distinct_token_type_and_session_claim) ... ok
test_rejects_short_and_common_passwords (test_auth.AuthenticationServiceTests.test_rejects_short_and_common_passwords) ... ok
test_rejects_wrong_token_type_and_invalid_signature (test_auth.AuthenticationServiceTests.test_rejects_wrong_token_type_and_invalid_signature) ... ok
test_token_hash_is_stable_and_one_way (test_auth.AuthenticationServiceTests.test_token_hash_is_stable_and_one_way) ... ok
test_authentication_contract_routes_are_registered (test_auth_routes.AuthenticationRouteTests.test_authentication_contract_routes_are_registered) ... ok
test_authentication_routes_fail_closed_when_disabled (test_auth_routes.AuthenticationRouteTests.test_authentication_routes_fail_closed_when_disabled) ... ERROR
test_browser_auth_cookies_are_http_only_and_csrf_cookie_is_accessible (test_auth_routes.AuthenticationRouteTests.test_browser_auth_cookies_are_http_only_and_csrf_cookie_is_accessible) ... ok
test_demo_login_accepts_demo_credentials_only_when_demo_mode_is_enabled (test_auth_routes.AuthenticationRouteTests.test_demo_login_accepts_demo_credentials_only_when_demo_mode_is_enabled) ... ok
test_demo_login_rejects_an_incorrect_password (test_auth_routes.AuthenticationRouteTests.test_demo_login_rejects_an_incorrect_password) ... ok
test_google_provider_is_reported_available_when_fully_configured (test_auth_routes.AuthenticationRouteTests.test_google_provider_is_reported_available_when_fully_configured) ... [INFO] HTTP Request: GET http://testserver/api/auth/providers "HTTP/1.1 200 OK"
ok
test_google_provider_is_reported_unavailable_when_auth_is_disabled (test_auth_routes.AuthenticationRouteTests.test_google_provider_is_reported_unavailable_when_auth_is_disabled) ... ERROR
test_mfa_challenge_is_sent_in_the_request_body_not_the_url (test_auth_routes.AuthenticationRouteTests.test_mfa_challenge_is_sent_in_the_request_body_not_the_url) ... ok
test_passkey_verification_handlers_are_not_duplicated (test_auth_routes.AuthenticationRouteTests.test_passkey_verification_handlers_are_not_duplicated) ... ok
test_totp_secrets_are_encrypted_and_codes_are_time_bounded (test_auth_routes.AuthenticationRouteTests.test_totp_secrets_are_encrypted_and_codes_are_time_bounded) ... ok
test_auth_cannot_be_enabled_without_a_strong_secret (test_config.SettingsTests.test_auth_cannot_be_enabled_without_a_strong_secret) ... FAIL
test_authentication_configuration_rejects_invalid_session_lifetimes (test_config.SettingsTests.test_authentication_configuration_rejects_invalid_session_lifetimes) ... ok
test_authentication_configuration_rejects_mismatched_provider_secrets (test_config.SettingsTests.test_authentication_configuration_rejects_mismatched_provider_secrets) ... ok
test_authentication_is_disabled_without_explicit_secrets (test_config.SettingsTests.test_authentication_is_disabled_without_explicit_secrets) ... ERROR
test_bedrock_configuration_is_optional (test_config.SettingsTests.test_bedrock_configuration_is_optional) ... FAIL
test_bedrock_model_and_region_can_be_configured (test_config.SettingsTests.test_bedrock_model_and_region_can_be_configured) ... ok
test_case_data_cannot_be_enabled_without_authentication (test_config.SettingsTests.test_case_data_cannot_be_enabled_without_authentication) ... FAIL
test_case_materials_require_auth_and_case_data (test_config.SettingsTests.test_case_materials_require_auth_and_case_data) ... ok
test_demo_mode_is_local_only_and_cannot_enable_case_data (test_config.SettingsTests.test_demo_mode_is_local_only_and_cannot_enable_case_data) ... ok
test_local_loopback_storage_can_be_explicitly_enabled_without_kms (test_config.SettingsTests.test_local_loopback_storage_can_be_explicitly_enabled_without_kms) ... ok
test_non_local_auth_origins_require_https (test_config.SettingsTests.test_non_local_auth_origins_require_https) ... ok
test_production_case_data_requires_kms_even_before_materials_toggle (test_config.SettingsTests.test_production_case_data_requires_kms_even_before_materials_toggle) ... FAIL
test_production_case_materials_require_a_kms_key (test_config.SettingsTests.test_production_case_materials_require_a_kms_key) ... FAIL
test_remote_http_s3_endpoint_is_rejected (test_config.SettingsTests.test_remote_http_s3_endpoint_is_rejected) ... ok
test_s3_endpoint_cannot_embed_credentials (test_config.SettingsTests.test_s3_endpoint_cannot_embed_credentials) ... ok
test_samesite_none_requires_secure_cookies (test_config.SettingsTests.test_samesite_none_requires_secure_cookies) ... ok
test_status_reports_database_failure_as_retryable_service_error (test_dashboard.DashboardStatusTests.test_status_reports_database_failure_as_retryable_service_error) ... [ERROR] Dashboard case-status lookup failed.
Traceback (most recent call last):
  File "/app/src/app/main.py", line 334, in dashboard_status
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
  File "/app/src/app/main.py", line 663, in delete_document
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
test_document_deletion_requires_case_membership_and_non_viewer_role (test_main.MainWorkflowTests.test_document_deletion_requires_case_membership_and_non_viewer_role) ... ERROR
test_onboarding_paths_serve_the_authenticated_preview_page (test_main.MainWorkflowTests.test_onboarding_paths_serve_the_authenticated_preview_page) ... ok
test_pdf_preview_is_inline_and_not_cacheable (test_main.MainWorkflowTests.test_pdf_preview_is_inline_and_not_cacheable) ... ok
test_root_displays_mode_choices_and_authentication_gate (test_main.MainWorkflowTests.test_root_displays_mode_choices_and_authentication_gate) ... ok
test_cleanup_failure_logs_no_object_key (test_materials.MaterialsImportTests.test_cleanup_failure_logs_no_object_key) ... ok
test_config_reports_runtime_upload_limit_and_unconfigured_providers (test_materials.MaterialsImportTests.test_config_reports_runtime_upload_limit_and_unconfigured_providers) ... ERROR
test_database_failure_cleans_up_the_uploaded_object (test_materials.MaterialsImportTests.test_database_failure_cleans_up_the_uploaded_object) ... ERROR
test_import_fails_closed_when_case_data_is_disabled (test_materials.MaterialsImportTests.test_import_fails_closed_when_case_data_is_disabled) ... ERROR
test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case) ... ERROR
test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again) ... ERROR
test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file) ... ERROR
test_analysis_jobs_and_proposals_keep_source_provenance (test_models.AuthenticationModelTests.test_analysis_jobs_and_proposals_keep_source_provenance) ... ok
test_authentication_tables_are_registered (test_models.AuthenticationModelTests.test_authentication_tables_are_registered) ... ok
test_case_profile_facts_are_append_only_and_keep_source_provenance (test_models.AuthenticationModelTests.test_case_profile_facts_are_append_only_and_keep_source_provenance) ... ok
test_provider_and_case_access_constraints_are_explicit (test_models.AuthenticationModelTests.test_provider_and_case_access_constraints_are_explicit) ... ok
test_compose_demo_login_is_explicit_and_case_data_remains_disabled (test_project_configuration.ProjectConfigurationTests.test_compose_demo_login_is_explicit_and_case_data_remains_disabled) ... ok
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
test_package_includes_the_landing_page_asset (test_project_configuration.ProjectConfigurationTests.test_package_includes_the_landing_page_asset) ... ok
test_project_declares_specified_stack (test_project_configuration.ProjectConfigurationTests.test_project_declares_specified_stack) ... ok
test_adoption_requires_explicit_confirmation_and_unique_proposals (test_review.ProposalReviewContractTests.test_adoption_requires_explicit_confirmation_and_unique_proposals) ... ok
test_adoption_retry_returns_the_existing_outcome (test_review.ProposalReviewContractTests.test_adoption_retry_returns_the_existing_outcome) ... ok
test_adoption_uses_reviewed_value_and_keeps_json_profile_unchanged (test_review.ProposalReviewContractTests.test_adoption_uses_reviewed_value_and_keeps_json_profile_unchanged) ... ok
test_case_membership_blocks_viewers_and_hides_unknown_cases (test_review.ProposalReviewContractTests.test_case_membership_blocks_viewers_and_hides_unknown_cases) ... ok
test_docx_source_text_reports_unavailable_physical_page (test_review.ProposalReviewContractTests.test_docx_source_text_reports_unavailable_physical_page) ... ok
test_edit_decision_requires_a_nonempty_bounded_value (test_review.ProposalReviewContractTests.test_edit_decision_requires_a_nonempty_bounded_value) ... ok
test_fact_disposition_requires_confirmation_and_profile_revision (test_review.ProposalReviewContractTests.test_fact_disposition_requires_confirmation_and_profile_revision) ... ok
test_non_edit_decisions_cannot_supply_a_replacement_value (test_review.ProposalReviewContractTests.test_non_edit_decisions_cannot_supply_a_replacement_value) ... ok
test_review_cannot_accept_a_missing_or_changed_source (test_review.ProposalReviewContractTests.test_review_cannot_accept_a_missing_or_changed_source) ... ok
test_review_decision_is_append_only_and_does_not_adopt_a_fact (test_review.ProposalReviewContractTests.test_review_decision_is_append_only_and_does_not_adopt_a_fact) ... ok
test_same_field_facts_are_both_preserved_and_marked_as_conflicts (test_review.ProposalReviewContractTests.test_same_field_facts_are_both_preserved_and_marked_as_conflicts) ... FAIL
test_stale_profile_revision_does_not_partially_adopt (test_review.ProposalReviewContractTests.test_stale_profile_revision_does_not_partially_adopt) ... ERROR
test_withdrawal_retry_returns_the_existing_event (test_review.ProposalReviewContractTests.test_withdrawal_retry_returns_the_existing_event) ... ok
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

======================================================================
ERROR: test_analysis_request_persists_consent_and_one_job_per_eligible_file (test_analysis.AnalysisConfigurationTests.test_analysis_request_persists_consent_and_one_job_per_eligible_file)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_analysis.py", line 97, in test_analysis_request_persists_consent_and_one_job_per_eligible_file
    enabled_settings(),
    ^^^^^^^^^^^^^^^^^^
  File "/app/tests/test_analysis.py", line 265, in enabled_settings
    return Settings(
           ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, Case-material storage cannot be enabled in demo mode. [type=value_error, input_value={'database_url': 'postgre...ey-that-is-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_analysis_request_rejects_unprocessed_documents_without_queueing (test_analysis.AnalysisConfigurationTests.test_analysis_request_rejects_unprocessed_documents_without_queueing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_analysis.py", line 129, in test_analysis_request_rejects_unprocessed_documents_without_queueing
    enabled_settings(),
    ^^^^^^^^^^^^^^^^^^
  File "/app/tests/test_analysis.py", line 265, in enabled_settings
    return Settings(
           ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, Case-material storage cannot be enabled in demo mode. [type=value_error, input_value={'database_url': 'postgre...ey-that-is-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_analysis_requires_provider_region_and_deployment_notice (test_analysis.AnalysisConfigurationTests.test_analysis_requires_provider_region_and_deployment_notice)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_analysis.py", line 40, in test_analysis_requires_provider_region_and_deployment_notice
    self.assertTrue(is_analysis_available(Settings(**base)))
                                          ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, Case-material storage cannot be enabled in demo mode. [type=value_error, input_value={'database_url': 'postgre...ey-that-is-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_retry_only_requeues_a_failed_job_with_active_consent_and_same_source (test_analysis.AnalysisConfigurationTests.test_retry_only_requeues_a_failed_job_with_active_consent_and_same_source)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_analysis.py", line 179, in test_retry_only_requeues_a_failed_job_with_active_consent_and_same_source
    enabled_settings(),
    ^^^^^^^^^^^^^^^^^^
  File "/app/tests/test_analysis.py", line 265, in enabled_settings
    return Settings(
           ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, Case-material storage cannot be enabled in demo mode. [type=value_error, input_value={'database_url': 'postgre...ey-that-is-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_revoked_consent_cancels_job_without_calling_bedrock (test_analysis_worker.AnalysisWorkerTests.test_revoked_consent_cancels_job_without_calling_bedrock)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_analysis_worker.py", line 194, in test_revoked_consent_cancels_job_without_calling_bedrock
    settings=enabled_settings(),
             ^^^^^^^^^^^^^^^^^^
  File "/app/tests/test_analysis_worker.py", line 34, in enabled_settings
    return Settings(
           ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, Case-material storage cannot be enabled in demo mode. [type=value_error, input_value={'database_url': 'postgre...ey-that-is-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_worker_persists_only_a_verified_proposal (test_analysis_worker.AnalysisWorkerTests.test_worker_persists_only_a_verified_proposal)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_analysis_worker.py", line 148, in test_worker_persists_only_a_verified_proposal
    settings=enabled_settings(),
             ^^^^^^^^^^^^^^^^^^
  File "/app/tests/test_analysis_worker.py", line 34, in enabled_settings
    return Settings(
           ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, Case-material storage cannot be enabled in demo mode. [type=value_error, input_value={'database_url': 'postgre...ey-that-is-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_authentication_fails_closed_without_a_signing_secret (test_auth.AuthenticationServiceTests.test_authentication_fails_closed_without_a_signing_secret)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_auth.py", line 91, in test_authentication_fails_closed_without_a_signing_secret
    Settings(
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...'auth_jwt_secret': None}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_authentication_routes_fail_closed_when_disabled (test_auth_routes.AuthenticationRouteTests.test_authentication_routes_fail_closed_when_disabled)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_auth_routes.py", line 90, in test_authentication_routes_fail_closed_when_disabled
    disabled = Settings(
               ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...'auth_jwt_secret': None}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_google_provider_is_reported_unavailable_when_auth_is_disabled (test_auth_routes.AuthenticationRouteTests.test_google_provider_is_reported_unavailable_when_auth_is_disabled)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_auth_routes.py", line 104, in test_google_provider_is_reported_unavailable_when_auth_is_disabled
    disabled = Settings(
               ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...'auth_jwt_secret': None}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_authentication_is_disabled_without_explicit_secrets (test_config.SettingsTests.test_authentication_is_disabled_without_explicit_secrets)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_config.py", line 23, in test_authentication_is_disabled_without_explicit_secrets
    settings = Settings(
               ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...'auth_jwt_secret': None}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_document_deletion_requires_case_membership_and_non_viewer_role (test_main.MainWorkflowTests.test_document_deletion_requires_case_membership_and_non_viewer_role)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_main.py", line 261, in test_document_deletion_requires_case_membership_and_non_viewer_role
    settings = Settings(
               ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...et-that-is-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_config_reports_runtime_upload_limit_and_unconfigured_providers (test_materials.MaterialsImportTests.test_config_reports_runtime_upload_limit_and_unconfigured_providers)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_materials.py", line 33, in test_config_reports_runtime_upload_limit_and_unconfigured_providers
    settings = Settings(
               ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...ax_upload_bytes': 12345}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_database_failure_cleans_up_the_uploaded_object (test_materials.MaterialsImportTests.test_database_failure_cleans_up_the_uploaded_object)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_materials.py", line 176, in test_database_failure_cleans_up_the_uploaded_object
    settings = Settings(
               ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...ing-secret-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_import_fails_closed_when_case_data_is_disabled (test_materials.MaterialsImportTests.test_import_fails_closed_when_case_data_is_disabled)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_materials.py", line 57, in test_import_fails_closed_when_case_data_is_disabled
    settings = Settings(
               ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...ing-secret-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_materials.py", line 74, in test_import_validates_file_before_creating_a_case
    settings = Settings(
               ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...ing-secret-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_materials.py", line 152, in test_retry_returns_existing_document_without_uploading_again
    settings = Settings(
               ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...ing-secret-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_materials.py", line 96, in test_successful_import_creates_one_owned_draft_and_stores_the_file
    settings = Settings(
               ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...ing-secret-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_stale_profile_revision_does_not_partially_adopt (test_review.ProposalReviewContractTests.test_stale_profile_revision_does_not_partially_adopt)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_review.py", line 342, in test_stale_profile_revision_does_not_partially_adopt
    adopt_case_proposals(db, case_id, uuid4(), payload)
  File "/app/src/app/review.py", line 670, in adopt_case_proposals
    existing = db.scalar(
               ^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/mock.py", line 1200, in _execute_mock_call
    result = next(effect)
             ^^^^^^^^^^^^
StopIteration

======================================================================
FAIL: test_auth_cannot_be_enabled_without_a_strong_secret (test_config.SettingsTests.test_auth_cannot_be_enabled_without_a_strong_secret)
----------------------------------------------------------------------
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...'auth_jwt_secret': None}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/app/tests/test_config.py", line 50, in test_auth_cannot_be_enabled_without_a_strong_secret
    with self.assertRaisesRegex(ValueError, "at least 32 bytes"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "at least 32 bytes" does not match "1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...'auth_jwt_secret': None}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error"

======================================================================
FAIL: test_bedrock_configuration_is_optional (test_config.SettingsTests.test_bedrock_configuration_is_optional)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_config.py", line 10, in test_bedrock_configuration_is_optional
    self.assertIsNone(settings.bedrock_model_id)
AssertionError: '' is not None

======================================================================
FAIL: test_case_data_cannot_be_enabled_without_authentication (test_config.SettingsTests.test_case_data_cannot_be_enabled_without_authentication)
----------------------------------------------------------------------
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...mo_mode_enabled': False}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/app/tests/test_config.py", line 62, in test_case_data_cannot_be_enabled_without_authentication
    with self.assertRaisesRegex(ValueError, "requires AUTH_ENABLED"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "requires AUTH_ENABLED" does not match "1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...mo_mode_enabled': False}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error"

======================================================================
FAIL: test_production_case_data_requires_kms_even_before_materials_toggle (test_config.SettingsTests.test_production_case_data_requires_kms_even_before_materials_toggle)
----------------------------------------------------------------------
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...et-that-is-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/app/tests/test_config.py", line 117, in test_production_case_data_requires_kms_even_before_materials_toggle
    with self.assertRaisesRegex(ValueError, "before production case-data access"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "before production case-data access" does not match "1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...et-that-is-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error"

======================================================================
FAIL: test_production_case_materials_require_a_kms_key (test_config.SettingsTests.test_production_case_materials_require_a_kms_key)
----------------------------------------------------------------------
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...et-that-is-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/app/tests/test_config.py", line 95, in test_production_case_materials_require_a_kms_key
    with self.assertRaisesRegex(ValueError, "S3_KMS_KEY_ID"):
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "S3_KMS_KEY_ID" does not match "1 validation error for Settings
  Value error, S3_ENDPOINT_URL must use HTTPS outside loopback development. [type=value_error, input_value={'database_url': 'postgre...et-that-is-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error"

======================================================================
FAIL: test_same_field_facts_are_both_preserved_and_marked_as_conflicts (test_review.ProposalReviewContractTests.test_same_field_facts_are_both_preserved_and_marked_as_conflicts)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_review.py", line 320, in test_same_field_facts_are_both_preserved_and_marked_as_conflicts
    self.assertEqual([item.value for item in result.facts], ["$5,000", "$5,200"])
AssertionError: Lists differ: [] != ['$5,000', '$5,200']

Second list contains 2 additional elements.
First extra element 0:
'$5,000'

- []
+ ['$5,000', '$5,200']

----------------------------------------------------------------------
Ran 143 tests in 1.009s

FAILED (failures=6, errors=18)
FAIL: Python unit tests failed.
Validation failed with 1 missing requirement(s).
```

## Prompt - 2026-10-31T16:25:13Z

### Exact user prompt

````text
implement the latest spec
````

### Execution - 2026-10-31T16:25:13Z

- Invocation: `INTERACTION_CAPTURE=1 INTERACTION_LOG=interactions/09-ai-suggestion-review/response-09-ai-suggestion-review.md bash harness/validate.sh -- python -m unittest discover -s tests -p test_review.py -v`
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
/usr/local/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  from starlette.testclient import TestClient as TestClient  # noqa
warning: The `fitz` API is deprecated and will be removed in future. Use `import pymupdf` instead.
test_upgrade_creates_authentication_schema_and_downgrade_removes_it (test_0002_authentication.AuthenticationMigrationTests.test_upgrade_creates_authentication_schema_and_downgrade_removes_it) ... ok
test_upgrade_creates_import_batch_and_idempotency_tables (test_0003_material_imports.MaterialImportsMigrationTests.test_upgrade_creates_import_batch_and_idempotency_tables) ... ok
test_downgrade_removes_jobs_and_page_provenance (test_0004_document_extraction_jobs.DocumentExtractionJobMigrationTests.test_downgrade_removes_jobs_and_page_provenance) ... ok
test_upgrade_adds_page_provenance_and_durable_jobs (test_0004_document_extraction_jobs.DocumentExtractionJobMigrationTests.test_upgrade_adds_page_provenance_and_durable_jobs) ... ok
test_downgrade_removes_analysis_tables_in_dependency_order (test_0005_document_analysis.DocumentAnalysisMigrationTests.test_downgrade_removes_analysis_tables_in_dependency_order) ... ok
test_upgrade_creates_consent_request_job_and_proposal_tables (test_0005_document_analysis.DocumentAnalysisMigrationTests.test_upgrade_creates_consent_request_job_and_proposal_tables) ... ok
test_downgrade_removes_tables_before_profile_revision (test_0006_proposal_review_and_adoption.ProposalReviewMigrationTests.test_downgrade_removes_tables_before_profile_revision) ... ok
test_upgrade_adds_profile_revision_and_review_adoption_tables (test_0006_proposal_review_and_adoption.ProposalReviewMigrationTests.test_upgrade_adds_profile_revision_and_review_adoption_tables) ... ok
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
  File "/app/src/app/main.py", line 334, in dashboard_status
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
  File "/app/src/app/main.py", line 663, in delete_document
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
test_pdf_preview_is_inline_and_not_cacheable (test_main.MainWorkflowTests.test_pdf_preview_is_inline_and_not_cacheable) ... ok
test_root_displays_mode_choices_and_authentication_gate (test_main.MainWorkflowTests.test_root_displays_mode_choices_and_authentication_gate) ... ok
test_cleanup_failure_logs_no_object_key (test_materials.MaterialsImportTests.test_cleanup_failure_logs_no_object_key) ... ok
test_config_reports_runtime_upload_limit_and_unconfigured_providers (test_materials.MaterialsImportTests.test_config_reports_runtime_upload_limit_and_unconfigured_providers) ... [INFO] HTTP Request: GET http://testserver/api/v1/materials/config "HTTP/1.1 200 OK"
ok
test_database_failure_cleans_up_the_uploaded_object (test_materials.MaterialsImportTests.test_database_failure_cleans_up_the_uploaded_object) ... [ERROR] Material import database transaction failed (SQLAlchemyError).
[INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/2bbf3e06-252b-4521-be63-f43d0459dc7d/files/c2ad93a6-53c6-488b-99e1-89c317ada0c6 "HTTP/1.1 503 Service Unavailable"
ok
test_import_fails_closed_when_case_data_is_disabled (test_materials.MaterialsImportTests.test_import_fails_closed_when_case_data_is_disabled) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/ec69393d-5f39-443e-ad75-137bc135d649/files/bb3b22d6-96b8-45be-aa8b-d9a37ffe14d5 "HTTP/1.1 503 Service Unavailable"
ok
test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/9843e1b7-e65d-4d26-ac51-28aae58dbffd/files/b319553b-5fd8-4e12-8fb4-826906993d5b "HTTP/1.1 415 Unsupported Media Type"
ok
test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/1053ed3e-e49c-43a9-8eb6-cea3c93045fd/files/2ac0127d-222a-4d0e-9b34-1d3046f8f117 "HTTP/1.1 201 Created"
ok
test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/17c07d13-c13d-46ef-b21f-4feb9f542cb5/files/c6c6f787-c209-4684-aaec-635bd2227ac0 "HTTP/1.1 201 Created"
ok
test_analysis_jobs_and_proposals_keep_source_provenance (test_models.AuthenticationModelTests.test_analysis_jobs_and_proposals_keep_source_provenance) ... ok
test_authentication_tables_are_registered (test_models.AuthenticationModelTests.test_authentication_tables_are_registered) ... ok
test_case_profile_facts_are_append_only_and_keep_source_provenance (test_models.AuthenticationModelTests.test_case_profile_facts_are_append_only_and_keep_source_provenance) ... ok
test_provider_and_case_access_constraints_are_explicit (test_models.AuthenticationModelTests.test_provider_and_case_access_constraints_are_explicit) ... ok
test_compose_demo_login_is_explicit_and_case_data_remains_disabled (test_project_configuration.ProjectConfigurationTests.test_compose_demo_login_is_explicit_and_case_data_remains_disabled) ... ok
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
test_package_includes_the_landing_page_asset (test_project_configuration.ProjectConfigurationTests.test_package_includes_the_landing_page_asset) ... ok
test_project_declares_specified_stack (test_project_configuration.ProjectConfigurationTests.test_project_declares_specified_stack) ... ok
test_adoption_requires_explicit_confirmation_and_unique_proposals (test_review.ProposalReviewContractTests.test_adoption_requires_explicit_confirmation_and_unique_proposals) ... ok
test_adoption_retry_returns_the_existing_outcome (test_review.ProposalReviewContractTests.test_adoption_retry_returns_the_existing_outcome) ... ok
test_adoption_uses_reviewed_value_and_keeps_json_profile_unchanged (test_review.ProposalReviewContractTests.test_adoption_uses_reviewed_value_and_keeps_json_profile_unchanged) ... ok
test_case_membership_blocks_viewers_and_hides_unknown_cases (test_review.ProposalReviewContractTests.test_case_membership_blocks_viewers_and_hides_unknown_cases) ... ok
test_docx_source_text_reports_unavailable_physical_page (test_review.ProposalReviewContractTests.test_docx_source_text_reports_unavailable_physical_page) ... ok
test_edit_decision_requires_a_nonempty_bounded_value (test_review.ProposalReviewContractTests.test_edit_decision_requires_a_nonempty_bounded_value) ... ok
test_fact_disposition_requires_confirmation_and_profile_revision (test_review.ProposalReviewContractTests.test_fact_disposition_requires_confirmation_and_profile_revision) ... ok
test_non_edit_decisions_cannot_supply_a_replacement_value (test_review.ProposalReviewContractTests.test_non_edit_decisions_cannot_supply_a_replacement_value) ... ok
test_review_cannot_accept_a_missing_or_changed_source (test_review.ProposalReviewContractTests.test_review_cannot_accept_a_missing_or_changed_source) ... ok
test_review_decision_is_append_only_and_does_not_adopt_a_fact (test_review.ProposalReviewContractTests.test_review_decision_is_append_only_and_does_not_adopt_a_fact) ... ok
test_same_field_facts_are_both_preserved_and_marked_as_conflicts (test_review.ProposalReviewContractTests.test_same_field_facts_are_both_preserved_and_marked_as_conflicts) ... ok
test_stale_profile_revision_does_not_partially_adopt (test_review.ProposalReviewContractTests.test_stale_profile_revision_does_not_partially_adopt) ... ERROR
test_withdrawal_retry_returns_the_existing_event (test_review.ProposalReviewContractTests.test_withdrawal_retry_returns_the_existing_event) ... ok
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

======================================================================
ERROR: test_stale_profile_revision_does_not_partially_adopt (test_review.ProposalReviewContractTests.test_stale_profile_revision_does_not_partially_adopt)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/app/tests/test_review.py", line 342, in test_stale_profile_revision_does_not_partially_adopt
    adopt_case_proposals(db, case_id, uuid4(), payload)
  File "/app/src/app/review.py", line 670, in adopt_case_proposals
    existing = db.scalar(
               ^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/mock.py", line 1139, in __call__
    return self._mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/mock.py", line 1143, in _mock_call
    return self._execute_mock_call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/unittest/mock.py", line 1200, in _execute_mock_call
    result = next(effect)
             ^^^^^^^^^^^^
StopIteration

----------------------------------------------------------------------
Ran 143 tests in 1.018s

FAILED (errors=1)
FAIL: Python unit tests failed.
Validation failed with 1 missing requirement(s).
```

## Prompt - 2026-10-31T16:26:47Z

### Exact user prompt

````text
implement the latest spec
````

### Execution - 2026-10-31T16:26:47Z

- Invocation: `INTERACTION_CAPTURE=1 INTERACTION_LOG=interactions/09-ai-suggestion-review/response-09-ai-suggestion-review.md bash harness/validate.sh -- python -m unittest discover -s tests -p test_review.py -v`
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
test_downgrade_removes_tables_before_profile_revision (test_0006_proposal_review_and_adoption.ProposalReviewMigrationTests.test_downgrade_removes_tables_before_profile_revision) ... ok
test_upgrade_adds_profile_revision_and_review_adoption_tables (test_0006_proposal_review_and_adoption.ProposalReviewMigrationTests.test_upgrade_adds_profile_revision_and_review_adoption_tables) ... ok
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
  File "/app/src/app/main.py", line 334, in dashboard_status
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
  File "/app/src/app/main.py", line 663, in delete_document
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
test_pdf_preview_is_inline_and_not_cacheable (test_main.MainWorkflowTests.test_pdf_preview_is_inline_and_not_cacheable) ... ok
test_root_displays_mode_choices_and_authentication_gate (test_main.MainWorkflowTests.test_root_displays_mode_choices_and_authentication_gate) ... ok
test_cleanup_failure_logs_no_object_key (test_materials.MaterialsImportTests.test_cleanup_failure_logs_no_object_key) ... ok
test_config_reports_runtime_upload_limit_and_unconfigured_providers (test_materials.MaterialsImportTests.test_config_reports_runtime_upload_limit_and_unconfigured_providers) ... [INFO] HTTP Request: GET http://testserver/api/v1/materials/config "HTTP/1.1 200 OK"
ok
test_database_failure_cleans_up_the_uploaded_object (test_materials.MaterialsImportTests.test_database_failure_cleans_up_the_uploaded_object) ... [ERROR] Material import database transaction failed (SQLAlchemyError).
[INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/6a1677a9-be92-4222-b25b-b65510238036/files/62f6a50d-a1a2-49d6-ac21-5f5c905c0e43 "HTTP/1.1 503 Service Unavailable"
ok
test_import_fails_closed_when_case_data_is_disabled (test_materials.MaterialsImportTests.test_import_fails_closed_when_case_data_is_disabled) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/3d7146c9-16f9-4467-a0e9-a64cf6e26b36/files/34d3662f-3e6d-44a1-822a-055b80196276 "HTTP/1.1 503 Service Unavailable"
ok
test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/9a043733-4fe0-494d-b6e6-69e62e50f383/files/6c8e5b7c-7d3a-453f-864c-f1aaa78ba893 "HTTP/1.1 415 Unsupported Media Type"
ok
test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/1b92e275-a55f-48d3-a29e-056c678aff33/files/f51d4d6f-0522-4b34-a67d-36677aa06f54 "HTTP/1.1 201 Created"
ok
test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/00c27879-28ff-43e8-983e-829276784a89/files/1aef01cf-c1bb-4d84-b23b-9bfc318dcf7b "HTTP/1.1 201 Created"
ok
test_analysis_jobs_and_proposals_keep_source_provenance (test_models.AuthenticationModelTests.test_analysis_jobs_and_proposals_keep_source_provenance) ... ok
test_authentication_tables_are_registered (test_models.AuthenticationModelTests.test_authentication_tables_are_registered) ... ok
test_case_profile_facts_are_append_only_and_keep_source_provenance (test_models.AuthenticationModelTests.test_case_profile_facts_are_append_only_and_keep_source_provenance) ... ok
test_provider_and_case_access_constraints_are_explicit (test_models.AuthenticationModelTests.test_provider_and_case_access_constraints_are_explicit) ... ok
test_compose_demo_login_is_explicit_and_case_data_remains_disabled (test_project_configuration.ProjectConfigurationTests.test_compose_demo_login_is_explicit_and_case_data_remains_disabled) ... ok
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
test_package_includes_the_landing_page_asset (test_project_configuration.ProjectConfigurationTests.test_package_includes_the_landing_page_asset) ... ok
test_project_declares_specified_stack (test_project_configuration.ProjectConfigurationTests.test_project_declares_specified_stack) ... ok
test_adoption_requires_explicit_confirmation_and_unique_proposals (test_review.ProposalReviewContractTests.test_adoption_requires_explicit_confirmation_and_unique_proposals) ... ok
test_adoption_retry_returns_the_existing_outcome (test_review.ProposalReviewContractTests.test_adoption_retry_returns_the_existing_outcome) ... ok
test_adoption_uses_reviewed_value_and_keeps_json_profile_unchanged (test_review.ProposalReviewContractTests.test_adoption_uses_reviewed_value_and_keeps_json_profile_unchanged) ... ok
test_case_membership_blocks_viewers_and_hides_unknown_cases (test_review.ProposalReviewContractTests.test_case_membership_blocks_viewers_and_hides_unknown_cases) ... ok
test_docx_source_text_reports_unavailable_physical_page (test_review.ProposalReviewContractTests.test_docx_source_text_reports_unavailable_physical_page) ... ok
test_edit_decision_requires_a_nonempty_bounded_value (test_review.ProposalReviewContractTests.test_edit_decision_requires_a_nonempty_bounded_value) ... ok
test_fact_disposition_requires_confirmation_and_profile_revision (test_review.ProposalReviewContractTests.test_fact_disposition_requires_confirmation_and_profile_revision) ... ok
test_non_edit_decisions_cannot_supply_a_replacement_value (test_review.ProposalReviewContractTests.test_non_edit_decisions_cannot_supply_a_replacement_value) ... ok
test_review_cannot_accept_a_missing_or_changed_source (test_review.ProposalReviewContractTests.test_review_cannot_accept_a_missing_or_changed_source) ... ok
test_review_decision_is_append_only_and_does_not_adopt_a_fact (test_review.ProposalReviewContractTests.test_review_decision_is_append_only_and_does_not_adopt_a_fact) ... ok
test_same_field_facts_are_both_preserved_and_marked_as_conflicts (test_review.ProposalReviewContractTests.test_same_field_facts_are_both_preserved_and_marked_as_conflicts) ... ok
test_stale_profile_revision_does_not_partially_adopt (test_review.ProposalReviewContractTests.test_stale_profile_revision_does_not_partially_adopt) ... ok
test_withdrawal_retry_returns_the_existing_event (test_review.ProposalReviewContractTests.test_withdrawal_retry_returns_the_existing_event) ... ok
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
Ran 143 tests in 1.093s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
test_adoption_requires_explicit_confirmation_and_unique_proposals (test_review.ProposalReviewContractTests.test_adoption_requires_explicit_confirmation_and_unique_proposals) ... ok
test_adoption_retry_returns_the_existing_outcome (test_review.ProposalReviewContractTests.test_adoption_retry_returns_the_existing_outcome) ... ok
test_adoption_uses_reviewed_value_and_keeps_json_profile_unchanged (test_review.ProposalReviewContractTests.test_adoption_uses_reviewed_value_and_keeps_json_profile_unchanged) ... ok
test_case_membership_blocks_viewers_and_hides_unknown_cases (test_review.ProposalReviewContractTests.test_case_membership_blocks_viewers_and_hides_unknown_cases) ... ok
test_docx_source_text_reports_unavailable_physical_page (test_review.ProposalReviewContractTests.test_docx_source_text_reports_unavailable_physical_page) ... ok
test_edit_decision_requires_a_nonempty_bounded_value (test_review.ProposalReviewContractTests.test_edit_decision_requires_a_nonempty_bounded_value) ... ok
test_fact_disposition_requires_confirmation_and_profile_revision (test_review.ProposalReviewContractTests.test_fact_disposition_requires_confirmation_and_profile_revision) ... ok
test_non_edit_decisions_cannot_supply_a_replacement_value (test_review.ProposalReviewContractTests.test_non_edit_decisions_cannot_supply_a_replacement_value) ... ok
test_review_cannot_accept_a_missing_or_changed_source (test_review.ProposalReviewContractTests.test_review_cannot_accept_a_missing_or_changed_source) ... ok
test_review_decision_is_append_only_and_does_not_adopt_a_fact (test_review.ProposalReviewContractTests.test_review_decision_is_append_only_and_does_not_adopt_a_fact) ... ok
test_same_field_facts_are_both_preserved_and_marked_as_conflicts (test_review.ProposalReviewContractTests.test_same_field_facts_are_both_preserved_and_marked_as_conflicts) ... ok
test_stale_profile_revision_does_not_partially_adopt (test_review.ProposalReviewContractTests.test_stale_profile_revision_does_not_partially_adopt) ... ok
test_withdrawal_retry_returns_the_existing_event (test_review.ProposalReviewContractTests.test_withdrawal_retry_returns_the_existing_event) ... ok

----------------------------------------------------------------------
Ran 13 tests in 0.035s

OK
```

## Prompt - 2026-10-31T16:28:32Z

### Exact user prompt

````text
implement the latest spec
````

### Execution - 2026-10-31T16:28:32Z

- Invocation: `INTERACTION_CAPTURE=1 INTERACTION_LOG=interactions/09-ai-suggestion-review/response-09-ai-suggestion-review.md bash harness/validate.sh`
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
test_downgrade_removes_tables_before_profile_revision (test_0006_proposal_review_and_adoption.ProposalReviewMigrationTests.test_downgrade_removes_tables_before_profile_revision) ... ok
test_upgrade_adds_profile_revision_and_review_adoption_tables (test_0006_proposal_review_and_adoption.ProposalReviewMigrationTests.test_upgrade_adds_profile_revision_and_review_adoption_tables) ... ok
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
  File "/app/src/app/main.py", line 334, in dashboard_status
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
  File "/app/src/app/main.py", line 663, in delete_document
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
test_pdf_preview_is_inline_and_not_cacheable (test_main.MainWorkflowTests.test_pdf_preview_is_inline_and_not_cacheable) ... ok
test_root_displays_mode_choices_and_authentication_gate (test_main.MainWorkflowTests.test_root_displays_mode_choices_and_authentication_gate) ... ok
test_cleanup_failure_logs_no_object_key (test_materials.MaterialsImportTests.test_cleanup_failure_logs_no_object_key) ... ok
test_config_reports_runtime_upload_limit_and_unconfigured_providers (test_materials.MaterialsImportTests.test_config_reports_runtime_upload_limit_and_unconfigured_providers) ... [INFO] HTTP Request: GET http://testserver/api/v1/materials/config "HTTP/1.1 200 OK"
ok
test_database_failure_cleans_up_the_uploaded_object (test_materials.MaterialsImportTests.test_database_failure_cleans_up_the_uploaded_object) ... [ERROR] Material import database transaction failed (SQLAlchemyError).
[INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/d82f8be5-0a76-4752-8c6f-de2e83172b33/files/29b4bcdb-f045-4cdc-9dbf-61b7ddfdf02d "HTTP/1.1 503 Service Unavailable"
ok
test_import_fails_closed_when_case_data_is_disabled (test_materials.MaterialsImportTests.test_import_fails_closed_when_case_data_is_disabled) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/d4e2128e-4773-4fb2-80d5-0e52886ce73d/files/1ae7d061-b656-4dc7-812a-4571cbb718c0 "HTTP/1.1 503 Service Unavailable"
ok
test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/27bf3630-0455-40c4-9608-096d3bb683c5/files/70b71dcf-f1a3-491d-a2ab-e9069aaf5fd7 "HTTP/1.1 415 Unsupported Media Type"
ok
test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/0cfbf62d-aa78-4753-900a-0c957c87cd56/files/12107161-853a-4f00-97cc-19ec634cd92f "HTTP/1.1 201 Created"
ok
test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/18f7f6d6-66e6-460a-9c12-ddf944e2da78/files/ab1073ab-d9e8-4f0c-8710-8ee6c01c361e "HTTP/1.1 201 Created"
ok
test_analysis_jobs_and_proposals_keep_source_provenance (test_models.AuthenticationModelTests.test_analysis_jobs_and_proposals_keep_source_provenance) ... ok
test_authentication_tables_are_registered (test_models.AuthenticationModelTests.test_authentication_tables_are_registered) ... ok
test_case_profile_facts_are_append_only_and_keep_source_provenance (test_models.AuthenticationModelTests.test_case_profile_facts_are_append_only_and_keep_source_provenance) ... ok
test_provider_and_case_access_constraints_are_explicit (test_models.AuthenticationModelTests.test_provider_and_case_access_constraints_are_explicit) ... ok
test_compose_demo_login_is_explicit_and_case_data_remains_disabled (test_project_configuration.ProjectConfigurationTests.test_compose_demo_login_is_explicit_and_case_data_remains_disabled) ... ok
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
test_package_includes_the_landing_page_asset (test_project_configuration.ProjectConfigurationTests.test_package_includes_the_landing_page_asset) ... ok
test_project_declares_specified_stack (test_project_configuration.ProjectConfigurationTests.test_project_declares_specified_stack) ... ok
test_adoption_requires_explicit_confirmation_and_unique_proposals (test_review.ProposalReviewContractTests.test_adoption_requires_explicit_confirmation_and_unique_proposals) ... ok
test_adoption_retry_returns_the_existing_outcome (test_review.ProposalReviewContractTests.test_adoption_retry_returns_the_existing_outcome) ... ok
test_adoption_uses_reviewed_value_and_keeps_json_profile_unchanged (test_review.ProposalReviewContractTests.test_adoption_uses_reviewed_value_and_keeps_json_profile_unchanged) ... ok
test_case_membership_blocks_viewers_and_hides_unknown_cases (test_review.ProposalReviewContractTests.test_case_membership_blocks_viewers_and_hides_unknown_cases) ... ok
test_docx_source_text_reports_unavailable_physical_page (test_review.ProposalReviewContractTests.test_docx_source_text_reports_unavailable_physical_page) ... ok
test_edit_decision_requires_a_nonempty_bounded_value (test_review.ProposalReviewContractTests.test_edit_decision_requires_a_nonempty_bounded_value) ... ok
test_fact_disposition_requires_confirmation_and_profile_revision (test_review.ProposalReviewContractTests.test_fact_disposition_requires_confirmation_and_profile_revision) ... ok
test_non_edit_decisions_cannot_supply_a_replacement_value (test_review.ProposalReviewContractTests.test_non_edit_decisions_cannot_supply_a_replacement_value) ... ok
test_review_cannot_accept_a_missing_or_changed_source (test_review.ProposalReviewContractTests.test_review_cannot_accept_a_missing_or_changed_source) ... ok
test_review_decision_is_append_only_and_does_not_adopt_a_fact (test_review.ProposalReviewContractTests.test_review_decision_is_append_only_and_does_not_adopt_a_fact) ... ok
test_same_field_facts_are_both_preserved_and_marked_as_conflicts (test_review.ProposalReviewContractTests.test_same_field_facts_are_both_preserved_and_marked_as_conflicts) ... ok
test_stale_profile_revision_does_not_partially_adopt (test_review.ProposalReviewContractTests.test_stale_profile_revision_does_not_partially_adopt) ... ok
test_withdrawal_retry_returns_the_existing_event (test_review.ProposalReviewContractTests.test_withdrawal_retry_returns_the_existing_event) ... ok
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
Ran 143 tests in 1.031s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
```

## Prompt - 2026-10-31T16:30:39Z

### Exact user prompt

````text
implement the latest spec
````

### Execution - 2026-10-31T16:30:39Z

- Invocation: `INTERACTION_CAPTURE=1 INTERACTION_LOG=interactions/09-ai-suggestion-review/response-09-ai-suggestion-review.md bash harness/validate.sh`
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
test_downgrade_removes_tables_before_profile_revision (test_0006_proposal_review_and_adoption.ProposalReviewMigrationTests.test_downgrade_removes_tables_before_profile_revision) ... ok
test_upgrade_adds_profile_revision_and_review_adoption_tables (test_0006_proposal_review_and_adoption.ProposalReviewMigrationTests.test_upgrade_adds_profile_revision_and_review_adoption_tables) ... ok
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
  File "/app/src/app/main.py", line 334, in dashboard_status
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
  File "/app/src/app/main.py", line 663, in delete_document
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
test_pdf_preview_is_inline_and_not_cacheable (test_main.MainWorkflowTests.test_pdf_preview_is_inline_and_not_cacheable) ... ok
test_root_displays_mode_choices_and_authentication_gate (test_main.MainWorkflowTests.test_root_displays_mode_choices_and_authentication_gate) ... ok
test_cleanup_failure_logs_no_object_key (test_materials.MaterialsImportTests.test_cleanup_failure_logs_no_object_key) ... ok
test_config_reports_runtime_upload_limit_and_unconfigured_providers (test_materials.MaterialsImportTests.test_config_reports_runtime_upload_limit_and_unconfigured_providers) ... [INFO] HTTP Request: GET http://testserver/api/v1/materials/config "HTTP/1.1 200 OK"
ok
test_database_failure_cleans_up_the_uploaded_object (test_materials.MaterialsImportTests.test_database_failure_cleans_up_the_uploaded_object) ... [ERROR] Material import database transaction failed (SQLAlchemyError).
[INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/591a6d9a-fba7-421e-a07b-61ff93e713bc/files/536b1fce-804a-4707-b9f9-713802a3b1d0 "HTTP/1.1 503 Service Unavailable"
ok
test_import_fails_closed_when_case_data_is_disabled (test_materials.MaterialsImportTests.test_import_fails_closed_when_case_data_is_disabled) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/2f568b64-f68c-4b1e-9c1a-b13fbb62220c/files/69e4df9d-5a77-4746-9810-6a1111aa4106 "HTTP/1.1 503 Service Unavailable"
ok
test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/2b76b1ca-15f5-4468-a141-b18521007be9/files/946533ac-8af1-4b03-8470-d3e97ef90cdc "HTTP/1.1 415 Unsupported Media Type"
ok
test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/baa143a5-49ae-4fed-84de-e92cacb6fbe3/files/7a4df5b7-a0e4-49b0-8166-bf12105b6d8a "HTTP/1.1 201 Created"
ok
test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/82c6f7d1-4af1-4b03-93a6-b8efe7a52757/files/198d31a3-842a-4ce4-a267-eea162386a00 "HTTP/1.1 201 Created"
ok
test_analysis_jobs_and_proposals_keep_source_provenance (test_models.AuthenticationModelTests.test_analysis_jobs_and_proposals_keep_source_provenance) ... ok
test_authentication_tables_are_registered (test_models.AuthenticationModelTests.test_authentication_tables_are_registered) ... ok
test_case_profile_facts_are_append_only_and_keep_source_provenance (test_models.AuthenticationModelTests.test_case_profile_facts_are_append_only_and_keep_source_provenance) ... ok
test_provider_and_case_access_constraints_are_explicit (test_models.AuthenticationModelTests.test_provider_and_case_access_constraints_are_explicit) ... ok
test_compose_demo_login_is_explicit_and_case_data_remains_disabled (test_project_configuration.ProjectConfigurationTests.test_compose_demo_login_is_explicit_and_case_data_remains_disabled) ... ok
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
test_package_includes_the_landing_page_asset (test_project_configuration.ProjectConfigurationTests.test_package_includes_the_landing_page_asset) ... ok
test_project_declares_specified_stack (test_project_configuration.ProjectConfigurationTests.test_project_declares_specified_stack) ... ok
test_adoption_requires_explicit_confirmation_and_unique_proposals (test_review.ProposalReviewContractTests.test_adoption_requires_explicit_confirmation_and_unique_proposals) ... ok
test_adoption_retry_returns_the_existing_outcome (test_review.ProposalReviewContractTests.test_adoption_retry_returns_the_existing_outcome) ... ok
test_adoption_uses_reviewed_value_and_keeps_json_profile_unchanged (test_review.ProposalReviewContractTests.test_adoption_uses_reviewed_value_and_keeps_json_profile_unchanged) ... ok
test_case_membership_blocks_viewers_and_hides_unknown_cases (test_review.ProposalReviewContractTests.test_case_membership_blocks_viewers_and_hides_unknown_cases) ... ok
test_docx_source_text_reports_unavailable_physical_page (test_review.ProposalReviewContractTests.test_docx_source_text_reports_unavailable_physical_page) ... ok
test_edit_decision_requires_a_nonempty_bounded_value (test_review.ProposalReviewContractTests.test_edit_decision_requires_a_nonempty_bounded_value) ... ok
test_fact_disposition_requires_confirmation_and_profile_revision (test_review.ProposalReviewContractTests.test_fact_disposition_requires_confirmation_and_profile_revision) ... ok
test_non_edit_decisions_cannot_supply_a_replacement_value (test_review.ProposalReviewContractTests.test_non_edit_decisions_cannot_supply_a_replacement_value) ... ok
test_review_cannot_accept_a_missing_or_changed_source (test_review.ProposalReviewContractTests.test_review_cannot_accept_a_missing_or_changed_source) ... ok
test_review_decision_is_append_only_and_does_not_adopt_a_fact (test_review.ProposalReviewContractTests.test_review_decision_is_append_only_and_does_not_adopt_a_fact) ... ok
test_same_field_facts_are_both_preserved_and_marked_as_conflicts (test_review.ProposalReviewContractTests.test_same_field_facts_are_both_preserved_and_marked_as_conflicts) ... ok
test_stale_profile_revision_does_not_partially_adopt (test_review.ProposalReviewContractTests.test_stale_profile_revision_does_not_partially_adopt) ... ok
test_withdrawal_retry_returns_the_existing_event (test_review.ProposalReviewContractTests.test_withdrawal_retry_returns_the_existing_event) ... ok
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
Ran 143 tests in 1.137s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
```

## Prompt - 2026-10-31T16:32:24Z

### Exact user prompt

````text
implement the latest spec
````

### Execution - 2026-10-31T16:32:24Z

- Invocation: `INTERACTION_CAPTURE=1 INTERACTION_LOG=interactions/09-ai-suggestion-review/response-09-ai-suggestion-review.md bash harness/validate.sh`
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
test_downgrade_removes_tables_before_profile_revision (test_0006_proposal_review_and_adoption.ProposalReviewMigrationTests.test_downgrade_removes_tables_before_profile_revision) ... ok
test_upgrade_adds_profile_revision_and_review_adoption_tables (test_0006_proposal_review_and_adoption.ProposalReviewMigrationTests.test_upgrade_adds_profile_revision_and_review_adoption_tables) ... ok
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
  File "/app/src/app/main.py", line 334, in dashboard_status
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
  File "/app/src/app/main.py", line 663, in delete_document
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
test_pdf_preview_is_inline_and_not_cacheable (test_main.MainWorkflowTests.test_pdf_preview_is_inline_and_not_cacheable) ... ok
test_root_displays_mode_choices_and_authentication_gate (test_main.MainWorkflowTests.test_root_displays_mode_choices_and_authentication_gate) ... ok
test_cleanup_failure_logs_no_object_key (test_materials.MaterialsImportTests.test_cleanup_failure_logs_no_object_key) ... ok
test_config_reports_runtime_upload_limit_and_unconfigured_providers (test_materials.MaterialsImportTests.test_config_reports_runtime_upload_limit_and_unconfigured_providers) ... [INFO] HTTP Request: GET http://testserver/api/v1/materials/config "HTTP/1.1 200 OK"
ok
test_database_failure_cleans_up_the_uploaded_object (test_materials.MaterialsImportTests.test_database_failure_cleans_up_the_uploaded_object) ... [ERROR] Material import database transaction failed (SQLAlchemyError).
[INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/77eb9bb5-c727-4c93-8668-0fdf9a955b1a/files/67ef0cca-0168-406e-aed2-89040e4d5560 "HTTP/1.1 503 Service Unavailable"
ok
test_import_fails_closed_when_case_data_is_disabled (test_materials.MaterialsImportTests.test_import_fails_closed_when_case_data_is_disabled) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/b3b6727e-ca2a-46bc-87e0-cc825fe42f2e/files/227334ad-5c04-4258-bbfc-deb065d0d33e "HTTP/1.1 503 Service Unavailable"
ok
test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/0d7f5a40-bc88-415e-8168-8f44d4a9f7f0/files/2b1a0c7f-cd4d-4ee5-8860-8d0c0be86c30 "HTTP/1.1 415 Unsupported Media Type"
ok
test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/506d3dc0-c5a6-4c74-b65d-45279ad5b57d/files/024a8d5c-759c-41e1-9709-d37d283e0616 "HTTP/1.1 201 Created"
ok
test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/b6fc0baf-b80c-4784-8abe-d77fbf6c6d20/files/4366dd47-3cdc-412b-b004-dc3727999781 "HTTP/1.1 201 Created"
ok
test_analysis_jobs_and_proposals_keep_source_provenance (test_models.AuthenticationModelTests.test_analysis_jobs_and_proposals_keep_source_provenance) ... ok
test_authentication_tables_are_registered (test_models.AuthenticationModelTests.test_authentication_tables_are_registered) ... ok
test_case_profile_facts_are_append_only_and_keep_source_provenance (test_models.AuthenticationModelTests.test_case_profile_facts_are_append_only_and_keep_source_provenance) ... ok
test_provider_and_case_access_constraints_are_explicit (test_models.AuthenticationModelTests.test_provider_and_case_access_constraints_are_explicit) ... ok
test_compose_demo_login_is_explicit_and_case_data_remains_disabled (test_project_configuration.ProjectConfigurationTests.test_compose_demo_login_is_explicit_and_case_data_remains_disabled) ... ok
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
test_package_includes_the_landing_page_asset (test_project_configuration.ProjectConfigurationTests.test_package_includes_the_landing_page_asset) ... ok
test_project_declares_specified_stack (test_project_configuration.ProjectConfigurationTests.test_project_declares_specified_stack) ... ok
test_adoption_requires_explicit_confirmation_and_unique_proposals (test_review.ProposalReviewContractTests.test_adoption_requires_explicit_confirmation_and_unique_proposals) ... ok
test_adoption_retry_returns_the_existing_outcome (test_review.ProposalReviewContractTests.test_adoption_retry_returns_the_existing_outcome) ... ok
test_adoption_uses_reviewed_value_and_keeps_json_profile_unchanged (test_review.ProposalReviewContractTests.test_adoption_uses_reviewed_value_and_keeps_json_profile_unchanged) ... ok
test_case_membership_blocks_viewers_and_hides_unknown_cases (test_review.ProposalReviewContractTests.test_case_membership_blocks_viewers_and_hides_unknown_cases) ... ok
test_docx_source_text_reports_unavailable_physical_page (test_review.ProposalReviewContractTests.test_docx_source_text_reports_unavailable_physical_page) ... ok
test_edit_decision_requires_a_nonempty_bounded_value (test_review.ProposalReviewContractTests.test_edit_decision_requires_a_nonempty_bounded_value) ... ok
test_fact_disposition_requires_confirmation_and_profile_revision (test_review.ProposalReviewContractTests.test_fact_disposition_requires_confirmation_and_profile_revision) ... ok
test_non_edit_decisions_cannot_supply_a_replacement_value (test_review.ProposalReviewContractTests.test_non_edit_decisions_cannot_supply_a_replacement_value) ... ok
test_review_cannot_accept_a_missing_or_changed_source (test_review.ProposalReviewContractTests.test_review_cannot_accept_a_missing_or_changed_source) ... ok
test_review_decision_is_append_only_and_does_not_adopt_a_fact (test_review.ProposalReviewContractTests.test_review_decision_is_append_only_and_does_not_adopt_a_fact) ... ok
test_same_field_facts_are_both_preserved_and_marked_as_conflicts (test_review.ProposalReviewContractTests.test_same_field_facts_are_both_preserved_and_marked_as_conflicts) ... ok
test_stale_profile_revision_does_not_partially_adopt (test_review.ProposalReviewContractTests.test_stale_profile_revision_does_not_partially_adopt) ... ok
test_withdrawal_retry_returns_the_existing_event (test_review.ProposalReviewContractTests.test_withdrawal_retry_returns_the_existing_event) ... ok
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
Ran 143 tests in 1.231s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
```

## Final verification - 2026-10-31

- Full validation harness: passed; 143 tests passed.
- Embedded JavaScript syntax check (`node --check`, Node v24.22.1): passed.
- `docker compose config -q`: passed.
- Offline migration generation (`alembic upgrade --sql head`): passed through revision `0006_proposal_review_and_adoption`; no database migration was applied.
- `docker compose build api extraction-worker analysis-worker`: passed for all three images.
- `git diff --check`: passed.

## Commit and PR outcome - 2026-10-31

- Spec commit: `98a6517b099fdfc26e488bba0e464412970b4986`.
- Implementation commit: `d9ae1da` (`Implement AI suggestion review and adoption`); the commit hook reran the full suite and all 143 tests passed.
- Pushed `feature/ai-suggestion-review`.
- Created [PR #37](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/pull/37) against `feature/consent-based-document-analysis`; the description ends with `Resolves #33`.
- Attempted self-approval once; GitHub rejected it because authors cannot approve their own pull requests.
- PR remains open; GitHub reports no review requests and an empty review decision, so no external review is currently required.


## Prompt - 2026-10-31T02:26:02Z

### Exact user prompt

````text
Implement the latest specification
````

### Execution - 2026-10-31T02:26:02Z

- Invocation: `INTERACTION_CAPTURE=1 INTERACTION_LOG=interactions/05-case-materials-import/response-05-case-materials-import.md bash harness/validate.sh -- python3 -m unittest discover -s tests -p test_materials.py -v`
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
test_rejects_unverifiable_source_quotes (test_ai.BedrockExtractionTests.test_rejects_unverifiable_source_quotes) ... ok
test_requires_a_configured_model (test_ai.BedrockExtractionTests.test_requires_a_configured_model) ... ok
test_returns_only_fields_with_verifiable_source_quotes (test_ai.BedrockExtractionTests.test_returns_only_fields_with_verifiable_source_quotes) ... ok
test_surfaces_invalid_model_output (test_ai.BedrockExtractionTests.test_surfaces_invalid_model_output) ... [WARNING] Bedrock returned non-JSON case extraction output.
ok
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
test_demo_mode_is_local_only_and_cannot_enable_case_data (test_config.SettingsTests.test_demo_mode_is_local_only_and_cannot_enable_case_data) ... ok
test_non_local_auth_origins_require_https (test_config.SettingsTests.test_non_local_auth_origins_require_https) ... ok
test_samesite_none_requires_secure_cookies (test_config.SettingsTests.test_samesite_none_requires_secure_cookies) ... ok
test_status_reports_database_failure_as_retryable_service_error (test_dashboard.DashboardStatusTests.test_status_reports_database_failure_as_retryable_service_error) ... [ERROR] Dashboard case-status lookup failed.
Traceback (most recent call last):
  File "/workspace/src/app/main.py", line 313, in dashboard_status
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
test_case_data_endpoints_fail_closed_until_authentication_is_configured (test_main.MainWorkflowTests.test_case_data_endpoints_fail_closed_until_authentication_is_configured) ... ok
test_onboarding_paths_serve_the_authenticated_preview_page (test_main.MainWorkflowTests.test_onboarding_paths_serve_the_authenticated_preview_page) ... ok
test_root_displays_mode_choices_and_authentication_gate (test_main.MainWorkflowTests.test_root_displays_mode_choices_and_authentication_gate) ... ok
test_config_reports_runtime_upload_limit_and_unconfigured_providers (test_materials.MaterialsImportTests.test_config_reports_runtime_upload_limit_and_unconfigured_providers) ... [INFO] HTTP Request: GET http://testserver/api/v1/materials/config "HTTP/1.1 200 OK"
ok
test_database_failure_cleans_up_the_uploaded_object (test_materials.MaterialsImportTests.test_database_failure_cleans_up_the_uploaded_object) ... ERROR
test_import_fails_closed_when_case_data_is_disabled (test_materials.MaterialsImportTests.test_import_fails_closed_when_case_data_is_disabled) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/b5acf1a1-7b3c-46e3-abbb-5a68bf77333b/files/18580a6c-7d71-46bc-b794-6bd9dd24edbb "HTTP/1.1 503 Service Unavailable"
ok
test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case) ... ERROR
test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again) ... ERROR
test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file) ... ERROR
test_authentication_tables_are_registered (test_models.AuthenticationModelTests.test_authentication_tables_are_registered) ... ok
test_provider_and_case_access_constraints_are_explicit (test_models.AuthenticationModelTests.test_provider_and_case_access_constraints_are_explicit) ... ok
test_compose_demo_login_is_explicit_and_case_data_remains_disabled (test_project_configuration.ProjectConfigurationTests.test_compose_demo_login_is_explicit_and_case_data_remains_disabled) ... ok
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
test_package_includes_the_landing_page_asset (test_project_configuration.ProjectConfigurationTests.test_package_includes_the_landing_page_asset) ... ok
test_project_declares_specified_stack (test_project_configuration.ProjectConfigurationTests.test_project_declares_specified_stack) ... ok
test_accepts_docx_container_with_required_parts (test_upload_validation.UploadValidationTests.test_accepts_docx_container_with_required_parts) ... ok
test_accepts_pdf_header_with_leading_bytes (test_upload_validation.UploadValidationTests.test_accepts_pdf_header_with_leading_bytes) ... ok
test_accepts_pdf_signature (test_upload_validation.UploadValidationTests.test_accepts_pdf_signature) ... ok
test_rejects_empty_file (test_upload_validation.UploadValidationTests.test_rejects_empty_file) ... ok
test_rejects_malformed_docx (test_upload_validation.UploadValidationTests.test_rejects_malformed_docx) ... ok
test_rejects_mismatched_extension (test_upload_validation.UploadValidationTests.test_rejects_mismatched_extension) ... ok
test_rejects_oversized_file (test_upload_validation.UploadValidationTests.test_rejects_oversized_file) ... ok
test_rejects_unknown_document_type (test_upload_validation.UploadValidationTests.test_rejects_unknown_document_type) ... ok
test_rejects_zip_missing_word_document (test_upload_validation.UploadValidationTests.test_rejects_zip_missing_word_document) ... ok

======================================================================
ERROR: test_database_failure_cleans_up_the_uploaded_object (test_materials.MaterialsImportTests.test_database_failure_cleans_up_the_uploaded_object)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/tests/test_materials.py", line 160, in test_database_failure_cleans_up_the_uploaded_object
    settings = Settings(
               ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, Demo mode cannot enable case-data APIs. [type=value_error, input_value={'database_url': 'postgre...ing-secret-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/tests/test_materials.py", line 68, in test_import_validates_file_before_creating_a_case
    settings = Settings(
               ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, Demo mode cannot enable case-data APIs. [type=value_error, input_value={'database_url': 'postgre...ing-secret-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/tests/test_materials.py", line 139, in test_retry_returns_existing_document_without_uploading_again
    settings = Settings(
               ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, Demo mode cannot enable case-data APIs. [type=value_error, input_value={'database_url': 'postgre...ing-secret-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

======================================================================
ERROR: test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/tests/test_materials.py", line 87, in test_successful_import_creates_one_owned_draft_and_stores_the_file
    settings = Settings(
               ^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/pydantic_settings/main.py", line 292, in __init__
    super().__init__(**__pydantic_self__.__class__._settings_build_values(sources, init_kwargs))
  File "/usr/local/lib/python3.12/site-packages/pydantic/main.py", line 280, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
  Value error, Demo mode cannot enable case-data APIs. [type=value_error, input_value={'database_url': 'postgre...ing-secret-long-enough'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.14/v/value_error

----------------------------------------------------------------------
Ran 67 tests in 0.670s

FAILED (errors=4)
FAIL: Python unit tests failed.
Validation failed with 1 missing requirement(s).
```

## Prompt - 2026-10-31T02:26:30Z

### Exact user prompt

````text
Implement the latest specification
````

### Execution - 2026-10-31T02:26:30Z

- Invocation: `INTERACTION_CAPTURE=1 INTERACTION_LOG=interactions/05-case-materials-import/response-05-case-materials-import.md bash harness/validate.sh -- python3 -m unittest discover -s tests -p test_materials.py -v`
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
test_rejects_unverifiable_source_quotes (test_ai.BedrockExtractionTests.test_rejects_unverifiable_source_quotes) ... ok
test_requires_a_configured_model (test_ai.BedrockExtractionTests.test_requires_a_configured_model) ... ok
test_returns_only_fields_with_verifiable_source_quotes (test_ai.BedrockExtractionTests.test_returns_only_fields_with_verifiable_source_quotes) ... ok
test_surfaces_invalid_model_output (test_ai.BedrockExtractionTests.test_surfaces_invalid_model_output) ... [WARNING] Bedrock returned non-JSON case extraction output.
ok
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
test_demo_mode_is_local_only_and_cannot_enable_case_data (test_config.SettingsTests.test_demo_mode_is_local_only_and_cannot_enable_case_data) ... ok
test_non_local_auth_origins_require_https (test_config.SettingsTests.test_non_local_auth_origins_require_https) ... ok
test_samesite_none_requires_secure_cookies (test_config.SettingsTests.test_samesite_none_requires_secure_cookies) ... ok
test_status_reports_database_failure_as_retryable_service_error (test_dashboard.DashboardStatusTests.test_status_reports_database_failure_as_retryable_service_error) ... [ERROR] Dashboard case-status lookup failed.
Traceback (most recent call last):
  File "/workspace/src/app/main.py", line 313, in dashboard_status
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
test_case_data_endpoints_fail_closed_until_authentication_is_configured (test_main.MainWorkflowTests.test_case_data_endpoints_fail_closed_until_authentication_is_configured) ... ok
test_onboarding_paths_serve_the_authenticated_preview_page (test_main.MainWorkflowTests.test_onboarding_paths_serve_the_authenticated_preview_page) ... ok
test_root_displays_mode_choices_and_authentication_gate (test_main.MainWorkflowTests.test_root_displays_mode_choices_and_authentication_gate) ... ok
test_config_reports_runtime_upload_limit_and_unconfigured_providers (test_materials.MaterialsImportTests.test_config_reports_runtime_upload_limit_and_unconfigured_providers) ... [INFO] HTTP Request: GET http://testserver/api/v1/materials/config "HTTP/1.1 200 OK"
ok
test_database_failure_cleans_up_the_uploaded_object (test_materials.MaterialsImportTests.test_database_failure_cleans_up_the_uploaded_object) ... [ERROR] Material import database transaction failed.
Traceback (most recent call last):
  File "/workspace/src/app/materials.py", line 216, in import_material_file
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
[INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/1b3832ee-3824-490b-84ec-230744622d78/files/fa8d226d-1108-44f3-bbaf-b5014d1ceb88 "HTTP/1.1 503 Service Unavailable"
ok
test_import_fails_closed_when_case_data_is_disabled (test_materials.MaterialsImportTests.test_import_fails_closed_when_case_data_is_disabled) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/2b409671-ec6d-4f6d-bed8-fa10adab7afe/files/fa54ded7-c42b-47af-9658-b7eda4c42363 "HTTP/1.1 503 Service Unavailable"
ok
test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/cb3281f8-32d7-4435-912a-0e849fd778e3/files/3c133eba-8412-482d-b061-c4342a9e17a9 "HTTP/1.1 415 Unsupported Media Type"
ok
test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/64f3de2b-de4d-4824-9a5b-85d3ea50dd2d/files/8677c203-2f9e-46ec-87c0-a630594bf11d "HTTP/1.1 201 Created"
ok
test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/247f7db8-1548-48ae-a7be-13ce2201ca5f/files/6b571da3-cdfd-470a-ad6f-0d8df9aa1e66 "HTTP/1.1 201 Created"
ok
test_authentication_tables_are_registered (test_models.AuthenticationModelTests.test_authentication_tables_are_registered) ... ok
test_provider_and_case_access_constraints_are_explicit (test_models.AuthenticationModelTests.test_provider_and_case_access_constraints_are_explicit) ... ok
test_compose_demo_login_is_explicit_and_case_data_remains_disabled (test_project_configuration.ProjectConfigurationTests.test_compose_demo_login_is_explicit_and_case_data_remains_disabled) ... ok
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
test_package_includes_the_landing_page_asset (test_project_configuration.ProjectConfigurationTests.test_package_includes_the_landing_page_asset) ... ok
test_project_declares_specified_stack (test_project_configuration.ProjectConfigurationTests.test_project_declares_specified_stack) ... ok
test_accepts_docx_container_with_required_parts (test_upload_validation.UploadValidationTests.test_accepts_docx_container_with_required_parts) ... ok
test_accepts_pdf_header_with_leading_bytes (test_upload_validation.UploadValidationTests.test_accepts_pdf_header_with_leading_bytes) ... ok
test_accepts_pdf_signature (test_upload_validation.UploadValidationTests.test_accepts_pdf_signature) ... ok
test_rejects_empty_file (test_upload_validation.UploadValidationTests.test_rejects_empty_file) ... ok
test_rejects_malformed_docx (test_upload_validation.UploadValidationTests.test_rejects_malformed_docx) ... ok
test_rejects_mismatched_extension (test_upload_validation.UploadValidationTests.test_rejects_mismatched_extension) ... ok
test_rejects_oversized_file (test_upload_validation.UploadValidationTests.test_rejects_oversized_file) ... ok
test_rejects_unknown_document_type (test_upload_validation.UploadValidationTests.test_rejects_unknown_document_type) ... ok
test_rejects_zip_missing_word_document (test_upload_validation.UploadValidationTests.test_rejects_zip_missing_word_document) ... ok

----------------------------------------------------------------------
Ran 67 tests in 0.687s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
/usr/local/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  from starlette.testclient import TestClient as TestClient  # noqa
warning: The `fitz` API is deprecated and will be removed in future. Use `import pymupdf` instead.
test_config_reports_runtime_upload_limit_and_unconfigured_providers (test_materials.MaterialsImportTests.test_config_reports_runtime_upload_limit_and_unconfigured_providers) ... [INFO] HTTP Request: GET http://testserver/api/v1/materials/config "HTTP/1.1 200 OK"
ok
test_database_failure_cleans_up_the_uploaded_object (test_materials.MaterialsImportTests.test_database_failure_cleans_up_the_uploaded_object) ... [ERROR] Material import database transaction failed.
Traceback (most recent call last):
  File "/workspace/src/app/materials.py", line 216, in import_material_file
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
[INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/7b29f05f-5ff0-40d1-82c5-cf01d905016c/files/b6d8ec4d-dbe9-47c9-b118-360e422d09d3 "HTTP/1.1 503 Service Unavailable"
ok
test_import_fails_closed_when_case_data_is_disabled (test_materials.MaterialsImportTests.test_import_fails_closed_when_case_data_is_disabled) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/168949b7-5d38-4fb8-aa07-590636cc740e/files/76fd2a33-171f-41a9-a51c-b1ce5ad2c741 "HTTP/1.1 503 Service Unavailable"
ok
test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/f9f044ad-bb36-4055-ae56-3024f6437309/files/1336d6b2-72e0-4284-9906-bd8f2a71396a "HTTP/1.1 415 Unsupported Media Type"
ok
test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/7210d003-bd81-46ee-9c78-b285207fb781/files/ad3bd165-c7de-4ac6-b6d7-0f59b4ac0fcf "HTTP/1.1 201 Created"
ok
test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/fb83ad61-14eb-4828-aebf-1075e8aafdbc/files/b09547df-5078-4f49-85d6-712c6e71f71d "HTTP/1.1 201 Created"
ok

----------------------------------------------------------------------
Ran 6 tests in 0.109s

OK
```

### Additional verification

- Embedded JavaScript passed `node --check`.
- Docker Compose rebuilt the API and applied Alembic revision `0003_material_imports`; `alembic current` reported `0003_material_imports (head)`.
- `GET /healthz` returned `{"status":"ok"}`. An unauthenticated `GET /api/v1/materials/config` returned `401`.
- The signed-in local preview rendered the materials page with the configured 20 MiB file limit, device selection, and disabled cloud-provider buttons.
- Google Drive and Dropbox remain unavailable until provider application registration, permissions, and token handling are configured.

### Final response

Implemented on `feature/case-materials-import-spec`: the materials page now supports selecting, locally validating, reviewing, removing, and retrying PDF/DOCX files; authenticated import endpoints create an owned draft case only after a valid file is confirmed and use persistent per-file idempotency. The local Compose demo still blocks uploads. Google Drive and Dropbox remain disabled pending provider configuration.

Validation passed: 67 repository tests, 6 focused materials tests, JavaScript syntax check, database migration, and live health/auth checks.

## Prompt - 2026-10-31T02:30:11Z

### Exact user prompt

````text
Implement the latest specification
````

### Execution - 2026-10-31T02:30:11Z

- Invocation: `INTERACTION_CAPTURE=1 INTERACTION_LOG=interactions/05-case-materials-import/response-05-case-materials-import.md bash harness/validate.sh -- python3 -m unittest discover -s tests -p test_materials.py -v`
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
test_rejects_unverifiable_source_quotes (test_ai.BedrockExtractionTests.test_rejects_unverifiable_source_quotes) ... ok
test_requires_a_configured_model (test_ai.BedrockExtractionTests.test_requires_a_configured_model) ... ok
test_returns_only_fields_with_verifiable_source_quotes (test_ai.BedrockExtractionTests.test_returns_only_fields_with_verifiable_source_quotes) ... ok
test_surfaces_invalid_model_output (test_ai.BedrockExtractionTests.test_surfaces_invalid_model_output) ... [WARNING] Bedrock returned non-JSON case extraction output.
ok
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
test_demo_mode_is_local_only_and_cannot_enable_case_data (test_config.SettingsTests.test_demo_mode_is_local_only_and_cannot_enable_case_data) ... ok
test_non_local_auth_origins_require_https (test_config.SettingsTests.test_non_local_auth_origins_require_https) ... ok
test_samesite_none_requires_secure_cookies (test_config.SettingsTests.test_samesite_none_requires_secure_cookies) ... ok
test_status_reports_database_failure_as_retryable_service_error (test_dashboard.DashboardStatusTests.test_status_reports_database_failure_as_retryable_service_error) ... [ERROR] Dashboard case-status lookup failed.
Traceback (most recent call last):
  File "/workspace/src/app/main.py", line 313, in dashboard_status
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
test_case_data_endpoints_fail_closed_until_authentication_is_configured (test_main.MainWorkflowTests.test_case_data_endpoints_fail_closed_until_authentication_is_configured) ... ok
test_onboarding_paths_serve_the_authenticated_preview_page (test_main.MainWorkflowTests.test_onboarding_paths_serve_the_authenticated_preview_page) ... ok
test_root_displays_mode_choices_and_authentication_gate (test_main.MainWorkflowTests.test_root_displays_mode_choices_and_authentication_gate) ... ok
test_config_reports_runtime_upload_limit_and_unconfigured_providers (test_materials.MaterialsImportTests.test_config_reports_runtime_upload_limit_and_unconfigured_providers) ... [INFO] HTTP Request: GET http://testserver/api/v1/materials/config "HTTP/1.1 200 OK"
ok
test_database_failure_cleans_up_the_uploaded_object (test_materials.MaterialsImportTests.test_database_failure_cleans_up_the_uploaded_object) ... [ERROR] Material import database transaction failed.
Traceback (most recent call last):
  File "/workspace/src/app/materials.py", line 216, in import_material_file
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
[INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/b3474523-0341-4d65-9d6c-e7eefca2aec9/files/ed1510c8-a26a-44df-bc3a-9b62abd3ca86 "HTTP/1.1 503 Service Unavailable"
ok
test_import_fails_closed_when_case_data_is_disabled (test_materials.MaterialsImportTests.test_import_fails_closed_when_case_data_is_disabled) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/938f5724-cad5-4816-a1c1-ea48e39f952d/files/69b14a88-7d8e-4c56-a44d-e891f947390d "HTTP/1.1 503 Service Unavailable"
ok
test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/3c39b9a1-9a88-433b-9298-66e49ab0c1cd/files/7e55244c-6852-4597-aefd-2094e010d9e6 "HTTP/1.1 415 Unsupported Media Type"
ok
test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/9300e3d5-839d-45b0-8a10-1def17275955/files/8e352dc0-a8ad-4d6c-a20c-41afdb8ab965 "HTTP/1.1 201 Created"
ok
test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/2171ed60-5b48-487a-af5e-04349f13a88d/files/f90a2ea4-c00b-4083-babf-c89b95bb7ced "HTTP/1.1 201 Created"
ok
test_authentication_tables_are_registered (test_models.AuthenticationModelTests.test_authentication_tables_are_registered) ... ok
test_provider_and_case_access_constraints_are_explicit (test_models.AuthenticationModelTests.test_provider_and_case_access_constraints_are_explicit) ... ok
test_compose_demo_login_is_explicit_and_case_data_remains_disabled (test_project_configuration.ProjectConfigurationTests.test_compose_demo_login_is_explicit_and_case_data_remains_disabled) ... ok
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
test_package_includes_the_landing_page_asset (test_project_configuration.ProjectConfigurationTests.test_package_includes_the_landing_page_asset) ... ok
test_project_declares_specified_stack (test_project_configuration.ProjectConfigurationTests.test_project_declares_specified_stack) ... ok
test_accepts_docx_container_with_required_parts (test_upload_validation.UploadValidationTests.test_accepts_docx_container_with_required_parts) ... ok
test_accepts_pdf_header_with_leading_bytes (test_upload_validation.UploadValidationTests.test_accepts_pdf_header_with_leading_bytes) ... ok
test_accepts_pdf_signature (test_upload_validation.UploadValidationTests.test_accepts_pdf_signature) ... ok
test_rejects_empty_file (test_upload_validation.UploadValidationTests.test_rejects_empty_file) ... ok
test_rejects_malformed_docx (test_upload_validation.UploadValidationTests.test_rejects_malformed_docx) ... ok
test_rejects_mismatched_extension (test_upload_validation.UploadValidationTests.test_rejects_mismatched_extension) ... ok
test_rejects_oversized_file (test_upload_validation.UploadValidationTests.test_rejects_oversized_file) ... ok
test_rejects_unknown_document_type (test_upload_validation.UploadValidationTests.test_rejects_unknown_document_type) ... ok
test_rejects_zip_missing_word_document (test_upload_validation.UploadValidationTests.test_rejects_zip_missing_word_document) ... ok

----------------------------------------------------------------------
Ran 67 tests in 0.679s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
/usr/local/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  from starlette.testclient import TestClient as TestClient  # noqa
warning: The `fitz` API is deprecated and will be removed in future. Use `import pymupdf` instead.
test_config_reports_runtime_upload_limit_and_unconfigured_providers (test_materials.MaterialsImportTests.test_config_reports_runtime_upload_limit_and_unconfigured_providers) ... [INFO] HTTP Request: GET http://testserver/api/v1/materials/config "HTTP/1.1 200 OK"
ok
test_database_failure_cleans_up_the_uploaded_object (test_materials.MaterialsImportTests.test_database_failure_cleans_up_the_uploaded_object) ... [ERROR] Material import database transaction failed.
Traceback (most recent call last):
  File "/workspace/src/app/materials.py", line 216, in import_material_file
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
[INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/20d566e7-0a7b-4e09-9373-21bac968377f/files/9c6fada7-b6c0-4780-8e70-b791b01735dc "HTTP/1.1 503 Service Unavailable"
ok
test_import_fails_closed_when_case_data_is_disabled (test_materials.MaterialsImportTests.test_import_fails_closed_when_case_data_is_disabled) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/675585f5-e34e-4ea0-8a8a-3b6fe9a8a817/files/d7e1243c-562c-4a94-8e75-eb32c165b471 "HTTP/1.1 503 Service Unavailable"
ok
test_import_validates_file_before_creating_a_case (test_materials.MaterialsImportTests.test_import_validates_file_before_creating_a_case) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/1497342c-75b0-4ee4-a58c-27bed85e3944/files/0bbdcb40-b248-43f3-8df6-6e3e694df32b "HTTP/1.1 415 Unsupported Media Type"
ok
test_retry_returns_existing_document_without_uploading_again (test_materials.MaterialsImportTests.test_retry_returns_existing_document_without_uploading_again) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/af3062f9-d8c0-4558-80d6-54c4be9962c6/files/dee75a2b-9924-40c5-94fe-76ad020be8ca "HTTP/1.1 201 Created"
ok
test_successful_import_creates_one_owned_draft_and_stores_the_file (test_materials.MaterialsImportTests.test_successful_import_creates_one_owned_draft_and_stores_the_file) ... [INFO] HTTP Request: POST http://testserver/api/v1/materials/imports/62550d45-a63d-4e88-8043-5488a57d293a/files/baa36ddc-bbf0-4cda-ac21-05f511f3e725 "HTTP/1.1 201 Created"
ok

----------------------------------------------------------------------
Ran 6 tests in 0.109s

OK
```


## Prompt - 2026-10-30T18:07:30Z

### Exact user prompt

````text
go and implement the latest spec
````

### Execution - 2026-10-30T18:07:30Z

- Invocation: `INTERACTION_CAPTURE=1 INTERACTION_LOG=interactions/04-initial-onboarding-empty-state/response-04-initial-onboarding-empty-state.md bash harness/validate.sh`
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
  File "/workspace/src/app/main.py", line 311, in dashboard_status
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
Ran 60 tests in 0.777s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
```

## Supplemental verification

### Browser and live-service checks

- The rebuilt local app served `GET /` with HTTP 200; the unauthenticated dashboard status endpoint returned HTTP 401; `/onboarding/upload` returned HTTP 200.
- Signing in to the local demo showed both specified empty-account actions. The upload and wizard links opened their corresponding preview screens.
- Both preparation screens state that no case is created and no case data or documents are saved.
- A stubbed one-case dashboard response displayed the case ID prefix and `draft` status without showing case contents; returning to the live demo restored the empty state.
- A simulated dashboard HTTP 503 displayed an actionable error. Retrying recovered to the empty state.
- Inline JavaScript syntax validation passed. Editor diagnostics reported no errors in the changed Python files.

### Final assistant response

```text
Spec 04 implemented on `feature/empty-state-onboarding-implementation`. The authenticated dashboard and membership-filtered status API are live at http://localhost:8000. Both requested choices route to preview screens; uploads, case creation, and wizard data entry remain disabled, so no case information is accepted or stored.

The full harness passed (60 tests). Browser checks covered sign-in, both routes, existing-case display, and status-error retry. No commit was made.
```

## Prompt - 2026-10-30T18:12:12Z

### Exact user prompt

````text
go and implement the latest spec
````

### Execution - 2026-10-30T18:12:12Z

- Invocation: `INTERACTION_CAPTURE=1 INTERACTION_LOG=interactions/04-initial-onboarding-empty-state/response-04-initial-onboarding-empty-state.md bash harness/validate.sh`
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
  File "/workspace/src/app/main.py", line 311, in dashboard_status
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
Ran 60 tests in 0.811s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
```

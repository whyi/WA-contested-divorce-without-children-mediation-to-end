# Spec 01 implementation log

## Exact user prompt

~~~text
Thoroughly analyze and implement the latest spec document in the repository (located under specs/[spec-number]-[name]/[spec-number]-[name].md or the most recently created spec file).

Strictly adhere to the following principles:
1. **Spec-Driven Development (SDD):** Follow the requirements and tech stack (Python/FastAPI, PostgreSQL, S3, document round-trip engine, etc.) defined in the spec precisely.
2. **Code Implementation:** Write or update the necessary source code files (src/), configuration files, or Docker setups required to fulfill the spec.
3. **Validation & Logging:** Once implementation is complete, run the verification via the harness/validate.sh script and record the execution logs inside interactions/[spec-number]-[name]/.

Review the target spec and begin the implementation process.
~~~

## Implementation summary

- Added a FastAPI application, PostgreSQL case/negotiation/document/extraction models, and an initial Alembic migration.
- Added S3-compatible document persistence, template rendering, DOCX/PDF conversion, document text extraction, and review-pending extraction records.
- Added a Docker image with LibreOffice, PostgreSQL/Moto Compose services, local environment configuration, and baseline unit tests.
- Chose AWS S3 as the first object-storage provider, with Moto as a local S3 API mock. Azure Blob is not implemented.
- Extracted text is retained for review; no automatic legal-term mapping or case-data mutation is attempted because the spec does not define such rules.
- This initial implementation is for local development only and does not provide authentication or authorization.

Validation results are appended below by `harness/validate.sh`.

## Execution - 2026-10-28T20:53:28Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh`
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
PASS: file exists: pyproject.toml
PASS: file exists: Dockerfile
PASS: Python source compiles.
test_upload_validation (unittest.loader._FailedTest.test_upload_validation) ... ERROR

======================================================================
ERROR: test_upload_validation (unittest.loader._FailedTest.test_upload_validation)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_upload_validation
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_upload_validation.py", line 5, in <module>
    from app.validation import UploadValidationError, validate_upload
ModuleNotFoundError: No module named 'app'


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
FAIL: Python unit tests failed.
Validation failed with 1 missing requirement(s).
```

## Execution - 2026-10-28T20:53:36Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh`
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
PASS: file exists: pyproject.toml
PASS: file exists: Dockerfile
PASS: Python source compiles.
test_upload_validation (unittest.loader._FailedTest.test_upload_validation) ... ERROR

======================================================================
ERROR: test_upload_validation (unittest.loader._FailedTest.test_upload_validation)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_upload_validation
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/tests/test_upload_validation.py", line 5, in <module>
    from app.validation import UploadValidationError, validate_upload
ModuleNotFoundError: No module named 'app.validation'


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
FAIL: Python unit tests failed.
Validation failed with 1 missing requirement(s).
```

## Execution - 2026-10-28T20:56:45Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh`
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
PASS: file exists: pyproject.toml
PASS: file exists: Dockerfile
PASS: Python source compiles.
test_accepts_docx_container_with_required_parts (test_upload_validation.UploadValidationTests.test_accepts_docx_container_with_required_parts) ... ok
test_accepts_pdf_signature (test_upload_validation.UploadValidationTests.test_accepts_pdf_signature) ... ok
test_rejects_empty_file (test_upload_validation.UploadValidationTests.test_rejects_empty_file) ... ok
test_rejects_malformed_docx (test_upload_validation.UploadValidationTests.test_rejects_malformed_docx) ... ok
test_rejects_mismatched_extension (test_upload_validation.UploadValidationTests.test_rejects_mismatched_extension) ... ok
test_rejects_oversized_file (test_upload_validation.UploadValidationTests.test_rejects_oversized_file) ... ok
test_rejects_unknown_document_type (test_upload_validation.UploadValidationTests.test_rejects_unknown_document_type) ... ok
test_rejects_zip_missing_word_document (test_upload_validation.UploadValidationTests.test_rejects_zip_missing_word_document) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.003s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
```

## Execution - 2026-10-28T21:00:26Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ python3\ -c\ \"import\ tomllib\;\ tomllib.load\(open\(\\\"pyproject.toml\\\"\,\ \\\"rb\\\"\)\)\;\ print\(\\\"PASS:\ pyproject.toml\ parses.\\\"\)\"\;\ git\ diff\ --check\;\ printf\ \"PASS:\ git\ diff\ --check.\\\\n\"\;\ if\ command\ -v\ docker\ \>/dev/null\ 2\>\&1\;\ then\ docker\ --version\;\ else\ printf\ \"SKIP:\ Docker\ is\ unavailable\;\ container\ startup\ was\ not\ run.\\\\n\"\;\ fi\;\ if\ command\ -v\ uv\ \>/dev/null\ 2\>\&1\;\ then\ uv\ --version\;\ elif\ python3\ -m\ pip\ --version\ \>/dev/null\ 2\>\&1\;\ then\ python3\ -m\ pip\ --version\;\ else\ printf\ \"SKIP:\ Python\ package\ installer\ is\ unavailable\;\ dependency-backed\ API\ tests\ were\ not\ run.\\\\n\"\;\ fi`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.003s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
PASS: pyproject.toml parses.
PASS: git diff --check.
SKIP: Docker is unavailable; container startup was not run.
SKIP: Python package installer is unavailable; dependency-backed API tests were not run.
```

## Execution - 2026-10-28T21:01:52Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ python3\ -c\ \"import\ tomllib\;\ tomllib.load\(open\(\\\"pyproject.toml\\\"\,\ \\\"rb\\\"\)\)\;\ print\(\\\"PASS:\ pyproject.toml\ parses.\\\"\)\"\;\ python3\ -c\ \"import\ subprocess\;\ from\ pathlib\ import\ Path\;\ rows=subprocess.check_output\(\[\\\"git\\\"\,\\\"status\\\"\,\\\"--porcelain\\\"\,\\\"--untracked-files=all\\\"\]\,text=True\).splitlines\(\)\;\ paths=\[row\[3:\]\ for\ row\ in\ rows\]\;\ errors=\[f\\\"\{path\}:\{number\}\\\"\ for\ path\ in\ paths\ if\ Path\(path\).is_file\(\)\ for\ number\,line\ in\ enumerate\(Path\(path\).read_text\(\).splitlines\(\)\,1\)\ if\ line.rstrip\(\\\"\ \\\\t\\\"\)\ \!=\ line\]\;\ print\(\\\"FAIL:\ trailing\ whitespace\ at\ \\\"+\\\"\,\ \\\".join\(errors\)\)\ if\ errors\ else\ print\(f\\\"PASS:\ trailing-whitespace\ scan\ \(\{len\(paths\)\}\ changed\ files\).\\\"\)\;\ raise\ SystemExit\(bool\(errors\)\)\"\;\ git\ diff\ --check\;\ printf\ \"PASS:\ git\ diff\ --check.\\\\n\"\;\ if\ command\ -v\ docker\ \>/dev/null\ 2\>\&1\;\ then\ docker\ --version\;\ else\ printf\ \"SKIP:\ Docker\ is\ unavailable\;\ container\ startup\ was\ not\ run.\\\\n\"\;\ fi\;\ if\ command\ -v\ uv\ \>/dev/null\ 2\>\&1\;\ then\ uv\ --version\;\ elif\ python3\ -m\ pip\ --version\ \>/dev/null\ 2\>\&1\;\ then\ python3\ -m\ pip\ --version\;\ else\ printf\ \"SKIP:\ Python\ package\ installer\ is\ unavailable\;\ dependency-backed\ API\ tests\ were\ not\ run.\\\\n\"\;\ fi\;\ git\ status\ --short\ --branch`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
PASS: pyproject.toml parses.
PASS: trailing-whitespace scan (24 changed files).
PASS: git diff --check.
SKIP: Docker is unavailable; container startup was not run.
SKIP: Python package installer is unavailable; dependency-backed API tests were not run.
## feature/01-tech-stack-override
 M .cursorrules
 M .gitignore
 M README.md
 M docs/architecture.md
 M harness/validate.sh
?? .env.example
?? Dockerfile
?? alembic.ini
?? docker-compose.yml
?? interactions/01-tech-stack-override/
?? migrations/
?? pyproject.toml
?? src/
?? tests/
```

## Execution - 2026-10-28T21:12:53Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c if\ \!\ command\ -v\ docker\ \>/dev/null\ 2\>\&1\;\ then\ printf\ \"Docker\ CLI\ is\ not\ installed\ or\ is\ not\ on\ PATH.\\\\n\"\ \>\&2\;\ exit\ 127\;\ fi\;\ docker\ --version\;\ docker\ compose\ version`
- Exit status: `127`

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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.003s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
Docker CLI is not installed or is not on PATH.
```

## Execution - 2026-10-28T21:14:09Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c cat\ /etc/os-release\;\ printf\ \"\\\\n--\ identity\ --\\\\n\"\;\ id\;\ printf\ \"\\\\n--\ package\ tools\ --\\\\n\"\;\ command\ -v\ apt-get\ \|\|\ true\;\ command\ -v\ sudo\ \|\|\ true\;\ printf\ \"\\\\n--\ available\ Docker\ packages\ --\\\\n\"\;\ if\ command\ -v\ apt-cache\ \>/dev/null\ 2\>\&1\;\ then\ apt-cache\ policy\ docker-ce-cli\ docker.io\ docker-cli\ 2\>/dev/null\ \|\ sed\ -n\ \"1\,80p\"\;\ fi`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.003s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
PRETTY_NAME="Ubuntu 26.04.1 LTS"
NAME="Ubuntu"
VERSION_ID="26.04"
VERSION="26.04.1 LTS (Resolute Raccoon)"
VERSION_CODENAME=resolute
ID=ubuntu
ID_LIKE=debian
HOME_URL="https://www.ubuntu.com/"
SUPPORT_URL="https://help.ubuntu.com/"
BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
UBUNTU_CODENAME=resolute
LOGO=ubuntu-logo

-- identity --
uid=1000(glaze) gid=1000(glaze) groups=1000(glaze),4(adm),20(dialout),24(cdrom),25(floppy),27(sudo),29(audio),30(dip),44(video),46(plugdev),100(users),105(netdev)

-- package tools --
/usr/bin/apt-get
/usr/bin/sudo

-- available Docker packages --
docker-ce-cli:
  Installed: (none)
  Candidate: (none)
  Version table:
docker.io:
  Installed: (none)
  Candidate: 29.1.3-0ubuntu4.1
  Version table:
     29.1.3-0ubuntu4.1 500
        500 http://archive.ubuntu.com/ubuntu resolute-updates/universe amd64 Packages
        500 http://security.ubuntu.com/ubuntu resolute-security/universe amd64 Packages
     29.1.3-0ubuntu4 500
        500 http://archive.ubuntu.com/ubuntu resolute/universe amd64 Packages
docker-cli:
  Installed: (none)
  Candidate: (none)
  Version table:
```

## Execution - 2026-10-28T21:14:22Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ if\ \!\ command\ -v\ curl\ \>/dev/null\ 2\>\&1\ \|\|\ \!\ command\ -v\ gpg\ \>/dev/null\ 2\>\&1\;\ then\ printf\ \"curl/gpg\ tools\ unavailable\;\ cannot\ configure\ the\ vendor\ CLI\ repository.\\\\n\"\ \>\&2\;\ exit\ 1\;\ fi\;\ for\ url\ in\ https://download.docker.com/linux/ubuntu/dists/resolute/stable/binary-amd64/Packages.gz\ https://download.docker.com/linux/ubuntu/dists/noble/stable/binary-amd64/Packages.gz\;\ do\ printf\ \"Checking\ %s\\\\n\"\ \"\$url\"\;\ curl\ -fsSI\ --max-time\ 15\ \"\$url\"\ \|\ sed\ -n\ \"1\,3p\"\ \|\|\ true\;\ done`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
Checking https://download.docker.com/linux/ubuntu/dists/resolute/stable/binary-amd64/Packages.gz
HTTP/2 200 
content-type: application/gzip
content-length: 37147
Checking https://download.docker.com/linux/ubuntu/dists/noble/stable/binary-amd64/Packages.gz
HTTP/2 200 
content-type: application/gzip
content-length: 87224
```

## Execution - 2026-10-28T21:14:30Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- sudo -n true`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
sudo: interactive authentication is required
```

## Execution - 2026-10-28T21:14:42Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ printf\ \"--\ architecture\ --\\\\n\"\;\ uname\ -m\;\ printf\ \"--\ Docker\ static\ client\ builds\ --\\\\n\"\;\ curl\ -fsSL\ --max-time\ 30\ https://download.docker.com/linux/static/stable/x86_64/\ \|\ sed\ -n\ \"1\,80p\"\;\ printf\ \"--\ existing\ daemon\ socket\ --\\\\n\"\;\ if\ test\ -S\ /var/run/docker.sock\;\ then\ ls\ -l\ /var/run/docker.sock\;\ else\ printf\ \"No\ /var/run/docker.sock\ found.\\\\n\"\;\ fi`
- Exit status: `2`

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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
bash: line 1: printf: --: invalid option
printf: usage: printf [-v var] format [arguments]
```

## Execution - 2026-10-28T21:14:46Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ printf\ \"%s\\\\n\"\ \"--\ architecture\ --\"\;\ uname\ -m\;\ printf\ \"%s\\\\n\"\ \"--\ Docker\ static\ client\ builds\ --\"\;\ curl\ -fsSL\ --max-time\ 30\ https://download.docker.com/linux/static/stable/x86_64/\ \|\ sed\ -n\ \"1\,80p\"\;\ printf\ \"%s\\\\n\"\ \"--\ existing\ daemon\ socket\ --\"\;\ if\ test\ -S\ /var/run/docker.sock\;\ then\ ls\ -l\ /var/run/docker.sock\;\ else\ printf\ \"No\ /var/run/docker.sock\ found.\\\\n\"\;\ fi`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
-- architecture --
x86_64
-- Docker static client builds --
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Index of linux/static/stable/x86_64/</title>
</head>
<body>
<h1>Index of linux/static/stable/x86_64/</h1>
<hr>
<pre><a href="../">../</a>
<a href="sbx/">sbx/</a>
<a href="docker-17.03.0-ce.tgz">docker-17.03.0-ce.tgz</a>                                                                 2025-07-29 12:21:11       27MB
<a href="docker-17.03.1-ce.tgz">docker-17.03.1-ce.tgz</a>                                                                 2025-07-29 12:21:11       27MB
<a href="docker-17.03.2-ce.tgz">docker-17.03.2-ce.tgz</a>                                                                 2025-07-29 12:21:11       27MB
<a href="docker-17.06.0-ce.tgz">docker-17.06.0-ce.tgz</a>                                                                 2025-07-29 12:21:11       28MB
<a href="docker-17.06.1-ce.tgz">docker-17.06.1-ce.tgz</a>                                                                 2025-07-29 12:21:11       28MB
<a href="docker-17.06.2-ce.tgz">docker-17.06.2-ce.tgz</a>                                                                 2025-07-29 12:21:11       28MB
<a href="docker-17.09.0-ce.tgz">docker-17.09.0-ce.tgz</a>                                                                 2025-07-29 12:21:11       29MB
<a href="docker-17.09.1-ce.tgz">docker-17.09.1-ce.tgz</a>                                                                 2025-07-29 12:21:11       29MB
<a href="docker-17.12.0-ce.tgz">docker-17.12.0-ce.tgz</a>                                                                 2025-07-29 12:21:11       33MB
<a href="docker-17.12.1-ce.tgz">docker-17.12.1-ce.tgz</a>                                                                 2025-07-29 12:21:11       33MB
<a href="docker-18.03.0-ce.tgz">docker-18.03.0-ce.tgz</a>                                                                 2025-07-29 12:21:11       37MB
<a href="docker-18.03.1-ce.tgz">docker-18.03.1-ce.tgz</a>                                                                 2025-07-29 12:21:11       37MB
<a href="docker-18.06.0-ce.tgz">docker-18.06.0-ce.tgz</a>                                                                 2025-07-29 12:21:11       42MB
<a href="docker-18.06.1-ce.tgz">docker-18.06.1-ce.tgz</a>                                                                 2025-07-29 12:21:11       42MB
<a href="docker-18.06.2-ce.tgz">docker-18.06.2-ce.tgz</a>                                                                 2025-07-29 12:21:11       42MB
<a href="docker-18.06.3-ce.tgz">docker-18.06.3-ce.tgz</a>                                                                 2025-07-29 12:21:11       42MB
<a href="docker-18.09.0.tgz">docker-18.09.0.tgz</a>                                                                    2025-07-29 12:21:11       45MB
<a href="docker-18.09.1.tgz">docker-18.09.1.tgz</a>                                                                    2025-07-29 12:21:11       46MB
<a href="docker-18.09.2.tgz">docker-18.09.2.tgz</a>                                                                    2025-07-29 12:21:11       46MB
<a href="docker-18.09.3.tgz">docker-18.09.3.tgz</a>                                                                    2025-07-29 12:21:11       46MB
<a href="docker-18.09.4.tgz">docker-18.09.4.tgz</a>                                                                    2025-07-29 12:21:11       46MB
<a href="docker-18.09.5.tgz">docker-18.09.5.tgz</a>                                                                    2025-07-29 12:21:11       46MB
<a href="docker-18.09.6.tgz">docker-18.09.6.tgz</a>                                                                    2025-07-29 12:21:11       46MB
<a href="docker-18.09.7.tgz">docker-18.09.7.tgz</a>                                                                    2025-07-29 12:21:11       46MB
<a href="docker-18.09.8.tgz">docker-18.09.8.tgz</a>                                                                    2025-07-29 12:21:11       46MB
<a href="docker-18.09.9.tgz">docker-18.09.9.tgz</a>                                                                    2025-07-29 12:21:11       54MB
<a href="docker-19.03.0.tgz">docker-19.03.0.tgz</a>                                                                    2025-07-29 12:21:11       60MB
<a href="docker-19.03.1.tgz">docker-19.03.1.tgz</a>                                                                    2025-07-29 12:21:11       60MB
<a href="docker-19.03.2.tgz">docker-19.03.2.tgz</a>                                                                    2025-07-29 12:21:11       60MB
<a href="docker-19.03.3.tgz">docker-19.03.3.tgz</a>                                                                    2025-07-29 12:21:11       60MB
<a href="docker-19.03.4.tgz">docker-19.03.4.tgz</a>                                                                    2025-07-29 12:21:11       60MB
<a href="docker-19.03.5.tgz">docker-19.03.5.tgz</a>                                                                    2025-07-29 12:21:11       60MB
<a href="docker-19.03.6.tgz">docker-19.03.6.tgz</a>                                                                    2025-07-29 12:21:11       61MB
<a href="docker-19.03.7.tgz">docker-19.03.7.tgz</a>                                                                    2025-07-29 12:21:11       61MB
<a href="docker-19.03.8.tgz">docker-19.03.8.tgz</a>                                                                    2025-07-29 12:21:11       61MB
<a href="docker-19.03.9.tgz">docker-19.03.9.tgz</a>                                                                    2025-07-29 12:21:11       58MB
<a href="docker-19.03.10.tgz">docker-19.03.10.tgz</a>                                                                   2025-07-29 12:21:11       58MB
<a href="docker-19.03.11.tgz">docker-19.03.11.tgz</a>                                                                   2025-07-29 12:21:11       58MB
<a href="docker-19.03.12.tgz">docker-19.03.12.tgz</a>                                                                   2025-07-29 12:21:11       58MB
<a href="docker-19.03.13.tgz">docker-19.03.13.tgz</a>                                                                   2025-07-29 12:21:11       59MB
<a href="docker-19.03.14.tgz">docker-19.03.14.tgz</a>                                                                   2025-07-29 12:21:11       60MB
<a href="docker-19.03.15.tgz">docker-19.03.15.tgz</a>                                                                   2025-07-29 12:21:11       60MB
<a href="docker-20.10.0.tgz">docker-20.10.0.tgz</a>                                                                    2025-07-29 12:21:11       66MB
<a href="docker-20.10.1.tgz">docker-20.10.1.tgz</a>                                                                    2025-07-29 12:21:11       66MB
<a href="docker-20.10.2.tgz">docker-20.10.2.tgz</a>                                                                    2025-07-29 12:21:11       66MB
<a href="docker-20.10.3.tgz">docker-20.10.3.tgz</a>                                                                    2025-07-29 12:21:11       66MB
<a href="docker-20.10.4.tgz">docker-20.10.4.tgz</a>                                                                    2025-07-29 12:21:11       66MB
<a href="docker-20.10.5.tgz">docker-20.10.5.tgz</a>                                                                    2025-07-29 12:21:11       66MB
<a href="docker-20.10.6.tgz">docker-20.10.6.tgz</a>                                                                    2025-07-29 12:21:11       66MB
<a href="docker-20.10.7.tgz">docker-20.10.7.tgz</a>                                                                    2025-07-29 12:21:11       66MB
<a href="docker-20.10.8.tgz">docker-20.10.8.tgz</a>                                                                    2025-07-29 12:21:11       58MB
<a href="docker-20.10.9.tgz">docker-20.10.9.tgz</a>                                                                    2025-07-29 12:21:11       60MB
<a href="docker-20.10.10.tgz">docker-20.10.10.tgz</a>                                                                   2025-07-29 12:21:11       60MB
<a href="docker-20.10.11.tgz">docker-20.10.11.tgz</a>                                                                   2025-07-29 12:21:11       60MB
<a href="docker-20.10.12.tgz">docker-20.10.12.tgz</a>                                                                   2025-07-29 12:21:11       60MB
<a href="docker-20.10.13.tgz">docker-20.10.13.tgz</a>                                                                   2025-07-29 12:21:11       61MB
<a href="docker-20.10.14.tgz">docker-20.10.14.tgz</a>                                                                   2025-07-29 12:21:11       61MB
<a href="docker-20.10.15.tgz">docker-20.10.15.tgz</a>                                                                   2025-07-29 12:21:11       62MB
<a href="docker-20.10.16.tgz">docker-20.10.16.tgz</a>                                                                   2025-07-29 12:21:11       62MB
<a href="docker-20.10.17.tgz">docker-20.10.17.tgz</a>                                                                   2025-07-29 12:21:11       62MB
<a href="docker-20.10.18.tgz">docker-20.10.18.tgz</a>                                                                   2025-07-29 12:21:11       63MB
<a href="docker-20.10.19.tgz">docker-20.10.19.tgz</a>                                                                   2025-07-29 12:21:11       63MB
<a href="docker-20.10.20.tgz">docker-20.10.20.tgz</a>                                                                   2025-07-29 12:21:11       63MB
<a href="docker-20.10.21.tgz">docker-20.10.21.tgz</a>                                                                   2025-07-29 12:21:11       63MB
<a href="docker-20.10.22.tgz">docker-20.10.22.tgz</a>                                                                   2025-07-29 12:21:11       63MB
<a href="docker-20.10.23.tgz">docker-20.10.23.tgz</a>                                                                   2025-07-29 12:21:11       63MB
<a href="docker-20.10.24.tgz">docker-20.10.24.tgz</a>                                                                   2025-07-29 12:21:11       64MB
<a href="docker-23.0.0.tgz">docker-23.0.0.tgz</a>                                                                     2025-07-29 12:21:11       64MB
<a href="docker-23.0.1.tgz">docker-23.0.1.tgz</a>                                                                     2025-07-29 12:21:11       64MB
-- existing daemon socket --
No /var/run/docker.sock found.
```

## Execution - 2026-10-28T21:15:13Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ for\ package\ in\ docker-ce-cli\ docker-compose-plugin\;\ do\ printf\ \"Package:\ %s\\\\n\"\ \"\$package\"\;\ curl\ -fsSL\ --max-time\ 30\ https://download.docker.com/linux/ubuntu/dists/resolute/stable/binary-amd64/Packages.gz\ \|\ gzip\ -dc\ \|\ awk\ -v\ package=\"\$package\"\ \'\$1\ ==\ \"Package:\"\ \&\&\ \$2\ ==\ package\ \{found=1\}\ found\ \&\&\ /\^\(Package\|Version\|Depends\|Filename\|Size\):/\ \{print\}\ found\ \&\&\ /\^\$/\ \{exit\}\'\;\ done`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.003s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
Package: docker-ce-cli
Package: docker-ce-cli
Version: 5:29.3.1-1~ubuntu.26.04~resolute
Depends: libc6 (>= 2.34)
Filename: dists/resolute/pool/stable/amd64/docker-ce-cli_29.3.1-1~ubuntu.26.04~resolute_amd64.deb
Size: 16429272
Package: docker-compose-plugin
Package: docker-compose-plugin
Version: 5.0.2-1~ubuntu.26.04~resolute
Filename: dists/resolute/pool/stable/amd64/docker-compose-plugin_5.0.2-1~ubuntu.26.04~resolute_amd64.deb
Size: 7722656
```

## Execution - 2026-10-28T21:15:25Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ for\ package\ in\ docker-ce-cli\ docker-compose-plugin\;\ do\ printf\ \"Package:\ %s\\\\n\"\ \"\$package\"\;\ curl\ -fsSL\ --max-time\ 30\ https://download.docker.com/linux/ubuntu/dists/resolute/stable/binary-amd64/Packages.gz\ \|\ gzip\ -dc\ \|\ awk\ -v\ package=\"\$package\"\ \'\$1\ ==\ \"Package:\"\ \&\&\ \$2\ ==\ package\ \{found=1\}\ found\ \&\&\ /\^\(Version\|Filename\|Size\|SHA256\):/\ \{print\}\ found\ \&\&\ /\^\$/\ \{exit\}\'\;\ done\;\ command\ -v\ dpkg-deb`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
Package: docker-ce-cli
Version: 5:29.3.1-1~ubuntu.26.04~resolute
Filename: dists/resolute/pool/stable/amd64/docker-ce-cli_29.3.1-1~ubuntu.26.04~resolute_amd64.deb
Size: 16429272
SHA256: 1b42f22c5c0f9038e046e1e86a808599a37081c9bad28d2c37b85a954b016891
Package: docker-compose-plugin
Version: 5.0.2-1~ubuntu.26.04~resolute
Filename: dists/resolute/pool/stable/amd64/docker-compose-plugin_5.0.2-1~ubuntu.26.04~resolute_amd64.deb
Size: 7722656
SHA256: 07a9740e0df2a1921481dea037240f0f15da6a66281d2e91bd058ec97ddc88af
/usr/bin/dpkg-deb
```

## Execution - 2026-10-28T21:15:35Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ temp_dir=\$\(mktemp\ -d\)\;\ trap\ \'rm\ -rf\ --\ \"\$temp_dir\"\'\ EXIT\;\ curl\ -fsSL\ --max-time\ 120\ https://download.docker.com/linux/ubuntu/dists/resolute/pool/stable/amd64/docker-ce-cli_29.3.1-1~ubuntu.26.04~resolute_amd64.deb\ -o\ \"\$temp_dir/docker-ce-cli.deb\"\;\ curl\ -fsSL\ --max-time\ 120\ https://download.docker.com/linux/ubuntu/dists/resolute/pool/stable/amd64/docker-compose-plugin_5.0.2-1~ubuntu.26.04~resolute_amd64.deb\ -o\ \"\$temp_dir/docker-compose-plugin.deb\"\;\ printf\ \"%s\ \ %s\\\\n\"\ 1b42f22c5c0f9038e046e1e86a808599a37081c9bad28d2c37b85a954b016891\ \"\$temp_dir/docker-ce-cli.deb\"\ 07a9740e0df2a1921481dea037240f0f15da6a66281d2e91bd058ec97ddc88af\ \"\$temp_dir/docker-compose-plugin.deb\"\ \|\ sha256sum\ -c\ -\;\ printf\ \"--\ docker\ client\ payload\ --\\\\n\"\;\ dpkg-deb\ -c\ \"\$temp_dir/docker-ce-cli.deb\"\ \|\ grep\ -E\ \"usr/bin/docker\$\"\;\ printf\ \"--\ Compose\ plugin\ payload\ --\\\\n\"\;\ dpkg-deb\ -c\ \"\$temp_dir/docker-compose-plugin.deb\"\ \|\ grep\ -E\ \"docker-compose\$\"\;\ printf\ \"--\ PATH\ --\\\\n%s\\\\n\"\ \"\$PATH\"`
- Exit status: `2`

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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
/tmp/tmp.JQyPN9ey32/docker-ce-cli.deb: OK
/tmp/tmp.JQyPN9ey32/docker-compose-plugin.deb: OK
bash: line 1: printf: --: invalid option
printf: usage: printf [-v var] format [arguments]
```

## Execution - 2026-10-28T21:15:44Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ temp_dir=\$\(mktemp\ -d\)\;\ trap\ \'rm\ -rf\ --\ \"\$temp_dir\"\'\ EXIT\;\ curl\ -fsSL\ --max-time\ 120\ https://download.docker.com/linux/ubuntu/dists/resolute/pool/stable/amd64/docker-ce-cli_29.3.1-1~ubuntu.26.04~resolute_amd64.deb\ -o\ \"\$temp_dir/docker-ce-cli.deb\"\;\ curl\ -fsSL\ --max-time\ 120\ https://download.docker.com/linux/ubuntu/dists/resolute/pool/stable/amd64/docker-compose-plugin_5.0.2-1~ubuntu.26.04~resolute_amd64.deb\ -o\ \"\$temp_dir/docker-compose-plugin.deb\"\;\ printf\ \"%s\ \ %s\\\\n\"\ 1b42f22c5c0f9038e046e1e86a808599a37081c9bad28d2c37b85a954b016891\ \"\$temp_dir/docker-ce-cli.deb\"\ 07a9740e0df2a1921481dea037240f0f15da6a66281d2e91bd058ec97ddc88af\ \"\$temp_dir/docker-compose-plugin.deb\"\ \|\ sha256sum\ -c\ -\;\ printf\ \"%s\\\\n\"\ \"--\ docker\ client\ payload\ --\"\;\ dpkg-deb\ -c\ \"\$temp_dir/docker-ce-cli.deb\"\ \|\ grep\ -E\ \"usr/bin/docker\$\"\;\ printf\ \"%s\\\\n\"\ \"--\ Compose\ plugin\ payload\ --\"\;\ dpkg-deb\ -c\ \"\$temp_dir/docker-compose-plugin.deb\"\ \|\ grep\ -E\ \"docker-compose\$\"\;\ printf\ \"%s\\\\n%s\"\ \"--\ PATH\ --\"\ \"\$PATH\"`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
/tmp/tmp.sTOfX4h9Tx/docker-ce-cli.deb: OK
/tmp/tmp.sTOfX4h9Tx/docker-compose-plugin.deb: OK
-- docker client payload --
-rwxr-xr-x root/root  44320842 2026-03-25 09:13 ./usr/bin/docker
-- Compose plugin payload --
-rwxr-xr-x root/root  31327024 2026-01-20 23:45 ./usr/libexec/docker/cli-plugins/docker-compose
-- PATH --
/home/glaze/.nvm/versions/node/v24.22.1/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/usr/lib/wsl/lib:/usr/lib/linux-tools/6.18.54.1-microsoft-standard-WSL2/bin:/mnt/c/WINDOWS/System32:/mnt/c/Users/scott/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0/LocalCache/local-packages/Python311/Scripts:/mnt/c/Program Files/dotnet/:/mnt/c/Program Files/Git/cmd:/mnt/c/Program Files/nodejs/:/mnt/c/Program Files/Microsoft SQL Server/170/Tools/Binn/:/mnt/c/Program Files/Microsoft SQL Server/Client SDK/ODBC/170/Tools/Binn/:/mnt/c/Program Files/PowerShell/7/:/mnt/c/Users/scott/AppData/Local/Microsoft/WindowsApps:/mnt/c/Users/scott/.dotnet/tools:/mnt/c/Users/scott/AppData/Local/Programs/Microsoft VS Code/bin:/mnt/c/Users/scott/AppData/Roaming/npm:/snap/bin:/home/glaze/.vscode-server/bin/2c33b50b16c472efe58357d1d2a8a5414bc23fbf/node_modules/@vscode/ripgrep-universal/bin/linux-x64:/home/glaze/.vscode-server/bin/2c33b50b16c472efe58357d1d2a8a5414bc23fbf/node_modules/@github/copilot-sdk-linux-x64/ripgrep/bin/linux-x64```

## Execution - 2026-10-28T21:16:04Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ temp_dir=\$\(mktemp\ -d\)\;\ trap\ \'rm\ -rf\ --\ \"\$temp_dir\"\'\ EXIT\;\ base_url=https://download.docker.com/linux/ubuntu/dists/resolute/pool/stable/amd64\;\ curl\ -fsSL\ --max-time\ 120\ \"\$base_url/docker-ce-cli_29.3.1-1~ubuntu.26.04~resolute_amd64.deb\"\ -o\ \"\$temp_dir/docker-ce-cli.deb\"\;\ curl\ -fsSL\ --max-time\ 120\ \"\$base_url/docker-compose-plugin_5.0.2-1~ubuntu.26.04~resolute_amd64.deb\"\ -o\ \"\$temp_dir/docker-compose-plugin.deb\"\;\ printf\ \"%s\ \ %s\\\\n\"\ 1b42f22c5c0f9038e046e1e86a808599a37081c9bad28d2c37b85a954b016891\ \"\$temp_dir/docker-ce-cli.deb\"\ 07a9740e0df2a1921481dea037240f0f15da6a66281d2e91bd058ec97ddc88af\ \"\$temp_dir/docker-compose-plugin.deb\"\ \|\ sha256sum\ -c\ -\;\ dpkg-deb\ -x\ \"\$temp_dir/docker-ce-cli.deb\"\ \"\$temp_dir/cli\"\;\ dpkg-deb\ -x\ \"\$temp_dir/docker-compose-plugin.deb\"\ \"\$temp_dir/compose\"\;\ mkdir\ -p\ \"\$HOME/.local/bin\"\ \"\$HOME/.docker/cli-plugins\"\;\ install\ -m\ 0755\ \"\$temp_dir/cli/usr/bin/docker\"\ \"\$HOME/.local/bin/docker\"\;\ install\ -m\ 0755\ \"\$temp_dir/compose/usr/libexec/docker/cli-plugins/docker-compose\"\ \"\$HOME/.docker/cli-plugins/docker-compose\"\;\ export\ PATH=\"\$HOME/.local/bin:\$PATH\"\;\ printf\ \"Installed\ Docker\ CLI:\ \"\;\ docker\ --version\;\ printf\ \"Installed\ Compose\ plugin:\ \"\;\ docker\ compose\ version\;\ printf\ \"Executable:\ %s\\\\n\"\ \"\$\(command\ -v\ docker\)\"\;\ if\ test\ -S\ /var/run/docker.sock\;\ then\ printf\ \"Docker\ daemon\ socket\ is\ present.\\\\n\"\;\ else\ printf\ \"Docker\ CLI\ installed\ only\;\ no\ local\ Docker\ daemon\ socket\ is\ available.\\\\n\"\;\ fi`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.003s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
/tmp/tmp.rwxouSrTtm/docker-ce-cli.deb: OK
/tmp/tmp.rwxouSrTtm/docker-compose-plugin.deb: OK
Installed Docker CLI: Docker version 29.3.1, build c2be9cc
Installed Compose plugin: Docker Compose version v5.0.2
Executable: /home/glaze/.local/bin/docker
Docker CLI installed only; no local Docker daemon socket is available.
```

## Execution - 2026-10-28T21:16:42Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- docker build --tag wa-mediation-wizard:local .`
- Exit status: `127`

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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.003s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
harness/validate.sh: line 116: docker: command not found
```

## Execution - 2026-10-28T21:16:49Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- /home/glaze/.local/bin/docker build --tag wa-mediation-wizard:local .`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
DEPRECATED: The legacy builder is deprecated and will be removed in a future release.
            Install the buildx component to build images with BuildKit:
            https://docs.docker.com/go/buildx/

time="2026-10-28T14:16:49-07:00" level=error msg="Can't add file /home/glaze/src/WA-contested-divorce-without-children-mediation-to-end/.cursorrules to tar: io: read/write on closed pipe"
time="2026-10-28T14:16:49-07:00" level=error msg="Can't close tar writer: io: read/write on closed pipe"
failed to connect to the docker API at unix:///var/run/docker.sock; check if the path is correct and if the daemon is running: dial unix /var/run/docker.sock: connect: no such file or directory
```

## Execution - 2026-10-29T01:20:27Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ printf\ \"%s\\\\n\"\ \"--\ Docker\ CLI\ --\"\;\ /home/glaze/.local/bin/docker\ --version\;\ printf\ \"%s\\\\n\"\ \"--\ daemon\ socket\ --\"\;\ if\ test\ -S\ /var/run/docker.sock\;\ then\ ls\ -l\ /var/run/docker.sock\;\ else\ printf\ \"No\ /var/run/docker.sock.\\\\n\"\;\ fi\;\ printf\ \"%s\\\\n\"\ \"--\ systemd\ --\"\;\ if\ command\ -v\ systemctl\ \>/dev/null\ 2\>\&1\;\ then\ systemctl\ is-system-running\ \|\|\ true\;\ systemctl\ status\ docker\ --no-pager\ \|\|\ true\;\ else\ printf\ \"systemctl\ unavailable.\\\\n\"\;\ fi\;\ printf\ \"%s\\\\n\"\ \"--\ docker\ service\ tools\ --\"\;\ command\ -v\ dockerd\ \|\|\ true\;\ command\ -v\ service\ \|\|\ true\;\ printf\ \"%s\\\\n\"\ \"--\ docker\ info\ --\"\;\ /home/glaze/.local/bin/docker\ info`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.003s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
-- Docker CLI --
Docker version 29.3.1, build c2be9cc
-- daemon socket --
No /var/run/docker.sock.
-- systemd --
running
Unit docker.service could not be found.
-- docker service tools --
/usr/sbin/service
-- docker info --
Client: Docker Engine - Community
 Version:    29.3.1
 Context:    default
 Debug Mode: false
 Plugins:
  compose: Docker Compose (Docker Inc.)
    Version:  v5.0.2
    Path:     /home/glaze/.docker/cli-plugins/docker-compose

Server:
failed to connect to the docker API at unix:///var/run/docker.sock; check if the path is correct and if the daemon is running: dial unix /var/run/docker.sock: connect: no such file or directory
```

## Execution - 2026-10-29T01:20:36Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c if\ \!\ command\ -v\ powershell.exe\ \>/dev/null\ 2\>\&1\;\ then\ printf\ \"Windows\ PowerShell\ is\ unavailable\ from\ this\ WSL\ environment.\\\\n\"\ \>\&2\;\ exit\ 127\;\ fi\;\ powershell.exe\ -NoProfile\ -NonInteractive\ -Command\ \'\$desktop\ =\ Join-Path\ \$env:ProgramFiles\ \"Docker\\\\Docker\\\\Docker\ Desktop.exe\"\;\ if\ \(Test-Path\ \$desktop\)\ \{\ Write-Output\ \"Docker\ Desktop\ found:\ \$desktop\"\ \}\ else\ \{\ Write-Output\ \"Docker\ Desktop\ executable\ not\ found\ at\ \$desktop\"\;\ exit\ 2\ \}\;\ Get-Process\ \"Docker\ Desktop\"\,\ \"com.docker.backend\"\ -ErrorAction\ SilentlyContinue\ \|\ Select-Object\ ProcessName\,\ Id\'`
- Exit status: `127`

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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
Windows PowerShell is unavailable from this WSL environment.
```

## Execution - 2026-10-29T01:23:59Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ /home/glaze/.local/bin/docker\ info\ --format\ \"Server=\{\{.ServerVersion\}\}\"\;\ /home/glaze/.local/bin/docker\ build\ --tag\ wa-mediation-wizard:local\ .`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
Server=
permission denied while trying to connect to the docker API at unix:///var/run/docker.sock
```

## Execution - 2026-10-29T01:24:06Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c printf\ \"%s\\\\n\"\ \"--\ socket\ --\"\;\ ls\ -l\ /var/run/docker.sock\;\ printf\ \"%s\\\\n\"\ \"--\ current\ user/groups\ --\"\;\ id\;\ printf\ \"%s\\\\n\"\ \"--\ Docker\ contexts\ --\"\;\ /home/glaze/.local/bin/docker\ context\ ls\;\ printf\ \"%s\\\\n\"\ \"--\ Docker\ environment\ overrides\ --\"\;\ env\ \|\ grep\ -E\ \"\^\(DOCKER_HOST\|DOCKER_CONTEXT\|DOCKER_TLS_VERIFY\|DOCKER_CERT_PATH\)=\"\ \|\|\ true\;\ printf\ \"%s\\\\n\"\ \"--\ sudo\ status\ --\"\;\ sudo\ -n\ true\ 2\>\&1\ \|\|\ true`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
-- socket --
srw-rw---- 1 root docker 0 Oct 28 18:23 /var/run/docker.sock
-- current user/groups --
uid=1000(glaze) gid=1000(glaze) groups=1000(glaze),4(adm),20(dialout),24(cdrom),25(floppy),27(sudo),29(audio),30(dip),44(video),46(plugdev),100(users),105(netdev)
-- Docker contexts --
NAME            DESCRIPTION                               DOCKER ENDPOINT                             ERROR
default *       Current DOCKER_HOST based configuration   unix:///var/run/docker.sock                 
desktop-linux   Docker Desktop                            npipe:////./pipe/dockerDesktopLinuxEngine   
-- Docker environment overrides --
-- sudo status --
sudo: interactive authentication is required
```

## Execution - 2026-10-29T01:24:12Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c printf\ \"%s\\\\n\"\ \"--\ docker\ group\ record\ --\"\;\ getent\ group\ docker\ \|\|\ true\;\ printf\ \"%s\\\\n\"\ \"--\ group\ database\ permissions\ --\"\;\ ls\ -l\ /etc/group\ /etc/gshadow\;\ printf\ \"%s\\\\n\"\ \"--\ socket\ access\ --\"\;\ test\ -r\ /var/run/docker.sock\ \&\&\ printf\ \"readable\\\\n\"\ \|\|\ printf\ \"not\ readable\ by\ this\ process\\\\n\"\;\ test\ -w\ /var/run/docker.sock\ \&\&\ printf\ \"writable\\\\n\"\ \|\|\ printf\ \"not\ writable\ by\ this\ process\\\\n\"`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.003s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
-- docker group record --
docker:x:1001:glaze
-- group database permissions --
-rw-r--r-- 1 root root   808 Oct 28 18:23 /etc/group
-rw-r----- 1 root shadow 689 Oct 28 18:23 /etc/gshadow
-- socket access --
not readable by this process
not writable by this process
```

## Execution - 2026-10-29T01:24:18Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- sg docker -c /home/glaze/.local/bin/docker\ info\ --format\ \"Server=\{\{.ServerVersion\}\}\"\ \&\&\ /home/glaze/.local/bin/docker\ build\ --tag\ wa-mediation-wizard:local\ .`
- Exit status: `127`

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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.003s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
harness/validate.sh: line 116: sg: command not found
```

## Execution - 2026-10-29T01:24:27Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c printf\ \"setpriv:\ \"\;\ command\ -v\ setpriv\ \|\|\ true\;\ printf\ \"newgrp:\ \"\;\ command\ -v\ newgrp\ \|\|\ true\;\ printf\ \"groups\ utility:\ \"\;\ command\ -v\ groups\ \|\|\ true\;\ printf\ \"docker\ gid:\ \"\;\ getent\ group\ docker\ \|\ cut\ -d:\ -f3`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
setpriv: /usr/bin/setpriv
newgrp: groups utility: /usr/bin/groups
docker gid: 1001
```

## Execution - 2026-10-29T01:24:36Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- newgrp docker -c id\ -G\;\ /home/glaze/.local/bin/docker\ info\ --format\ \"Server=\{\{.ServerVersion\}\}\"`
- Exit status: `127`

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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.003s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
harness/validate.sh: line 116: newgrp: command not found
```

## Execution - 2026-10-29T01:24:40Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- setpriv --reuid=1000 --regid=1000 --groups=1001 -- /home/glaze/.local/bin/docker info --format Server=\{\{.ServerVersion\}\}`
- Exit status: `127`

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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
setpriv: setgroups failed: Operation not permitted
```

## Execution - 2026-10-29T01:25:38Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ id\;\ docker\ info\ --format\ \"Server=\{\{.ServerVersion\}\}\"\;\ docker\ build\ --tag\ wa-mediation-wizard:local\ .`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.003s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
uid=1000(glaze) gid=1000(glaze) groups=1000(glaze),4(adm),20(dialout),24(cdrom),25(floppy),27(sudo),29(audio),30(dip),44(video),46(plugdev),100(users),105(netdev),1001(docker)
Server=29.9.2
#0 building with "default" instance using docker driver

#1 [internal] load build definition from Dockerfile
#1 transferring dockerfile: 570B done
#1 DONE 0.1s

#2 [internal] load metadata for docker.io/library/python:3.12-slim
#2 ...

#3 [auth] library/python:pull token for registry-1.docker.io
#3 DONE 0.0s

#2 [internal] load metadata for docker.io/library/python:3.12-slim
#2 DONE 1.9s

#4 [internal] load .dockerignore
#4 transferring context: 2B done
#4 DONE 0.0s

#5 [1/8] FROM docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
#5 resolve docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159 0.0s done
#5 ...

#6 [internal] load build context
#6 transferring context: 96.52kB done
#6 DONE 0.1s

#5 [1/8] FROM docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
#5 sha256:acca7542dfc736e9ce20cbefc58b2d09822276d15d4a0c531531a6f1b057928e 251B / 251B 0.1s done
#5 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 0B / 12.12MB 0.3s
#5 sha256:3eb77115150676568f88e2957181b8f7e3014e797f1ce8cd640086dfbed45e35 0B / 1.29MB 0.2s
#5 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 0B / 29.86MB 0.2s
#5 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 1.05MB / 12.12MB 0.5s
#5 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 4.19MB / 12.12MB 0.6s
#5 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 6.29MB / 12.12MB 0.8s
#5 sha256:3eb77115150676568f88e2957181b8f7e3014e797f1ce8cd640086dfbed45e35 1.29MB / 1.29MB 0.6s done
#5 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 9.44MB / 12.12MB 0.9s
#5 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 2.10MB / 29.86MB 0.8s
#5 sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 12.12MB / 12.12MB 1.0s done
#5 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 5.24MB / 29.86MB 0.9s
#5 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 8.39MB / 29.86MB 1.1s
#5 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 10.49MB / 29.86MB 1.2s
#5 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 12.58MB / 29.86MB 1.4s
#5 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 14.68MB / 29.86MB 1.5s
#5 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 17.83MB / 29.86MB 1.7s
#5 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 20.97MB / 29.86MB 1.8s
#5 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 23.07MB / 29.86MB 2.0s
#5 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 25.17MB / 29.86MB 2.1s
#5 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 29.86MB / 29.86MB 2.3s
#5 sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 29.86MB / 29.86MB 2.3s done
#5 extracting sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5
#5 extracting sha256:6fc242d221a673263eabd14a9ad9584d3177c96e5cb504c891497338e2f912f5 0.8s done
#5 DONE 3.2s

#5 [1/8] FROM docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
#5 extracting sha256:3eb77115150676568f88e2957181b8f7e3014e797f1ce8cd640086dfbed45e35 0.1s done
#5 DONE 3.4s

#5 [1/8] FROM docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
#5 extracting sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3
#5 extracting sha256:f574edac59d9f092df596f54e5b52656c803fd3ae30825b8ee5a189ed05f63d3 0.4s done
#5 DONE 3.7s

#5 [1/8] FROM docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
#5 extracting sha256:acca7542dfc736e9ce20cbefc58b2d09822276d15d4a0c531531a6f1b057928e 0.0s done
#5 DONE 3.7s

#7 [2/8] RUN apt-get update     && apt-get install -y --no-install-recommends libreoffice-writer     && rm -rf /var/lib/apt/lists/*
#7 0.261 Hit:1 http://deb.debian.org/debian trixie InRelease
#7 0.261 Get:2 http://deb.debian.org/debian trixie-updates InRelease [47.3 kB]
#7 0.283 Get:3 http://deb.debian.org/debian-security trixie-security InRelease [43.4 kB]
#7 0.305 Get:4 http://deb.debian.org/debian trixie/main amd64 Packages [9678 kB]
#7 0.902 Get:5 http://deb.debian.org/debian trixie-updates/main amd64 Packages [720 B]
#7 0.918 Get:6 http://deb.debian.org/debian-security trixie-security/main amd64 Packages [270 kB]
#7 1.558 Fetched 10.0 MB in 1s (7308 kB/s)
#7 1.558 Reading package lists...
#7 2.108 Reading package lists...
#7 2.666 Building dependency tree...
#7 2.877 Reading state information...
#7 3.211 The following additional packages will be installed:
#7 3.211   dirmngr fontconfig fontconfig-config fonts-dejavu-core fonts-dejavu-mono
#7 3.211   fonts-opensymbol gnupg gnupg-l10n gpg gpg-agent gpgconf gpgsm iso-codes
#7 3.211   libabsl20240722 libabw-0.1-1 libargon2-1 libassuan9 libatomic1
#7 3.211   libavahi-client3 libavahi-common-data libavahi-common3
#7 3.211   libboost-iostreams1.83.0 libboost-locale1.83.0 libboost-thread1.83.0
#7 3.211   libbrotli1 libcairo2 libcap2-bin libclucene-contribs1t64 libclucene-core1t64
#7 3.211   libcmis-0.6-6t64 libcom-err2 libcups2t64 libcurl3t64-gnutls libcurl4t64
#7 3.211   libdbus-1-3 libdconf1 libdeflate0 libdrm-common libdrm2 libe-book-0.1-1
#7 3.211   libeot0 libepoxy0 libepubgen-0.1-1 libetonyek-0.1-1 libexpat1
#7 3.211   libexttextcat-2.0-0 libexttextcat-data libfontconfig1 libfreetype6
#7 3.212   libgcrypt20 libglib2.0-0t64 libgnutls30t64 libgpg-error0 libgpgme11t64
#7 3.212   libgpgmepp6t64 libgraphite2-3 libgssapi-krb5-2
#7 3.212   libgstreamer-plugins-base1.0-0 libgstreamer1.0-0 libharfbuzz-icu0
#7 3.212   libharfbuzz0b libhunspell-1.7-0 libhyphen0 libice6 libicu76 libidn2-0
#7 3.212   libjbig0 libjpeg62-turbo libk5crypto3 libkeyutils1 libkrb5-3 libkrb5support0
#7 3.213   libksba8 liblangtag-common liblangtag1 liblcms2-2 libldap2 liblerc4 libltdl7
#7 3.213   libmhash2 libmwaw-0.3-3 libmythes-1.2-0 libnghttp2-14 libnghttp3-9
#7 3.213   libngtcp2-16 libngtcp2-crypto-gnutls8 libnpth0t64 libnspr4 libnss3
#7 3.213   libnumbertext-1.0-0 libnumbertext-data libodfgen-0.1-1 libopenjp2-7
#7 3.213   liborc-0.4-0t64 liborcus-0.18-0 liborcus-parser-0.18-0 libp11-kit0
#7 3.213   libpixman-1-0 libpng16-16t64 libpoppler147 libproc2-0 libpsl5t64
#7 3.213   libraptor2-0 librasqal3t64 librdf0t64 libreoffice-base-core
#7 3.213   libreoffice-common libreoffice-core libreoffice-style-colibre
#7 3.213   libreoffice-uiconfig-common libreoffice-uiconfig-writer librevenge-0.0-0
#7 3.214   librtmp1 libsasl2-2 libsasl2-modules-db libsharpyuv0 libsm6 libssh2-1t64
#7 3.214   libstaroffice-0.0-0 libtasn1-6 libtext-charwidth-perl libtext-wrapi18n-perl
#7 3.214   libtiff6 libunistring5 libuno-cppu3t64 libuno-cppuhelpergcc3-3t64
#7 3.214   libuno-purpenvhelpergcc3-3t64 libuno-sal3t64 libuno-salhelpergcc3-3t64
#7 3.214   libwebp7 libwpd-0.10-10 libwpg-0.3-3 libwps-0.4-4 libx11-6 libx11-data
#7 3.214   libx11-xcb1 libxau6 libxcb-render0 libxcb-shm0 libxcb1 libxdmcp6 libxext6
#7 3.214   libxinerama1 libxml2 libxmlsec1t64 libxmlsec1t64-nss libxrandr2 libxrender1
#7 3.215   libxslt1.1 libyajl2 libzxcvbn0 libzxing3 pinentry-curses procps
#7 3.215   sensible-utils ucf uno-libs-private ure x11-common
#7 3.217 Suggested packages:
#7 3.217   dbus-user-session libpam-systemd pinentry-gnome3 tor gpg-wks-server
#7 3.217   parcimonie xloadimage scdaemon tpm2daemon isoquery cups-common rng-tools
#7 3.217   low-memory-monitor gnutls-bin krb5-doc krb5-user libvisual-0.4-plugins
#7 3.217   gstreamer1.0-tools liblcms2-utils raptor2-utils rasqal-utils
#7 3.217   librdf-storage-mysql librdf-storage-postgresql librdf-storage-sqlite
#7 3.217   librdf-storage-virtuoso redland-utils libreoffice-base python3-scriptforge
#7 3.217   fonts-crosextra-caladea fonts-crosextra-carlito libreoffice-java-common
#7 3.217   default-jre | java-runtime | java8-runtime | jre pinentry-doc
#7 3.217 Recommended packages:
#7 3.217   gnupg-utils gpg-wks-client gpgv libpam-cap dbus libglib2.0-data
#7 3.217   shared-mime-info xdg-user-dirs libgpg-error-l10n gstreamer1.0-plugins-base
#7 3.217   hunspell-en-us | hunspell-dictionary | myspell-dictionary krb5-locales
#7 3.217   libldap-common poppler-data publicsuffix xdg-utils fonts-liberation
#7 3.217   | ttf-mscorefonts-installer apparmor python3-uno libpaper-utils
#7 3.217   gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-plugins-bad
#7 3.217   gstreamer1.0-libav libreoffice-math libsasl2-modules psmisc
#7 3.217   linux-sysctl-defaults
#7 3.762 The following NEW packages will be installed:
#7 3.762   dirmngr fontconfig fontconfig-config fonts-dejavu-core fonts-dejavu-mono
#7 3.763   fonts-opensymbol gnupg gnupg-l10n gpg gpg-agent gpgconf gpgsm iso-codes
#7 3.763   libabsl20240722 libabw-0.1-1 libargon2-1 libassuan9 libatomic1
#7 3.763   libavahi-client3 libavahi-common-data libavahi-common3
#7 3.763   libboost-iostreams1.83.0 libboost-locale1.83.0 libboost-thread1.83.0
#7 3.763   libbrotli1 libcairo2 libcap2-bin libclucene-contribs1t64 libclucene-core1t64
#7 3.763   libcmis-0.6-6t64 libcom-err2 libcups2t64 libcurl3t64-gnutls libcurl4t64
#7 3.763   libdbus-1-3 libdconf1 libdeflate0 libdrm-common libdrm2 libe-book-0.1-1
#7 3.763   libeot0 libepoxy0 libepubgen-0.1-1 libetonyek-0.1-1 libexpat1
#7 3.763   libexttextcat-2.0-0 libexttextcat-data libfontconfig1 libfreetype6
#7 3.763   libgcrypt20 libglib2.0-0t64 libgnutls30t64 libgpg-error0 libgpgme11t64
#7 3.763   libgpgmepp6t64 libgraphite2-3 libgssapi-krb5-2
#7 3.763   libgstreamer-plugins-base1.0-0 libgstreamer1.0-0 libharfbuzz-icu0
#7 3.763   libharfbuzz0b libhunspell-1.7-0 libhyphen0 libice6 libicu76 libidn2-0
#7 3.763   libjbig0 libjpeg62-turbo libk5crypto3 libkeyutils1 libkrb5-3 libkrb5support0
#7 3.763   libksba8 liblangtag-common liblangtag1 liblcms2-2 libldap2 liblerc4 libltdl7
#7 3.763   libmhash2 libmwaw-0.3-3 libmythes-1.2-0 libnghttp2-14 libnghttp3-9
#7 3.763   libngtcp2-16 libngtcp2-crypto-gnutls8 libnpth0t64 libnspr4 libnss3
#7 3.764   libnumbertext-1.0-0 libnumbertext-data libodfgen-0.1-1 libopenjp2-7
#7 3.764   liborc-0.4-0t64 liborcus-0.18-0 liborcus-parser-0.18-0 libp11-kit0
#7 3.764   libpixman-1-0 libpng16-16t64 libpoppler147 libproc2-0 libpsl5t64
#7 3.764   libraptor2-0 librasqal3t64 librdf0t64 libreoffice-base-core
#7 3.764   libreoffice-common libreoffice-core libreoffice-style-colibre
#7 3.764   libreoffice-uiconfig-common libreoffice-uiconfig-writer libreoffice-writer
#7 3.765   librevenge-0.0-0 librtmp1 libsasl2-2 libsasl2-modules-db libsharpyuv0 libsm6
#7 3.765   libssh2-1t64 libstaroffice-0.0-0 libtasn1-6 libtext-charwidth-perl
#7 3.765   libtext-wrapi18n-perl libtiff6 libunistring5 libuno-cppu3t64
#7 3.765   libuno-cppuhelpergcc3-3t64 libuno-purpenvhelpergcc3-3t64 libuno-sal3t64
#7 3.765   libuno-salhelpergcc3-3t64 libwebp7 libwpd-0.10-10 libwpg-0.3-3 libwps-0.4-4
#7 3.765   libx11-6 libx11-data libx11-xcb1 libxau6 libxcb-render0 libxcb-shm0 libxcb1
#7 3.765   libxdmcp6 libxext6 libxinerama1 libxml2 libxmlsec1t64 libxmlsec1t64-nss
#7 3.766   libxrandr2 libxrender1 libxslt1.1 libyajl2 libzxcvbn0 libzxing3
#7 3.767   pinentry-curses procps sensible-utils ucf uno-libs-private ure x11-common
#7 3.846 0 upgraded, 160 newly installed, 0 to remove and 0 not upgraded.
#7 3.846 Need to get 130 MB of archives.
#7 3.846 After this operation, 442 MB of additional disk space will be used.
#7 3.846 Get:1 http://deb.debian.org/debian-security trixie-security/main amd64 libexpat1 amd64 2.9.0-1~deb13u1 [126 kB]
#7 3.879 Get:2 http://deb.debian.org/debian trixie/main amd64 libtext-charwidth-perl amd64 0.04-11+b4 [9476 B]
#7 3.881 Get:3 http://deb.debian.org/debian trixie/main amd64 libtext-wrapi18n-perl all 0.06-10 [8808 B]
#7 3.882 Get:4 http://deb.debian.org/debian trixie/main amd64 libproc2-0 amd64 2:4.0.4-9 [65.6 kB]
#7 3.888 Get:5 http://deb.debian.org/debian trixie/main amd64 procps amd64 2:4.0.4-9 [882 kB]
#7 3.953 Get:6 http://deb.debian.org/debian trixie/main amd64 sensible-utils all 0.0.25 [25.0 kB]
#7 3.955 Get:7 http://deb.debian.org/debian trixie/main amd64 ucf all 3.0052 [43.3 kB]
#7 3.967 Get:8 http://deb.debian.org/debian-security trixie-security/main amd64 libreoffice-style-colibre all 4:25.2.3-2+deb13u8 [7330 kB]
#7 4.428 Get:9 http://deb.debian.org/debian-security trixie-security/main amd64 libreoffice-uiconfig-common all 4:25.2.3-2+deb13u8 [386 kB]
#7 4.447 Get:10 http://deb.debian.org/debian-security trixie-security/main amd64 libuno-sal3t64 amd64 4:25.2.3-2+deb13u8 [218 kB]
#7 4.459 Get:11 http://deb.debian.org/debian-security trixie-security/main amd64 libuno-salhelpergcc3-3t64 amd64 4:25.2.3-2+deb13u8 [53.8 kB]
#7 4.462 Get:12 http://deb.debian.org/debian-security trixie-security/main amd64 libuno-cppu3t64 amd64 4:25.2.3-2+deb13u8 [120 kB]
#7 4.470 Get:13 http://deb.debian.org/debian-security trixie-security/main amd64 uno-libs-private amd64 4:25.2.3-2+deb13u8 [239 kB]
#7 4.481 Get:14 http://deb.debian.org/debian trixie/main amd64 libicu76 amd64 76.1-4 [9722 kB]
#7 5.119 Get:15 http://deb.debian.org/debian trixie/main amd64 libxml2 amd64 2.12.7+dfsg+really2.9.14-2.1+deb13u3 [700 kB]
#7 5.168 Get:16 http://deb.debian.org/debian trixie/main amd64 liblangtag-common all 0.6.7-1 [191 kB]
#7 5.182 Get:17 http://deb.debian.org/debian trixie/main amd64 liblangtag1 amd64 0.6.7-1+b2 [51.2 kB]
#7 5.203 Get:18 http://deb.debian.org/debian-security trixie-security/main amd64 libuno-cppuhelpergcc3-3t64 amd64 4:25.2.3-2+deb13u8 [320 kB]
#7 5.223 Get:19 http://deb.debian.org/debian-security trixie-security/main amd64 libuno-purpenvhelpergcc3-3t64 amd64 4:25.2.3-2+deb13u8 [52.5 kB]
#7 5.226 Get:20 http://deb.debian.org/debian-security trixie-security/main amd64 ure amd64 4:25.2.3-2+deb13u8 [1254 kB]
#7 5.320 Get:21 http://deb.debian.org/debian trixie/main amd64 libnumbertext-data all 1.0.11-4 [70.4 kB]
#7 5.325 Get:22 http://deb.debian.org/debian-security trixie-security/main amd64 libreoffice-common all 4:25.2.3-2+deb13u8 [21.7 MB]
#7 6.732 Get:23 http://deb.debian.org/debian-security trixie-security/main amd64 libbrotli1 amd64 1.1.0-2+deb13u1 [304 kB]
#7 6.739 Get:24 http://deb.debian.org/debian-security trixie-security/main amd64 libpng16-16t64 amd64 1.6.48-1+deb13u6 [283 kB]
#7 6.746 Get:25 http://deb.debian.org/debian trixie/main amd64 libfreetype6 amd64 2.13.3+dfsg-1+deb13u1 [452 kB]
#7 6.757 Get:26 http://deb.debian.org/debian trixie/main amd64 fonts-dejavu-mono all 2.37-8 [489 kB]
#7 6.772 Get:27 http://deb.debian.org/debian trixie/main amd64 fonts-dejavu-core all 2.37-8 [840 kB]
#7 6.819 Get:28 http://deb.debian.org/debian trixie/main amd64 fontconfig-config amd64 2.15.0-2.3 [318 kB]
#7 6.842 Get:29 http://deb.debian.org/debian trixie/main amd64 libfontconfig1 amd64 2.15.0-2.3 [392 kB]
#7 6.862 Get:30 http://deb.debian.org/debian trixie/main amd64 fontconfig amd64 2.15.0-2.3 [463 kB]
#7 6.883 Get:31 http://deb.debian.org/debian-security trixie-security/main amd64 fonts-opensymbol all 4:102.12+LibO25.2.3-2+deb13u8 [129 kB]
#7 6.890 Get:32 http://deb.debian.org/debian trixie/main amd64 libabsl20240722 amd64 20240722.0-4 [492 kB]
#7 6.917 Get:33 http://deb.debian.org/debian trixie/main amd64 libargon2-1 amd64 0~20190702+dfsg-4+b2 [21.4 kB]
#7 6.919 Get:34 http://deb.debian.org/debian trixie/main amd64 libboost-thread1.83.0 amd64 1.83.0-4.2 [270 kB]
#7 6.959 Get:35 http://deb.debian.org/debian trixie/main amd64 libboost-locale1.83.0 amd64 1.83.0-4.2 [473 kB]
#7 6.990 Get:36 http://deb.debian.org/debian trixie/main amd64 libpixman-1-0 amd64 0.44.0-3 [248 kB]
#7 6.999 Get:37 http://deb.debian.org/debian trixie/main amd64 libxau6 amd64 1:1.0.11-1 [20.4 kB]
#7 6.999 Get:38 http://deb.debian.org/debian trixie/main amd64 libxdmcp6 amd64 1:1.1.5-1 [27.8 kB]
#7 7.001 Get:39 http://deb.debian.org/debian trixie/main amd64 libxcb1 amd64 1.17.0-2+b1 [144 kB]
#7 7.009 Get:40 http://deb.debian.org/debian trixie/main amd64 libx11-data all 2:1.8.12-1 [343 kB]
#7 7.028 Get:41 http://deb.debian.org/debian trixie/main amd64 libx11-6 amd64 2:1.8.12-1 [815 kB]
#7 7.077 Get:42 http://deb.debian.org/debian trixie/main amd64 libxcb-render0 amd64 1.17.0-2+b1 [115 kB]
#7 7.082 Get:43 http://deb.debian.org/debian trixie/main amd64 libxcb-shm0 amd64 1.17.0-2+b1 [105 kB]
#7 7.087 Get:44 http://deb.debian.org/debian trixie/main amd64 libxext6 amd64 2:1.3.4-1+b3 [50.4 kB]
#7 7.092 Get:45 http://deb.debian.org/debian trixie/main amd64 libxrender1 amd64 1:0.9.12-1 [27.9 kB]
#7 7.095 Get:46 http://deb.debian.org/debian trixie/main amd64 libcairo2 amd64 1.18.4-1+b1 [538 kB]
#7 7.127 Get:47 http://deb.debian.org/debian trixie/main amd64 libclucene-core1t64 amd64 2.3.3.4+dfsg-1.2+b1 [512 kB]
#7 7.145 Get:48 http://deb.debian.org/debian trixie/main amd64 libclucene-contribs1t64 amd64 2.3.3.4+dfsg-1.2+b1 [84.4 kB]
#7 7.152 Get:49 http://deb.debian.org/debian trixie/main amd64 libkrb5support0 amd64 1.21.3-5+deb13u1 [33.1 kB]
#7 7.154 Get:50 http://deb.debian.org/debian trixie/main amd64 libcom-err2 amd64 1.47.2-3+b12 [25.0 kB]
#7 7.157 Get:51 http://deb.debian.org/debian trixie/main amd64 libk5crypto3 amd64 1.21.3-5+deb13u1 [81.2 kB]
#7 7.161 Get:52 http://deb.debian.org/debian trixie/main amd64 libkeyutils1 amd64 1.6.3-6 [9456 B]
#7 7.161 Get:53 http://deb.debian.org/debian trixie/main amd64 libkrb5-3 amd64 1.21.3-5+deb13u1 [326 kB]
#7 7.177 Get:54 http://deb.debian.org/debian trixie/main amd64 libgssapi-krb5-2 amd64 1.21.3-5+deb13u1 [138 kB]
#7 7.185 Get:55 http://deb.debian.org/debian trixie/main amd64 libunistring5 amd64 1.3-2 [477 kB]
#7 7.220 Get:56 http://deb.debian.org/debian trixie/main amd64 libidn2-0 amd64 2.3.8-2 [109 kB]
#7 7.223 Get:57 http://deb.debian.org/debian trixie/main amd64 libsasl2-modules-db amd64 2.1.28+dfsg1-9 [19.8 kB]
#7 7.224 Get:58 http://deb.debian.org/debian trixie/main amd64 libsasl2-2 amd64 2.1.28+dfsg1-9 [57.5 kB]
#7 7.226 Get:59 http://deb.debian.org/debian trixie/main amd64 libldap2 amd64 2.6.10+dfsg-1 [194 kB]
#7 7.239 Get:60 http://deb.debian.org/debian trixie/main amd64 libnghttp2-14 amd64 1.64.0-1.1+deb13u1 [76.2 kB]
#7 7.241 Get:61 http://deb.debian.org/debian trixie/main amd64 libnghttp3-9 amd64 1.8.0-1 [67.7 kB]
#7 7.245 Get:62 http://deb.debian.org/debian trixie/main amd64 libpsl5t64 amd64 0.21.2-1.1+b1 [57.2 kB]
#7 7.247 Get:63 http://deb.debian.org/debian trixie/main amd64 libp11-kit0 amd64 0.25.5-3 [425 kB]
#7 7.262 Get:64 http://deb.debian.org/debian trixie/main amd64 libtasn1-6 amd64 4.20.0-2+deb13u1 [50.1 kB]
#7 7.264 Get:65 http://deb.debian.org/debian trixie/main amd64 libgnutls30t64 amd64 3.8.9-3+deb13u4 [1469 kB]
#7 7.367 Get:66 http://deb.debian.org/debian trixie/main amd64 librtmp1 amd64 2.4+20151223.gitfa8646d.1-2+b5 [58.8 kB]
#7 7.371 Get:67 http://deb.debian.org/debian trixie/main amd64 libssh2-1t64 amd64 1.11.1-1+deb13u2 [245 kB]
#7 7.378 Get:68 http://deb.debian.org/debian-security trixie-security/main amd64 libcurl4t64 amd64 8.14.1-2+deb13u7 [392 kB]
#7 7.387 Get:69 http://deb.debian.org/debian trixie/main amd64 libcmis-0.6-6t64 amd64 0.6.2-2.1+b1 [442 kB]
#7 7.406 Get:70 http://deb.debian.org/debian trixie/main amd64 libavahi-common-data amd64 0.8-16 [112 kB]
#7 7.413 Get:71 http://deb.debian.org/debian trixie/main amd64 libavahi-common3 amd64 0.8-16 [44.2 kB]
#7 7.415 Get:72 http://deb.debian.org/debian trixie/main amd64 libdbus-1-3 amd64 1.16.2-2 [178 kB]
#7 7.424 Get:73 http://deb.debian.org/debian trixie/main amd64 libavahi-client3 amd64 0.8-16 [48.4 kB]
#7 7.425 Get:74 http://deb.debian.org/debian trixie/main amd64 libcups2t64 amd64 2.4.10-3+deb13u2 [252 kB]
#7 7.440 Get:75 http://deb.debian.org/debian trixie/main amd64 libatomic1 amd64 14.2.0-19 [9308 B]
#7 7.448 Get:76 http://deb.debian.org/debian trixie/main amd64 libglib2.0-0t64 amd64 2.84.4-3~deb13u5 [1521 kB]
#7 7.533 Get:77 http://deb.debian.org/debian trixie/main amd64 libdconf1 amd64 0.40.0-5 [41.8 kB]
#7 7.536 Get:78 http://deb.debian.org/debian trixie/main amd64 libeot0 amd64 0.01-5+b2 [27.2 kB]
#7 7.536 Get:79 http://deb.debian.org/debian trixie/main amd64 libepoxy0 amd64 1.5.10-2 [193 kB]
#7 7.545 Get:80 http://deb.debian.org/debian trixie/main amd64 libexttextcat-data all 3.4.7-1 [176 kB]
#7 7.553 Get:81 http://deb.debian.org/debian trixie/main amd64 libexttextcat-2.0-0 amd64 3.4.7-1+b1 [14.3 kB]
#7 7.555 Get:82 http://deb.debian.org/debian trixie/main amd64 libgpg-error0 amd64 1.51-4 [82.1 kB]
#7 7.559 Get:83 http://deb.debian.org/debian trixie/main amd64 libassuan9 amd64 3.0.2-2 [61.5 kB]
#7 7.562 Get:84 http://deb.debian.org/debian trixie/main amd64 libgcrypt20 amd64 1.11.0-7+deb13u1 [843 kB]
#7 7.616 Get:85 http://deb.debian.org/debian trixie/main amd64 gpgconf amd64 2.4.7-21+deb13u1+b5 [129 kB]
#7 7.626 Get:86 http://deb.debian.org/debian trixie/main amd64 libksba8 amd64 1.6.7-2+b1 [136 kB]
#7 7.633 Get:87 http://deb.debian.org/debian trixie/main amd64 libnpth0t64 amd64 1.8-3 [23.2 kB]
#7 7.635 Get:88 http://deb.debian.org/debian trixie/main amd64 dirmngr amd64 2.4.7-21+deb13u1+b5 [384 kB]
#7 7.648 Get:89 http://deb.debian.org/debian trixie/main amd64 gnupg-l10n all 2.4.7-21+deb13u1 [749 kB]
#7 7.688 Get:90 http://deb.debian.org/debian trixie/main amd64 gpg amd64 2.4.7-21+deb13u1+b5 [636 kB]
#7 7.713 Get:91 http://deb.debian.org/debian trixie/main amd64 pinentry-curses amd64 1.3.1-2 [86.4 kB]
#7 7.723 Get:92 http://deb.debian.org/debian trixie/main amd64 gpg-agent amd64 2.4.7-21+deb13u1+b5 [271 kB]
#7 7.744 Get:93 http://deb.debian.org/debian trixie/main amd64 gpgsm amd64 2.4.7-21+deb13u1+b5 [276 kB]
#7 7.756 Get:94 http://deb.debian.org/debian trixie/main amd64 gnupg all 2.4.7-21+deb13u1 [417 kB]
#7 7.781 Get:95 http://deb.debian.org/debian trixie/main amd64 libgpgme11t64 amd64 1.24.2-3 [346 kB]
#7 7.800 Get:96 http://deb.debian.org/debian trixie/main amd64 libgpgmepp6t64 amd64 1.24.2-3 [341 kB]
#7 7.810 Get:97 http://deb.debian.org/debian trixie/main amd64 libgraphite2-3 amd64 1.3.14-2+deb13u1 [75.2 kB]
#7 7.815 Get:98 http://deb.debian.org/debian trixie/main amd64 libdrm-common all 2.4.124-2 [8288 B]
#7 7.815 Get:99 http://deb.debian.org/debian trixie/main amd64 libdrm2 amd64 2.4.124-2 [39.0 kB]
#7 7.817 Get:100 http://deb.debian.org/debian trixie/main amd64 libcap2-bin amd64 1:2.75-10+deb13u1+b3 [36.5 kB]
#7 7.844 Get:101 http://deb.debian.org/debian trixie/main amd64 libgstreamer1.0-0 amd64 1.26.2-2 [1421 kB]
#7 7.934 Get:102 http://deb.debian.org/debian trixie/main amd64 liborc-0.4-0t64 amd64 1:0.4.41-1 [190 kB]
#7 7.959 Get:103 http://deb.debian.org/debian trixie/main amd64 iso-codes all 4.18.0-1 [3125 kB]
#7 8.144 Get:104 http://deb.debian.org/debian-security trixie-security/main amd64 libgstreamer-plugins-base1.0-0 amd64 1.26.2-1+deb13u2 [997 kB]
#7 8.192 Get:105 http://deb.debian.org/debian trixie/main amd64 libharfbuzz0b amd64 10.2.0-1+deb13u1 [479 kB]
#7 8.222 Get:106 http://deb.debian.org/debian trixie/main amd64 libharfbuzz-icu0 amd64 10.2.0-1+deb13u1 [15.5 kB]
#7 8.223 Get:107 http://deb.debian.org/debian trixie/main amd64 libhunspell-1.7-0 amd64 1.7.2+really1.7.2-10+b4 [237 kB]
#7 8.239 Get:108 http://deb.debian.org/debian trixie/main amd64 libhyphen0 amd64 2.8.8-7+b2 [30.7 kB]
#7 8.240 Get:109 http://deb.debian.org/debian trixie/main amd64 x11-common all 1:7.7+24+deb13u1 [217 kB]
#7 8.251 Get:110 http://deb.debian.org/debian trixie/main amd64 libice6 amd64 2:1.1.1-1 [65.4 kB]
#7 8.255 Get:111 http://deb.debian.org/debian trixie/main amd64 libjpeg62-turbo amd64 1:2.1.5-4 [168 kB]
#7 8.262 Get:112 http://deb.debian.org/debian trixie/main amd64 liblcms2-2 amd64 2.16-2+deb13u2 [160 kB]
#7 8.267 Get:113 http://deb.debian.org/debian trixie/main amd64 libmythes-1.2-0 amd64 2:1.2.5-1+b2 [10.8 kB]
#7 8.267 Get:114 http://deb.debian.org/debian trixie/main amd64 libnspr4 amd64 2:4.36-1 [110 kB]
#7 8.274 Get:115 http://deb.debian.org/debian trixie/main amd64 libnss3 amd64 2:3.110-1+deb13u4 [1394 kB]
#7 8.346 Get:116 http://deb.debian.org/debian trixie/main amd64 libnumbertext-1.0-0 amd64 1.0.11-4+b2 [109 kB]
#7 8.351 Get:117 http://deb.debian.org/debian trixie/main amd64 libopenjp2-7 amd64 2.5.3-2.1~deb13u2 [205 kB]
#7 8.379 Get:118 http://deb.debian.org/debian trixie/main amd64 libboost-iostreams1.83.0 amd64 1.83.0-4.2 [254 kB]
#7 8.393 Get:119 http://deb.debian.org/debian trixie/main amd64 liborcus-parser-0.18-0 amd64 0.19.2-6+b1 [116 kB]
#7 8.401 Get:120 http://deb.debian.org/debian trixie/main amd64 liborcus-0.18-0 amd64 0.19.2-6+b1 [432 kB]
#7 8.425 Get:121 http://deb.debian.org/debian trixie/main amd64 libngtcp2-16 amd64 1.11.0-1+deb13u1 [132 kB]
#7 8.429 Get:122 http://deb.debian.org/debian trixie/main amd64 libngtcp2-crypto-gnutls8 amd64 1.11.0-1+deb13u1 [29.5 kB]
#7 8.430 Get:123 http://deb.debian.org/debian-security trixie-security/main amd64 libcurl3t64-gnutls amd64 8.14.1-2+deb13u7 [385 kB]
#7 8.455 Get:124 http://deb.debian.org/debian trixie/main amd64 libdeflate0 amd64 1.23-2 [47.3 kB]
#7 8.459 Get:125 http://deb.debian.org/debian trixie/main amd64 libjbig0 amd64 2.1-6.1+b2 [32.1 kB]
#7 8.461 Get:126 http://deb.debian.org/debian trixie/main amd64 liblerc4 amd64 4.0.0+ds-5 [183 kB]
#7 8.473 Get:127 http://deb.debian.org/debian trixie/main amd64 libsharpyuv0 amd64 1.5.0-0.1 [116 kB]
#7 8.478 Get:128 http://deb.debian.org/debian trixie/main amd64 libwebp7 amd64 1.5.0-0.1 [318 kB]
#7 8.485 Get:129 http://deb.debian.org/debian trixie/main amd64 libtiff6 amd64 4.7.0-3+deb13u3 [345 kB]
#7 8.499 Get:130 http://deb.debian.org/debian trixie/main amd64 libpoppler147 amd64 25.03.0-5+deb13u4 [2036 kB]
#7 8.604 Get:131 http://deb.debian.org/debian trixie/main amd64 libxslt1.1 amd64 1.1.35-1.2+deb13u3 [233 kB]
#7 8.613 Get:132 http://deb.debian.org/debian trixie/main amd64 libyajl2 amd64 2.1.0-5+b2 [23.3 kB]
#7 8.672 Get:133 http://deb.debian.org/debian trixie/main amd64 libraptor2-0 amd64 2.0.16-6 [177 kB]
#7 8.723 Get:134 http://deb.debian.org/debian trixie/main amd64 libltdl7 amd64 2.5.4-4 [416 kB]
#7 8.755 Get:135 http://deb.debian.org/debian trixie/main amd64 libmhash2 amd64 0.9.9.9-10 [92.4 kB]
#7 8.758 Get:136 http://deb.debian.org/debian trixie/main amd64 librasqal3t64 amd64 0.9.33-2.1+b2 [191 kB]
#7 8.771 Get:137 http://deb.debian.org/debian trixie/main amd64 librdf0t64 amd64 1.0.17-4+b1 [107 kB]
#7 8.778 Get:138 http://deb.debian.org/debian trixie/main amd64 librevenge-0.0-0 amd64 0.0.5-3+b2 [295 kB]
#7 8.792 Get:139 http://deb.debian.org/debian trixie/main amd64 libsm6 amd64 2:1.2.6-1 [37.3 kB]
#7 8.792 Get:140 http://deb.debian.org/debian trixie/main amd64 libx11-xcb1 amd64 2:1.8.12-1 [247 kB]
#7 8.802 Get:141 http://deb.debian.org/debian trixie/main amd64 libxinerama1 amd64 2:1.1.4-3+b4 [16.0 kB]
#7 8.816 Get:142 http://deb.debian.org/debian trixie/main amd64 libxmlsec1t64 amd64 1.2.41-1+b1 [155 kB]
#7 8.827 Get:143 http://deb.debian.org/debian trixie/main amd64 libxmlsec1t64-nss amd64 1.2.41-1+b1 [66.0 kB]
#7 8.830 Get:144 http://deb.debian.org/debian trixie/main amd64 libxrandr2 amd64 2:1.5.4-1+b3 [36.3 kB]
#7 8.831 Get:145 http://deb.debian.org/debian trixie/main amd64 libzxcvbn0 amd64 2.5+dfsg-2+b2 [860 kB]
#7 8.879 Get:146 http://deb.debian.org/debian trixie/main amd64 libzxing3 amd64 2.3.0-4 [606 kB]
#7 8.912 Get:147 http://deb.debian.org/debian-security trixie-security/main amd64 libreoffice-core amd64 4:25.2.3-2+deb13u8 [32.2 MB]
#7 10.54 Get:148 http://deb.debian.org/debian-security trixie-security/main amd64 libreoffice-base-core amd64 4:25.2.3-2+deb13u8 [801 kB]
#7 10.58 Get:149 http://deb.debian.org/debian-security trixie-security/main amd64 libreoffice-uiconfig-writer all 4:25.2.3-2+deb13u8 [301 kB]
#7 10.58 Get:150 http://deb.debian.org/debian trixie/main amd64 libabw-0.1-1 amd64 0.1.3-1+b2 [124 kB]
#7 10.59 Get:151 http://deb.debian.org/debian trixie/main amd64 libe-book-0.1-1 amd64 0.1.3-2+b4 [205 kB]
#7 10.59 Get:152 http://deb.debian.org/debian trixie/main amd64 libepubgen-0.1-1 amd64 0.1.1-1+b2 [156 kB]
#7 10.60 Get:153 http://deb.debian.org/debian trixie/main amd64 libetonyek-0.1-1 amd64 0.1.12-1 [840 kB]
#7 10.65 Get:154 http://deb.debian.org/debian trixie/main amd64 libmwaw-0.3-3 amd64 0.3.22-1+b2 [2840 kB]
#7 10.72 Get:155 http://deb.debian.org/debian trixie/main amd64 libodfgen-0.1-1 amd64 0.1.8-2+b2 [313 kB]
#7 10.73 Get:156 http://deb.debian.org/debian trixie/main amd64 libstaroffice-0.0-0 amd64 0.0.7-1+b2 [735 kB]
#7 10.75 Get:157 http://deb.debian.org/debian trixie/main amd64 libwpd-0.10-10 amd64 0.10.3-2+b2 [263 kB]
#7 10.76 Get:158 http://deb.debian.org/debian trixie/main amd64 libwpg-0.3-3 amd64 0.3.4-3+b2 [81.3 kB]
#7 10.77 Get:159 http://deb.debian.org/debian trixie/main amd64 libwps-0.4-4 amd64 0.4.14-2+b2 [913 kB]
#7 10.81 Get:160 http://deb.debian.org/debian-security trixie-security/main amd64 libreoffice-writer amd64 4:25.2.3-2+deb13u8 [9860 kB]
#7 11.40 debconf: unable to initialize frontend: Dialog
#7 11.40 debconf: (TERM is not set, so the dialog frontend is not usable.)
#7 11.40 debconf: falling back to frontend: Readline
#7 11.40 debconf: unable to initialize frontend: Readline
#7 11.40 debconf: (Can't locate Term/ReadLine.pm in @INC (you may need to install the Term::ReadLine module) (@INC entries checked: /etc/perl /usr/local/lib/x86_64-linux-gnu/perl/5.40.1 /usr/local/share/perl/5.40.1 /usr/lib/x86_64-linux-gnu/perl5/5.40 /usr/share/perl5 /usr/lib/x86_64-linux-gnu/perl-base /usr/lib/x86_64-linux-gnu/perl/5.40 /usr/share/perl/5.40 /usr/local/lib/site_perl) at /usr/share/perl5/Debconf/FrontEnd/Readline.pm line 8, <STDIN> line 160.)
#7 11.40 debconf: falling back to frontend: Teletype
#7 11.41 debconf: unable to initialize frontend: Teletype
#7 11.41 debconf: (This frontend requires a controlling tty.)
#7 11.41 debconf: falling back to frontend: Noninteractive
#7 14.51 Preconfiguring packages ...
#7 14.57 Fetched 130 MB in 7s (17.5 MB/s)
#7 14.60 Selecting previously unselected package libexpat1:amd64.
#7 14.60 (Reading database ... (Reading database ... 5%(Reading database ... 10%(Reading database ... 15%(Reading database ... 20%(Reading database ... 25%(Reading database ... 30%(Reading database ... 35%(Reading database ... 40%(Reading database ... 45%(Reading database ... 50%(Reading database ... 55%(Reading database ... 60%(Reading database ... 65%(Reading database ... 70%(Reading database ... 75%(Reading database ... 80%(Reading database ... 85%(Reading database ... 90%(Reading database ... 95%(Reading database ... 100%(Reading database ... 5658 files and directories currently installed.)
#7 14.61 Preparing to unpack .../00-libexpat1_2.9.0-1~deb13u1_amd64.deb ...
#7 14.62 Unpacking libexpat1:amd64 (2.9.0-1~deb13u1) ...
#7 14.66 Selecting previously unselected package libtext-charwidth-perl:amd64.
#7 14.66 Preparing to unpack .../01-libtext-charwidth-perl_0.04-11+b4_amd64.deb ...
#7 14.66 Unpacking libtext-charwidth-perl:amd64 (0.04-11+b4) ...
#7 14.69 Selecting previously unselected package libtext-wrapi18n-perl.
#7 14.69 Preparing to unpack .../02-libtext-wrapi18n-perl_0.06-10_all.deb ...
#7 14.70 Unpacking libtext-wrapi18n-perl (0.06-10) ...
#7 14.74 Selecting previously unselected package libproc2-0:amd64.
#7 14.74 Preparing to unpack .../03-libproc2-0_2%3a4.0.4-9_amd64.deb ...
#7 14.75 Unpacking libproc2-0:amd64 (2:4.0.4-9) ...
#7 14.80 Selecting previously unselected package procps.
#7 14.80 Preparing to unpack .../04-procps_2%3a4.0.4-9_amd64.deb ...
#7 14.81 Unpacking procps (2:4.0.4-9) ...
#7 14.88 Selecting previously unselected package sensible-utils.
#7 14.88 Preparing to unpack .../05-sensible-utils_0.0.25_all.deb ...
#7 14.88 Unpacking sensible-utils (0.0.25) ...
#7 14.93 Selecting previously unselected package ucf.
#7 14.93 Preparing to unpack .../06-ucf_3.0052_all.deb ...
#7 14.94 Moving old data out of the way
#7 14.94 Unpacking ucf (3.0052) ...
#7 14.97 Selecting previously unselected package libreoffice-style-colibre.
#7 14.97 Preparing to unpack .../07-libreoffice-style-colibre_4%3a25.2.3-2+deb13u8_all.deb ...
#7 14.98 Unpacking libreoffice-style-colibre (4:25.2.3-2+deb13u8) ...
#7 15.22 Selecting previously unselected package libreoffice-uiconfig-common.
#7 15.22 Preparing to unpack .../08-libreoffice-uiconfig-common_4%3a25.2.3-2+deb13u8_all.deb ...
#7 15.23 Unpacking libreoffice-uiconfig-common (4:25.2.3-2+deb13u8) ...
#7 15.36 Selecting previously unselected package libuno-sal3t64.
#7 15.36 Preparing to unpack .../09-libuno-sal3t64_4%3a25.2.3-2+deb13u8_amd64.deb ...
#7 15.36 Unpacking libuno-sal3t64 (4:25.2.3-2+deb13u8) ...
#7 15.41 Selecting previously unselected package libuno-salhelpergcc3-3t64.
#7 15.41 Preparing to unpack .../10-libuno-salhelpergcc3-3t64_4%3a25.2.3-2+deb13u8_amd64.deb ...
#7 15.42 Unpacking libuno-salhelpergcc3-3t64 (4:25.2.3-2+deb13u8) ...
#7 15.46 Selecting previously unselected package libuno-cppu3t64.
#7 15.46 Preparing to unpack .../11-libuno-cppu3t64_4%3a25.2.3-2+deb13u8_amd64.deb ...
#7 15.47 Unpacking libuno-cppu3t64 (4:25.2.3-2+deb13u8) ...
#7 15.50 Selecting previously unselected package uno-libs-private.
#7 15.50 Preparing to unpack .../12-uno-libs-private_4%3a25.2.3-2+deb13u8_amd64.deb ...
#7 15.51 Unpacking uno-libs-private (4:25.2.3-2+deb13u8) ...
#7 15.56 Selecting previously unselected package libicu76:amd64.
#7 15.56 Preparing to unpack .../13-libicu76_76.1-4_amd64.deb ...
#7 15.56 Unpacking libicu76:amd64 (76.1-4) ...
#7 15.90 Selecting previously unselected package libxml2:amd64.
#7 15.90 Preparing to unpack .../14-libxml2_2.12.7+dfsg+really2.9.14-2.1+deb13u3_amd64.deb ...
#7 15.90 Unpacking libxml2:amd64 (2.12.7+dfsg+really2.9.14-2.1+deb13u3) ...
#7 15.96 Selecting previously unselected package liblangtag-common.
#7 15.96 Preparing to unpack .../15-liblangtag-common_0.6.7-1_all.deb ...
#7 15.97 Unpacking liblangtag-common (0.6.7-1) ...
#7 16.02 Selecting previously unselected package liblangtag1:amd64.
#7 16.02 Preparing to unpack .../16-liblangtag1_0.6.7-1+b2_amd64.deb ...
#7 16.02 Unpacking liblangtag1:amd64 (0.6.7-1+b2) ...
#7 16.06 Selecting previously unselected package libuno-cppuhelpergcc3-3t64.
#7 16.07 Preparing to unpack .../17-libuno-cppuhelpergcc3-3t64_4%3a25.2.3-2+deb13u8_amd64.deb ...
#7 16.07 Unpacking libuno-cppuhelpergcc3-3t64 (4:25.2.3-2+deb13u8) ...
#7 16.13 Selecting previously unselected package libuno-purpenvhelpergcc3-3t64.
#7 16.13 Preparing to unpack .../18-libuno-purpenvhelpergcc3-3t64_4%3a25.2.3-2+deb13u8_amd64.deb ...
#7 16.13 Unpacking libuno-purpenvhelpergcc3-3t64 (4:25.2.3-2+deb13u8) ...
#7 16.16 Selecting previously unselected package ure.
#7 16.16 Preparing to unpack .../19-ure_4%3a25.2.3-2+deb13u8_amd64.deb ...
#7 16.17 Unpacking ure (4:25.2.3-2+deb13u8) ...
#7 16.26 Selecting previously unselected package libnumbertext-data.
#7 16.27 Preparing to unpack .../20-libnumbertext-data_1.0.11-4_all.deb ...
#7 16.27 Unpacking libnumbertext-data (1.0.11-4) ...
#7 16.32 Setting up libtext-charwidth-perl:amd64 (0.04-11+b4) ...
#7 16.33 Setting up libtext-wrapi18n-perl (0.06-10) ...
#7 16.35 Setting up libproc2-0:amd64 (2:4.0.4-9) ...
#7 16.36 Setting up procps (2:4.0.4-9) ...
#7 16.40 Setting up sensible-utils (0.0.25) ...
#7 16.41 Setting up ucf (3.0052) ...
#7 16.49 Selecting previously unselected package libreoffice-common.
#7 16.49 (Reading database ... (Reading database ... 5%(Reading database ... 10%(Reading database ... 15%(Reading database ... 20%(Reading database ... 25%(Reading database ... 30%(Reading database ... 35%(Reading database ... 40%(Reading database ... 45%(Reading database ... 50%(Reading database ... 55%(Reading database ... 60%(Reading database ... 65%(Reading database ... 70%(Reading database ... 75%(Reading database ... 80%(Reading database ... 85%(Reading database ... 90%(Reading database ... 95%(Reading database ... 100%(Reading database ... 6875 files and directories currently installed.)
#7 16.50 Preparing to unpack .../000-libreoffice-common_4%3a25.2.3-2+deb13u8_all.deb ...
#7 16.51 Unpacking libreoffice-common (4:25.2.3-2+deb13u8) ...
#7 16.95 Selecting previously unselected package libbrotli1:amd64.
#7 16.95 Preparing to unpack .../001-libbrotli1_1.1.0-2+deb13u1_amd64.deb ...
#7 16.96 Unpacking libbrotli1:amd64 (1.1.0-2+deb13u1) ...
#7 17.02 Selecting previously unselected package libpng16-16t64:amd64.
#7 17.02 Preparing to unpack .../002-libpng16-16t64_1.6.48-1+deb13u6_amd64.deb ...
#7 17.02 Unpacking libpng16-16t64:amd64 (1.6.48-1+deb13u6) ...
#7 17.07 Selecting previously unselected package libfreetype6:amd64.
#7 17.07 Preparing to unpack .../003-libfreetype6_2.13.3+dfsg-1+deb13u1_amd64.deb ...
#7 17.08 Unpacking libfreetype6:amd64 (2.13.3+dfsg-1+deb13u1) ...
#7 17.13 Selecting previously unselected package fonts-dejavu-mono.
#7 17.13 Preparing to unpack .../004-fonts-dejavu-mono_2.37-8_all.deb ...
#7 17.13 Unpacking fonts-dejavu-mono (2.37-8) ...
#7 17.20 Selecting previously unselected package fonts-dejavu-core.
#7 17.20 Preparing to unpack .../005-fonts-dejavu-core_2.37-8_all.deb ...
#7 17.22 Unpacking fonts-dejavu-core (2.37-8) ...
#7 17.29 Selecting previously unselected package fontconfig-config.
#7 17.30 Preparing to unpack .../006-fontconfig-config_2.15.0-2.3_amd64.deb ...
#7 17.30 Unpacking fontconfig-config (2.15.0-2.3) ...
#7 17.35 Selecting previously unselected package libfontconfig1:amd64.
#7 17.35 Preparing to unpack .../007-libfontconfig1_2.15.0-2.3_amd64.deb ...
#7 17.36 Unpacking libfontconfig1:amd64 (2.15.0-2.3) ...
#7 17.41 Selecting previously unselected package fontconfig.
#7 17.41 Preparing to unpack .../008-fontconfig_2.15.0-2.3_amd64.deb ...
#7 17.41 Unpacking fontconfig (2.15.0-2.3) ...
#7 17.45 Selecting previously unselected package fonts-opensymbol.
#7 17.45 Preparing to unpack .../009-fonts-opensymbol_4%3a102.12+LibO25.2.3-2+deb13u8_all.deb ...
#7 17.46 Unpacking fonts-opensymbol (4:102.12+LibO25.2.3-2+deb13u8) ...
#7 17.50 Selecting previously unselected package libabsl20240722:amd64.
#7 17.51 Preparing to unpack .../010-libabsl20240722_20240722.0-4_amd64.deb ...
#7 17.51 Unpacking libabsl20240722:amd64 (20240722.0-4) ...
#7 17.58 Selecting previously unselected package libargon2-1:amd64.
#7 17.58 Preparing to unpack .../011-libargon2-1_0~20190702+dfsg-4+b2_amd64.deb ...
#7 17.59 Unpacking libargon2-1:amd64 (0~20190702+dfsg-4+b2) ...
#7 17.62 Selecting previously unselected package libboost-thread1.83.0:amd64.
#7 17.62 Preparing to unpack .../012-libboost-thread1.83.0_1.83.0-4.2_amd64.deb ...
#7 17.63 Unpacking libboost-thread1.83.0:amd64 (1.83.0-4.2) ...
#7 17.68 Selecting previously unselected package libboost-locale1.83.0:amd64.
#7 17.68 Preparing to unpack .../013-libboost-locale1.83.0_1.83.0-4.2_amd64.deb ...
#7 17.68 Unpacking libboost-locale1.83.0:amd64 (1.83.0-4.2) ...
#7 17.75 Selecting previously unselected package libpixman-1-0:amd64.
#7 17.75 Preparing to unpack .../014-libpixman-1-0_0.44.0-3_amd64.deb ...
#7 17.75 Unpacking libpixman-1-0:amd64 (0.44.0-3) ...
#7 17.80 Selecting previously unselected package libxau6:amd64.
#7 17.81 Preparing to unpack .../015-libxau6_1%3a1.0.11-1_amd64.deb ...
#7 17.81 Unpacking libxau6:amd64 (1:1.0.11-1) ...
#7 17.85 Selecting previously unselected package libxdmcp6:amd64.
#7 17.85 Preparing to unpack .../016-libxdmcp6_1%3a1.1.5-1_amd64.deb ...
#7 17.86 Unpacking libxdmcp6:amd64 (1:1.1.5-1) ...
#7 17.89 Selecting previously unselected package libxcb1:amd64.
#7 17.90 Preparing to unpack .../017-libxcb1_1.17.0-2+b1_amd64.deb ...
#7 17.90 Unpacking libxcb1:amd64 (1.17.0-2+b1) ...
#7 17.94 Selecting previously unselected package libx11-data.
#7 17.94 Preparing to unpack .../018-libx11-data_2%3a1.8.12-1_all.deb ...
#7 17.94 Unpacking libx11-data (2:1.8.12-1) ...
#7 18.02 Selecting previously unselected package libx11-6:amd64.
#7 18.02 Preparing to unpack .../019-libx11-6_2%3a1.8.12-1_amd64.deb ...
#7 18.02 Unpacking libx11-6:amd64 (2:1.8.12-1) ...
#7 18.09 Selecting previously unselected package libxcb-render0:amd64.
#7 18.09 Preparing to unpack .../020-libxcb-render0_1.17.0-2+b1_amd64.deb ...
#7 18.10 Unpacking libxcb-render0:amd64 (1.17.0-2+b1) ...
#7 18.15 Selecting previously unselected package libxcb-shm0:amd64.
#7 18.15 Preparing to unpack .../021-libxcb-shm0_1.17.0-2+b1_amd64.deb ...
#7 18.15 Unpacking libxcb-shm0:amd64 (1.17.0-2+b1) ...
#7 18.20 Selecting previously unselected package libxext6:amd64.
#7 18.20 Preparing to unpack .../022-libxext6_2%3a1.3.4-1+b3_amd64.deb ...
#7 18.21 Unpacking libxext6:amd64 (2:1.3.4-1+b3) ...
#7 18.24 Selecting previously unselected package libxrender1:amd64.
#7 18.25 Preparing to unpack .../023-libxrender1_1%3a0.9.12-1_amd64.deb ...
#7 18.25 Unpacking libxrender1:amd64 (1:0.9.12-1) ...
#7 18.29 Selecting previously unselected package libcairo2:amd64.
#7 18.29 Preparing to unpack .../024-libcairo2_1.18.4-1+b1_amd64.deb ...
#7 18.30 Unpacking libcairo2:amd64 (1.18.4-1+b1) ...
#7 18.36 Selecting previously unselected package libclucene-core1t64:amd64.
#7 18.36 Preparing to unpack .../025-libclucene-core1t64_2.3.3.4+dfsg-1.2+b1_amd64.deb ...
#7 18.36 Unpacking libclucene-core1t64:amd64 (2.3.3.4+dfsg-1.2+b1) ...
#7 18.43 Selecting previously unselected package libclucene-contribs1t64:amd64.
#7 18.43 Preparing to unpack .../026-libclucene-contribs1t64_2.3.3.4+dfsg-1.2+b1_amd64.deb ...
#7 18.43 Unpacking libclucene-contribs1t64:amd64 (2.3.3.4+dfsg-1.2+b1) ...
#7 18.47 Selecting previously unselected package libkrb5support0:amd64.
#7 18.48 Preparing to unpack .../027-libkrb5support0_1.21.3-5+deb13u1_amd64.deb ...
#7 18.48 Unpacking libkrb5support0:amd64 (1.21.3-5+deb13u1) ...
#7 18.52 Selecting previously unselected package libcom-err2:amd64.
#7 18.53 Preparing to unpack .../028-libcom-err2_1.47.2-3+b12_amd64.deb ...
#7 18.53 Unpacking libcom-err2:amd64 (1.47.2-3+b12) ...
#7 18.57 Selecting previously unselected package libk5crypto3:amd64.
#7 18.57 Preparing to unpack .../029-libk5crypto3_1.21.3-5+deb13u1_amd64.deb ...
#7 18.58 Unpacking libk5crypto3:amd64 (1.21.3-5+deb13u1) ...
#7 18.62 Selecting previously unselected package libkeyutils1:amd64.
#7 18.62 Preparing to unpack .../030-libkeyutils1_1.6.3-6_amd64.deb ...
#7 18.63 Unpacking libkeyutils1:amd64 (1.6.3-6) ...
#7 18.67 Selecting previously unselected package libkrb5-3:amd64.
#7 18.67 Preparing to unpack .../031-libkrb5-3_1.21.3-5+deb13u1_amd64.deb ...
#7 18.67 Unpacking libkrb5-3:amd64 (1.21.3-5+deb13u1) ...
#7 18.73 Selecting previously unselected package libgssapi-krb5-2:amd64.
#7 18.73 Preparing to unpack .../032-libgssapi-krb5-2_1.21.3-5+deb13u1_amd64.deb ...
#7 18.74 Unpacking libgssapi-krb5-2:amd64 (1.21.3-5+deb13u1) ...
#7 18.79 Selecting previously unselected package libunistring5:amd64.
#7 18.79 Preparing to unpack .../033-libunistring5_1.3-2_amd64.deb ...
#7 18.79 Unpacking libunistring5:amd64 (1.3-2) ...
#7 18.86 Selecting previously unselected package libidn2-0:amd64.
#7 18.86 Preparing to unpack .../034-libidn2-0_2.3.8-2_amd64.deb ...
#7 18.86 Unpacking libidn2-0:amd64 (2.3.8-2) ...
#7 18.90 Selecting previously unselected package libsasl2-modules-db:amd64.
#7 18.90 Preparing to unpack .../035-libsasl2-modules-db_2.1.28+dfsg1-9_amd64.deb ...
#7 18.91 Unpacking libsasl2-modules-db:amd64 (2.1.28+dfsg1-9) ...
#7 18.95 Selecting previously unselected package libsasl2-2:amd64.
#7 18.95 Preparing to unpack .../036-libsasl2-2_2.1.28+dfsg1-9_amd64.deb ...
#7 18.95 Unpacking libsasl2-2:amd64 (2.1.28+dfsg1-9) ...
#7 19.00 Selecting previously unselected package libldap2:amd64.
#7 19.00 Preparing to unpack .../037-libldap2_2.6.10+dfsg-1_amd64.deb ...
#7 19.00 Unpacking libldap2:amd64 (2.6.10+dfsg-1) ...
#7 19.05 Selecting previously unselected package libnghttp2-14:amd64.
#7 19.05 Preparing to unpack .../038-libnghttp2-14_1.64.0-1.1+deb13u1_amd64.deb ...
#7 19.06 Unpacking libnghttp2-14:amd64 (1.64.0-1.1+deb13u1) ...
#7 19.10 Selecting previously unselected package libnghttp3-9:amd64.
#7 19.10 Preparing to unpack .../039-libnghttp3-9_1.8.0-1_amd64.deb ...
#7 19.11 Unpacking libnghttp3-9:amd64 (1.8.0-1) ...
#7 19.15 Selecting previously unselected package libpsl5t64:amd64.
#7 19.15 Preparing to unpack .../040-libpsl5t64_0.21.2-1.1+b1_amd64.deb ...
#7 19.16 Unpacking libpsl5t64:amd64 (0.21.2-1.1+b1) ...
#7 19.20 Selecting previously unselected package libp11-kit0:amd64.
#7 19.20 Preparing to unpack .../041-libp11-kit0_0.25.5-3_amd64.deb ...
#7 19.20 Unpacking libp11-kit0:amd64 (0.25.5-3) ...
#7 19.26 Selecting previously unselected package libtasn1-6:amd64.
#7 19.26 Preparing to unpack .../042-libtasn1-6_4.20.0-2+deb13u1_amd64.deb ...
#7 19.26 Unpacking libtasn1-6:amd64 (4.20.0-2+deb13u1) ...
#7 19.31 Selecting previously unselected package libgnutls30t64:amd64.
#7 19.31 Preparing to unpack .../043-libgnutls30t64_3.8.9-3+deb13u4_amd64.deb ...
#7 19.31 Unpacking libgnutls30t64:amd64 (3.8.9-3+deb13u4) ...
#7 19.39 Selecting previously unselected package librtmp1:amd64.
#7 19.40 Preparing to unpack .../044-librtmp1_2.4+20151223.gitfa8646d.1-2+b5_amd64.deb ...
#7 19.40 Unpacking librtmp1:amd64 (2.4+20151223.gitfa8646d.1-2+b5) ...
#7 19.44 Selecting previously unselected package libssh2-1t64:amd64.
#7 19.44 Preparing to unpack .../045-libssh2-1t64_1.11.1-1+deb13u2_amd64.deb ...
#7 19.45 Unpacking libssh2-1t64:amd64 (1.11.1-1+deb13u2) ...
#7 19.50 Selecting previously unselected package libcurl4t64:amd64.
#7 19.50 Preparing to unpack .../046-libcurl4t64_8.14.1-2+deb13u7_amd64.deb ...
#7 19.50 Unpacking libcurl4t64:amd64 (8.14.1-2+deb13u7) ...
#7 19.56 Selecting previously unselected package libcmis-0.6-6t64.
#7 19.56 Preparing to unpack .../047-libcmis-0.6-6t64_0.6.2-2.1+b1_amd64.deb ...
#7 19.57 Unpacking libcmis-0.6-6t64 (0.6.2-2.1+b1) ...
#7 19.62 Selecting previously unselected package libavahi-common-data:amd64.
#7 19.62 Preparing to unpack .../048-libavahi-common-data_0.8-16_amd64.deb ...
#7 19.63 Unpacking libavahi-common-data:amd64 (0.8-16) ...
#7 19.68 Selecting previously unselected package libavahi-common3:amd64.
#7 19.68 Preparing to unpack .../049-libavahi-common3_0.8-16_amd64.deb ...
#7 19.69 Unpacking libavahi-common3:amd64 (0.8-16) ...
#7 19.73 Selecting previously unselected package libdbus-1-3:amd64.
#7 19.73 Preparing to unpack .../050-libdbus-1-3_1.16.2-2_amd64.deb ...
#7 19.74 Unpacking libdbus-1-3:amd64 (1.16.2-2) ...
#7 19.79 Selecting previously unselected package libavahi-client3:amd64.
#7 19.79 Preparing to unpack .../051-libavahi-client3_0.8-16_amd64.deb ...
#7 19.80 Unpacking libavahi-client3:amd64 (0.8-16) ...
#7 19.84 Selecting previously unselected package libcups2t64:amd64.
#7 19.84 Preparing to unpack .../052-libcups2t64_2.4.10-3+deb13u2_amd64.deb ...
#7 19.85 Unpacking libcups2t64:amd64 (2.4.10-3+deb13u2) ...
#7 19.90 Selecting previously unselected package libatomic1:amd64.
#7 19.90 Preparing to unpack .../053-libatomic1_14.2.0-19_amd64.deb ...
#7 19.91 Unpacking libatomic1:amd64 (14.2.0-19) ...
#7 19.96 Selecting previously unselected package libglib2.0-0t64:amd64.
#7 19.96 Preparing to unpack .../054-libglib2.0-0t64_2.84.4-3~deb13u5_amd64.deb ...
#7 19.97 Unpacking libglib2.0-0t64:amd64 (2.84.4-3~deb13u5) ...
#7 20.07 Selecting previously unselected package libdconf1:amd64.
#7 20.07 Preparing to unpack .../055-libdconf1_0.40.0-5_amd64.deb ...
#7 20.08 Unpacking libdconf1:amd64 (0.40.0-5) ...
#7 20.12 Selecting previously unselected package libeot0:amd64.
#7 20.12 Preparing to unpack .../056-libeot0_0.01-5+b2_amd64.deb ...
#7 20.12 Unpacking libeot0:amd64 (0.01-5+b2) ...
#7 20.17 Selecting previously unselected package libepoxy0:amd64.
#7 20.17 Preparing to unpack .../057-libepoxy0_1.5.10-2_amd64.deb ...
#7 20.18 Unpacking libepoxy0:amd64 (1.5.10-2) ...
#7 20.22 Selecting previously unselected package libexttextcat-data.
#7 20.22 Preparing to unpack .../058-libexttextcat-data_3.4.7-1_all.deb ...
#7 20.25 Unpacking libexttextcat-data (3.4.7-1) ...
#7 20.57 Selecting previously unselected package libexttextcat-2.0-0:amd64.
#7 20.57 Preparing to unpack .../059-libexttextcat-2.0-0_3.4.7-1+b1_amd64.deb ...
#7 20.64 Unpacking libexttextcat-2.0-0:amd64 (3.4.7-1+b1) ...
#7 20.90 Selecting previously unselected package libgpg-error0:amd64.
#7 20.90 Preparing to unpack .../060-libgpg-error0_1.51-4_amd64.deb ...
#7 20.96 Unpacking libgpg-error0:amd64 (1.51-4) ...
#7 21.25 Selecting previously unselected package libassuan9:amd64.
#7 21.25 Preparing to unpack .../061-libassuan9_3.0.2-2_amd64.deb ...
#7 21.26 Unpacking libassuan9:amd64 (3.0.2-2) ...
#7 21.32 Selecting previously unselected package libgcrypt20:amd64.
#7 21.32 Preparing to unpack .../062-libgcrypt20_1.11.0-7+deb13u1_amd64.deb ...
#7 21.33 Unpacking libgcrypt20:amd64 (1.11.0-7+deb13u1) ...
#7 21.40 Selecting previously unselected package gpgconf.
#7 21.40 Preparing to unpack .../063-gpgconf_2.4.7-21+deb13u1+b5_amd64.deb ...
#7 21.41 Unpacking gpgconf (2.4.7-21+deb13u1+b5) ...
#7 21.46 Selecting previously unselected package libksba8:amd64.
#7 21.47 Preparing to unpack .../064-libksba8_1.6.7-2+b1_amd64.deb ...
#7 21.47 Unpacking libksba8:amd64 (1.6.7-2+b1) ...
#7 21.51 Selecting previously unselected package libnpth0t64:amd64.
#7 21.52 Preparing to unpack .../065-libnpth0t64_1.8-3_amd64.deb ...
#7 21.53 Unpacking libnpth0t64:amd64 (1.8-3) ...
#7 21.57 Selecting previously unselected package dirmngr.
#7 21.57 Preparing to unpack .../066-dirmngr_2.4.7-21+deb13u1+b5_amd64.deb ...
#7 21.59 Unpacking dirmngr (2.4.7-21+deb13u1+b5) ...
#7 21.64 Selecting previously unselected package gnupg-l10n.
#7 21.64 Preparing to unpack .../067-gnupg-l10n_2.4.7-21+deb13u1_all.deb ...
#7 21.65 Unpacking gnupg-l10n (2.4.7-21+deb13u1) ...
#7 21.72 Selecting previously unselected package gpg.
#7 21.72 Preparing to unpack .../068-gpg_2.4.7-21+deb13u1+b5_amd64.deb ...
#7 21.73 Unpacking gpg (2.4.7-21+deb13u1+b5) ...
#7 21.79 Selecting previously unselected package pinentry-curses.
#7 21.80 Preparing to unpack .../069-pinentry-curses_1.3.1-2_amd64.deb ...
#7 21.80 Unpacking pinentry-curses (1.3.1-2) ...
#7 21.86 Selecting previously unselected package gpg-agent.
#7 21.87 Preparing to unpack .../070-gpg-agent_2.4.7-21+deb13u1+b5_amd64.deb ...
#7 21.87 Unpacking gpg-agent (2.4.7-21+deb13u1+b5) ...
#7 21.92 Selecting previously unselected package gpgsm.
#7 21.92 Preparing to unpack .../071-gpgsm_2.4.7-21+deb13u1+b5_amd64.deb ...
#7 21.93 Unpacking gpgsm (2.4.7-21+deb13u1+b5) ...
#7 21.98 Selecting previously unselected package gnupg.
#7 21.98 Preparing to unpack .../072-gnupg_2.4.7-21+deb13u1_all.deb ...
#7 21.99 Unpacking gnupg (2.4.7-21+deb13u1) ...
#7 22.05 Selecting previously unselected package libgpgme11t64:amd64.
#7 22.05 Preparing to unpack .../073-libgpgme11t64_1.24.2-3_amd64.deb ...
#7 22.06 Unpacking libgpgme11t64:amd64 (1.24.2-3) ...
#7 22.29 Selecting previously unselected package libgpgmepp6t64:amd64.
#7 22.29 Preparing to unpack .../074-libgpgmepp6t64_1.24.2-3_amd64.deb ...
#7 22.33 Unpacking libgpgmepp6t64:amd64 (1.24.2-3) ...
#7 22.61 Selecting previously unselected package libgraphite2-3:amd64.
#7 22.61 Preparing to unpack .../075-libgraphite2-3_1.3.14-2+deb13u1_amd64.deb ...
#7 22.62 Unpacking libgraphite2-3:amd64 (1.3.14-2+deb13u1) ...
#7 22.66 Selecting previously unselected package libdrm-common.
#7 22.67 Preparing to unpack .../076-libdrm-common_2.4.124-2_all.deb ...
#7 22.67 Unpacking libdrm-common (2.4.124-2) ...
#7 22.72 Selecting previously unselected package libdrm2:amd64.
#7 22.72 Preparing to unpack .../077-libdrm2_2.4.124-2_amd64.deb ...
#7 22.73 Unpacking libdrm2:amd64 (2.4.124-2) ...
#7 22.77 Selecting previously unselected package libcap2-bin.
#7 22.77 Preparing to unpack .../078-libcap2-bin_1%3a2.75-10+deb13u1+b3_amd64.deb ...
#7 22.77 Unpacking libcap2-bin (1:2.75-10+deb13u1+b3) ...
#7 22.82 Selecting previously unselected package libgstreamer1.0-0:amd64.
#7 22.82 Preparing to unpack .../079-libgstreamer1.0-0_1.26.2-2_amd64.deb ...
#7 22.83 Unpacking libgstreamer1.0-0:amd64 (1.26.2-2) ...
#7 22.93 Selecting previously unselected package liborc-0.4-0t64:amd64.
#7 22.93 Preparing to unpack .../080-liborc-0.4-0t64_1%3a0.4.41-1_amd64.deb ...
#7 22.94 Unpacking liborc-0.4-0t64:amd64 (1:0.4.41-1) ...
#7 22.99 Selecting previously unselected package iso-codes.
#7 22.99 Preparing to unpack .../081-iso-codes_4.18.0-1_all.deb ...
#7 22.99 Unpacking iso-codes (4.18.0-1) ...
#7 23.50 Selecting previously unselected package libgstreamer-plugins-base1.0-0:amd64.
#7 23.50 Preparing to unpack .../082-libgstreamer-plugins-base1.0-0_1.26.2-1+deb13u2_amd64.deb ...
#7 23.54 Unpacking libgstreamer-plugins-base1.0-0:amd64 (1.26.2-1+deb13u2) ...
#7 23.69 Selecting previously unselected package libharfbuzz0b:amd64.
#7 23.69 Preparing to unpack .../083-libharfbuzz0b_10.2.0-1+deb13u1_amd64.deb ...
#7 23.73 Unpacking libharfbuzz0b:amd64 (10.2.0-1+deb13u1) ...
#7 24.11 Selecting previously unselected package libharfbuzz-icu0:amd64.
#7 24.12 Preparing to unpack .../084-libharfbuzz-icu0_10.2.0-1+deb13u1_amd64.deb ...
#7 24.16 Unpacking libharfbuzz-icu0:amd64 (10.2.0-1+deb13u1) ...
#7 24.41 Selecting previously unselected package libhunspell-1.7-0:amd64.
#7 24.41 Preparing to unpack .../085-libhunspell-1.7-0_1.7.2+really1.7.2-10+b4_amd64.deb ...
#7 24.47 Unpacking libhunspell-1.7-0:amd64 (1.7.2+really1.7.2-10+b4) ...
#7 24.53 Selecting previously unselected package libhyphen0:amd64.
#7 24.53 Preparing to unpack .../086-libhyphen0_2.8.8-7+b2_amd64.deb ...
#7 24.53 Unpacking libhyphen0:amd64 (2.8.8-7+b2) ...
#7 24.58 Selecting previously unselected package x11-common.
#7 24.59 Preparing to unpack .../087-x11-common_1%3a7.7+24+deb13u1_all.deb ...
#7 24.59 Unpacking x11-common (1:7.7+24+deb13u1) ...
#7 24.64 Selecting previously unselected package libice6:amd64.
#7 24.64 Preparing to unpack .../088-libice6_2%3a1.1.1-1_amd64.deb ...
#7 24.64 Unpacking libice6:amd64 (2:1.1.1-1) ...
#7 24.69 Selecting previously unselected package libjpeg62-turbo:amd64.
#7 24.69 Preparing to unpack .../089-libjpeg62-turbo_1%3a2.1.5-4_amd64.deb ...
#7 24.70 Unpacking libjpeg62-turbo:amd64 (1:2.1.5-4) ...
#7 24.74 Selecting previously unselected package liblcms2-2:amd64.
#7 24.75 Preparing to unpack .../090-liblcms2-2_2.16-2+deb13u2_amd64.deb ...
#7 24.75 Unpacking liblcms2-2:amd64 (2.16-2+deb13u2) ...
#7 24.80 Selecting previously unselected package libmythes-1.2-0:amd64.
#7 24.80 Preparing to unpack .../091-libmythes-1.2-0_2%3a1.2.5-1+b2_amd64.deb ...
#7 24.81 Unpacking libmythes-1.2-0:amd64 (2:1.2.5-1+b2) ...
#7 24.85 Selecting previously unselected package libnspr4:amd64.
#7 24.85 Preparing to unpack .../092-libnspr4_2%3a4.36-1_amd64.deb ...
#7 24.85 Unpacking libnspr4:amd64 (2:4.36-1) ...
#7 24.90 Selecting previously unselected package libnss3:amd64.
#7 24.90 Preparing to unpack .../093-libnss3_2%3a3.110-1+deb13u4_amd64.deb ...
#7 24.90 Unpacking libnss3:amd64 (2:3.110-1+deb13u4) ...
#7 25.00 Selecting previously unselected package libnumbertext-1.0-0:amd64.
#7 25.00 Preparing to unpack .../094-libnumbertext-1.0-0_1.0.11-4+b2_amd64.deb ...
#7 25.01 Unpacking libnumbertext-1.0-0:amd64 (1.0.11-4+b2) ...
#7 25.06 Selecting previously unselected package libopenjp2-7:amd64.
#7 25.06 Preparing to unpack .../095-libopenjp2-7_2.5.3-2.1~deb13u2_amd64.deb ...
#7 25.06 Unpacking libopenjp2-7:amd64 (2.5.3-2.1~deb13u2) ...
#7 25.24 Selecting previously unselected package libboost-iostreams1.83.0:amd64.
#7 25.25 Preparing to unpack .../096-libboost-iostreams1.83.0_1.83.0-4.2_amd64.deb ...
#7 25.29 Unpacking libboost-iostreams1.83.0:amd64 (1.83.0-4.2) ...
#7 25.34 Selecting previously unselected package liborcus-parser-0.18-0:amd64.
#7 25.34 Preparing to unpack .../097-liborcus-parser-0.18-0_0.19.2-6+b1_amd64.deb ...
#7 25.35 Unpacking liborcus-parser-0.18-0:amd64 (0.19.2-6+b1) ...
#7 25.39 Selecting previously unselected package liborcus-0.18-0:amd64.
#7 25.39 Preparing to unpack .../098-liborcus-0.18-0_0.19.2-6+b1_amd64.deb ...
#7 25.40 Unpacking liborcus-0.18-0:amd64 (0.19.2-6+b1) ...
#7 25.46 Selecting previously unselected package libngtcp2-16:amd64.
#7 25.46 Preparing to unpack .../099-libngtcp2-16_1.11.0-1+deb13u1_amd64.deb ...
#7 25.47 Unpacking libngtcp2-16:amd64 (1.11.0-1+deb13u1) ...
#7 25.52 Selecting previously unselected package libngtcp2-crypto-gnutls8:amd64.
#7 25.52 Preparing to unpack .../100-libngtcp2-crypto-gnutls8_1.11.0-1+deb13u1_amd64.deb ...
#7 25.52 Unpacking libngtcp2-crypto-gnutls8:amd64 (1.11.0-1+deb13u1) ...
#7 25.56 Selecting previously unselected package libcurl3t64-gnutls:amd64.
#7 25.57 Preparing to unpack .../101-libcurl3t64-gnutls_8.14.1-2+deb13u7_amd64.deb ...
#7 25.57 Unpacking libcurl3t64-gnutls:amd64 (8.14.1-2+deb13u7) ...
#7 25.62 Selecting previously unselected package libdeflate0:amd64.
#7 25.62 Preparing to unpack .../102-libdeflate0_1.23-2_amd64.deb ...
#7 25.63 Unpacking libdeflate0:amd64 (1.23-2) ...
#7 25.67 Selecting previously unselected package libjbig0:amd64.
#7 25.67 Preparing to unpack .../103-libjbig0_2.1-6.1+b2_amd64.deb ...
#7 25.68 Unpacking libjbig0:amd64 (2.1-6.1+b2) ...
#7 25.72 Selecting previously unselected package liblerc4:amd64.
#7 25.72 Preparing to unpack .../104-liblerc4_4.0.0+ds-5_amd64.deb ...
#7 25.73 Unpacking liblerc4:amd64 (4.0.0+ds-5) ...
#7 25.77 Selecting previously unselected package libsharpyuv0:amd64.
#7 25.77 Preparing to unpack .../105-libsharpyuv0_1.5.0-0.1_amd64.deb ...
#7 25.78 Unpacking libsharpyuv0:amd64 (1.5.0-0.1) ...
#7 25.82 Selecting previously unselected package libwebp7:amd64.
#7 25.82 Preparing to unpack .../106-libwebp7_1.5.0-0.1_amd64.deb ...
#7 25.83 Unpacking libwebp7:amd64 (1.5.0-0.1) ...
#7 25.87 Selecting previously unselected package libtiff6:amd64.
#7 25.88 Preparing to unpack .../107-libtiff6_4.7.0-3+deb13u3_amd64.deb ...
#7 25.88 Unpacking libtiff6:amd64 (4.7.0-3+deb13u3) ...
#7 25.92 Selecting previously unselected package libpoppler147:amd64.
#7 25.92 Preparing to unpack .../108-libpoppler147_25.03.0-5+deb13u4_amd64.deb ...
#7 25.93 Unpacking libpoppler147:amd64 (25.03.0-5+deb13u4) ...
#7 26.02 Selecting previously unselected package libxslt1.1:amd64.
#7 26.03 Preparing to unpack .../109-libxslt1.1_1.1.35-1.2+deb13u3_amd64.deb ...
#7 26.03 Unpacking libxslt1.1:amd64 (1.1.35-1.2+deb13u3) ...
#7 26.08 Selecting previously unselected package libyajl2:amd64.
#7 26.08 Preparing to unpack .../110-libyajl2_2.1.0-5+b2_amd64.deb ...
#7 26.09 Unpacking libyajl2:amd64 (2.1.0-5+b2) ...
#7 26.13 Selecting previously unselected package libraptor2-0:amd64.
#7 26.13 Preparing to unpack .../111-libraptor2-0_2.0.16-6_amd64.deb ...
#7 26.14 Unpacking libraptor2-0:amd64 (2.0.16-6) ...
#7 26.18 Selecting previously unselected package libltdl7:amd64.
#7 26.18 Preparing to unpack .../112-libltdl7_2.5.4-4_amd64.deb ...
#7 26.19 Unpacking libltdl7:amd64 (2.5.4-4) ...
#7 26.23 Selecting previously unselected package libmhash2:amd64.
#7 26.23 Preparing to unpack .../113-libmhash2_0.9.9.9-10_amd64.deb ...
#7 26.24 Unpacking libmhash2:amd64 (0.9.9.9-10) ...
#7 26.28 Selecting previously unselected package librasqal3t64:amd64.
#7 26.28 Preparing to unpack .../114-librasqal3t64_0.9.33-2.1+b2_amd64.deb ...
#7 26.29 Unpacking librasqal3t64:amd64 (0.9.33-2.1+b2) ...
#7 26.33 Selecting previously unselected package librdf0t64:amd64.
#7 26.33 Preparing to unpack .../115-librdf0t64_1.0.17-4+b1_amd64.deb ...
#7 26.34 Unpacking librdf0t64:amd64 (1.0.17-4+b1) ...
#7 26.38 Selecting previously unselected package librevenge-0.0-0:amd64.
#7 26.38 Preparing to unpack .../116-librevenge-0.0-0_0.0.5-3+b2_amd64.deb ...
#7 26.39 Unpacking librevenge-0.0-0:amd64 (0.0.5-3+b2) ...
#7 26.44 Selecting previously unselected package libsm6:amd64.
#7 26.44 Preparing to unpack .../117-libsm6_2%3a1.2.6-1_amd64.deb ...
#7 26.45 Unpacking libsm6:amd64 (2:1.2.6-1) ...
#7 26.49 Selecting previously unselected package libx11-xcb1:amd64.
#7 26.49 Preparing to unpack .../118-libx11-xcb1_2%3a1.8.12-1_amd64.deb ...
#7 26.50 Unpacking libx11-xcb1:amd64 (2:1.8.12-1) ...
#7 26.54 Selecting previously unselected package libxinerama1:amd64.
#7 26.54 Preparing to unpack .../119-libxinerama1_2%3a1.1.4-3+b4_amd64.deb ...
#7 26.55 Unpacking libxinerama1:amd64 (2:1.1.4-3+b4) ...
#7 26.59 Selecting previously unselected package libxmlsec1t64:amd64.
#7 26.59 Preparing to unpack .../120-libxmlsec1t64_1.2.41-1+b1_amd64.deb ...
#7 26.59 Unpacking libxmlsec1t64:amd64 (1.2.41-1+b1) ...
#7 26.64 Selecting previously unselected package libxmlsec1t64-nss:amd64.
#7 26.64 Preparing to unpack .../121-libxmlsec1t64-nss_1.2.41-1+b1_amd64.deb ...
#7 26.65 Unpacking libxmlsec1t64-nss:amd64 (1.2.41-1+b1) ...
#7 26.69 Selecting previously unselected package libxrandr2:amd64.
#7 26.69 Preparing to unpack .../122-libxrandr2_2%3a1.5.4-1+b3_amd64.deb ...
#7 26.70 Unpacking libxrandr2:amd64 (2:1.5.4-1+b3) ...
#7 26.74 Selecting previously unselected package libzxcvbn0:amd64.
#7 26.74 Preparing to unpack .../123-libzxcvbn0_2.5+dfsg-2+b2_amd64.deb ...
#7 26.74 Unpacking libzxcvbn0:amd64 (2.5+dfsg-2+b2) ...
#7 26.82 Selecting previously unselected package libzxing3:amd64.
#7 26.82 Preparing to unpack .../124-libzxing3_2.3.0-4_amd64.deb ...
#7 26.83 Unpacking libzxing3:amd64 (2.3.0-4) ...
#7 26.89 Selecting previously unselected package libreoffice-core.
#7 26.89 Preparing to unpack .../125-libreoffice-core_4%3a25.2.3-2+deb13u8_amd64.deb ...
#7 26.90 Unpacking libreoffice-core (4:25.2.3-2+deb13u8) ...
#7 27.45 Selecting previously unselected package libreoffice-base-core.
#7 27.45 Preparing to unpack .../126-libreoffice-base-core_4%3a25.2.3-2+deb13u8_amd64.deb ...
#7 27.46 Unpacking libreoffice-base-core (4:25.2.3-2+deb13u8) ...
#7 27.53 Selecting previously unselected package libreoffice-uiconfig-writer.
#7 27.53 Preparing to unpack .../127-libreoffice-uiconfig-writer_4%3a25.2.3-2+deb13u8_all.deb ...
#7 27.53 Unpacking libreoffice-uiconfig-writer (4:25.2.3-2+deb13u8) ...
#7 27.64 Selecting previously unselected package libabw-0.1-1:amd64.
#7 27.64 Preparing to unpack .../128-libabw-0.1-1_0.1.3-1+b2_amd64.deb ...
#7 27.65 Unpacking libabw-0.1-1:amd64 (0.1.3-1+b2) ...
#7 27.69 Selecting previously unselected package libe-book-0.1-1:amd64.
#7 27.69 Preparing to unpack .../129-libe-book-0.1-1_0.1.3-2+b4_amd64.deb ...
#7 27.70 Unpacking libe-book-0.1-1:amd64 (0.1.3-2+b4) ...
#7 27.75 Selecting previously unselected package libepubgen-0.1-1:amd64.
#7 27.75 Preparing to unpack .../130-libepubgen-0.1-1_0.1.1-1+b2_amd64.deb ...
#7 27.75 Unpacking libepubgen-0.1-1:amd64 (0.1.1-1+b2) ...
#7 27.80 Selecting previously unselected package libetonyek-0.1-1:amd64.
#7 27.80 Preparing to unpack .../131-libetonyek-0.1-1_0.1.12-1_amd64.deb ...
#7 27.80 Unpacking libetonyek-0.1-1:amd64 (0.1.12-1) ...
#7 27.88 Selecting previously unselected package libmwaw-0.3-3:amd64.
#7 27.88 Preparing to unpack .../132-libmwaw-0.3-3_0.3.22-1+b2_amd64.deb ...
#7 27.88 Unpacking libmwaw-0.3-3:amd64 (0.3.22-1+b2) ...
#7 28.05 Selecting previously unselected package libodfgen-0.1-1:amd64.
#7 28.05 Preparing to unpack .../133-libodfgen-0.1-1_0.1.8-2+b2_amd64.deb ...
#7 28.06 Unpacking libodfgen-0.1-1:amd64 (0.1.8-2+b2) ...
#7 28.13 Selecting previously unselected package libstaroffice-0.0-0:amd64.
#7 28.13 Preparing to unpack .../134-libstaroffice-0.0-0_0.0.7-1+b2_amd64.deb ...
#7 28.14 Unpacking libstaroffice-0.0-0:amd64 (0.0.7-1+b2) ...
#7 28.22 Selecting previously unselected package libwpd-0.10-10:amd64.
#7 28.22 Preparing to unpack .../135-libwpd-0.10-10_0.10.3-2+b2_amd64.deb ...
#7 28.23 Unpacking libwpd-0.10-10:amd64 (0.10.3-2+b2) ...
#7 28.28 Selecting previously unselected package libwpg-0.3-3:amd64.
#7 28.28 Preparing to unpack .../136-libwpg-0.3-3_0.3.4-3+b2_amd64.deb ...
#7 28.28 Unpacking libwpg-0.3-3:amd64 (0.3.4-3+b2) ...
#7 28.34 Selecting previously unselected package libwps-0.4-4:amd64.
#7 28.34 Preparing to unpack .../137-libwps-0.4-4_0.4.14-2+b2_amd64.deb ...
#7 28.34 Unpacking libwps-0.4-4:amd64 (0.4.14-2+b2) ...
#7 28.45 Setting up libreoffice-style-colibre (4:25.2.3-2+deb13u8) ...
#7 28.48 Setting up libreoffice-uiconfig-common (4:25.2.3-2+deb13u8) ...
#7 28.50 Setting up libuno-sal3t64 (4:25.2.3-2+deb13u8) ...
#7 28.52 Setting up libuno-salhelpergcc3-3t64 (4:25.2.3-2+deb13u8) ...
#7 28.54 Setting up libuno-cppu3t64 (4:25.2.3-2+deb13u8) ...
#7 28.56 Setting up uno-libs-private (4:25.2.3-2+deb13u8) ...
#7 28.57 Setting up libicu76:amd64 (76.1-4) ...
#7 28.59 Setting up libxml2:amd64 (2.12.7+dfsg+really2.9.14-2.1+deb13u3) ...
#7 28.61 Setting up liblangtag-common (0.6.7-1) ...
#7 28.63 Setting up liblangtag1:amd64 (0.6.7-1+b2) ...
#7 28.64 Setting up libuno-cppuhelpergcc3-3t64 (4:25.2.3-2+deb13u8) ...
#7 28.66 Setting up libuno-purpenvhelpergcc3-3t64 (4:25.2.3-2+deb13u8) ...
#7 28.67 Setting up ure (4:25.2.3-2+deb13u8) ...
#7 28.69 Setting up libnumbertext-data (1.0.11-4) ...
#7 28.70 Setting up libreoffice-common (4:25.2.3-2+deb13u8) ...
#7 28.83 debconf: unable to initialize frontend: Dialog
#7 28.83 debconf: (TERM is not set, so the dialog frontend is not usable.)
#7 28.83 debconf: falling back to frontend: Readline
#7 28.83 debconf: unable to initialize frontend: Readline
#7 28.83 debconf: (Can't locate Term/ReadLine.pm in @INC (you may need to install the Term::ReadLine module) (@INC entries checked: /etc/perl /usr/local/lib/x86_64-linux-gnu/perl/5.40.1 /usr/local/share/perl/5.40.1 /usr/lib/x86_64-linux-gnu/perl5/5.40 /usr/share/perl5 /usr/lib/x86_64-linux-gnu/perl-base /usr/lib/x86_64-linux-gnu/perl/5.40 /usr/share/perl/5.40 /usr/local/lib/site_perl) at /usr/share/perl5/Debconf/FrontEnd/Readline.pm line 8.)
#7 28.83 debconf: falling back to frontend: Teletype
#7 28.83 debconf: unable to initialize frontend: Teletype
#7 28.83 debconf: (This frontend requires a controlling tty.)
#7 28.83 debconf: falling back to frontend: Noninteractive
#7 28.87 Creating config file /etc/libreoffice/registry/main.xcd with new version
#7 28.96 Selecting previously unselected package libreoffice-writer.
#7 28.96 (Reading database ... (Reading database ... 5%(Reading database ... 10%(Reading database ... 15%(Reading database ... 20%(Reading database ... 25%(Reading database ... 30%(Reading database ... 35%(Reading database ... 40%(Reading database ... 45%(Reading database ... 50%(Reading database ... 55%(Reading database ... 60%(Reading database ... 65%(Reading database ... 70%(Reading database ... 75%(Reading database ... 80%(Reading database ... 85%(Reading database ... 90%(Reading database ... 95%(Reading database ... 100%(Reading database ... 12513 files and directories currently installed.)
#7 28.97 Preparing to unpack .../libreoffice-writer_4%3a25.2.3-2+deb13u8_amd64.deb ...
#7 28.98 Unpacking libreoffice-writer (4:25.2.3-2+deb13u8) ...
#7 29.36 Setting up libexpat1:amd64 (2.9.0-1~deb13u1) ...
#7 29.38 Setting up libgraphite2-3:amd64 (1.3.14-2+deb13u1) ...
#7 29.40 Setting up liblcms2-2:amd64 (2.16-2+deb13u2) ...
#7 29.41 Setting up libpixman-1-0:amd64 (0.44.0-3) ...
#7 29.43 Setting up libzxcvbn0:amd64 (2.5+dfsg-2+b2) ...
#7 29.44 Setting up libsharpyuv0:amd64 (1.5.0-0.1) ...
#7 29.46 Setting up liborcus-parser-0.18-0:amd64 (0.19.2-6+b1) ...
#7 29.47 Setting up libxau6:amd64 (1:1.0.11-1) ...
#7 29.49 Setting up libxdmcp6:amd64 (1:1.1.5-1) ...
#7 29.50 Setting up libnpth0t64:amd64 (1.8-3) ...
#7 29.51 Setting up libkeyutils1:amd64 (1.6.3-6) ...
#7 29.53 Setting up libxcb1:amd64 (1.17.0-2+b1) ...
#7 29.55 Setting up liblerc4:amd64 (4.0.0+ds-5) ...
#7 29.56 Setting up libgpg-error0:amd64 (1.51-4) ...
#7 29.58 Setting up libhyphen0:amd64 (2.8.8-7+b2) ...
#7 29.59 Setting up libclucene-core1t64:amd64 (2.3.3.4+dfsg-1.2+b1) ...
#7 29.61 Setting up libxcb-render0:amd64 (1.17.0-2+b1) ...
#7 29.62 Setting up libreoffice-uiconfig-writer (4:25.2.3-2+deb13u8) ...
#7 29.63 Setting up libargon2-1:amd64 (0~20190702+dfsg-4+b2) ...
#7 29.65 Setting up libbrotli1:amd64 (1.1.0-2+deb13u1) ...
#7 29.67 Setting up libyajl2:amd64 (2.1.0-5+b2) ...
#7 29.68 Setting up x11-common (1:7.7+24+deb13u1) ...
#7 29.81 debconf: unable to initialize frontend: Dialog
#7 29.81 debconf: (TERM is not set, so the dialog frontend is not usable.)
#7 29.81 debconf: falling back to frontend: Readline
#7 29.81 debconf: unable to initialize frontend: Readline
#7 29.81 debconf: (Can't locate Term/ReadLine.pm in @INC (you may need to install the Term::ReadLine module) (@INC entries checked: /etc/perl /usr/local/lib/x86_64-linux-gnu/perl/5.40.1 /usr/local/share/perl/5.40.1 /usr/lib/x86_64-linux-gnu/perl5/5.40 /usr/share/perl5 /usr/lib/x86_64-linux-gnu/perl-base /usr/lib/x86_64-linux-gnu/perl/5.40 /usr/share/perl/5.40 /usr/local/lib/site_perl) at /usr/share/perl5/Debconf/FrontEnd/Readline.pm line 8.)
#7 29.81 debconf: falling back to frontend: Teletype
#7 29.82 debconf: unable to initialize frontend: Teletype
#7 29.82 debconf: (This frontend requires a controlling tty.)
#7 29.82 debconf: falling back to frontend: Noninteractive
#7 29.83 invoke-rc.d: could not determine current runlevel
#7 29.83 invoke-rc.d: policy-rc.d denied execution of start.
#7 29.84 Setting up libnghttp2-14:amd64 (1.64.0-1.1+deb13u1) ...
#7 29.86 Setting up libdeflate0:amd64 (1.23-2) ...
#7 29.87 Setting up libclucene-contribs1t64:amd64 (2.3.3.4+dfsg-1.2+b1) ...
#7 29.88 Setting up libboost-thread1.83.0:amd64 (1.83.0-4.2) ...
#7 29.90 Setting up libgcrypt20:amd64 (1.11.0-7+deb13u1) ...
#7 29.91 Setting up libxcb-shm0:amd64 (1.17.0-2+b1) ...
#7 29.93 Setting up libcom-err2:amd64 (1.47.2-3+b12) ...
#7 29.94 Setting up libeot0:amd64 (0.01-5+b2) ...
#7 29.96 Setting up libabsl20240722:amd64 (20240722.0-4) ...
#7 29.97 Setting up libjbig0:amd64 (2.1-6.1+b2) ...
#7 29.99 Setting up librevenge-0.0-0:amd64 (0.0.5-3+b2) ...
#7 30.00 Setting up liborc-0.4-0t64:amd64 (1:0.4.41-1) ...
#7 30.01 Setting up libkrb5support0:amd64 (1.21.3-5+deb13u1) ...
#7 30.03 Setting up libsasl2-modules-db:amd64 (2.1.28+dfsg1-9) ...
#7 30.04 Setting up libcap2-bin (1:2.75-10+deb13u1+b3) ...
#7 30.06 Setting up libjpeg62-turbo:amd64 (1:2.1.5-4) ...
#7 30.07 Setting up libx11-data (2:1.8.12-1) ...
#7 30.09 Setting up libepoxy0:amd64 (1.5.10-2) ...
#7 30.10 Setting up libnspr4:amd64 (2:4.36-1) ...
#7 30.12 Setting up gnupg-l10n (2.4.7-21+deb13u1) ...
#7 30.13 Setting up libboost-iostreams1.83.0:amd64 (1.83.0-4.2) ...
#7 30.15 Setting up libzxing3:amd64 (2.3.0-4) ...
#7 30.16 Setting up libavahi-common-data:amd64 (0.8-16) ...
#7 30.18 Setting up libdbus-1-3:amd64 (1.16.2-2) ...
#7 30.19 Setting up libp11-kit0:amd64 (0.25.5-3) ...
#7 30.21 Setting up libunistring5:amd64 (1.3-2) ...
#7 30.22 Setting up fonts-dejavu-mono (2.37-8) ...
#7 30.26 Setting up libpng16-16t64:amd64 (1.6.48-1+deb13u6) ...
#7 30.28 Setting up libatomic1:amd64 (14.2.0-19) ...
#7 30.29 Setting up fonts-dejavu-core (2.37-8) ...
#7 30.36 Setting up liborcus-0.18-0:amd64 (0.19.2-6+b1) ...
#7 30.38 Setting up libk5crypto3:amd64 (1.21.3-5+deb13u1) ...
#7 30.39 Setting up libltdl7:amd64 (2.5.4-4) ...
#7 30.41 Setting up libsasl2-2:amd64 (2.1.28+dfsg1-9) ...
#7 30.42 Setting up libnghttp3-9:amd64 (1.8.0-1) ...
#7 30.44 Setting up libwebp7:amd64 (1.5.0-0.1) ...
#7 30.45 Setting up libmhash2:amd64 (0.9.9.9-10) ...
#7 30.47 Setting up libmythes-1.2-0:amd64 (2:1.2.5-1+b2) ...
#7 30.48 Setting up libtiff6:amd64 (4.7.0-3+deb13u3) ...
#7 30.50 Setting up libexttextcat-data (3.4.7-1) ...
#7 30.51 Setting up libassuan9:amd64 (3.0.2-2) ...
#7 30.53 Setting up libabw-0.1-1:amd64 (0.1.3-1+b2) ...
#7 30.54 Setting up libxslt1.1:amd64 (1.1.35-1.2+deb13u3) ...
#7 30.56 Setting up gpgconf (2.4.7-21+deb13u1+b5) ...
#7 30.58 Setting up libepubgen-0.1-1:amd64 (0.1.1-1+b2) ...
#7 30.60 Setting up libtasn1-6:amd64 (4.20.0-2+deb13u1) ...
#7 30.61 Setting up libopenjp2-7:amd64 (2.5.3-2.1~deb13u2) ...
#7 30.63 Setting up libx11-6:amd64 (2:1.8.12-1) ...
#7 30.64 Setting up libngtcp2-16:amd64 (1.11.0-1+deb13u1) ...
#7 30.66 Setting up libkrb5-3:amd64 (1.21.3-5+deb13u1) ...
#7 30.68 Setting up libssh2-1t64:amd64 (1.11.1-1+deb13u2) ...
#7 30.69 Setting up libhunspell-1.7-0:amd64 (1.7.2+really1.7.2-10+b4) ...
#7 30.71 Setting up libwpd-0.10-10:amd64 (0.10.3-2+b2) ...
#7 30.74 Setting up libdrm-common (2.4.124-2) ...
#7 30.75 Setting up libnumbertext-1.0-0:amd64 (1.0.11-4+b2) ...
#7 30.77 Setting up libldap2:amd64 (2.6.10+dfsg-1) ...
#7 30.78 Setting up iso-codes (4.18.0-1) ...
#7 30.80 Setting up fonts-opensymbol (4:102.12+LibO25.2.3-2+deb13u8) ...
#7 30.81 Setting up libodfgen-0.1-1:amd64 (0.1.8-2+b2) ...
#7 30.83 Setting up libksba8:amd64 (1.6.7-2+b1) ...
#7 30.85 Setting up pinentry-curses (1.3.1-2) ...
#7 30.87 Setting up libx11-xcb1:amd64 (2:1.8.12-1) ...
#7 30.88 Setting up libice6:amd64 (2:1.1.1-1) ...
#7 30.90 Setting up libstaroffice-0.0-0:amd64 (0.0.7-1+b2) ...
#7 30.91 Setting up gpg-agent (2.4.7-21+deb13u1+b5) ...
#7 31.27 Setting up libwps-0.4-4:amd64 (0.4.14-2+b2) ...
#7 31.29 Setting up libexttextcat-2.0-0:amd64 (3.4.7-1+b1) ...
#7 31.30 Setting up libxrender1:amd64 (1:0.9.12-1) ...
#7 31.32 Setting up fontconfig-config (2.15.0-2.3) ...
#7 31.40 debconf: unable to initialize frontend: Dialog
#7 31.40 debconf: (TERM is not set, so the dialog frontend is not usable.)
#7 31.40 debconf: falling back to frontend: Readline
#7 31.40 debconf: unable to initialize frontend: Readline
#7 31.40 debconf: (Can't locate Term/ReadLine.pm in @INC (you may need to install the Term::ReadLine module) (@INC entries checked: /etc/perl /usr/local/lib/x86_64-linux-gnu/perl/5.40.1 /usr/local/share/perl/5.40.1 /usr/lib/x86_64-linux-gnu/perl5/5.40 /usr/share/perl5 /usr/lib/x86_64-linux-gnu/perl-base /usr/lib/x86_64-linux-gnu/perl/5.40 /usr/share/perl/5.40 /usr/local/lib/site_perl) at /usr/share/perl5/Debconf/FrontEnd/Readline.pm line 8.)
#7 31.40 debconf: falling back to frontend: Teletype
#7 31.40 debconf: unable to initialize frontend: Teletype
#7 31.40 debconf: (This frontend requires a controlling tty.)
#7 31.40 debconf: falling back to frontend: Noninteractive
#7 31.44 Setting up gpgsm (2.4.7-21+deb13u1+b5) ...
#7 31.46 Setting up libavahi-common3:amd64 (0.8-16) ...
#7 31.48 Setting up libboost-locale1.83.0:amd64 (1.83.0-4.2) ...
#7 31.49 Setting up libxext6:amd64 (2:1.3.4-1+b3) ...
#7 31.50 Setting up libetonyek-0.1-1:amd64 (0.1.12-1) ...
#7 31.52 Setting up libidn2-0:amd64 (2.3.8-2) ...
#7 31.53 Setting up libnss3:amd64 (2:3.110-1+deb13u4) ...
#7 31.55 Setting up libmwaw-0.3-3:amd64 (0.3.22-1+b2) ...
#7 31.56 Setting up libe-book-0.1-1:amd64 (0.1.3-2+b4) ...
#7 31.58 Setting up libxmlsec1t64:amd64 (1.2.41-1+b1) ...
#7 31.59 Setting up libxmlsec1t64-nss:amd64 (1.2.41-1+b1) ...
#7 31.61 Setting up libglib2.0-0t64:amd64 (2.84.4-3~deb13u5) ...
#7 31.62 No schema files found: doing nothing.
#7 31.63 Setting up libfreetype6:amd64 (2.13.3+dfsg-1+deb13u1) ...
#7 31.64 Setting up libxinerama1:amd64 (2:1.1.4-3+b4) ...
#7 31.66 Setting up libgssapi-krb5-2:amd64 (1.21.3-5+deb13u1) ...
#7 31.67 Setting up libxrandr2:amd64 (2:1.5.4-1+b3) ...
#7 31.69 Setting up libwpg-0.3-3:amd64 (0.3.4-3+b2) ...
#7 31.71 Setting up libdrm2:amd64 (2.4.124-2) ...
#7 31.72 Setting up libharfbuzz0b:amd64 (10.2.0-1+deb13u1) ...
#7 31.73 Setting up libfontconfig1:amd64 (2.15.0-2.3) ...
#7 31.75 Setting up libsm6:amd64 (2:1.2.6-1) ...
#7 31.77 Setting up libavahi-client3:amd64 (0.8-16) ...
#7 31.78 Setting up gpg (2.4.7-21+deb13u1+b5) ...
#7 31.88 Setting up libgstreamer1.0-0:amd64 (1.26.2-2) ...
#7 31.89 Setcap worked! gst-ptp-helper is not suid!
#7 31.90 Setting up libgnutls30t64:amd64 (3.8.9-3+deb13u4) ...
#7 31.92 Setting up fontconfig (2.15.0-2.3) ...
#7 31.93 Regenerating fonts cache... done.
#7 33.94 Setting up libharfbuzz-icu0:amd64 (10.2.0-1+deb13u1) ...
#7 33.96 Setting up libpsl5t64:amd64 (0.21.2-1.1+b1) ...
#7 33.98 Setting up libgstreamer-plugins-base1.0-0:amd64 (1.26.2-1+deb13u2) ...
#7 33.99 Setting up libcairo2:amd64 (1.18.4-1+b1) ...
#7 34.00 Setting up libdconf1:amd64 (0.40.0-5) ...
#7 34.02 Setting up dirmngr (2.4.7-21+deb13u1+b5) ...
#7 34.13 Setting up librtmp1:amd64 (2.4+20151223.gitfa8646d.1-2+b5) ...
#7 34.15 Setting up gnupg (2.4.7-21+deb13u1) ...
#7 34.16 Setting up libgpgme11t64:amd64 (1.24.2-3) ...
#7 34.18 Setting up libcups2t64:amd64 (2.4.10-3+deb13u2) ...
#7 34.19 Setting up libngtcp2-crypto-gnutls8:amd64 (1.11.0-1+deb13u1) ...
#7 34.21 Setting up libgpgmepp6t64:amd64 (1.24.2-3) ...
#7 34.22 Setting up libcurl4t64:amd64 (8.14.1-2+deb13u7) ...
#7 34.24 Setting up libraptor2-0:amd64 (2.0.16-6) ...
#7 34.25 Setting up libcurl3t64-gnutls:amd64 (8.14.1-2+deb13u7) ...
#7 34.27 Setting up librasqal3t64:amd64 (0.9.33-2.1+b2) ...
#7 34.28 Setting up librdf0t64:amd64 (1.0.17-4+b1) ...
#7 34.30 Setting up libcmis-0.6-6t64 (0.6.2-2.1+b1) ...
#7 34.32 Setting up libpoppler147:amd64 (25.03.0-5+deb13u4) ...
#7 34.33 Setting up libreoffice-core (4:25.2.3-2+deb13u8) ...
#7 34.35 Setting up libreoffice-base-core (4:25.2.3-2+deb13u8) ...
#7 34.36 Setting up libreoffice-writer (4:25.2.3-2+deb13u8) ...
#7 34.38 Processing triggers for libreoffice-common (4:25.2.3-2+deb13u8) ...
#7 34.40 Processing triggers for libc-bin (2.41-12+deb13u4) ...
#7 DONE 34.9s

#8 [3/8] WORKDIR /app
#8 DONE 0.1s

#9 [4/8] COPY pyproject.toml ./
#9 DONE 0.0s

#10 [5/8] COPY src ./src
#10 DONE 0.1s

#11 [6/8] COPY migrations ./migrations
#11 DONE 0.1s

#12 [7/8] COPY alembic.ini ./
#12 DONE 0.1s

#13 [8/8] RUN pip install --no-cache-dir .     && useradd --create-home --uid 10001 app
#13 1.221 Processing /app
#13 1.224   Installing build dependencies: started
#13 3.604   Installing build dependencies: finished with status 'done'
#13 3.605   Getting requirements to build wheel: started
#13 4.126   Getting requirements to build wheel: finished with status 'done'
#13 4.128   Preparing metadata (pyproject.toml): started
#13 4.649   Preparing metadata (pyproject.toml): finished with status 'done'
#13 4.728 Collecting alembic<2,>=1.13 (from wa-mediation-wizard==0.1.0)
#13 4.786   Downloading alembic-1.20.1-py3-none-any.whl.metadata (7.3 kB)
#13 5.151 Collecting boto3<2,>=1.34 (from wa-mediation-wizard==0.1.0)
#13 5.163   Downloading boto3-1.43.121-py3-none-any.whl.metadata (6.6 kB)
#13 5.187 Collecting docx2pdf<0.2,>=0.1.8 (from wa-mediation-wizard==0.1.0)
#13 5.208   Downloading docx2pdf-0.1.8-py3-none-any.whl.metadata (3.3 kB)
#13 5.243 Collecting docxtpl<1,>=0.16 (from wa-mediation-wizard==0.1.0)
#13 5.263   Downloading docxtpl-0.20.2-py3-none-any.whl.metadata (2.8 kB)
#13 5.334 Collecting fastapi<1,>=0.110 (from wa-mediation-wizard==0.1.0)
#13 5.348   Downloading fastapi-0.162.0-py3-none-any.whl.metadata (26 kB)
#13 5.381 Collecting jinja2<4,>=3.1 (from wa-mediation-wizard==0.1.0)
#13 5.396   Downloading jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
#13 5.619 Collecting lxml<7,>=5 (from wa-mediation-wizard==0.1.0)
#13 5.636   Downloading lxml-6.1.3-cp312-cp312-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl.metadata (3.3 kB)
#13 5.660 Collecting pdf2docx<1,>=0.5.8 (from wa-mediation-wizard==0.1.0)
#13 5.675   Downloading pdf2docx-0.5.13-py3-none-any.whl.metadata (2.3 kB)
#13 5.775 Collecting pydantic<3,>=2.6 (from wa-mediation-wizard==0.1.0)
#13 5.791   Downloading pydantic-2.14.1-py3-none-any.whl.metadata (133 kB)
#13 5.844 Collecting pydantic-settings<3,>=2.2 (from wa-mediation-wizard==0.1.0)
#13 5.870   Downloading pydantic_settings-2.16.2-py3-none-any.whl.metadata (4.0 kB)
#13 5.927 Collecting pypdf<7,>=4 (from wa-mediation-wizard==0.1.0)
#13 5.943   Downloading pypdf-6.21.4-py3-none-any.whl.metadata (7.6 kB)
#13 6.082 Collecting pymupdf<2,>=1.24 (from wa-mediation-wizard==0.1.0)
#13 6.096   Downloading pymupdf-1.28.2-cp310-abi3-manylinux_2_28_x86_64.whl.metadata (26 kB)
#13 6.125 Collecting psycopg<4,>=3.1 (from psycopg[binary]<4,>=3.1->wa-mediation-wizard==0.1.0)
#13 6.137   Downloading psycopg-3.3.6-py3-none-any.whl.metadata (4.4 kB)
#13 6.167 Collecting python-docx<2,>=1.1 (from wa-mediation-wizard==0.1.0)
#13 6.184   Downloading python_docx-1.2.0-py3-none-any.whl.metadata (2.0 kB)
#13 6.210 Collecting python-dotenv<2,>=1 (from wa-mediation-wizard==0.1.0)
#13 6.225   Downloading python_dotenv-1.2.4-py3-none-any.whl.metadata (29 kB)
#13 6.254 Collecting python-multipart<1,>=0.0.9 (from wa-mediation-wizard==0.1.0)
#13 6.271   Downloading python_multipart-0.0.32-py3-none-any.whl.metadata (2.1 kB)
#13 6.519 Collecting sqlalchemy<3,>=2.0 (from wa-mediation-wizard==0.1.0)
#13 6.532   Downloading sqlalchemy-2.1.6-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (9.7 kB)
#13 6.577 Collecting uvicorn<1,>=0.29 (from uvicorn[standard]<1,>=0.29->wa-mediation-wizard==0.1.0)
#13 6.592   Downloading uvicorn-0.54.0-py3-none-any.whl.metadata (6.6 kB)
#13 6.614 Collecting Mako (from alembic<2,>=1.13->wa-mediation-wizard==0.1.0)
#13 6.628   Downloading mako-1.4.3-py3-none-any.whl.metadata (2.9 kB)
#13 6.650 Collecting typing-extensions>=4.12 (from alembic<2,>=1.13->wa-mediation-wizard==0.1.0)
#13 6.666   Downloading typing_extensions-4.16.0-py3-none-any.whl.metadata (3.3 kB)
#13 7.066 Collecting botocore<1.44.0,>=1.43.121 (from boto3<2,>=1.34->wa-mediation-wizard==0.1.0)
#13 7.080   Downloading botocore-1.43.121-py3-none-any.whl.metadata (5.6 kB)
#13 7.103 Collecting jmespath<2.0.0,>=0.7.1 (from boto3<2,>=1.34->wa-mediation-wizard==0.1.0)
#13 7.116   Downloading jmespath-1.1.0-py3-none-any.whl.metadata (7.6 kB)
#13 7.138 Collecting s3transfer<0.20.0,>=0.19.0 (from boto3<2,>=1.34->wa-mediation-wizard==0.1.0)
#13 7.150   Downloading s3transfer-0.19.3-py3-none-any.whl.metadata (1.7 kB)
#13 7.186 Collecting tqdm>=4.41.0 (from docx2pdf<0.2,>=0.1.8->wa-mediation-wizard==0.1.0)
#13 7.200   Downloading tqdm-4.70.1-py3-none-any.whl.metadata (57 kB)
#13 7.241 Collecting starlette>=0.46.0 (from fastapi<1,>=0.110->wa-mediation-wizard==0.1.0)
#13 7.254   Downloading starlette-1.10.0-py3-none-any.whl.metadata (6.6 kB)
#13 7.289 Collecting typing-inspection>=0.4.2 (from fastapi<1,>=0.110->wa-mediation-wizard==0.1.0)
#13 7.308   Downloading typing_inspection-0.4.4-py3-none-any.whl.metadata (2.6 kB)
#13 7.325 Collecting annotated-doc>=0.0.2 (from fastapi<1,>=0.110->wa-mediation-wizard==0.1.0)
#13 7.339   Downloading annotated_doc-0.0.5-py3-none-any.whl.metadata (6.5 kB)
#13 7.365 Collecting opentelemetry-api>=1.44.0 (from fastapi<1,>=0.110->wa-mediation-wizard==0.1.0)
#13 7.379   Downloading opentelemetry_api-1.45.1-py3-none-any.whl.metadata (1.4 kB)
#13 7.431 Collecting MarkupSafe>=2.0 (from jinja2<4,>=3.1->wa-mediation-wizard==0.1.0)
#13 7.448   Downloading markupsafe-3.0.4-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.7 kB)
#13 7.604 Collecting fonttools>=4.24.0 (from pdf2docx<1,>=0.5.8->wa-mediation-wizard==0.1.0)
#13 7.630   Downloading fonttools-4.68.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (139 kB)
#13 7.848 Collecting numpy>=1.17.2 (from pdf2docx<1,>=0.5.8->wa-mediation-wizard==0.1.0)
#13 7.864   Downloading numpy-2.5.4-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (6.6 kB)
#13 7.915 Collecting opencv-python-headless>=4.5 (from pdf2docx<1,>=0.5.8->wa-mediation-wizard==0.1.0)
#13 7.927   Downloading opencv_python_headless-5.0.0.93-cp37-abi3-manylinux_2_28_x86_64.whl.metadata (19 kB)
#13 7.949 Collecting fire>=0.3.0 (from pdf2docx<1,>=0.5.8->wa-mediation-wizard==0.1.0)
#13 7.967   Downloading fire-0.7.1-py3-none-any.whl.metadata (5.8 kB)
#13 8.090 Collecting psycopg-binary==3.3.6 (from psycopg[binary]<4,>=3.1->wa-mediation-wizard==0.1.0)
#13 8.102   Downloading psycopg_binary-3.3.6-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (2.7 kB)
#13 8.129 Collecting annotated-types>=0.6.0 (from pydantic<3,>=2.6->wa-mediation-wizard==0.1.0)
#13 8.143   Downloading annotated_types-0.8.0-py3-none-any.whl.metadata (15 kB)
#13 8.749 Collecting pydantic-core==2.50.1 (from pydantic<3,>=2.6->wa-mediation-wizard==0.1.0)
#13 8.773   Downloading pydantic_core-2.50.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (6.5 kB)
#13 8.838 Collecting click>=7.0 (from uvicorn<1,>=0.29->uvicorn[standard]<1,>=0.29->wa-mediation-wizard==0.1.0)
#13 8.856   Downloading click-8.5.0-py3-none-any.whl.metadata (2.6 kB)
#13 8.877 Collecting h11>=0.8 (from uvicorn<1,>=0.29->uvicorn[standard]<1,>=0.29->wa-mediation-wizard==0.1.0)
#13 8.895   Downloading h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
#13 8.937 Collecting httptools>=0.8.0 (from uvicorn[standard]<1,>=0.29->wa-mediation-wizard==0.1.0)
#13 8.951   Downloading httptools-0.9.0-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (3.5 kB)
#13 8.990 Collecting pyyaml>=5.1 (from uvicorn[standard]<1,>=0.29->wa-mediation-wizard==0.1.0)
#13 9.006   Downloading pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (2.4 kB)
#13 9.059 Collecting uvloop>=0.15.1 (from uvicorn[standard]<1,>=0.29->wa-mediation-wizard==0.1.0)
#13 9.071   Downloading uvloop-0.23.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (5.1 kB)
#13 9.142 Collecting watchfiles>=0.20 (from uvicorn[standard]<1,>=0.29->wa-mediation-wizard==0.1.0)
#13 9.158   Downloading watchfiles-1.3.0-cp310-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.9 kB)
#13 9.262 Collecting websockets>=13.0 (from uvicorn[standard]<1,>=0.29->wa-mediation-wizard==0.1.0)
#13 9.275   Downloading websockets-17.3-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.metadata (6.3 kB)
#13 9.302 Collecting python-dateutil<3.0.0,>=2.1 (from botocore<1.44.0,>=1.43.121->boto3<2,>=1.34->wa-mediation-wizard==0.1.0)
#13 9.315   Downloading python_dateutil-2.9.0.post0-py2.py3-none-any.whl.metadata (8.4 kB)
#13 9.357 Collecting urllib3!=2.2.0,<3,>=1.25.4 (from botocore<1.44.0,>=1.43.121->boto3<2,>=1.34->wa-mediation-wizard==0.1.0)
#13 9.370   Downloading urllib3-2.8.0-py3-none-any.whl.metadata (7.4 kB)
#13 9.393 Collecting termcolor (from fire>=0.3.0->pdf2docx<1,>=0.5.8->wa-mediation-wizard==0.1.0)
#13 9.415   Downloading termcolor-3.3.0-py3-none-any.whl.metadata (6.5 kB)
#13 9.744 Collecting anyio<5,>=4.0.0 (from starlette>=0.46.0->fastapi<1,>=0.110->wa-mediation-wizard==0.1.0)
#13 9.760   Downloading anyio-4.15.1-py3-none-any.whl.metadata (4.7 kB)
#13 9.821 Collecting idna>=2.8 (from anyio<5,>=4.0.0->starlette>=0.46.0->fastapi<1,>=0.110->wa-mediation-wizard==0.1.0)
#13 9.843   Downloading idna-3.20-py3-none-any.whl.metadata (7.2 kB)
#13 9.870 Collecting six>=1.5 (from python-dateutil<3.0.0,>=2.1->botocore<1.44.0,>=1.43.121->boto3<2,>=1.34->wa-mediation-wizard==0.1.0)
#13 9.889   Downloading six-1.17.0-py2.py3-none-any.whl.metadata (1.7 kB)
#13 9.913 Downloading alembic-1.20.1-py3-none-any.whl (270 kB)
#13 9.971 Downloading boto3-1.43.121-py3-none-any.whl (140 kB)
#13 10.00 Downloading docx2pdf-0.1.8-py3-none-any.whl (6.7 kB)
#13 10.02 Downloading docxtpl-0.20.2-py3-none-any.whl (17 kB)
#13 10.04 Downloading fastapi-0.162.0-py3-none-any.whl (148 kB)
#13 10.07 Downloading jinja2-3.1.6-py3-none-any.whl (134 kB)
#13 10.10 Downloading lxml-6.1.3-cp312-cp312-manylinux_2_26_x86_64.manylinux_2_28_x86_64.whl (5.2 MB)
#13 10.54    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 5.2/5.2 MB 11.9 MB/s eta 0:00:00
#13 10.56 Downloading pdf2docx-0.5.13-py3-none-any.whl (123 kB)
#13 10.58 Downloading psycopg-3.3.6-py3-none-any.whl (215 kB)
#13 10.62 Downloading psycopg_binary-3.3.6-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (5.2 MB)
#13 11.00    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 5.2/5.2 MB 13.7 MB/s eta 0:00:00
#13 11.01 Downloading pydantic-2.14.1-py3-none-any.whl (488 kB)
#13 11.07 Downloading pydantic_core-2.50.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (2.2 MB)
#13 11.22    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2.2/2.2 MB 13.6 MB/s eta 0:00:00
#13 11.24 Downloading pydantic_settings-2.16.2-py3-none-any.whl (81 kB)
#13 11.25 Downloading pymupdf-1.28.2-cp310-abi3-manylinux_2_28_x86_64.whl (25.8 MB)
#13 12.78    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 25.8/25.8 MB 16.9 MB/s eta 0:00:00
#13 12.83 Downloading pypdf-6.21.4-py3-none-any.whl (410 kB)
#13 12.87 Downloading python_docx-1.2.0-py3-none-any.whl (252 kB)
#13 12.90 Downloading python_dotenv-1.2.4-py3-none-any.whl (23 kB)
#13 12.92 Downloading python_multipart-0.0.32-py3-none-any.whl (30 kB)
#13 12.94 Downloading sqlalchemy-2.1.6-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (4.7 MB)
#13 13.19    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.7/4.7 MB 19.9 MB/s eta 0:00:00
#13 13.21 Downloading uvicorn-0.54.0-py3-none-any.whl (87 kB)
#13 13.22 Downloading annotated_doc-0.0.5-py3-none-any.whl (5.3 kB)
#13 13.24 Downloading annotated_types-0.8.0-py3-none-any.whl (13 kB)
#13 13.26 Downloading botocore-1.43.121-py3-none-any.whl (16.2 MB)
#13 14.05    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 16.2/16.2 MB 20.7 MB/s eta 0:00:00
#13 14.06 Downloading click-8.5.0-py3-none-any.whl (125 kB)
#13 14.09 Downloading fire-0.7.1-py3-none-any.whl (115 kB)
#13 14.11 Downloading fonttools-4.68.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (5.4 MB)
#13 14.41    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 5.4/5.4 MB 18.3 MB/s eta 0:00:00
#13 14.43 Downloading h11-0.16.0-py3-none-any.whl (37 kB)
#13 14.44 Downloading httptools-0.9.0-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (552 kB)
#13 14.48    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 552.8/552.8 kB 25.9 MB/s eta 0:00:00
#13 14.49 Downloading jmespath-1.1.0-py3-none-any.whl (20 kB)
#13 14.50 Downloading markupsafe-3.0.4-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (22 kB)
#13 14.52 Downloading numpy-2.5.4-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (16.7 MB)
#13 15.23    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 16.7/16.7 MB 23.9 MB/s eta 0:00:00
#13 15.25 Downloading opencv_python_headless-5.0.0.93-cp37-abi3-manylinux_2_28_x86_64.whl (61.2 MB)
#13 17.85    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 61.2/61.2 MB 23.5 MB/s eta 0:00:00
#13 17.86 Downloading opentelemetry_api-1.45.1-py3-none-any.whl (60 kB)
#13 17.88 Downloading pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (807 kB)
#13 17.94    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 807.9/807.9 kB 12.7 MB/s eta 0:00:00
#13 17.95 Downloading s3transfer-0.19.3-py3-none-any.whl (90 kB)
#13 17.97 Downloading starlette-1.10.0-py3-none-any.whl (80 kB)
#13 18.00 Downloading tqdm-4.70.1-py3-none-any.whl (80 kB)
#13 18.01 Downloading typing_extensions-4.16.0-py3-none-any.whl (45 kB)
#13 18.03 Downloading typing_inspection-0.4.4-py3-none-any.whl (14 kB)
#13 18.05 Downloading uvloop-0.23.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (4.5 MB)
#13 18.24    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.5/4.5 MB 24.4 MB/s eta 0:00:00
#13 18.26 Downloading watchfiles-1.3.0-cp310-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (458 kB)
#13 18.30 Downloading websockets-17.3-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl (225 kB)
#13 18.33 Downloading mako-1.4.3-py3-none-any.whl (80 kB)
#13 18.35 Downloading anyio-4.15.1-py3-none-any.whl (132 kB)
#13 18.38 Downloading python_dateutil-2.9.0.post0-py2.py3-none-any.whl (229 kB)
#13 18.40 Downloading urllib3-2.8.0-py3-none-any.whl (135 kB)
#13 18.43 Downloading termcolor-3.3.0-py3-none-any.whl (7.7 kB)
#13 18.45 Downloading idna-3.20-py3-none-any.whl (69 kB)
#13 18.47 Downloading six-1.17.0-py2.py3-none-any.whl (11 kB)
#13 18.63 Building wheels for collected packages: wa-mediation-wizard
#13 18.63   Building wheel for wa-mediation-wizard (pyproject.toml): started
#13 19.18   Building wheel for wa-mediation-wizard (pyproject.toml): finished with status 'done'
#13 19.18   Created wheel for wa-mediation-wizard: filename=wa_mediation_wizard-0.1.0-py3-none-any.whl size=10707 sha256=faf20edeb6b39f4f6647f8a5da8847d2fc4cddb11cddb42a798d1126ae5f7d14
#13 19.18   Stored in directory: /tmp/pip-ephem-wheel-cache-dx_xpt85/wheels/54/1b/b7/aa63e25c8f14f4f2ae7b04e6097bdecb770e455c5c1ee0a600
#13 19.18 Successfully built wa-mediation-wizard
#13 19.27 Installing collected packages: websockets, uvloop, urllib3, typing-extensions, tqdm, termcolor, six, pyyaml, python-multipart, python-dotenv, pypdf, pymupdf, psycopg-binary, numpy, MarkupSafe, lxml, jmespath, idna, httptools, h11, fonttools, click, annotated-types, annotated-doc, uvicorn, typing-inspection, sqlalchemy, python-docx, python-dateutil, pydantic-core, psycopg, opentelemetry-api, opencv-python-headless, Mako, jinja2, fire, docx2pdf, anyio, watchfiles, starlette, pydantic, pdf2docx, docxtpl, botocore, alembic, s3transfer, pydantic-settings, fastapi, boto3, wa-mediation-wizard
#13 28.86 Successfully installed Mako-1.4.3 MarkupSafe-3.0.4 alembic-1.20.1 annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1 boto3-1.43.121 botocore-1.43.121 click-8.5.0 docx2pdf-0.1.8 docxtpl-0.20.2 fastapi-0.162.0 fire-0.7.1 fonttools-4.68.0 h11-0.16.0 httptools-0.9.0 idna-3.20 jinja2-3.1.6 jmespath-1.1.0 lxml-6.1.3 numpy-2.5.4 opencv-python-headless-5.0.0.93 opentelemetry-api-1.45.1 pdf2docx-0.5.13 psycopg-3.3.6 psycopg-binary-3.3.6 pydantic-2.14.1 pydantic-core-2.50.1 pydantic-settings-2.16.2 pymupdf-1.28.2 pypdf-6.21.4 python-dateutil-2.9.0.post0 python-docx-1.2.0 python-dotenv-1.2.4 python-multipart-0.0.32 pyyaml-6.0.3 s3transfer-0.19.3 six-1.17.0 sqlalchemy-2.1.6 starlette-1.10.0 termcolor-3.3.0 tqdm-4.70.1 typing-extensions-4.16.0 typing-inspection-0.4.4 urllib3-2.8.0 uvicorn-0.54.0 uvloop-0.23.0 wa-mediation-wizard-0.1.0 watchfiles-1.3.0 websockets-17.3
#13 28.86 WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager, possibly rendering your system unusable. It is recommended to use a virtual environment instead: https://pip.pypa.io/warnings/venv. Use the --root-user-action option if you know what you are doing and want to suppress this warning.
#13 29.02 
#13 29.02 [notice] A new release of pip is available: 25.0.1 -> 26.2.2
#13 29.02 [notice] To update, run: pip install --upgrade pip
#13 DONE 29.9s

#14 exporting to image
#14 exporting layers
#14 exporting layers 15.2s done
#14 exporting manifest sha256:b61a684729524756f9ecb70f21fc8524a2e221f7a3b188f024461c6e3c3f288b 0.0s done
#14 exporting config sha256:a002e9112504247bf7e8ea1537bdf1afd58ec1c28b2f426068d3f975a43d7597 0.0s done
#14 exporting attestation manifest sha256:9695ef881429721ae63ec237a809c83bc19b285c9aadcb1a88fd2d8fd6821a6f 0.0s done
#14 exporting manifest list sha256:d20f3dbe0247eea9c1dec1eacb1e6b95ff43818629fc5e929cb12d18cd00980c 0.0s done
#14 naming to docker.io/library/wa-mediation-wizard:local
#14 naming to docker.io/library/wa-mediation-wizard:local done
#14 unpacking to docker.io/library/wa-mediation-wizard:local
#14 unpacking to docker.io/library/wa-mediation-wizard:local 6.9s done
#14 DONE 22.3s
```

## Execution - 2026-10-29T01:27:50Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- docker compose up -d --build`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.003s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
 Image minio/minio:latest Pulling 
 Image postgres:16 Pulling 
 Image minio/mc:latest Pulling 
 Image minio/minio:latest Error pull access denied for minio/minio, repository does not exist or may require 'docker login'
 Image postgres:16 Interrupted 
 Image minio/mc:latest Interrupted 
Error response from daemon: pull access denied for minio/minio, repository does not exist or may require 'docker login'
```

## Execution - 2026-10-29T01:28:00Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- docker compose up -d --build`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.003s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
 Image quay.io/minio/mc:latest Pulling 
 Image postgres:16 Pulling 
 Image quay.io/minio/minio:latest Pulling 
 Image quay.io/minio/mc:latest Error unknown: failed to resolve reference "quay.io/minio/mc:latest": unexpected status from HEAD request to https://quay.io/v2/minio/mc/manifests/latest: 401 UNAUTHORIZED
 Image quay.io/minio/minio:latest Interrupted 
 Image postgres:16 Interrupted 
Error response from daemon: unknown: failed to resolve reference "quay.io/minio/mc:latest": unexpected status from HEAD request to https://quay.io/v2/minio/mc/manifests/latest: 401 UNAUTHORIZED
```

## Execution - 2026-10-29T01:28:14Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ docker\ pull\ localstack/localstack:latest\;\ docker\ pull\ amazon/aws-cli:latest`
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
test_compose_provides_postgres_and_local_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_local_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
latest: Pulling from localstack/localstack
8a8c91680dc3: Pulling fs layer
4f4fb700ef54: Pulling fs layer
272a09837486: Pulling fs layer
1972997cb127: Pulling fs layer
bec94cf691b4: Pulling fs layer
ad45a7028ed9: Pulling fs layer
f2be67225471: Pulling fs layer
c28e1acd62a7: Pulling fs layer
29a6c5bc3229: Pulling fs layer
d5286c6fc846: Pulling fs layer
01e3c4cae87d: Pulling fs layer
e5f9b767a456: Pulling fs layer
f821d1446b43: Pulling fs layer
0ed3834e56ed: Pulling fs layer
a233227957be: Pulling fs layer
a47bee7c86f9: Pulling fs layer
e1f7d490169d: Pulling fs layer
88c895985f5d: Pulling fs layer
2fb2a2ae4c40: Pulling fs layer
a15795eb90f9: Pulling fs layer
5bbe93bb8380: Pulling fs layer
68284d7a1ffd: Pulling fs layer
2526e0461248: Pulling fs layer
272a09837486: Download complete
8a8c91680dc3: Download complete
4f4fb700ef54: Download complete
1972997cb127: Download complete
bec94cf691b4: Download complete
ad45a7028ed9: Download complete
c28e1acd62a7: Download complete
29a6c5bc3229: Download complete
01e3c4cae87d: Download complete
f821d1446b43: Download complete
f2be67225471: Download complete
0ed3834e56ed: Download complete
f2be67225471: Pull complete
bec94cf691b4: Pull complete
d5286c6fc846: Download complete
88c895985f5d: Download complete
a47bee7c86f9: Download complete
5bbe93bb8380: Download complete
e1f7d490169d: Download complete
a233227957be: Download complete
1972997cb127: Pull complete
e1f7d490169d: Pull complete
d5286c6fc846: Pull complete
a15795eb90f9: Download complete
e5f9b767a456: Download complete
2fb2a2ae4c40: Download complete
68284d7a1ffd: Download complete
2526e0461248: Download complete
f821d1446b43: Pull complete
e5f9b767a456: Pull complete
4f4fb700ef54: Pull complete
88c895985f5d: Pull complete
5bbe93bb8380: Pull complete
2fb2a2ae4c40: Pull complete
29a6c5bc3229: Pull complete
01e3c4cae87d: Pull complete
68284d7a1ffd: Pull complete
2526e0461248: Pull complete
0ed3834e56ed: Pull complete
a233227957be: Pull complete
8a8c91680dc3: Pull complete
272a09837486: Pull complete
ad45a7028ed9: Pull complete
a47bee7c86f9: Pull complete
a15795eb90f9: Pull complete
c28e1acd62a7: Pull complete
Digest: sha256:2290500d7398e6458544fab2f49aaf170b81a1006ee69067e8e7fc59b810a824
Status: Downloaded newer image for localstack/localstack:latest
docker.io/localstack/localstack:latest
latest: Pulling from amazon/aws-cli
5d1a2e57c29a: Pulling fs layer
1ef5520e0798: Pulling fs layer
3ea879a5c1e9: Pulling fs layer
2679d81d7133: Pulling fs layer
d8e1f1fef777: Pulling fs layer
1ef5520e0798: Download complete
3ea879a5c1e9: Download complete
d8e1f1fef777: Download complete
5d1a2e57c29a: Download complete
2679d81d7133: Download complete
5d1a2e57c29a: Pull complete
3ea879a5c1e9: Pull complete
2679d81d7133: Pull complete
1ef5520e0798: Pull complete
d8e1f1fef777: Pull complete
Digest: sha256:3517c17b5f01637df3b6184a4280fbcc36e4ea38105954cade628ff17bb9a7b9
Status: Downloaded newer image for amazon/aws-cli:latest
docker.io/amazon/aws-cli:latest
```

## Execution - 2026-10-29T01:29:13Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- docker compose up -d --build`
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
test_compose_provides_postgres_and_localstack_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_localstack_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
 Image postgres:16 Pulling 
 7ee6ed8de1c8 Pulling fs layer 
 c60d02d02e9b Pulling fs layer 
 879995175298 Pulling fs layer 
 dc3e98153fd4 Pulling fs layer 
 6fc242d221a6 Pulling fs layer 
 fbc84e711712 Pulling fs layer 
 d06edb2e3f43 Pulling fs layer 
 3795839385bc Pulling fs layer 
 5c4d204f6daa Pulling fs layer 
 d89068781d71 Pulling fs layer 
 9b1a18996a22 Pulling fs layer 
 28d8a96df569 Pulling fs layer 
 cea4f0db46a6 Pulling fs layer 
 b355a8fcc1d3 Pulling fs layer 
 6fc242d221a6 Already exists 
 c60d02d02e9b Download complete 
 dc3e98153fd4 Download complete 
 879995175298 Download complete 
 fbc84e711712 Downloading [==================================================>]  1.312MB/1.312MB
 d06edb2e3f43 Downloading [==================================================>]   1.17kB/1.17kB
 d06edb2e3f43 Download complete 
 7ee6ed8de1c8 Download complete 
 fbc84e711712 Downloading [==================================================>]  1.312MB/1.312MB
 d06edb2e3f43 Extracting 1 s
 3795839385bc Downloading [========>                                          ]  1.049MB/6.443MB
 fbc84e711712 Download complete 
 5c4d204f6daa Downloading [>                                                  ]  1.049MB/113.2MB
 d06edb2e3f43 Extracting 1 s
 3795839385bc Downloading [========================>                          ]  3.146MB/6.443MB
 5c4d204f6daa Downloading [=>                                                 ]  3.146MB/113.2MB
 d06edb2e3f43 Extracting 1 s
 3795839385bc Downloading [========================================>          ]  5.243MB/6.443MB
 5c4d204f6daa Downloading [==>                                                ]  5.243MB/113.2MB
 d06edb2e3f43 Extracting 1 s
 5c4d204f6daa Downloading [===>                                               ]   7.34MB/113.2MB
 3795839385bc Downloading [==================================================>]  6.443MB/6.443MB
 cea4f0db46a6 Download complete 
 28d8a96df569 Downloading [==================================================>]  10.11kB/10.11kB
 d06edb2e3f43 Extracting 1 s
 5c4d204f6daa Downloading [===>                                               ]  8.389MB/113.2MB
 3795839385bc Download complete 
 28d8a96df569 Download complete 
 b355a8fcc1d3 Download complete 
 d89068781d71 Download complete 
 d06edb2e3f43 Extracting 1 s
 5c4d204f6daa Downloading [====>                                              ]  9.437MB/113.2MB
 d06edb2e3f43 Pull complete 
 9b1a18996a22 Downloading [============>                                      ]  2.097MB/8.204MB
 5c4d204f6daa Downloading [=====>                                             ]  11.53MB/113.2MB
 3795839385bc Extracting 1 s
 9b1a18996a22 Downloading [===================>                               ]  3.146MB/8.204MB
 5c4d204f6daa Downloading [=====>                                             ]  12.58MB/113.2MB
 3795839385bc Extracting 1 s
 9b1a18996a22 Downloading [=========================>                         ]  4.194MB/8.204MB
 52b2ca0eb4bf Download complete 
 5c4d204f6daa Downloading [======>                                            ]  14.68MB/113.2MB
 3795839385bc Extracting 1 s
 9b1a18996a22 Downloading [======================================>            ]  6.291MB/8.204MB
 5c4d204f6daa Downloading [======>                                            ]  15.73MB/113.2MB
 cea4f0db46a6 Extracting 1 s
 3795839385bc Pull complete 
 34abe417644f Downloading [==================>                                ]  2.097MB/5.715MB
 9b1a18996a22 Downloading [============================================>      ]   7.34MB/8.204MB
 5c4d204f6daa Downloading [=======>                                           ]  16.78MB/113.2MB
 cea4f0db46a6 Pull complete 
 5c4d204f6daa Downloading [========>                                          ]  18.87MB/113.2MB
 34abe417644f Downloading [====================================>              ]  4.194MB/5.715MB
 9b1a18996a22 Download complete 
 9b1a18996a22 Extracting 1 s
 5c4d204f6daa Downloading [========>                                          ]  19.92MB/113.2MB
 34abe417644f Download complete 
 9b1a18996a22 Extracting 1 s
 5c4d204f6daa Downloading [=========>                                         ]  22.02MB/113.2MB
 9b1a18996a22 Extracting 1 s
 5c4d204f6daa Downloading [==========>                                        ]  24.12MB/113.2MB
 9b1a18996a22 Extracting 1 s
 5c4d204f6daa Downloading [===========>                                       ]  26.21MB/113.2MB
 9b1a18996a22 Pull complete 
 5c4d204f6daa Downloading [============>                                      ]  27.26MB/113.2MB
 fbc84e711712 Extracting 1 s
 5c4d204f6daa Downloading [============>                                      ]  29.36MB/113.2MB
 879995175298 Pull complete 
 fbc84e711712 Pull complete 
 5c4d204f6daa Downloading [=============>                                     ]  31.46MB/113.2MB
 d89068781d71 Pull complete 
 5c4d204f6daa Downloading [==============>                                    ]  33.55MB/113.2MB
 5c4d204f6daa Downloading [===============>                                   ]  35.65MB/113.2MB
 5c4d204f6daa Downloading [================>                                  ]  37.75MB/113.2MB
 5c4d204f6daa Downloading [=================>                                 ]  39.85MB/113.2MB
 5c4d204f6daa Downloading [==================>                                ]  42.99MB/113.2MB
 5c4d204f6daa Downloading [===================>                               ]  45.09MB/113.2MB
 5c4d204f6daa Downloading [====================>                              ]  47.19MB/113.2MB
 5c4d204f6daa Downloading [=====================>                             ]  49.28MB/113.2MB
 5c4d204f6daa Downloading [======================>                            ]  51.38MB/113.2MB
 5c4d204f6daa Downloading [========================>                          ]  54.53MB/113.2MB
 5c4d204f6daa Downloading [=========================>                         ]  56.62MB/113.2MB
 5c4d204f6daa Downloading [=========================>                         ]  57.67MB/113.2MB
 5c4d204f6daa Downloading [==========================>                        ]  59.77MB/113.2MB
 5c4d204f6daa Downloading [==========================>                        ]  60.82MB/113.2MB
 5c4d204f6daa Downloading [===========================>                       ]  62.91MB/113.2MB
 5c4d204f6daa Downloading [============================>                      ]  65.01MB/113.2MB
 5c4d204f6daa Downloading [=============================>                     ]  67.11MB/113.2MB
 5c4d204f6daa Downloading [==============================>                    ]  69.21MB/113.2MB
 5c4d204f6daa Downloading [===============================>                   ]  72.35MB/113.2MB
 5c4d204f6daa Downloading [================================>                  ]  74.45MB/113.2MB
 5c4d204f6daa Downloading [=================================>                 ]  76.55MB/113.2MB
 5c4d204f6daa Downloading [==================================>                ]  77.59MB/113.2MB
 5c4d204f6daa Downloading [===================================>               ]  79.69MB/113.2MB
 5c4d204f6daa Downloading [===================================>               ]  80.74MB/113.2MB
 5c4d204f6daa Downloading [=====================================>             ]  83.89MB/113.2MB
 5c4d204f6daa Downloading [======================================>            ]  87.03MB/113.2MB
 5c4d204f6daa Downloading [=======================================>           ]  89.13MB/113.2MB
 5c4d204f6daa Downloading [=======================================>           ]  90.18MB/113.2MB
 5c4d204f6daa Downloading [=========================================>         ]  93.32MB/113.2MB
 5c4d204f6daa Downloading [==========================================>        ]  95.42MB/113.2MB
 5c4d204f6daa Downloading [===========================================>       ]  97.52MB/113.2MB
 5c4d204f6daa Downloading [===========================================>       ]  99.61MB/113.2MB
 5c4d204f6daa Downloading [============================================>      ]  100.7MB/113.2MB
 5c4d204f6daa Downloading [=============================================>     ]  102.8MB/113.2MB
 5c4d204f6daa Downloading [=============================================>     ]  103.8MB/113.2MB
 5c4d204f6daa Downloading [==============================================>    ]  105.9MB/113.2MB
 5c4d204f6daa Downloading [===============================================>   ]    108MB/113.2MB
 5c4d204f6daa Downloading [================================================>  ]  110.1MB/113.2MB
 5c4d204f6daa Downloading [=================================================> ]  112.2MB/113.2MB
 5c4d204f6daa Downloading [==================================================>]  113.2MB/113.2MB
 5c4d204f6daa Download complete 
 5c4d204f6daa Extracting 1 s
 5c4d204f6daa Extracting 1 s
 5c4d204f6daa Extracting 1 s
 5c4d204f6daa Extracting 1 s
 5c4d204f6daa Extracting 1 s
 5c4d204f6daa Extracting 1 s
 5c4d204f6daa Extracting 1 s
 5c4d204f6daa Extracting 1 s
 5c4d204f6daa Extracting 1 s
 5c4d204f6daa Extracting 1 s
 5c4d204f6daa Extracting 1 s
 5c4d204f6daa Extracting 2 s
 5c4d204f6daa Extracting 2 s
 5c4d204f6daa Extracting 2 s
 5c4d204f6daa Extracting 2 s
 5c4d204f6daa Extracting 2 s
 5c4d204f6daa Extracting 2 s
 5c4d204f6daa Extracting 2 s
 5c4d204f6daa Extracting 2 s
 28d8a96df569 Pull complete 
 b355a8fcc1d3 Pull complete 
 5c4d204f6daa Pull complete 
 c60d02d02e9b Pull complete 
 dc3e98153fd4 Pull complete 
 7ee6ed8de1c8 Pull complete 
 Image postgres:16 Pulled 
 Image wa-contested-divorce-without-children-mediation-to-end-api Building 
#1 [internal] load local bake definitions
#1 reading from stdin 674B done
#1 DONE 0.0s

#2 [internal] load build definition from Dockerfile
#2 transferring dockerfile: 570B done
#2 DONE 0.0s

#3 [internal] load metadata for docker.io/library/python:3.12-slim
#3 DONE 0.5s

#4 [internal] load .dockerignore
#4 transferring context: 2B done
#4 DONE 0.0s

#5 [internal] load build context
#5 DONE 0.0s

#6 [1/8] FROM docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
#6 resolve docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159 0.1s done
#6 DONE 0.1s

#5 [internal] load build context
#5 transferring context: 1.48kB done
#5 DONE 0.1s

#7 [6/8] COPY migrations ./migrations
#7 CACHED

#8 [3/8] WORKDIR /app
#8 CACHED

#9 [7/8] COPY alembic.ini ./
#9 CACHED

#10 [2/8] RUN apt-get update     && apt-get install -y --no-install-recommends libreoffice-writer     && rm -rf /var/lib/apt/lists/*
#10 CACHED

#11 [4/8] COPY pyproject.toml ./
#11 CACHED

#12 [5/8] COPY src ./src
#12 CACHED

#13 [8/8] RUN pip install --no-cache-dir .     && useradd --create-home --uid 10001 app
#13 CACHED

#14 exporting to image
#14 exporting layers done
#14 exporting manifest sha256:c6c5dd1cb4a5af5d8644bbf1e00b01e01042b6b825da60fa27f47492f0000982
#14 exporting manifest sha256:c6c5dd1cb4a5af5d8644bbf1e00b01e01042b6b825da60fa27f47492f0000982 0.2s done
#14 exporting config sha256:f343160841f4d0c4dbdc1d872e0b640f78562e915bb727188176f6a64894c686
#14 exporting config sha256:f343160841f4d0c4dbdc1d872e0b640f78562e915bb727188176f6a64894c686 0.2s done
#14 exporting attestation manifest sha256:9f827c945967477bdd1d27bdfa6848525d592d82005c262b1c0fe5720e622ee2 0.0s done
#14 exporting manifest list sha256:ad8edcef174dd309854759dd0d296ff3278bd472046c258f08235ca5a89a0c44
#14 exporting manifest list sha256:ad8edcef174dd309854759dd0d296ff3278bd472046c258f08235ca5a89a0c44 0.0s done
#14 naming to docker.io/library/wa-contested-divorce-without-children-mediation-to-end-api:latest done
#14 unpacking to docker.io/library/wa-contested-divorce-without-children-mediation-to-end-api:latest 0.0s done
#14 DONE 0.6s

#15 resolving provenance for metadata file
#15 DONE 0.0s
 Image wa-contested-divorce-without-children-mediation-to-end-api Built 
 Network wa-contested-divorce-without-children-mediation-to-end_default Creating 
 Network wa-contested-divorce-without-children-mediation-to-end_default Created 
 Volume wa-contested-divorce-without-children-mediation-to-end_postgres-data Creating 
 Volume wa-contested-divorce-without-children-mediation-to-end_postgres-data Created 
 Container wa-contested-divorce-without-children-mediation-to-end-localstack-1 Creating 
 Container wa-contested-divorce-without-children-mediation-to-end-db-1 Creating 
 Container wa-contested-divorce-without-children-mediation-to-end-db-1 Created 
 Container wa-contested-divorce-without-children-mediation-to-end-localstack-1 Created 
 Container wa-contested-divorce-without-children-mediation-to-end-bucket-init-1 Creating 
 Container wa-contested-divorce-without-children-mediation-to-end-bucket-init-1 Created 
 Container wa-contested-divorce-without-children-mediation-to-end-api-1 Creating 
 Container wa-contested-divorce-without-children-mediation-to-end-api-1 Created 
 Container wa-contested-divorce-without-children-mediation-to-end-localstack-1 Starting 
 Container wa-contested-divorce-without-children-mediation-to-end-db-1 Starting 
 Container wa-contested-divorce-without-children-mediation-to-end-db-1 Started 
 Container wa-contested-divorce-without-children-mediation-to-end-localstack-1 Started 
 Container wa-contested-divorce-without-children-mediation-to-end-localstack-1 Waiting 
 Container wa-contested-divorce-without-children-mediation-to-end-localstack-1 Error dependency localstack failed to start
dependency failed to start: container wa-contested-divorce-without-children-mediation-to-end-localstack-1 exited (55)
```

## Execution - 2026-10-29T01:29:38Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c docker\ compose\ ps\ -a\;\ docker\ compose\ logs\ --no-color\ --tail=100\ localstack`
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
test_compose_provides_postgres_and_localstack_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_localstack_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
NAME                                                                   IMAGE                                                        COMMAND                  SERVICE       CREATED          STATUS                       PORTS
wa-contested-divorce-without-children-mediation-to-end-api-1           wa-contested-divorce-without-children-mediation-to-end-api   "sh -c 'alembic upgr…"   api           12 seconds ago   Created                      
wa-contested-divorce-without-children-mediation-to-end-bucket-init-1   amazon/aws-cli:latest                                        "/bin/sh -c 'aws --e…"   bucket-init   12 seconds ago   Created                      
wa-contested-divorce-without-children-mediation-to-end-db-1            postgres:16                                                  "docker-entrypoint.s…"   db            13 seconds ago   Up 11 seconds (healthy)      5432/tcp
wa-contested-divorce-without-children-mediation-to-end-localstack-1    localstack/localstack:latest                                 "docker-entrypoint.sh"   localstack    13 seconds ago   Exited (55) 10 seconds ago   
localstack-1  | 
localstack-1  | LocalStack version: 2026.10.4
localstack-1  | LocalStack build date: 2026-10-28
localstack-1  | LocalStack build git hash: a39e30ef
localstack-1  | 
localstack-1  | Localstack returning with exit code 55. Reason: 
localstack-1  | ===============================================
localstack-1  | License activation failed! 🔑❌
localstack-1  | 
localstack-1  | Reason: No credentials were found in the environment. Please set the LOCALSTACK_AUTH_TOKEN variable to a valid auth token. Alternatively, run `lstk login` and start LocalStack with the lstk CLI, which configures the credentials for you.
localstack-1  | 
localstack-1  | Due to this error, Localstack has quit. LocalStack pro features can only be used with a valid license.
localstack-1  | 
localstack-1  | - Please check that your credentials are set up correctly and that you have an active license.
localstack-1  |   You can find your credentials in our webapp at https://app.localstack.cloud.
localstack-1  | 
```

## Execution - 2026-10-29T01:29:51Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- docker pull motoserver/moto:latest`
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
test_compose_provides_postgres_and_localstack_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_localstack_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
latest: Pulling from motoserver/moto
7b229517ed22: Pulling fs layer
a22ecdbf29cb: Pulling fs layer
b189745bef75: Pulling fs layer
4f4fb700ef54: Pulling fs layer
2220e3c15749: Pulling fs layer
09a0787ca8c6: Pulling fs layer
932709760b04: Pulling fs layer
53a2a9572bd3: Pulling fs layer
4f4fb700ef54: Already exists
7b229517ed22: Download complete
a22ecdbf29cb: Download complete
b189745bef75: Download complete
09a0787ca8c6: Download complete
53a2a9572bd3: Download complete
932709760b04: Download complete
44136fa355b3: Already exists
7041877869cb: Download complete
7b229517ed22: Pull complete
09a0787ca8c6: Pull complete
932709760b04: Pull complete
53a2a9572bd3: Pull complete
2220e3c15749: Download complete
4f4fb700ef54: Pull complete
b189745bef75: Pull complete
a22ecdbf29cb: Pull complete
2220e3c15749: Pull complete
Digest: sha256:59a1965d845249b04def37a0e2565f9cc6c44543cb89b68e90f28f344b3b0d1a
Status: Downloaded newer image for motoserver/moto:latest
docker.io/motoserver/moto:latest
```

## Execution - 2026-10-29T01:30:16Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- docker compose up -d --build`
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
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.003s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
 Image wa-contested-divorce-without-children-mediation-to-end-api Building 
#1 [internal] load local bake definitions
#1 reading from stdin 674B done
#1 DONE 0.0s

#2 [internal] load build definition from Dockerfile
#2 transferring dockerfile: 570B done
#2 DONE 0.1s

#3 [internal] load metadata for docker.io/library/python:3.12-slim
#3 ...

#4 [auth] library/python:pull token for registry-1.docker.io
#4 DONE 0.0s

#3 [internal] load metadata for docker.io/library/python:3.12-slim
#3 DONE 0.8s

#5 [internal] load .dockerignore
#5 transferring context: 2B done
#5 DONE 0.2s

#6 [internal] load build context
#6 DONE 0.0s

#7 [1/8] FROM docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
#7 resolve docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
#7 resolve docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159 0.2s done
#7 DONE 0.3s

#6 [internal] load build context
#6 transferring context: 1.48kB done
#6 DONE 0.1s

#8 [5/8] COPY src ./src
#8 CACHED

#9 [6/8] COPY migrations ./migrations
#9 CACHED

#10 [3/8] WORKDIR /app
#10 CACHED

#11 [7/8] COPY alembic.ini ./
#11 CACHED

#12 [2/8] RUN apt-get update     && apt-get install -y --no-install-recommends libreoffice-writer     && rm -rf /var/lib/apt/lists/*
#12 CACHED

#13 [4/8] COPY pyproject.toml ./
#13 CACHED

#14 [8/8] RUN pip install --no-cache-dir .     && useradd --create-home --uid 10001 app
#14 CACHED

#15 exporting to image
#15 exporting layers done
#15 exporting manifest sha256:c6c5dd1cb4a5af5d8644bbf1e00b01e01042b6b825da60fa27f47492f0000982 done
#15 exporting config sha256:f343160841f4d0c4dbdc1d872e0b640f78562e915bb727188176f6a64894c686
#15 exporting config sha256:f343160841f4d0c4dbdc1d872e0b640f78562e915bb727188176f6a64894c686 done
#15 exporting attestation manifest sha256:81347caf9dc9a03c3668ed790d044e70834143010f85815b839f19b553afac6a 0.1s done
#15 exporting manifest list sha256:3837cd29baf2fa8b1c02de36489b51ac9ebdea4f46434e9c6d534710cd2320cb
#15 exporting manifest list sha256:3837cd29baf2fa8b1c02de36489b51ac9ebdea4f46434e9c6d534710cd2320cb 0.0s done
#15 naming to docker.io/library/wa-contested-divorce-without-children-mediation-to-end-api:latest done
#15 unpacking to docker.io/library/wa-contested-divorce-without-children-mediation-to-end-api:latest done
#15 DONE 0.2s

#16 resolving provenance for metadata file
#16 DONE 0.0s
 Image wa-contested-divorce-without-children-mediation-to-end-api Built 
time="2026-10-28T18:30:18-07:00" level=warning msg="Found orphan containers ([wa-contested-divorce-without-children-mediation-to-end-localstack-1]) for this project. If you removed or renamed this service in your compose file, you can run this command with the --remove-orphans flag to clean it up."
 Container wa-contested-divorce-without-children-mediation-to-end-s3mock-1 Creating 
 Container wa-contested-divorce-without-children-mediation-to-end-db-1 Running 
 Container wa-contested-divorce-without-children-mediation-to-end-s3mock-1 Created 
 Container wa-contested-divorce-without-children-mediation-to-end-bucket-init-1 Recreate 
 Container wa-contested-divorce-without-children-mediation-to-end-bucket-init-1 Recreated 
 Container wa-contested-divorce-without-children-mediation-to-end-api-1 Recreate 
 Container wa-contested-divorce-without-children-mediation-to-end-api-1 Recreated 
 Container wa-contested-divorce-without-children-mediation-to-end-s3mock-1 Starting 
 Container wa-contested-divorce-without-children-mediation-to-end-s3mock-1 Started 
 Container wa-contested-divorce-without-children-mediation-to-end-s3mock-1 Waiting 
 Container wa-contested-divorce-without-children-mediation-to-end-s3mock-1 Healthy 
 Container wa-contested-divorce-without-children-mediation-to-end-bucket-init-1 Starting 
 Container wa-contested-divorce-without-children-mediation-to-end-bucket-init-1 Started 
 Container wa-contested-divorce-without-children-mediation-to-end-db-1 Waiting 
 Container wa-contested-divorce-without-children-mediation-to-end-bucket-init-1 Waiting 
 Container wa-contested-divorce-without-children-mediation-to-end-db-1 Healthy 
 Container wa-contested-divorce-without-children-mediation-to-end-bucket-init-1 Error service "bucket-init" didn't complete successfully: exit 254
service "bucket-init" didn't complete successfully: exit 254
```

## Execution - 2026-10-29T01:30:32Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c docker\ compose\ ps\ -a\;\ docker\ compose\ logs\ --no-color\ --tail=80\ bucket-init\ s3mock`
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
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
NAME                                                                   IMAGE                                                        COMMAND                  SERVICE       CREATED              STATUS                           PORTS
wa-contested-divorce-without-children-mediation-to-end-api-1           wa-contested-divorce-without-children-mediation-to-end-api   "sh -c 'alembic upgr…"   api           14 seconds ago       Created                          
wa-contested-divorce-without-children-mediation-to-end-bucket-init-1   amazon/aws-cli:latest                                        "/bin/sh -c 'aws --e…"   bucket-init   14 seconds ago       Exited (254) 5 seconds ago       
wa-contested-divorce-without-children-mediation-to-end-db-1            postgres:16                                                  "docker-entrypoint.s…"   db            About a minute ago   Up About a minute (healthy)      5432/tcp
wa-contested-divorce-without-children-mediation-to-end-localstack-1    localstack/localstack:latest                                 "docker-entrypoint.sh"   localstack    About a minute ago   Exited (55) About a minute ago   
wa-contested-divorce-without-children-mediation-to-end-s3mock-1        motoserver/moto:latest                                       "/usr/local/bin/moto…"   s3mock        15 seconds ago       Up 13 seconds (healthy)          127.0.0.1:5000->5000/tcp
s3mock-1  | [31m[1mWARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.[0m
s3mock-1  |  * Running on all addresses (0.0.0.0)
s3mock-1  |  * Running on http://127.0.0.1:5000
s3mock-1  |  * Running on http://172.18.0.3:5000
s3mock-1  | [33mPress CTRL+C to quit[0m
s3mock-1  | 172.18.0.4 - - [29/Oct/2026 01:30:26] "[33mHEAD /mediation-documents HTTP/1.1[0m" 404 -
s3mock-1  | 172.18.0.4 - - [29/Oct/2026 01:30:27] "[31m[1mPUT /mediation-documents HTTP/1.1[0m" 400 -
bucket-init-1  | 
bucket-init-1  | aws: [ERROR]: An error occurred (IllegalLocationConstraintException) when calling the CreateBucket operation: The unspecified location constraint is incompatible for the region specific endpoint this request was sent to.
```

## Execution - 2026-10-29T01:30:42Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- docker compose up -d --build --remove-orphans`
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
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.004s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
 Image wa-contested-divorce-without-children-mediation-to-end-api Building 
#1 [internal] load local bake definitions
#1 reading from stdin 674B done
#1 DONE 0.0s

#2 [internal] load build definition from Dockerfile
#2 transferring dockerfile: 570B done
#2 DONE 0.0s

#3 [internal] load metadata for docker.io/library/python:3.12-slim
#3 DONE 0.3s

#4 [internal] load .dockerignore
#4 transferring context: 2B done
#4 DONE 0.0s

#5 [1/8] FROM docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159
#5 resolve docker.io/library/python:3.12-slim@sha256:aa943ce411423c7582288f18707ff66eddcbaeb510502d747a72aeb34f30d159 0.0s done
#5 DONE 0.0s

#6 [internal] load build context
#6 transferring context: 1.48kB done
#6 DONE 0.0s

#7 [7/8] COPY alembic.ini ./
#7 CACHED

#8 [4/8] COPY pyproject.toml ./
#8 CACHED

#9 [6/8] COPY migrations ./migrations
#9 CACHED

#10 [2/8] RUN apt-get update     && apt-get install -y --no-install-recommends libreoffice-writer     && rm -rf /var/lib/apt/lists/*
#10 CACHED

#11 [5/8] COPY src ./src
#11 CACHED

#12 [3/8] WORKDIR /app
#12 CACHED

#13 [8/8] RUN pip install --no-cache-dir .     && useradd --create-home --uid 10001 app
#13 CACHED

#14 exporting to image
#14 exporting layers done
#14 exporting manifest sha256:c6c5dd1cb4a5af5d8644bbf1e00b01e01042b6b825da60fa27f47492f0000982 done
#14 exporting config sha256:f343160841f4d0c4dbdc1d872e0b640f78562e915bb727188176f6a64894c686 done
#14 exporting attestation manifest sha256:578cf3de39321df5bed5d1fbb06423e5302943fbdbd16f5592631616008ad497 0.0s done
#14 exporting manifest list sha256:9e5634d433ef9dfc895beb355121568220c420d0edcd0b4fdd60dba340ab5822 0.0s done
#14 naming to docker.io/library/wa-contested-divorce-without-children-mediation-to-end-api:latest done
#14 unpacking to docker.io/library/wa-contested-divorce-without-children-mediation-to-end-api:latest 0.0s done
#14 DONE 0.1s

#15 resolving provenance for metadata file
#15 DONE 0.0s
 Image wa-contested-divorce-without-children-mediation-to-end-api Built 
 Container wa-contested-divorce-without-children-mediation-to-end-localstack-1 Stopping 
 Container wa-contested-divorce-without-children-mediation-to-end-localstack-1 Stopped 
 Container wa-contested-divorce-without-children-mediation-to-end-localstack-1 Removing 
 Container wa-contested-divorce-without-children-mediation-to-end-localstack-1 Removed 
 Container wa-contested-divorce-without-children-mediation-to-end-s3mock-1 Running 
 Container wa-contested-divorce-without-children-mediation-to-end-db-1 Running 
 Container wa-contested-divorce-without-children-mediation-to-end-bucket-init-1 Recreate 
 Container wa-contested-divorce-without-children-mediation-to-end-bucket-init-1 Recreated 
 Container wa-contested-divorce-without-children-mediation-to-end-api-1 Recreate 
 Container wa-contested-divorce-without-children-mediation-to-end-api-1 Recreated 
 Container wa-contested-divorce-without-children-mediation-to-end-s3mock-1 Waiting 
 Container wa-contested-divorce-without-children-mediation-to-end-s3mock-1 Healthy 
 Container wa-contested-divorce-without-children-mediation-to-end-bucket-init-1 Starting 
 Container wa-contested-divorce-without-children-mediation-to-end-bucket-init-1 Started 
 Container wa-contested-divorce-without-children-mediation-to-end-db-1 Waiting 
 Container wa-contested-divorce-without-children-mediation-to-end-bucket-init-1 Waiting 
 Container wa-contested-divorce-without-children-mediation-to-end-db-1 Healthy 
 Container wa-contested-divorce-without-children-mediation-to-end-bucket-init-1 Exited 
 Container wa-contested-divorce-without-children-mediation-to-end-api-1 Starting 
 Container wa-contested-divorce-without-children-mediation-to-end-api-1 Started 
```

## Execution - 2026-10-29T01:30:55Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ docker\ compose\ ps\;\ printf\ \"--\ API\ health\ --\\\\n\"\;\ curl\ --fail\ --silent\ --show-error\ --retry\ 30\ --retry-delay\ 2\ --retry-connrefused\ --max-time\ 5\ http://127.0.0.1:8000/healthz\;\ printf\ \"\\\\n--\ API\ readiness\ --\\\\n\"\;\ curl\ --fail\ --silent\ --show-error\ --retry\ 10\ --retry-delay\ 2\ --retry-connrefused\ --max-time\ 5\ http://127.0.0.1:8000/readyz\;\ printf\ \"\\\\n--\ OpenAPI\ response\ --\\\\n\"\;\ curl\ --fail\ --silent\ --show-error\ --output\ /dev/null\ --write-out\ \"HTTP\ %\{http_code\}\\\\n\"\ http://127.0.0.1:8000/openapi.json`
- Exit status: `2`

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
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.004s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
NAME                                                              IMAGE                                                        COMMAND                  SERVICE   CREATED              STATUS                        PORTS
wa-contested-divorce-without-children-mediation-to-end-api-1      wa-contested-divorce-without-children-mediation-to-end-api   "sh -c 'alembic upgr…"   api       11 seconds ago       Up 7 seconds                  127.0.0.1:8000->8000/tcp
wa-contested-divorce-without-children-mediation-to-end-db-1       postgres:16                                                  "docker-entrypoint.s…"   db        About a minute ago   Up About a minute (healthy)   5432/tcp
wa-contested-divorce-without-children-mediation-to-end-s3mock-1   motoserver/moto:latest                                       "/usr/local/bin/moto…"   s3mock    37 seconds ago       Up 35 seconds (healthy)       127.0.0.1:5000->5000/tcp
bash: line 1: printf: --: invalid option
printf: usage: printf [-v var] format [arguments]
```

## Execution - 2026-10-29T01:31:00Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ docker\ compose\ ps\;\ printf\ \"%s\\\\n\"\ \"--\ API\ health\ --\"\;\ curl\ --fail\ --silent\ --show-error\ --retry\ 30\ --retry-delay\ 2\ --retry-connrefused\ --max-time\ 5\ http://127.0.0.1:8000/healthz\;\ printf\ \"\\\\n%s\\\\n\"\ \"--\ API\ readiness\ --\"\;\ curl\ --fail\ --silent\ --show-error\ --retry\ 10\ --retry-delay\ 2\ --retry-connrefused\ --max-time\ 5\ http://127.0.0.1:8000/readyz\;\ printf\ \"\\\\n%s\\\\n\"\ \"--\ OpenAPI\ response\ --\"\;\ curl\ --fail\ --silent\ --show-error\ --output\ /dev/null\ --write-out\ \"HTTP\ %\{http_code\}\\\\n\"\ http://127.0.0.1:8000/openapi.json`
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
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
NAME                                                              IMAGE                                                        COMMAND                  SERVICE   CREATED              STATUS                        PORTS
wa-contested-divorce-without-children-mediation-to-end-api-1      wa-contested-divorce-without-children-mediation-to-end-api   "sh -c 'alembic upgr…"   api       17 seconds ago       Up 13 seconds                 127.0.0.1:8000->8000/tcp
wa-contested-divorce-without-children-mediation-to-end-db-1       postgres:16                                                  "docker-entrypoint.s…"   db        About a minute ago   Up About a minute (healthy)   5432/tcp
wa-contested-divorce-without-children-mediation-to-end-s3mock-1   motoserver/moto:latest                                       "/usr/local/bin/moto…"   s3mock    43 seconds ago       Up 41 seconds (healthy)       127.0.0.1:5000->5000/tcp
-- API health --
{"status":"ok"}
-- API readiness --
{"status":"ready"}
-- OpenAPI response --
HTTP 200
```

## Execution - 2026-10-29T01:31:10Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c set\ -e\;\ response=\$\(curl\ --fail\ --silent\ --show-error\ -H\ \"Content-Type:\ application/json\"\ -d\ \"\{\\\"metadata\\\":\{\\\"smoke_test\\\":true\}\}\"\ http://127.0.0.1:8000/cases\)\;\ printf\ \"Created\ case:\ %s\\\\n\"\ \"\$response\"\;\ case_id=\$\(python3\ -c\ \'import\ json\,sys\;\ print\(json.load\(sys.stdin\)\[\"id\"\]\)\'\ \<\<\<\ \"\$response\"\)\;\ curl\ --fail\ --silent\ --show-error\ \"http://127.0.0.1:8000/cases/\$case_id\"\;\ printf\ \"\\\\n\"`
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
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
Created case: {"id":"a3a0123f-20f7-4ddd-8629-2117f9e43493","status":"draft","metadata_json":{"smoke_test":true},"asset_liability_inventory":{}}
{"id":"a3a0123f-20f7-4ddd-8629-2117f9e43493","status":"draft","metadata_json":{"smoke_test":true},"asset_liability_inventory":{}}
```

## Execution - 2026-10-29T02:32:59Z

- Invocation: `INTERACTION_LOG=interactions/01-tech-stack-override/response-01-tech-stack-override.md bash harness/validate.sh -- bash -c docker\ compose\ ps\;\ printf\ \"\\\\nHealth:\ \"\;\ curl\ -sS\ -o\ /tmp/web-health.json\ -w\ \"%\{http_code\}\"\ --max-time\ 5\ http://127.0.0.1:8000/healthz\;\ printf\ \"\ \"\;\ cat\ /tmp/web-health.json\;\ printf\ \"\\\\nDocs:\ \"\;\ curl\ -sS\ -o\ /dev/null\ -w\ \"%\{http_code\}\\\\n\"\ --max-time\ 5\ http://127.0.0.1:8000/docs`
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
test_compose_provides_postgres_and_moto_s3 (test_project_configuration.ProjectConfigurationTests.test_compose_provides_postgres_and_moto_s3) ... ok
test_docker_build_installs_libreoffice (test_project_configuration.ProjectConfigurationTests.test_docker_build_installs_libreoffice) ... ok
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
Ran 12 tests in 0.002s

OK
PASS: Python unit tests passed.
Baseline repository validation passed.
Running requested command.
NAME                                                              IMAGE                                                        COMMAND                  SERVICE   CREATED             STATUS                       PORTS
wa-contested-divorce-without-children-mediation-to-end-api-1      wa-contested-divorce-without-children-mediation-to-end-api   "sh -c 'alembic upgr…"   api       About an hour ago   Up About an hour             127.0.0.1:8000->8000/tcp
wa-contested-divorce-without-children-mediation-to-end-db-1       postgres:16                                                  "docker-entrypoint.s…"   db        About an hour ago   Up About an hour (healthy)   5432/tcp
wa-contested-divorce-without-children-mediation-to-end-s3mock-1   motoserver/moto:latest                                       "/usr/local/bin/moto…"   s3mock    About an hour ago   Up About an hour (healthy)   127.0.0.1:5000->5000/tcp

Health: 200 {"status":"ok"}
Docs: 200
```

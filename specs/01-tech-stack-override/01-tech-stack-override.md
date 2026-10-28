# Spec 01: Tech Stack Override & Final Architecture

- **Status:** Active / Supersedes Master Spec 00 (REA)
- **Decision:** Discard external turnkey REA frameworks (Docassemble, etc.).
- **Finalized Stack:**
  - Backend: Python (FastAPI)
  - DB/Storage: PostgreSQL + AWS S3 / Azure Blob
  - Document Round-trip: `python-docx-template`, `docx2pdf`, `pdf2docx`, `python-docx`
  - Deployment: Docker (LibreOffice containerized)
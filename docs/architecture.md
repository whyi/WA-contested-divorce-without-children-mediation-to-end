# Architecture & Technology Stack: WA Contested Divorce Mediation-to-Decree Wizard

## 1. Overview
This document defines the core technology stack, database architecture, file storage strategy, and document round-trip conversion pipeline for the Washington State contested divorce mediation-to-decree automation wizard.

The system bridges unstructured mediation negotiations (asset sharing, informal offers, and settlement clauses) with formal Washington State mandatory court forms and custom separation contracts.

---

## 2. Core Technology Stack

### Backend Framework
- **Python 3.11+ / FastAPI:** High-performance asynchronous API framework optimized for handling document uploads, data validation, and multi-step workflow states.

### Database & Storage
- **Relational Database (PostgreSQL):**
  - Manages user sessions, case metadata, negotiation logs (offer/counter-offer history), and structured asset/liability inventories.
- **Object Storage (AWS S3 / Azure Blob Storage):**
  - Secure storage for binary document assets, including generated Word templates, PDF previews, user-edited `.docx` files, and final court form packages.

---

## 3. Document Round-trip & Conversion Pipeline

To support the core user workflow—**"Generate PDF Preview ➔ Edit via Editable Word (`.docx`) ➔ Re-upload & Parse ➔ Update State & Finalize"**—the system integrates the following Python libraries:

1. **Template Generation (`python-docx-template` / `Jinja2`):**
   - Injects structured negotiation data (asset values, agreement clauses) into predefined Word templates to generate initial settlement drafts.
2. **Word-to-PDF Rendering (`docx2pdf` / LibreOffice Headless):**
   - Compiles `.docx` files into clean PDF format for web-based visual preview by users.
3. **PDF-to-Word Reverse Conversion (`pdf2docx`):**
   - Parses layout, tables, and text structures of PDF documents to provide editable `.docx` files when users request modifications.
4. **Parsing & State Synchronization (`python-docx`, `PyMuPDF`, `pypdf`):**
   - Extracts modified text and clause changes from re-uploaded Word files, updates the Single Source of Truth (SSOT) data model, and injects final data into official Washington State court form PDFs (`FL Divorce 241`, `FL All Family 131`, etc.).

---

## 4. Infrastructure & Deployment

- **Containerization (Docker):**
  - Mandatory for packaging system dependencies. Document conversion tools (`docx2pdf`, `pdf2docx`) require underlying OS-level document rendering binaries (**LibreOffice**). A custom Docker container ensures cross-platform consistency.
- **Hosting Target:**
  - **AWS ECS (Fargate)** or **Azure Container Apps** to maintain persistent container execution environments, avoiding serverless function execution limits and file system constraints.
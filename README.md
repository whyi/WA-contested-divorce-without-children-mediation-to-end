# Washington Divorce Mediation Workspace

An AI-assisted workspace for organizing documents, reviewing property information, and preparing settlement proposals for Washington divorce cases without children.

[![Tests](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/actions/workflows/test.yml)
[![Coverage](coverage.svg)](https://github.com/whyi/WA-contested-divorce-without-children-mediation-to-end/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![MIT License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[Live demo — coming soon](#live-demo)

> **Important:** This is an organizational tool, not legal advice. It does not determine legal rights or guarantee an outcome. Use fictional information in demos; do not submit real case information to local previews or unverified deployments.

## What it does

- Organizes case materials and keeps extracted text linked to its source pages.
- Helps users review property facts and compare settlement scenarios.
- Uses optional, consent-based AI to suggest source-grounded information. Suggestions require user review and are never applied automatically.
- Prepares editable proposal documents for users to review.

AI features are disabled by default and require explicit configuration and purpose-specific consent. The repository does not establish provider-side data handling or legal approval.

## Architecture

```mermaid
flowchart LR
    U[Case member] --> W[Web app]
    W --> API[FastAPI]
    API <--> DB[(PostgreSQL)]
    API <--> S3[(S3-compatible storage)]
    API -->|authorized jobs| DB
    DB --> X[Document extraction worker]
    X --> S3
    X --> DB
    DB -. "optional; enabled + consented jobs" .-> AI[AI analysis worker]
    AI --> B[Amazon Bedrock]
    AI -->|verified suggestions| DB
    DB --> API
```

The local preview uses Docker Compose, PostgreSQL, and a local S3-compatible service. A hosted demo is not live yet; AWS ECS/Fargate is the planned deployment direction.

## Live demo

**Coming soon.** No hosted demo URL is available yet. The local Compose preview is for development and fictional data only.

## Run locally

```sh
docker compose up --build
```

The current Compose configuration publishes the app at `http://192.168.1.17:8001`; API documentation is available at `/docs`.

Run the test suite with:

```sh
bash harness/validate.sh
```

## Tech

Python 3.11+, FastAPI, PostgreSQL, S3-compatible object storage, and Docker Compose.

## Project links

- [Deployment notes](deploy/aws/owner-beta/README.md)
- [Specifications](specs/)
- [License](LICENSE)

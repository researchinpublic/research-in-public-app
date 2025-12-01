# Contract-First Development Guide

This directory contains the **Consensus File** and all contract artifacts for Research In Public. These contracts enable frontend and backend teams to develop in parallel.

## Quick Start

### For Frontend Developers

1. **Generate Types:**
   ```bash
   python scripts/generate-types.py --lang typescript
   ```

2. **Start Mock Server:**
   ```bash
   ./scripts/mock-server.sh
   ```

3. **Use Generated Types:**
   ```typescript
   import { SessionResponse, MessageRequest } from '@/gen/types/typescript';
   ```

### For Backend Developers

1. **Implement API Endpoints:**
   - Follow `contract/openapi.yaml` specification
   - Use error codes from `contract/error-model.md`
   - Return response shapes matching OpenAPI schemas

2. **Run Contract Tests:**
   ```bash
   pytest tests/contract/ -v
   ```

## Contract Files

### Core Contracts

- **`CONTRACT.md`** - Main consensus file (start here!)
- **`openapi.yaml`** - Complete API specification
- **`error-model.md`** - Error codes and formats
- **`authz-authn.md`** - Authentication/authorization strategy
- **`pagination-filtering.md`** - Query parameter standards
- **`events.md`** - Event/async contract (future)

### Design System

- **`design-system/tokens.json`** - Design tokens (colors, spacing, typography)
- **`design-system/components.md`** - Component specifications

### Supporting Contracts

- **`routes.md`** - Route map and navigation
- **`state.md`** - Front-end state contracts
- **`testing.md`** - Testing strategy
- **`telemetry.md`** - Logging, metrics, tracing
- **`change-control.md`** - Versioning and deprecation

### Schemas

- **`schemas/*.json`** - JSON schemas for data models

## Working in Parallel

### Frontend Workflow

1. Generate types from OpenAPI
2. Start mock server
3. Develop UI against mocks
4. Run contract tests to validate

### Backend Workflow

1. Implement endpoints per OpenAPI spec
2. Run contract tests
3. Ensure error responses match error model
4. Update OpenAPI spec if needed (via CCR)

## Contract Change Request (CCR)

All contract changes must go through a CCR:

1. Create GitHub issue with `[CCR]` prefix
2. Use template from `contract/change-control.md`
3. Get approvals (FE, BE, Design, QA)
4. Update contract files
5. Regenerate types
6. Update implementation

See `contract/change-control.md` for details.

## Versioning

Contracts use semantic versioning (semver):

- **MAJOR:** Breaking changes
- **MINOR:** New endpoints/fields (backward compatible)
- **PATCH:** Bug fixes, documentation

Current version: **1.0.0**

## Tools

### Type Generation

```bash
# Generate TypeScript types
python scripts/generate-types.py --lang typescript

# Generate Python types
python scripts/generate-types.py --lang python
```

### Mock Server

```bash
# Start Prism mock server
./scripts/mock-server.sh

# Custom port
./scripts/mock-server.sh contract/openapi.yaml 4010
```

### Contract Validation

```bash
# Validate OpenAPI spec
openapi-spec-validator contract/openapi.yaml

# Run contract tests
pytest tests/contract/ -v
```

## Questions?

See `CONTRACT.md` for complete documentation, or contact:
- Frontend Lead: TBD
- Backend Lead: TBD


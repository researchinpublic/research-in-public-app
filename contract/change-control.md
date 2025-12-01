# Change Control

**Version:** 1.0.0  
**Last Updated:** 2024-11-19

This document defines the change control process for Research In Public contracts, including versioning, deprecation, and migration strategies.

---

## Contract Versioning

### Semantic Versioning (Semver)

**Format:** `MAJOR.MINOR.PATCH`

**Rules:**
- **MAJOR:** Breaking changes (removed endpoints, required fields added, incompatible changes)
- **MINOR:** New endpoints, optional fields added, backward-compatible additions
- **PATCH:** Bug fixes, documentation updates, non-breaking changes

### Version Bumping

**MAJOR Version Bump:**
- Removing an endpoint
- Adding a required field to request/response
- Changing field types (string → integer)
- Changing error codes
- Breaking API behavior

**MINOR Version Bump:**
- Adding a new endpoint
- Adding optional fields to request/response
- Adding new error codes
- Adding new query parameters

**PATCH Version Bump:**
- Fixing documentation errors
- Clarifying field descriptions
- Fixing example values
- Non-functional changes

### Examples

**1.0.0 → 1.1.0 (MINOR):**
- Added new endpoint `/v1/users/{user_id}/memory/timeline`
- Added optional field `metadata` to `MessageRequest`

**1.0.0 → 2.0.0 (MAJOR):**
- Removed endpoint `/v1/sessions/{session_id}/old-endpoint`
- Added required field `user_id` to `CreateSessionRequest`

**1.0.0 → 1.0.1 (PATCH):**
- Fixed typo in error message
- Updated example values in documentation

---

## Contract Change Request (CCR) Process

### CCR Template

**Title:** `[MAJOR/MINOR/PATCH] Brief description`

**Summary:**
- What is changing?
- Why is this change needed?
- What problem does it solve?

**Motivation:**
- Business justification
- User impact
- Technical rationale

**Alternatives Considered:**
- What other options were evaluated?
- Why was this approach chosen?

**Contract Diff:**
- OpenAPI diff (if API changes)
- Schema diff (if data model changes)
- Error model diff (if error changes)

**Migration Steps:**
- Step-by-step migration guide
- Timeline for migration
- Rollback plan

**Breaking Changes:**
- List of breaking changes (if MAJOR)
- Impact assessment
- Migration path

**Approvals Required:**
- [ ] Frontend Lead
- [ ] Backend Lead
- [ ] Design Lead (if UI changes)
- [ ] QA Lead (if test changes)
- [ ] Security Lead (if auth/data changes)

**Testing:**
- Contract tests updated
- Integration tests updated
- E2E tests updated

**Documentation:**
- API documentation updated
- Migration guide created
- Examples updated

---

## CCR Workflow

### 1. Create CCR

**Format:** GitHub Issue with `[CCR]` prefix

**Template:** Use CCR template above

**Labels:** `contract-change`, `major`/`minor`/`patch`

### 2. Review Process

**Monday:** Review open CCRs in team meeting

**Wednesday:** Design review (if UI changes)

**Friday:** Approve and merge CCRs

### 3. Approval

**Required Approvals:**
- Frontend Lead (if API/UI changes)
- Backend Lead (if API/data changes)
- Design Lead (if UI/design changes)
- QA Lead (if test changes)
- Security Lead (if auth/data changes)

**Approval Criteria:**
- All required approvals received
- Contract tests pass
- Migration plan approved
- Documentation updated

### 4. Implementation

**Steps:**
1. Update contract files (`contract/openapi.yaml`, `contract/schemas/*.json`)
2. Update version number
3. Generate types from updated contract
4. Update implementation code
5. Update tests
6. Update documentation

### 5. Release

**Version Bump:**
- Update `CONTRACT.md` version
- Update `openapi.yaml` version
- Create git tag (e.g., `contract-v1.1.0`)

**Communication:**
- Announce in team channel
- Update changelog
- Notify stakeholders

---

## Deprecation Policy

### Deprecation Window

**Minimum:** 90 days

**Process:**
1. Mark endpoint/field as deprecated in contract
2. Add `X-Deprecated: true` header to responses
3. Add deprecation notice to documentation
4. Wait 90 days
5. Remove deprecated endpoint/field in next MAJOR version

### Deprecation Notice

**In OpenAPI:**
```yaml
deprecated: true
x-deprecation-date: "2024-11-19"
x-deprecation-replacement: "/v1/new-endpoint"
x-deprecation-notice: "This endpoint will be removed in v2.0.0. Use /v1/new-endpoint instead."
```

**In Response Headers:**
```
X-Deprecated: true
X-Deprecation-Date: 2024-11-19
X-Deprecation-Replacement: /v1/new-endpoint
```

### Migration Guide

**Required for Deprecations:**
- Old endpoint/field usage
- New endpoint/field usage
- Code examples
- Migration timeline

---

## Breaking Changes

### Definition

A breaking change is any change that requires client code changes to maintain compatibility.

### Examples

**Breaking:**
- Removing an endpoint
- Adding a required field
- Changing field type
- Removing a field
- Changing error codes

**Non-Breaking:**
- Adding an optional field
- Adding a new endpoint
- Adding new error codes
- Clarifying documentation

### Breaking Change Process

1. **Announce:** Announce breaking change 90 days in advance
2. **Deprecate:** Mark old endpoint/field as deprecated
3. **Migrate:** Provide migration guide and support
4. **Remove:** Remove in next MAJOR version

---

## Migration Strategies

### Strangler Pattern

**Approach:** Gradually replace old API with new API

**Steps:**
1. Implement new API alongside old API
2. Migrate clients to new API
3. Deprecate old API
4. Remove old API after migration complete

### Versioned Endpoints

**Approach:** Support multiple API versions simultaneously

**Example:**
- `/v1/sessions` (old)
- `/v2/sessions` (new)

**Benefits:**
- Gradual migration
- No forced upgrades
- Backward compatibility

**Drawbacks:**
- Maintenance overhead
- Code duplication

---

## Change Log

### Format

**Version:** `[MAJOR.MINOR.PATCH] - YYYY-MM-DD`

**Changes:**
- Added: New features
- Changed: Modified features
- Deprecated: Soon-to-be removed features
- Removed: Removed features
- Fixed: Bug fixes
- Security: Security fixes

### Example

```markdown
## [1.1.0] - 2024-11-19

### Added
- New endpoint `/v1/users/{user_id}/memory/timeline`
- Optional field `metadata` to `MessageRequest`

### Changed
- Updated error messages for clarity

### Deprecated
- Endpoint `/v1/sessions/{session_id}/old-endpoint` (use `/v1/sessions/{session_id}/new-endpoint`)

## [1.0.1] - 2024-11-15

### Fixed
- Fixed typo in error message
- Updated example values in documentation
```

---

## Emergency Changes

### Definition

Changes needed immediately (security fixes, critical bugs)

### Process

1. **Create CCR:** Create CCR with `[EMERGENCY]` prefix
2. **Fast Track:** Expedited review (same day)
3. **Approve:** Get required approvals
4. **Implement:** Implement immediately
5. **Document:** Document after implementation

### Post-Implementation

- Update contract files
- Update documentation
- Communicate to team

---

## Contract Validation

### Automated Validation

**Tools:**
- OpenAPI spec validator
- JSON schema validator
- Contract tests

**CI/CD:**
- Validate contract on every PR
- Fail build if contract invalid
- Generate types from contract

### Manual Validation

**Checklist:**
- [ ] Contract follows OpenAPI 3.0 spec
- [ ] All endpoints documented
- [ ] All schemas defined
- [ ] Error responses match error model
- [ ] Examples provided
- [ ] Version number updated

---

## Communication

### Stakeholder Notification

**When:** On MAJOR version releases

**Who:**
- Frontend team
- Backend team
- QA team
- Product team

**How:**
- Team channel announcement
- Email (if external stakeholders)
- Documentation update

### User Notification

**When:** On breaking changes

**How:**
- In-app notification (future)
- Email (if registered users)
- Documentation update

---

## Examples

### Example CCR: Adding New Endpoint

**Title:** `[MINOR] Add memory timeline endpoint`

**Summary:**
Add new endpoint to retrieve user memory timeline for better journey visualization.

**Contract Diff:**
```yaml
# Added to openapi.yaml
/users/{user_id}/memory/timeline:
  get:
    summary: Get user memory timeline
    ...
```

**Migration Steps:**
1. Update OpenAPI spec
2. Generate types
3. Implement endpoint
4. Add tests
5. Update documentation

**Approvals:** Frontend Lead, Backend Lead, QA Lead

---

### Example CCR: Breaking Change

**Title:** `[MAJOR] Remove deprecated endpoint`

**Summary:**
Remove deprecated endpoint `/v1/sessions/{session_id}/old-endpoint` after 90-day deprecation period.

**Breaking Changes:**
- Endpoint `/v1/sessions/{session_id}/old-endpoint` removed
- Clients must use `/v1/sessions/{session_id}/new-endpoint`

**Migration Steps:**
1. Update all clients to use new endpoint
2. Remove deprecated endpoint
3. Update documentation

**Approvals:** Frontend Lead, Backend Lead, QA Lead

---

**End of Change Control**


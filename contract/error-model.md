# Error Model

**Version:** 1.0.0  
**Last Updated:** 2025-12-01

This document defines the canonical error format and error code catalog for Research In Public API.

---

## Error Format (RFC 7807 Problem+JSON)

All API errors follow the [RFC 7807 Problem Details for HTTP APIs](https://tools.ietf.org/html/rfc7807) format:

```json
{
  "type": "https://api.researchinpublic.ai/errors/agent-timeout",
  "title": "Agent Timeout",
  "status": 504,
  "detail": "The agent response exceeded the 10 second timeout",
  "instance": "/v1/sessions/123e4567-e89b-12d3-a456-426614174000/messages",
  "trace_id": "abc123def456",
  "code": "AGENT_TIMEOUT",
  "errors": [
    {
      "field": "agent_mode",
      "message": "Agent 'vent_validator' timed out"
    }
  ]
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | `string` (URI) | Yes | Error type URI (machine-readable) |
| `title` | `string` | Yes | Short, human-readable error title |
| `status` | `integer` | Yes | HTTP status code |
| `detail` | `string` | Yes | Detailed error message |
| `instance` | `string` (URI) | Yes | Request instance URI |
| `trace_id` | `string` | Yes | Trace ID for debugging |
| `code` | `string` | Yes | Machine-readable error code |
| `errors` | `Array<FieldError>` | No | Field-specific errors (for validation) |

### FieldError Object

```json
{
  "field": "content",
  "message": "Content is required"
}
```

---

## Error Code Catalog

### 4xx Client Errors

#### VALIDATION_ERROR (400)
**Title:** Validation Error  
**Status:** 400  
**Description:** Request validation failed (missing required fields, invalid format, etc.)

**Example:**
```json
{
  "type": "https://api.researchinpublic.ai/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Request validation failed",
  "instance": "/v1/sessions/123/messages",
  "trace_id": "abc123",
  "code": "VALIDATION_ERROR",
  "errors": [
    {
      "field": "content",
      "message": "Content is required"
    },
    {
      "field": "agent_mode",
      "message": "Invalid agent mode. Must be one of: auto, vent, pi, scribe"
    }
  ]
}
```

#### INVALID_SESSION (404)
**Title:** Session Not Found  
**Status:** 404  
**Description:** Session ID not found or invalid

**Example:**
```json
{
  "type": "https://api.researchinpublic.ai/errors/not-found",
  "title": "Session Not Found",
  "status": 404,
  "detail": "Session with ID '123e4567-e89b-12d3-a456-426614174000' not found",
  "instance": "/v1/sessions/123e4567-e89b-12d3-a456-426614174000/messages",
  "trace_id": "abc123",
  "code": "INVALID_SESSION"
}
```

#### GUARDIAN_BLOCKED (403)
**Title:** Content Blocked  
**Status:** 403  
**Description:** Content blocked by Guardian due to HIGH IP risk

**Example:**
```json
{
  "type": "https://api.researchinpublic.ai/errors/guardian-blocked",
  "title": "Content Blocked",
  "status": 403,
  "detail": "Content blocked due to HIGH IP risk. Please review and remove sensitive information.",
  "instance": "/v1/sessions/123/draft-post",
  "trace_id": "abc123",
  "code": "GUARDIAN_BLOCKED",
  "errors": [
    {
      "field": "content",
      "message": "HIGH risk detected: Contains chemical structure"
    }
  ]
}
```

#### NO_SHAREABLE_MOMENT (400)
**Title:** No Shareable Moment  
**Status:** 400  
**Description:** No suitable content found in conversation for drafting

**Example:**
```json
{
  "type": "https://api.researchinpublic.ai/errors/no-shareable-moment",
  "title": "No Shareable Moment",
  "status": 400,
  "detail": "No suitable content found in conversation for drafting a social media post",
  "instance": "/v1/sessions/123/draft-post",
  "trace_id": "abc123",
  "code": "NO_SHAREABLE_MOMENT"
}
```

#### MEMORY_NOT_FOUND (404)
**Title:** Memory Not Found  
**Status:** 404  
**Description:** No memories found for user

**Example:**
```json
{
  "type": "https://api.researchinpublic.ai/errors/memory-not-found",
  "title": "Memory Not Found",
  "status": 404,
  "detail": "No memories found for user 'demo_user'",
  "instance": "/v1/users/demo_user/memory/summary",
  "trace_id": "abc123",
  "code": "MEMORY_NOT_FOUND"
}
```

#### RATE_LIMIT_EXCEEDED (429)
**Title:** Rate Limit Exceeded  
**Status:** 429  
**Description:** Too many requests (future enhancement)

**Example:**
```json
{
  "type": "https://api.researchinpublic.ai/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Rate limit exceeded. Maximum 100 requests per minute.",
  "instance": "/v1/sessions/123/messages",
  "trace_id": "abc123",
  "code": "RATE_LIMIT_EXCEEDED"
}
```

**Headers:**
- `X-RateLimit-Limit: 100`
- `X-RateLimit-Remaining: 0`
- `X-RateLimit-Reset: 1638360000`
- `Retry-After: 60`

---

### 5xx Server Errors

#### AGENT_TIMEOUT (504)
**Title:** Agent Timeout  
**Status:** 504  
**Description:** Agent response exceeded timeout (10 seconds)

**Example:**
```json
{
  "type": "https://api.researchinpublic.ai/errors/agent-timeout",
  "title": "Agent Timeout",
  "status": 504,
  "detail": "The agent response exceeded the 10 second timeout",
  "instance": "/v1/sessions/123/messages",
  "trace_id": "abc123",
  "code": "AGENT_TIMEOUT",
  "errors": [
    {
      "field": "agent_mode",
      "message": "Agent 'vent_validator' timed out"
    }
  ]
}
```

#### MEMORY_ERROR (500)
**Title:** Memory Error  
**Status:** 500  
**Description:** Memory retrieval or save failed

**Example:**
```json
{
  "type": "https://api.researchinpublic.ai/errors/memory-error",
  "title": "Memory Error",
  "status": 500,
  "detail": "Failed to retrieve memory for user 'demo_user'",
  "instance": "/v1/users/demo_user/memory/summary",
  "trace_id": "abc123",
  "code": "MEMORY_ERROR"
}
```

#### MATCHMAKER_UNAVAILABLE (503)
**Title:** Matchmaker Unavailable  
**Status:** 503  
**Description:** Vector search service unavailable

**Example:**
```json
{
  "type": "https://api.researchinpublic.ai/errors/matchmaker-unavailable",
  "title": "Matchmaker Unavailable",
  "status": 503,
  "detail": "Vector search service is currently unavailable",
  "instance": "/v1/sessions/123/messages",
  "trace_id": "abc123",
  "code": "MATCHMAKER_UNAVAILABLE"
}
```

#### SERVER_ERROR (500)
**Title:** Internal Server Error  
**Status:** 500  
**Description:** Unexpected server error

**Example:**
```json
{
  "type": "https://api.researchinpublic.ai/errors/server-error",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "An unexpected error occurred. Please try again later.",
  "instance": "/v1/sessions/123/messages",
  "trace_id": "abc123",
  "code": "SERVER_ERROR"
}
```

**Note:** Server errors should not expose internal implementation details in production.

---

## Error Handling Guidelines

### Client-Side Handling

1. **Check `code` field** for machine-readable error code
2. **Display `detail`** to user (human-readable)
3. **Use `trace_id`** for support/debugging
4. **Handle `errors` array** for field-specific validation errors
5. **Check `status`** for HTTP status code

### Server-Side Handling

1. **Always include `trace_id`** for correlation
2. **Log full error** with trace_id for debugging
3. **Don't expose internal details** in production (use generic messages)
4. **Return appropriate HTTP status** code
5. **Include `instance` URI** for request identification

### Error Recovery

| Error Code | Retryable | Recovery Action |
|------------|-----------|-----------------|
| `AGENT_TIMEOUT` | Yes | Retry with exponential backoff |
| `MEMORY_ERROR` | Yes | Retry once, then show error |
| `MATCHMAKER_UNAVAILABLE` | Yes | Continue without matches |
| `GUARDIAN_BLOCKED` | No | Show error, ask user to revise |
| `VALIDATION_ERROR` | No | Show field errors, ask user to fix |
| `SERVER_ERROR` | Yes | Retry with exponential backoff |

---

## Error Code Reference Table

| Code | HTTP Status | Retryable | Description |
|------|-------------|-----------|-------------|
| `VALIDATION_ERROR` | 400 | No | Request validation failed |
| `INVALID_SESSION` | 404 | No | Session not found |
| `GUARDIAN_BLOCKED` | 403 | No | Content blocked by Guardian |
| `NO_SHAREABLE_MOMENT` | 400 | No | No shareable content found |
| `MEMORY_NOT_FOUND` | 404 | No | No memories found |
| `RATE_LIMIT_EXCEEDED` | 429 | Yes | Rate limit exceeded |
| `AGENT_TIMEOUT` | 504 | Yes | Agent timeout |
| `MEMORY_ERROR` | 500 | Yes | Memory operation failed |
| `MATCHMAKER_UNAVAILABLE` | 503 | Yes | Matchmaker unavailable |
| `SERVER_ERROR` | 500 | Yes | Unexpected server error |

---

**End of Error Model**


# Authorization and Authentication

**Version:** 1.0.0  
**Last Updated:** 2024-11-19

This document defines the authentication and authorization strategy for Research In Public API.

---

## Current Status (v1.0)

**Authentication:** None (demo mode)  
**Authorization:** None (all users have full access)

The system currently uses demo user IDs (`demo_user`) without authentication. This is sufficient for MVP/demo purposes.

---

## Future Authentication Strategy (v2.0)

### Authentication Method

**Protocol:** OAuth 2.0 with JWT tokens

**Flow:**
1. User authenticates via OAuth provider (Google, GitHub, or email/password)
2. Backend issues JWT access token
3. Client includes token in `Authorization` header
4. Backend validates token and extracts user ID

### Token Format

**Access Token (JWT):**
```json
{
  "sub": "user_123",
  "iat": 1638360000,
  "exp": 1638446400,
  "scope": "read write"
}
```

**Header:**
```
Authorization: Bearer <jwt_token>
```

### Token Lifecycle

- **Access Token:** 24 hours validity
- **Refresh Token:** 30 days validity (future)
- **Token Rotation:** On refresh (future)

---

## Authorization Model

### Roles (Future)

| Role | Permissions |
|------|-------------|
| **User** | Read/write own sessions, memory, drafts |
| **Admin** | Read/write all users, system configuration |

### Scopes (Future)

| Scope | Description |
|-------|-------------|
| `read` | Read own sessions and memory |
| `write` | Create/update own sessions and messages |
| `admin` | Admin access (future) |

### Resource Ownership

- **Sessions:** Owned by `user_id` (from token)
- **Memory:** Owned by `user_id` (from token)
- **Drafts:** Owned by `user_id` (from token)

**Authorization Check:**
- User can only access resources where `resource.user_id == token.user_id`
- Admin can access all resources

---

## CSRF Protection

**Current:** Not implemented (no authentication)

**Future (v2.0):**
- CSRF tokens for state-changing operations
- SameSite cookies for session management
- Origin validation for API requests

---

## CORS Policy

**Current:**
- Allow all origins (`*`)
- Allow all methods
- Allow all headers

**Future (v2.0):**
- Whitelist allowed origins
- Restrict methods to: GET, POST, PUT, DELETE
- Restrict headers to: Content-Type, Authorization

**CORS Headers:**
```
Access-Control-Allow-Origin: https://app.researchinpublic.ai
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
```

---

## Session Management

**Current:** Stateless (no server-side sessions)

**Future (v2.0):**
- JWT tokens stored client-side (localStorage or httpOnly cookies)
- Refresh tokens stored in httpOnly cookies
- Session invalidation on logout

---

## Security Best Practices

### Token Storage

- **Access Token:** localStorage (for SPA) or httpOnly cookie (for SSR)
- **Refresh Token:** httpOnly cookie only (never in localStorage)
- **Never expose tokens** in URLs or logs

### Token Validation

- Verify signature using public key
- Check expiration (`exp` claim)
- Validate issuer (`iss` claim)
- Validate audience (`aud` claim)

### Password Handling (Future)

- **Hashing:** bcrypt with salt rounds >= 10
- **Never store** plaintext passwords
- **Password Policy:** Minimum 8 characters, mixed case, numbers, symbols

### PII Handling

- **Logging:** Redact PII from logs (see `contract/telemetry.md`)
- **Storage:** Encrypt sensitive PII at rest
- **Transmission:** HTTPS only (TLS 1.2+)

---

## API Endpoints (Future)

### Authentication Endpoints

**POST /auth/login**
- Request: `{ email, password }` or `{ provider, code }`
- Response: `{ access_token, refresh_token, user_id }`

**POST /auth/refresh**
- Request: `{ refresh_token }`
- Response: `{ access_token }`

**POST /auth/logout**
- Request: `Authorization: Bearer <token>`
- Response: `{ success: true }`

**GET /auth/me**
- Request: `Authorization: Bearer <token>`
- Response: `{ user_id, email, role }`

---

## Migration Plan

### Phase 1: Add Authentication (v2.0)

1. Implement OAuth 2.0 flow
2. Add JWT token generation/validation
3. Update API endpoints to require authentication
4. Add user database (user_id, email, role)
5. Migrate existing demo users to real users

### Phase 2: Authorization (v2.1)

1. Implement role-based access control (RBAC)
2. Add scope-based permissions
3. Add resource ownership checks
4. Add admin endpoints

### Phase 3: Security Hardening (v2.2)

1. Add CSRF protection
2. Implement CORS whitelist
3. Add rate limiting per user
4. Add audit logging

---

## Testing

### Authentication Tests

- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] Token validation
- [ ] Token expiration
- [ ] Refresh token flow

### Authorization Tests

- [ ] User can access own resources
- [ ] User cannot access other users' resources
- [ ] Admin can access all resources
- [ ] Invalid token rejected
- [ ] Missing token rejected

---

**End of Authorization and Authentication**


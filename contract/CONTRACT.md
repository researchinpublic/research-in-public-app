# Research In Public: Contract-First Consensus File

**Version:** 1.0.0  
**Last Updated:** 2025-12-01  
**Status:** Active

---

## Table of Contents

1. [Scope and Goals](#1-scope-and-goals)
2. [Stakeholders and Glossary](#2-stakeholders-and-glossary)
3. [Functional Features](#3-functional-features)
4. [Non-Functional Requirements](#4-non-functional-requirements)
5. [API Contract](#5-api-contract)
6. [Event/Async Contract](#6-eventasync-contract)
7. [Design System and UI Rules](#7-design-system-and-ui-rules)
8. [Route Map and Navigation](#8-route-map-and-navigation)
9. [Front-End State Contracts](#9-front-end-state-contracts)
10. [Testing Strategy](#10-testing-strategy)
11. [Telemetry and Analytics](#11-telemetry-and-analytics)
12. [Change Control](#12-change-control)
13. [Sign-Off Checklist](#13-sign-off-checklist)
14. [Decision Log](#14-decision-log)

---

## 1. Scope and Goals

### 1.1 Product Mission Statement

**Research In Public** is a multi-agent AI system designed for PhD students and early-career researchers. It transforms the research process—failures, mental blocks, and iterations—into a dual-value asset:

1. **Internal Value:** Immediate emotional validation and semantic peer matching
2. **External Value:** IP-safe public narratives that help researchers build a personal brand

The system addresses a critical gap: while academic tools focus on the *product* (manuscripts, datasets), there's a vacuum in tooling for the *human experience* of research.

### 1.2 Success Criteria

- **Emotional Support:** Users receive empathetic, CBT-based responses to research struggles
- **Peer Matching:** Users discover anonymous peers facing similar challenges (struggle-based, not topic-based)
- **Content Generation:** Users can transform research insights into IP-safe social media content
- **Memory Persistence:** System remembers user journey across sessions for personalized responses
- **Safety:** IP risks are detected and blocked before public sharing
- **Performance:** Agent responses delivered within 3 seconds (p95)

### 1.3 Out of Scope (Explicit)

- **Direct User Connections:** System suggests matches but does not create direct messaging between users
- **Automatic Social Posting:** System drafts content but does not automatically post to LinkedIn/X (requires manual user action)
- **User Authentication:** Currently uses demo user IDs; full auth system is future enhancement
- **Real-time Collaboration:** No multi-user collaborative features
- **Mobile Native Apps:** Web-only (Streamlit) for initial version
- **Payment/Billing:** No monetization features in v1.0

---

## 2. Stakeholders and Glossary

### 2.1 Stakeholders

| Role | Owner | Responsibilities |
|------|-------|------------------|
| **Frontend Lead** | TBD | Streamlit UI, component library, design system implementation |
| **Backend Lead** | TBD | Agent orchestration, API endpoints, memory management |
| **Design Lead** | TBD | Design tokens, component specifications, accessibility |
| **QA Lead** | TBD | Contract tests, integration tests, E2E tests |
| **Security Lead** | TBD | IP safety, PII handling, auth strategy |
| **Ops Lead** | TBD | Observability, deployment, monitoring |

### 2.2 Glossary

| Term | Definition |
|------|------------|
| **Agent** | Specialized AI component (Vent Validator, Matchmaker, Scribe, Guardian, PI Simulator) |
| **Orchestrator** | Central hub coordinating multiple agents |
| **Session** | User conversation session with unique ID |
| **Memory Node** | Single memory unit in graph (struggle, insight, breakthrough, topic, question) |
| **Memory Edge** | Connection between memory nodes (related_to, led_to, similar_to, resolved_by, follows) |
| **Graph Memory** | Per-user knowledge graph storing conversation history |
| **Global Graph** | Anonymized graph for peer matching across users |
| **Struggle** | User's research challenge, failure, or emotional difficulty |
| **Shareable Moment** | Research insight suitable for public sharing (detected by Scribe) |
| **IP Risk** | Intellectual property risk level (LOW, MEDIUM, HIGH) detected by Guardian |
| **Intent** | User intent classification (vent, technical, grant, shareable, etc.) |
| **Memory Query** | User question about past conversations (quantitative, specific, summary, reference) |

---

## 3. Functional Features

### 3.1 Feature: Emotional Support (Vent Validator)

**User Story:** As a PhD student, I want to share my research struggles and receive empathetic, CBT-based support so I feel validated and less isolated.

**UX Flow:**
1. User types message expressing frustration/stress
2. Intent classifier detects "vent" or "emotional" intent
3. Orchestrator routes to Vent Validator agent
4. Vent Validator generates empathetic response using memory context
5. If struggle detected, Semantic Matchmaker suggests anonymous peers
6. Response displayed in chat interface
7. Memory saved to user's graph

**API Usage:**
- `POST /api/v1/sessions/{session_id}/messages` (agent_mode="vent" or "auto")

**Data Contracts:**
- Request: `MessageRequest` (see `contract/schemas/message.json`)
- Response: `MessageResponse` with `main_response`, `peer_matches`, `agent_used`

**Error Cases:**
- `AGENT_TIMEOUT`: Agent response exceeded 10 seconds
- `MEMORY_ERROR`: Failed to retrieve/save memory
- `INVALID_SESSION`: Session ID not found

**Authorization:**
- No auth required for v1.0 (demo mode)
- Future: User must own session_id

**Performance Budget:**
- Latency: < 3s (p95)
- Payload: < 10KB response
- Concurrency: 10 concurrent requests per user

**Telemetry:**
- Event: `agent.vent_validator.executed`
- Metrics: `agent.latency`, `agent.success_rate`, `agent.token_usage`
- Traces: `process_message` span with `agent_mode=vent`

**Acceptance Criteria:**
- ✅ User receives empathetic response within 3 seconds
- ✅ Response references past conversations if memory exists
- ✅ Peer matches shown when struggle detected
- ✅ Memory saved to graph after response
- ✅ Response quality score > 4.0/5.0 (empathy)

---

### 3.2 Feature: Peer Matching (Semantic Matchmaker)

**User Story:** As a researcher, I want to discover anonymous peers facing similar struggles so I feel less alone in my challenges.

**UX Flow:**
1. User shares struggle in conversation
2. Vent Validator processes message
3. Orchestrator triggers Matchmaker in parallel
4. Matchmaker searches global graph for similar struggles using embeddings
5. Top 3 matches returned with similarity scores
6. Matches displayed as "Someone facing a similar challenge" (anonymous)

**API Usage:**
- Automatically triggered via `POST /api/v1/sessions/{session_id}/messages`
- Response includes `peer_matches` field

**Data Contracts:**
- Response includes `MatchResult[]` (see `contract/schemas/match.json`)

**Error Cases:**
- `MATCHMAKER_UNAVAILABLE`: Vector search service unavailable
- `NO_MATCHES`: No similar struggles found (not an error, empty array returned)

**Authorization:**
- Same as message processing

**Performance Budget:**
- Latency: < 2s additional (parallel execution)
- Payload: < 5KB per match result

**Telemetry:**
- Event: `agent.matchmaker.executed`
- Metrics: `matchmaker.similarity_scores`, `matchmaker.match_count`

**Acceptance Criteria:**
- ✅ Matches shown within 2 seconds of message
- ✅ Similarity scores > 0.7
- ✅ Matches are anonymized (no PII)
- ✅ User can dismiss matches

---

### 3.3 Feature: Content Drafting (The Scribe)

**User Story:** As a researcher, I want to transform my research insights into professional LinkedIn posts so I can build my public brand safely.

**UX Flow:**
1. User clicks "✍️ Draft Post" button
2. Orchestrator calls `draft_social_post()` method
3. Scribe detects shareable moment in conversation
4. Scribe generates professional LinkedIn post
5. Guardian scans post for IP risks
6. Draft displayed with Guardian report
7. User can copy/paste to share manually

**API Usage:**
- `POST /api/v1/sessions/{session_id}/draft-post`

**Data Contracts:**
- Request: Optional `memory_context` override
- Response: `SocialDraftResponse` (see `contract/schemas/social_draft.json`)

**Error Cases:**
- `NO_SHAREABLE_MOMENT`: No suitable content found in conversation
- `GUARDIAN_BLOCKED`: Post blocked due to HIGH IP risk
- `DRAFT_FAILED`: LLM failed to generate draft

**Authorization:**
- User must own session_id

**Performance Budget:**
- Latency: < 5s (uses Gemini Pro for quality)
- Payload: < 15KB (includes Guardian report)

**Telemetry:**
- Event: `agent.scribe.draft_created`
- Event: `agent.guardian.scanned`
- Metrics: `scribe.draft_quality`, `guardian.risk_levels`

**Acceptance Criteria:**
- ✅ Draft generated within 5 seconds
- ✅ Draft is IP-safe (LOW or MEDIUM risk only)
- ✅ Draft includes relevant hashtags
- ✅ Guardian report clearly explains any risks
- ✅ Draft is professional and engaging (> 4.0/5.0 quality score)

---

### 3.4 Feature: IP Safety (The Guardian)

**User Story:** As a researcher, I want my content automatically scanned for IP risks so I don't accidentally share sensitive information.

**UX Flow:**
1. Content generated (draft post or user message)
2. Guardian agent scans content for IP risks
3. Risk level assigned (LOW, MEDIUM, HIGH)
4. If HIGH, content blocked
5. If MEDIUM, warning shown with suggestions
6. If LOW, content approved

**API Usage:**
- Automatically triggered for drafts
- `POST /api/v1/content/scan` (standalone endpoint)

**Data Contracts:**
- Request: `ContentScanRequest` (see `contract/schemas/guardian.json`)
- Response: `GuardianReport`

**Error Cases:**
- `SCAN_FAILED`: Guardian agent error
- `INVALID_CONTENT`: Content format invalid

**Authorization:**
- Same as content creation

**Performance Budget:**
- Latency: < 2s
- Payload: < 3KB

**Telemetry:**
- Event: `agent.guardian.scan_completed`
- Metrics: `guardian.risk_distribution`, `guardian.block_rate`

**Acceptance Criteria:**
- ✅ HIGH risk content always blocked
- ✅ Risk reasons clearly explained
- ✅ Suggestions provided for MEDIUM risk
- ✅ False positive rate < 5%

---

### 3.5 Feature: Grant Critique (PI Simulator)

**User Story:** As a researcher, I want to get feedback on my grant proposals from a simulated PI perspective so I can improve my applications.

**UX Flow:**
1. User selects "pi" agent mode or mentions grant/proposal
2. Intent classifier detects "grant" intent
3. Orchestrator routes to PI Simulator agent
4. PI Simulator provides critical, domain-specific feedback
5. Response displayed in chat

**API Usage:**
- `POST /api/v1/sessions/{session_id}/messages` (agent_mode="pi")

**Data Contracts:**
- Same as message processing

**Error Cases:**
- `AGENT_TIMEOUT`: Response exceeded 10 seconds
- `INVALID_GRANT_FORMAT`: Grant text format invalid

**Performance Budget:**
- Latency: < 5s (uses Gemini Pro)
- Payload: < 20KB (detailed feedback)

**Telemetry:**
- Event: `agent.pi_simulator.executed`
- Metrics: `pi_simulator.feedback_quality`

**Acceptance Criteria:**
- ✅ Feedback is constructive and specific
- ✅ Feedback references grant structure (background, methods, budget)
- ✅ Response quality score > 4.0/5.0

---

### 3.6 Feature: Cross-Session Memory

**User Story:** As a user, I want the system to remember my past conversations so I get personalized responses and can ask about my research journey.

**UX Flow:**
1. User sends message
2. Memory query classifier determines if query is about past memories
3. Graph memory service retrieves relevant context
4. Context passed to agent for personalized response
5. New memories saved to graph after response

**API Usage:**
- Automatic via `POST /api/v1/sessions/{session_id}/messages`
- `GET /api/v1/users/{user_id}/memory/summary` (memory summary)
- `GET /api/v1/users/{user_id}/memory/timeline` (journey timeline)

**Data Contracts:**
- Memory summary: `MemorySummaryResponse` (see `contract/schemas/memory.json`)
- Timeline: `MemoryTimelineResponse`

**Error Cases:**
- `MEMORY_NOT_FOUND`: No memories for user
- `MEMORY_RETRIEVAL_ERROR`: Graph traversal failed

**Performance Budget:**
- Latency: < 500ms for memory retrieval
- Payload: < 50KB for full summary

**Telemetry:**
- Event: `memory.retrieved`
- Metrics: `memory.retrieval_time`, `memory.nodes_count`

**Acceptance Criteria:**
- ✅ Memory retrieved within 500ms
- ✅ Relevant context included in agent responses
- ✅ Quantitative queries ("how many times") extract specific numbers
- ✅ Memory summary includes all node types (struggles, insights, breakthroughs)

---

## 4. Non-Functional Requirements

### 4.1 Accessibility (WCAG 2.1 Level AA)

- **Keyboard Navigation:** All interactive elements accessible via keyboard
- **Screen Readers:** All content has proper ARIA labels
- **Color Contrast:** Minimum 4.5:1 for text, 3:1 for UI components
- **Focus Management:** Visible focus indicators, logical tab order
- **Error Messages:** Clear, descriptive error messages announced to screen readers

**Implementation:**
- Streamlit components use semantic HTML
- Custom components include `aria-label` attributes
- Design tokens enforce contrast ratios (see `contract/design-system/tokens.json`)

### 4.2 Internationalization and Localization

- **Current:** English only
- **Future:** Multi-language support (i18n) planned for v2.0
- **Text Externalization:** All user-facing strings in translation files
- **Date/Time:** ISO 8601 format, UTC timezone

### 4.3 Security and Privacy

- **PII Handling:** User messages stored in graph memory (per-user graphs)
- **Anonymization:** Global graph uses anonymized content only
- **Logging Redaction:** PII redacted from logs (see `contract/telemetry.md`)
- **Data Retention:** User graphs persisted to JSON files, no automatic deletion
- **IP Safety:** Guardian agent scans all public-facing content

**Compliance:**
- GDPR-ready (user data deletion on request)
- No third-party analytics without consent

### 4.4 Observability

- **Structured Logging:** JSON logs with trace IDs (see `contract/telemetry.md`)
- **Metrics:** Prometheus-compatible metrics (latency, success rate, token usage)
- **Tracing:** Distributed tracing with span IDs
- **Error Tracking:** Errors logged with stack traces and context

**Tools:**
- Loguru for Python logging
- Custom observability service (see `services/observability.py`)

### 4.5 Reliability

- **Timeouts:** 10s timeout for agent responses
- **Retries:** 3 retries with exponential backoff for transient errors
- **Idempotency:** Message processing idempotent via `message_id` (future)
- **Circuit Breakers:** Not implemented in v1.0 (future enhancement)
- **Graceful Degradation:** System continues if non-critical agents fail (e.g., Matchmaker)

---

## 5. API Contract

### 5.1 Protocol and Versioning

- **Protocol:** HTTP/JSON (REST)
- **Base URL:** `https://api.researchinpublic.ai/v1` (production)
- **Versioning:** URL-based (`/v1/`, `/v2/`)
- **Content-Type:** `application/json`
- **Accept:** `application/json`

### 5.2 Naming Conventions

- **Resources:** Plural nouns (`/sessions`, `/users`, `/messages`)
- **Actions:** HTTP verbs (GET, POST, PUT, DELETE)
- **Query Parameters:** snake_case (`agent_mode`, `top_k`)
- **Request/Response Fields:** snake_case (`session_id`, `user_id`)

### 5.3 Resource Shapes

See `contract/openapi.yaml` for complete API specification.

**Core Resources:**
- `Session`: Conversation session with user
- `Message`: User or agent message
- `MemoryNode`: Single memory in graph
- `MemoryEdge`: Connection between memories
- `SocialDraft`: Drafted social media content
- `GuardianReport`: IP safety scan result
- `MatchResult`: Peer match suggestion

### 5.4 Pagination, Filtering, Sorting

See `contract/pagination-filtering.md` for details.

**Pagination:**
- Query params: `page` (1-indexed), `per_page` (default: 20, max: 100)
- Response includes: `total`, `page`, `per_page`, `has_next`, `has_prev`

**Filtering:**
- Query params: `filter[node_type]`, `filter[user_id]`, `filter[created_after]`
- Operators: `eq`, `ne`, `gt`, `lt`, `contains`

**Sorting:**
- Query param: `sort` (e.g., `sort=-created_at` for descending)

### 5.5 Idempotency

- **Unsafe Methods:** POST requests support `Idempotency-Key` header
- **Key Format:** UUID v4
- **Storage:** Keys stored for 24 hours
- **Response:** Duplicate requests return same response (200) with `X-Idempotent-Replay: true`

### 5.6 Error Model

See `contract/error-model.md` for complete error specification.

**Error Format (RFC 7807 Problem+JSON):**
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

**Error Codes:**
- `AGENT_TIMEOUT` (504): Agent response timeout
- `MEMORY_ERROR` (500): Memory retrieval/save failed
- `INVALID_SESSION` (404): Session not found
- `GUARDIAN_BLOCKED` (403): Content blocked by Guardian
- `VALIDATION_ERROR` (400): Request validation failed

### 5.7 Rate Limiting

- **Limit:** 100 requests per minute per user (future)
- **Headers:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- **Response:** 429 Too Many Requests with `Retry-After` header

### 5.8 Caching

- **Cache-Control:** `no-cache` for dynamic content (messages, drafts)
- **ETag:** Supported for memory summaries (future)
- **CDN:** Static assets cached (future)

---

## 6. Event/Async Contract

**Current Status:** Synchronous only (no async events in v1.0)

**Future Events (v2.0):**
- `user.message.sent`: User sends message
- `agent.response.generated`: Agent generates response
- `memory.node.created`: New memory node added
- `match.suggested`: Peer match suggested
- `draft.created`: Social draft created
- `guardian.scan.completed`: Guardian scan completed

**Event Schema:**
See `contract/events.md` for future event specifications.

**Delivery Semantics:**
- At-least-once delivery
- Idempotent handlers
- Retry policy: Exponential backoff (3 retries)

---

## 7. Design System and UI Rules

### 7.1 Design Tokens

See `contract/design-system/tokens.json` for complete token specification.

**Color Roles:**
- `primary`: Brand color (#2563EB)
- `surface`: Background surfaces (#FFFFFF light, #1F2937 dark)
- `success`: Success states (#10B981)
- `warning`: Warning states (#F59E0B)
- `danger`: Error/danger states (#EF4444)
- `info`: Informational states (#3B82F6)

**Spacing Scale:**
- Base unit: 4px
- Scale: 0, 2, 4, 8, 12, 16, 24, 32, 48, 64

**Typography:**
- Font family: System fonts (SF Pro, Segoe UI, Roboto)
- Sizes: 12px, 14px, 16px, 18px, 24px, 32px
- Weights: 400 (regular), 500 (medium), 600 (semibold), 700 (bold)

**Breakpoints:**
- `xs`: 0px
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px

### 7.2 Component Library

See `contract/design-system/components.md` for complete component specifications.

**Base Components:**
- `Button`: Primary, secondary, ghost variants
- `Input`: Text input with validation states
- `TextArea`: Multi-line text input
- `Select`: Dropdown selection
- `ChatMessage`: User/assistant message display
- `Card`: Container for content sections
- `Skeleton`: Loading state placeholder
- `Toast`: Notification/toast messages
- `Expander`: Collapsible content sections

**Accessibility Requirements:**
- All interactive elements keyboard accessible
- ARIA labels for screen readers
- Focus indicators visible
- Error states announced

### 7.3 Layout Grid

- **Container Width:** Max 1280px (centered)
- **Grid:** 12-column grid system
- **Gutters:** 16px (mobile), 24px (desktop)
- **Responsive:** Stack on mobile (< 768px)

### 7.4 Theming

- **Light Mode:** Default
- **Dark Mode:** Future enhancement (tokens defined)
- **Contrast Ratios:** WCAG AA compliant (4.5:1 text, 3:1 UI)

### 7.5 Empty/Loading/Error States

- **Empty:** "No messages yet. Start a conversation!"
- **Loading:** Skeleton components or spinners
- **Error:** Clear error message with retry action

---

## 8. Route Map and Navigation

See `contract/routes.md` for complete route specification.

**Current Routes (Streamlit):**
- `/`: Main chat interface
- Sidebar: Settings, Graph Memory, Observability Dashboard

**Future Routes (SPA):**
- `/`: Chat interface
- `/sessions`: Session list
- `/sessions/:id`: Session detail
- `/memory`: Memory timeline
- `/settings`: User settings

**Route Guards:**
- No authentication required in v1.0
- Future: Protected routes require authentication

**Breadcrumbs:**
- `Home > Sessions > Session Detail`
- `Home > Memory > Timeline`

---

## 9. Front-End State Contracts

See `contract/state.md` for complete state specification.

**State Slices:**
- `sessions`: Active sessions map
- `messages`: Current session messages
- `memory`: User memory graph
- `ui`: UI state (modals, expanders, etc.)

**Cache Keys:**
- `session:{session_id}`: Session data
- `memory:{user_id}`: User memory graph
- `matches:{session_id}`: Peer matches

**Invalidation:**
- Session cache invalidated on new message
- Memory cache invalidated on memory save
- Matches cache invalidated on new struggle

**Data Fetching:**
- Stale-while-revalidate pattern
- Optimistic updates for message sending

---

## 10. Testing Strategy

See `contract/testing.md` for complete testing specification.

**Contract Tests:**
- Validate OpenAPI schema against actual responses
- Run on every PR

**Unit Tests:**
- Agent logic, memory retrieval, intent classification
- Coverage target: 80%

**Integration Tests:**
- End-to-end message processing
- Memory save/retrieve cycles
- Mock external services (Gemini API)

**E2E Tests:**
- Full user flows (vent → match → draft)
- Playwright/Cypress for UI tests

**Accessibility Tests:**
- axe-core automated testing
- Manual keyboard navigation testing

**Mock Strategy:**
- MSW (Mock Service Worker) for API mocking
- Prism for OpenAPI mock server
- Seed data for consistent tests

---

## 11. Telemetry and Analytics

See `contract/telemetry.md` for complete telemetry specification.

**Events:**
- `agent.executed`: Agent execution (with agent name)
- `memory.retrieved`: Memory retrieval
- `draft.created`: Social draft created
- `match.suggested`: Peer match suggested

**Metrics:**
- `agent.latency`: Agent response time (histogram)
- `agent.success_rate`: Agent success rate (gauge)
- `agent.token_usage`: Token consumption (counter)
- `memory.retrieval_time`: Memory retrieval latency (histogram)

**Traces:**
- `process_message`: Full message processing span
- `agent.{name}`: Individual agent execution spans

**PII Policy:**
- User messages not logged (only metadata)
- Trace IDs used for correlation
- PII redacted from logs

---

## 12. Change Control

See `contract/change-control.md` for complete change control process.

**Contract Semver:**
- **MAJOR:** Breaking API changes (new required fields, removed endpoints)
- **MINOR:** New endpoints, optional fields added
- **PATCH:** Bug fixes, documentation updates

**Contract Change Request (CCR) Template:**
1. Summary and motivation
2. Contract diff (OpenAPI, schemas)
3. Migration steps and timeline
4. Approvals required (FE, BE, Design, QA)

**Deprecation Policy:**
- 90-day deprecation window
- Deprecated endpoints return `X-Deprecated: true` header
- Migration guide provided

**Approval Path:**
1. Create CCR in GitHub issue
2. Review by FE/BE leads
3. Design review (if UI changes)
4. QA review (if test changes)
5. Security review (if auth/data changes)
6. Merge after approvals

---

## 13. Sign-Off Checklist

- [ ] **Frontend Lead:** Design system tokens and components approved
- [ ] **Backend Lead:** API contract and error model approved
- [ ] **Design Lead:** UI components and accessibility requirements approved
- [ ] **QA Lead:** Testing strategy and contract tests approved
- [ ] **Security Lead:** PII handling and IP safety approved
- [ ] **Ops Lead:** Observability and telemetry approved

**Sign-off Date:** TBD  
**Contract Version:** 1.0.0

---

## 14. Decision Log

### 14.1 API Protocol: REST over GraphQL

**Decision:** Use REST API with OpenAPI specification instead of GraphQL.

**Rationale:**
- Simpler for initial implementation
- Better tooling support (OpenAPI generators, mock servers)
- Easier to understand for team members
- Can migrate to GraphQL later if needed

**Alternatives Considered:**
- GraphQL: More flexible but adds complexity
- tRPC: Type-safe but requires TypeScript

**Date:** 2025-12-01

### 14.2 Design System: Streamlit Native vs Custom Components

**Decision:** Use Streamlit native components with design token overrides.

**Rationale:**
- Faster development (no custom component library needed)
- Streamlit handles accessibility basics
- Design tokens ensure consistency
- Can migrate to custom components later if needed

**Alternatives Considered:**
- Custom React components: More control but requires separate FE framework
- Material-UI: Overkill for current scope

**Date:** 2025-12-01

### 14.3 Memory Storage: JSON Files vs Database

**Decision:** Use JSON files for memory persistence (current implementation).

**Rationale:**
- Simpler for MVP (no database setup)
- Easy to inspect and debug
- Can migrate to database later for scale
- Sufficient for single-user demo

**Alternatives Considered:**
- PostgreSQL: More scalable but adds infrastructure
- Redis: Fast but ephemeral (not suitable for long-term memory)

**Date:** 2025-12-01

### 14.4 Authentication: None vs OAuth2

**Decision:** No authentication in v1.0 (demo mode with user IDs).

**Rationale:**
- Faster MVP development
- Focus on core agent functionality first
- Authentication can be added in v2.0
- Current use case is single-user demo

**Alternatives Considered:**
- OAuth2: Standard but adds complexity
- JWT: Simple but still requires auth flow

**Date:** 2025-12-01

---

## How to Work in Parallel

### For Frontend Developers

1. **Start with Mocks:**
   ```bash
   # Generate types from OpenAPI
   npm run generate-types
   
   # Start mock server
   npm run mock-server
   ```

2. **Use Generated Types:**
   - Import from `src/gen/types`
   - Types match API contract exactly
   - TypeScript/IDE autocomplete works

3. **Implement UI Components:**
   - Follow design tokens from `contract/design-system/tokens.json`
   - Use component specs from `contract/design-system/components.md`
   - Test with mock API responses

4. **Contract Tests:**
   - Run contract tests: `npm run test:contract`
   - Ensures UI matches API contract

### For Backend Developers

1. **Implement API Endpoints:**
   - Follow OpenAPI spec in `contract/openapi.yaml`
   - Use generated types from schemas
   - Return exact response shapes

2. **Error Handling:**
   - Use error codes from `contract/error-model.md`
   - Return Problem+JSON format
   - Include trace IDs

3. **Contract Validation:**
   - Run contract tests: `pytest tests/contract/`
   - Validates responses match OpenAPI schema

4. **Memory Management:**
   - Follow memory contracts in `contract/schemas/memory.json`
   - Use graph memory service for persistence

### Weekly CCR Cadence

- **Monday:** Review open CCRs
- **Wednesday:** Design review (if UI changes)
- **Friday:** Approve and merge CCRs
- **Version bumps:** On merge (semver)

---

**End of Contract Document**


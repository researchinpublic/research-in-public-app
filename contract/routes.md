# Route Map and Navigation

**Version:** 1.0.0  
**Last Updated:** 2024-11-19

This document defines the route map and navigation structure for Research In Public.

---

## Current Routes (Streamlit v1.0)

### Main Application

**Route:** `/` (root)  
**Component:** Chat interface  
**Description:** Main conversation interface with agents

**Features:**
- Chat input and message display
- Agent mode selector (sidebar)
- Draft Post button
- Session info expander
- Observability dashboard

### Sidebar Routes

**Route:** Sidebar (always visible)  
**Components:**
- Agent information
- Settings (agent mode selector)
- New Session button
- Graph Memory expander
- Safety Tests button

---

## Future Routes (SPA v2.0)

### Public Routes

**Route:** `/`  
**Component:** Landing page  
**Description:** Product introduction and login

**Route:** `/login`  
**Component:** Login page  
**Description:** User authentication

**Route:** `/signup`  
**Component:** Signup page  
**Description:** User registration

### Protected Routes (Require Authentication)

**Route:** `/chat`  
**Component:** Chat interface  
**Description:** Main conversation interface  
**Breadcrumb:** `Home > Chat`

**Route:** `/sessions`  
**Component:** Session list  
**Description:** List of all user sessions  
**Breadcrumb:** `Home > Sessions`

**Route:** `/sessions/:id`  
**Component:** Session detail  
**Description:** View specific session and messages  
**Breadcrumb:** `Home > Sessions > Session Detail`

**Route:** `/memory`  
**Component:** Memory timeline  
**Description:** View user's research journey graph  
**Breadcrumb:** `Home > Memory`

**Route:** `/memory/summary`  
**Component:** Memory summary  
**Description:** Summary of user's memory  
**Breadcrumb:** `Home > Memory > Summary`

**Route:** `/drafts`  
**Component:** Draft list  
**Description:** List of drafted social media posts  
**Breadcrumb:** `Home > Drafts`

**Route:** `/settings`  
**Component:** User settings  
**Description:** User preferences and configuration  
**Breadcrumb:** `Home > Settings`

---

## URL Patterns

### Pattern Conventions

- **Lowercase** URLs
- **Hyphens** for word separation (not underscores)
- **Plural** nouns for resource collections
- **Singular** nouns for resource details

### Examples

```
/sessions              # List sessions
/sessions/123          # Session detail
/memory                # Memory timeline
/memory/summary        # Memory summary
/drafts                # List drafts
/settings              # User settings
```

---

## Route Guards

### Authentication Guard

**Current (v1.0):** None (demo mode)

**Future (v2.0):**
- Check for valid JWT token
- Redirect to `/login` if not authenticated
- Store intended route for post-login redirect

### Authorization Guard

**Future (v2.0):**
- Check user permissions for resource access
- Redirect to `/403` if unauthorized
- Show error message

### Session Guard

**Future (v2.0):**
- Validate session exists
- Redirect to `/sessions` if session not found
- Show error message

---

## Breadcrumbs

### Breadcrumb Rules

1. **Home** always first
2. **Current page** last (not linked)
3. **Intermediate pages** linked
4. **Maximum depth:** 3 levels

### Examples

```
Home > Chat
Home > Sessions > Session Detail
Home > Memory > Summary
Home > Settings
```

### Breadcrumb Component Props

```typescript
interface BreadcrumbItem {
  label: string;
  href?: string;  // undefined for current page
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}
```

---

## Navigation Structure

### Main Navigation (Header)

**Items:**
- Chat (active indicator)
- Sessions
- Memory
- Drafts
- Settings

**Mobile:** Hamburger menu

### Sidebar Navigation (Chat Page)

**Sections:**
- Agent Info
- Settings
- Actions (New Session, Draft Post)
- Memory Info
- Observability

---

## Canonical Links

### Session URLs

**Format:** `/sessions/{session_id}`

**Canonical:** Always use session ID (not slug)

### Memory URLs

**Format:** `/memory` (timeline) or `/memory/summary`

**Canonical:** Use consistent paths (no query params for navigation)

---

## Deep Linking

### Supported Deep Links

**Session:** `/sessions/{session_id}`  
**Memory Node:** `/memory?node={node_id}` (future)  
**Draft:** `/drafts/{draft_id}` (future)

### Deep Link Handling

1. Validate resource exists
2. Load resource data
3. Navigate to appropriate route
4. Show error if resource not found

---

## Route Transitions

### Loading States

- Show skeleton/spinner during route transition
- Show error state if route fails to load
- Preserve scroll position where possible

### Animation

- **Fade in/out:** 200ms (`motion.duration.normal`)
- **Slide:** For modal/drawer routes
- **No animation:** For instant navigation (same section)

---

## SEO and Meta Tags

### Meta Tags (Future)

**Home:**
- Title: "Research In Public - Agentic Support for Researchers"
- Description: "Transform your research journey into emotional support and public narratives"

**Chat:**
- Title: "Chat - Research In Public"
- Description: "Get support from AI agents"

**Sessions:**
- Title: "Sessions - Research In Public"
- Description: "View your conversation history"

---

## Implementation Notes

### Current Implementation (Streamlit)

- Single-page application (no routing)
- Sidebar for navigation
- Expanders for collapsible sections

### Future Implementation (SPA)

- **Router:** React Router or Next.js Router
- **Route Guards:** Higher-order components or hooks
- **Breadcrumbs:** Context-based breadcrumb provider
- **Deep Linking:** URL parameter parsing

---

**End of Route Map and Navigation**


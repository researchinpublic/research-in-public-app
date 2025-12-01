# Front-End State Contracts

**Version:** 1.0.0  
**Last Updated:** 2025-12-01

This document defines the front-end state management contracts for Research In Public.

---

## State Architecture

### Current Implementation (Streamlit)

**State Management:** Streamlit session state (`st.session_state`)

**State Slices:**
- `orchestrator`: AgentOrchestrator instance
- `sessions`: Dictionary of sessions (`{session_id: session}`)
- `current_session`: Current active session
- `messages`: List of chat messages
- `graph_memory`: GraphMemoryService instance
- `pending_draft`: Pending social draft (if any)

---

## Future State Architecture (SPA)

### State Store Structure

```typescript
interface AppState {
  sessions: SessionsState;
  messages: MessagesState;
  memory: MemoryState;
  ui: UIState;
  auth: AuthState;
}
```

---

## State Slices

### Sessions State

```typescript
interface SessionsState {
  sessions: Record<string, Session>;
  currentSessionId: string | null;
  loading: boolean;
  error: string | null;
}
```

**Cache Keys:**
- `session:{session_id}`: Individual session
- `sessions:list`: List of all sessions

**Invalidation:**
- Invalidate on new message
- Invalidate on session creation
- Invalidate on session update

---

### Messages State

```typescript
interface MessagesState {
  messages: Record<string, Message[]>;  // keyed by session_id
  loading: boolean;
  sending: boolean;
  error: string | null;
}
```

**Cache Keys:**
- `messages:{session_id}`: Messages for session

**Invalidation:**
- Invalidate on new message
- Invalidate on message update

---

### Memory State

```typescript
interface MemoryState {
  graph: GraphMemory | null;
  summary: MemorySummary | null;
  timeline: MemoryNode[];
  loading: boolean;
  error: string | null;
}
```

**Cache Keys:**
- `memory:{user_id}`: User memory graph
- `memory:{user_id}:summary`: Memory summary
- `memory:{user_id}:timeline`: Memory timeline

**Invalidation:**
- Invalidate on memory save
- Invalidate on new memory node
- Invalidate on memory update

---

### UI State

```typescript
interface UIState {
  sidebarOpen: boolean;
  modals: {
    draftPreview: boolean;
    sessionSettings: boolean;
  };
  expanders: {
    graphMemory: boolean;
    observability: boolean;
  };
  toasts: Toast[];
}
```

**Cache Keys:** None (UI state not cached)

**Invalidation:** N/A (ephemeral state)

---

### Auth State (Future)

```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}
```

**Cache Keys:**
- `auth:user`: Current user
- `auth:token`: Access token

**Invalidation:**
- Invalidate on logout
- Invalidate on token expiration

---

## Data Fetching Conventions

### Stale-While-Revalidate

**Pattern:** Return cached data immediately, then fetch fresh data in background

**Example:**
```typescript
function useSession(sessionId: string) {
  const cached = getCached(`session:${sessionId}`);
  const [data, setData] = useState(cached);
  
  useEffect(() => {
    // Return cached immediately
    if (cached) setData(cached);
    
    // Fetch fresh data
    fetchSession(sessionId).then(setData);
  }, [sessionId]);
  
  return data;
}
```

### Optimistic Updates

**Pattern:** Update UI immediately, rollback on error

**Example:**
```typescript
function sendMessage(message: string) {
  // Optimistic update
  const tempMessage = { id: 'temp', content: message, role: 'user' };
  addMessage(tempMessage);
  
  // Send to server
  api.sendMessage(message)
    .then(realMessage => {
      replaceMessage('temp', realMessage);
    })
    .catch(error => {
      removeMessage('temp');
      showError(error);
    });
}
```

---

## Cache Keys

### Key Format

**Pattern:** `{resource}:{identifier}` or `{resource}:{identifier}:{subresource}`

**Examples:**
- `session:123`
- `messages:123`
- `memory:demo_user`
- `memory:demo_user:summary`
- `memory:demo_user:timeline`

### Key Generation

```typescript
function getCacheKey(resource: string, ...identifiers: string[]): string {
  return `${resource}:${identifiers.join(':')}`;
}
```

---

## Cache Invalidation

### Invalidation Triggers

**On Message Sent:**
- Invalidate `messages:{session_id}`
- Invalidate `session:{session_id}` (update message_count)

**On Memory Save:**
- Invalidate `memory:{user_id}`
- Invalidate `memory:{user_id}:summary`
- Invalidate `memory:{user_id}:timeline`

**On Session Created:**
- Invalidate `sessions:list`
- Add new session to cache

**On Draft Created:**
- Invalidate `drafts:list` (future)

---

## Error Boundaries

### Error Boundary Strategy

**Component-Level:** Wrap major sections (Chat, Memory, Sessions)

**Route-Level:** Wrap entire routes

**Global:** Catch-all error boundary at app root

### Error State

```typescript
interface ErrorState {
  error: Error | null;
  errorInfo: ErrorInfo | null;
  retry: () => void;
}
```

### Error Recovery

- **Retry:** Show retry button
- **Fallback:** Show fallback UI
- **Logging:** Log error to telemetry

---

## State Persistence

### Local Storage

**Persist:**
- User preferences
- UI state (sidebar open/closed)
- Auth token (future)

**Don't Persist:**
- Messages (too large)
- Memory graph (too large)
- Sessions (fetch on load)

### Session Storage

**Persist:**
- Temporary UI state
- Form drafts

---

## State Management Library (Future)

### Recommended: Zustand or Redux Toolkit

**Zustand (Simpler):**
- Lightweight
- Good for small-medium apps
- Less boilerplate

**Redux Toolkit (More Features):**
- DevTools support
- Middleware ecosystem
- Better for large apps

---

## Testing State

### Unit Tests

- Test state reducers/actions
- Test cache invalidation logic
- Test error handling

### Integration Tests

- Test state updates on API calls
- Test cache behavior
- Test optimistic updates

---

## Performance Considerations

### State Size

- **Limit:** Keep state slices < 1MB
- **Pagination:** Use pagination for large lists
- **Lazy Loading:** Load data on demand

### Memoization

- Memoize expensive computations
- Use React.memo for expensive components
- Use useMemo for derived state

---

**End of Front-End State Contracts**


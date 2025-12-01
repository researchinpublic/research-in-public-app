# Event/Async Contract

**Version:** 1.0.0  
**Last Updated:** 2025-12-01

This document defines the event/async contract for Research In Public (future enhancement).

---

## Current Status (v1.0)

**Status:** Synchronous only (no async events)

All operations are synchronous HTTP requests/responses. No event-driven architecture in v1.0.

---

## Future Event Architecture (v2.0)

### Event Types

#### User Events

**user.message.sent**
- **Trigger:** User sends a message
- **Payload:**
```json
{
  "event_id": "evt_123",
  "event_type": "user.message.sent",
  "timestamp": "2025-12-01T10:00:00Z",
  "user_id": "demo_user",
  "session_id": "session_123",
  "data": {
    "message_id": "msg_456",
    "content": "I'm frustrated with my research",
    "agent_mode": "auto"
  }
}
```

**user.session.created**
- **Trigger:** New session created
- **Payload:**
```json
{
  "event_id": "evt_124",
  "event_type": "user.session.created",
  "timestamp": "2025-12-01T10:00:00Z",
  "user_id": "demo_user",
  "data": {
    "session_id": "session_123"
  }
}
```

#### Agent Events

**agent.response.generated**
- **Trigger:** Agent generates response
- **Payload:**
```json
{
  "event_id": "evt_125",
  "event_type": "agent.response.generated",
  "timestamp": "2025-12-01T10:00:05Z",
  "user_id": "demo_user",
  "session_id": "session_123",
  "data": {
    "agent_name": "Vent Validator",
    "message_id": "msg_457",
    "latency_ms": 2500,
    "token_usage": 150
  }
}
```

**agent.match.suggested**
- **Trigger:** Peer match suggested
- **Payload:**
```json
{
  "event_id": "evt_126",
  "event_type": "agent.match.suggested",
  "timestamp": "2025-12-01T10:00:06Z",
  "user_id": "demo_user",
  "session_id": "session_123",
  "data": {
    "match_count": 3,
    "similarity_scores": [0.85, 0.78, 0.72]
  }
}
```

#### Memory Events

**memory.node.created**
- **Trigger:** New memory node added
- **Payload:**
```json
{
  "event_id": "evt_127",
  "event_type": "memory.node.created",
  "timestamp": "2025-12-01T10:00:07Z",
  "user_id": "demo_user",
  "data": {
    "node_id": "node_789",
    "node_type": "struggle",
    "content_preview": "I'm frustrated with..."
  }
}
```

**memory.edge.created**
- **Trigger:** Memory edge created (connection between nodes)
- **Payload:**
```json
{
  "event_id": "evt_128",
  "event_type": "memory.edge.created",
  "timestamp": "2025-12-01T10:00:08Z",
  "user_id": "demo_user",
  "data": {
    "edge_id": "edge_456",
    "source_id": "node_789",
    "target_id": "node_790",
    "relationship": "led_to",
    "strength": 0.85
  }
}
```

#### Content Events

**draft.created**
- **Trigger:** Social draft created
- **Payload:**
```json
{
  "event_id": "evt_129",
  "event_type": "draft.created",
  "timestamp": "2025-12-01T10:05:00Z",
  "user_id": "demo_user",
  "session_id": "session_123",
  "data": {
    "draft_id": "draft_123",
    "platform": "linkedin",
    "risk_level": "LOW",
    "hashtags": ["Research", "Academia"]
  }
}
```

**guardian.scan.completed**
- **Trigger:** Guardian scan completed
- **Payload:**
```json
{
  "event_id": "evt_130",
  "event_type": "guardian.scan.completed",
  "timestamp": "2025-12-01T10:05:01Z",
  "user_id": "demo_user",
  "data": {
    "scan_id": "scan_456",
    "risk_level": "LOW",
    "blocked": false,
    "concerns": []
  }
}
```

---

## Event Schema

### Common Event Structure

```json
{
  "event_id": "string (UUID)",
  "event_type": "string",
  "timestamp": "ISO 8601 datetime",
  "user_id": "string",
  "session_id": "string (optional)",
  "trace_id": "string (optional)",
  "data": {
    // Event-specific payload
  }
}
```

### Event Metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | `string` (UUID) | Yes | Unique event identifier |
| `event_type` | `string` | Yes | Event type (e.g., "user.message.sent") |
| `timestamp` | `ISO 8601` | Yes | Event timestamp (UTC) |
| `user_id` | `string` | Yes | User identifier |
| `session_id` | `string` | No | Session identifier (if applicable) |
| `trace_id` | `string` | No | Trace ID for correlation |
| `data` | `object` | Yes | Event-specific payload |

---

## Event Topics/Queues

### Topic Structure

**Format:** `{service}.{entity}.{action}`

**Examples:**
- `user.message.sent`
- `agent.response.generated`
- `memory.node.created`
- `draft.created`

### Topic Naming Convention

- **Lowercase** with dots as separators
- **Service** (user, agent, memory, content)
- **Entity** (message, session, node, draft)
- **Action** (sent, created, updated, deleted)

---

## Delivery Semantics

### At-Least-Once Delivery

- Events are delivered **at least once**
- Handlers must be **idempotent**
- Use `event_id` for deduplication

### Idempotency

**Handler Requirements:**
- Check if event already processed (using `event_id`)
- Skip processing if duplicate
- Return success if already processed

**Example:**
```python
def handle_event(event):
    if event_already_processed(event.event_id):
        return  # Idempotent: skip duplicate
    process_event(event)
    mark_event_processed(event.event_id)
```

---

## Retry Policy

### Exponential Backoff

- **Initial delay:** 1 second
- **Max delay:** 60 seconds
- **Max retries:** 3
- **Backoff multiplier:** 2

**Retry Schedule:**
1. Retry 1: After 1 second
2. Retry 2: After 2 seconds
3. Retry 3: After 4 seconds
4. Give up: After 3 retries

### Dead Letter Queue

- Events that fail after max retries go to DLQ
- DLQ events require manual investigation
- DLQ events can be reprocessed after fix

---

## Event Ordering

### Per-User Ordering

- Events for same `user_id` are processed in order
- Events for different users can be processed in parallel

### Per-Session Ordering

- Events for same `session_id` are processed in order
- Ensures message processing order

---

## Event Consumers

### Real-Time Notifications (Future)

- WebSocket connections for real-time updates
- Push notifications for mobile apps
- Email notifications for important events

### Analytics Pipeline (Future)

- Event stream to analytics database
- Aggregation for dashboards
- User behavior analysis

### Audit Logging (Future)

- All events stored in audit log
- Compliance and debugging
- Retention: 90 days

---

## Implementation Notes

### Current Implementation

- No event system in v1.0
- All operations synchronous
- Events can be added in v2.0

### Future Implementation

- **Message Queue:** RabbitMQ or AWS SQS
- **Event Store:** Event sourcing pattern (optional)
- **Stream Processing:** Kafka or AWS Kinesis (for analytics)

---

**End of Event/Async Contract**


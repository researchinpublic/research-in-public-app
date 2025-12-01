# Telemetry and Analytics

**Version:** 1.0.0  
**Last Updated:** 2025-12-01

This document defines the telemetry, logging, metrics, and tracing strategy for Research In Public.

---

## Telemetry Overview

### Three Pillars

1. **Logs:** Structured logging for debugging and audit
2. **Metrics:** Numerical measurements for monitoring
3. **Traces:** Distributed tracing for request flow

---

## Logging

### Structured Logging

**Format:** JSON logs with consistent structure

**Example:**
```json
{
  "timestamp": "2025-12-01T10:00:00Z",
  "level": "INFO",
  "service": "agent_orchestrator",
  "trace_id": "abc123def456",
  "span_id": "span789",
  "message": "Message processed successfully",
  "fields": {
    "user_id": "demo_user",
    "session_id": "session_123",
    "agent_mode": "vent",
    "latency_ms": 2500
  }
}
```

### Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| `DEBUG` | Detailed debugging info | Function entry/exit |
| `INFO` | General information | Request processed |
| `WARNING` | Warning conditions | Agent timeout |
| `ERROR` | Error conditions | Agent failure |
| `CRITICAL` | Critical errors | System failure |

### Log Fields

**Required Fields:**
- `timestamp`: ISO 8601 datetime (UTC)
- `level`: Log level
- `message`: Human-readable message
- `trace_id`: Trace ID for correlation

**Optional Fields:**
- `span_id`: Span ID for tracing
- `user_id`: User identifier (if applicable)
- `session_id`: Session identifier (if applicable)
- `agent_name`: Agent name (if applicable)
- `error`: Error details (if error)

### PII Redaction

**Redaction Rules:**
- **User Messages:** Not logged (only metadata)
- **Memory Content:** Not logged (only node IDs)
- **Email Addresses:** Redacted (if logged)
- **API Keys:** Never logged

**Example:**
```python
# ❌ Don't log
logger.info(f"User message: {user_message}")

# ✅ Do log
logger.info("User message received", extra={
    "user_id": user_id,
    "message_length": len(user_message),
    "agent_mode": agent_mode
})
```

---

## Metrics

### Metric Types

#### Counter

**Purpose:** Count events (monotonically increasing)

**Examples:**
- `agent.executions.total` - Total agent executions
- `agent.tokens.used` - Total tokens used
- `memory.nodes.created` - Total memory nodes created

**Format:**
```
agent_executions_total{agent="vent_validator"} 150
```

#### Gauge

**Purpose:** Measure current value (can increase/decrease)

**Examples:**
- `agent.success_rate` - Agent success rate (0-1)
- `memory.nodes.count` - Current memory node count
- `sessions.active` - Active sessions

**Format:**
```
agent_success_rate{agent="vent_validator"} 0.95
```

#### Histogram

**Purpose:** Measure distribution of values

**Examples:**
- `agent.latency` - Agent response latency (seconds)
- `memory.retrieval_time` - Memory retrieval time (seconds)
- `api.request_duration` - API request duration (seconds)

**Format:**
```
agent_latency_bucket{agent="vent_validator",le="1.0"} 50
agent_latency_bucket{agent="vent_validator",le="3.0"} 140
agent_latency_bucket{agent="vent_validator",le="5.0"} 150
```

### Metric Labels

**Common Labels:**
- `agent`: Agent name (vent_validator, matchmaker, scribe, guardian, pi_simulator)
- `user_id`: User identifier
- `session_id`: Session identifier
- `status`: Status (success, error, timeout)

**Example:**
```
agent_latency{agent="vent_validator",status="success"} 2.5
```

### Metric Naming Convention

**Format:** `{service}.{entity}.{metric}`

**Examples:**
- `agent.executions.total`
- `agent.latency.seconds`
- `memory.nodes.count`
- `api.requests.total`

---

## Tracing

### Distributed Tracing

**Purpose:** Track request flow across services/components

### Trace Structure

```
Trace (trace_id: abc123)
├── Span: process_message (span_id: span1)
│   ├── Span: intent_classification (span_id: span2)
│   ├── Span: memory_retrieval (span_id: span3)
│   └── Span: agent_execution (span_id: span4)
│       ├── Span: vent_validator (span_id: span5)
│       └── Span: matchmaker (span_id: span6)
```

### Span Attributes

**Required:**
- `operation_name`: Operation name (e.g., "process_message")
- `start_time`: Span start time
- `duration`: Span duration (if completed)

**Optional:**
- `tags`: Key-value pairs (agent_name, user_id, etc.)
- `error`: Error details (if error)
- `logs`: Span logs

### Trace Context Propagation

**Headers:**
- `X-Trace-Id`: Trace ID
- `X-Span-Id`: Current span ID

**Example:**
```python
trace_id = observability_service.start_trace(
    "process_message",
    tags={"agent_mode": "vent", "user_id": "demo_user"}
)

# Propagate to child spans
span_id = observability_service.start_span(
    "agent_execution",
    parent_id=trace_id,
    tags={"agent_name": "vent_validator"}
)
```

---

## Events

### Event Types

#### Agent Events

**agent.executed**
- **Trigger:** Agent execution completed
- **Properties:**
  - `agent_name`: Agent name
  - `latency_ms`: Execution latency
  - `success`: Success status
  - `token_usage`: Token consumption

**agent.timeout**
- **Trigger:** Agent timeout
- **Properties:**
  - `agent_name`: Agent name
  - `timeout_seconds`: Timeout duration

#### Memory Events

**memory.retrieved**
- **Trigger:** Memory retrieval completed
- **Properties:**
  - `user_id`: User identifier
  - `retrieval_time_ms`: Retrieval latency
  - `nodes_count`: Number of nodes retrieved

**memory.node.created**
- **Trigger:** Memory node created
- **Properties:**
  - `user_id`: User identifier
  - `node_type`: Node type (struggle, insight, etc.)
  - `node_id`: Node identifier

#### Content Events

**draft.created**
- **Trigger:** Social draft created
- **Properties:**
  - `user_id`: User identifier
  - `platform`: Platform (linkedin, twitter)
  - `risk_level`: Guardian risk level

**guardian.scan.completed**
- **Trigger:** Guardian scan completed
- **Properties:**
  - `risk_level`: Risk level (LOW, MEDIUM, HIGH)
  - `blocked`: Whether content was blocked

---

## Observability Dashboard

### Metrics Displayed

**Agent Performance:**
- Average latency per agent
- Success rate per agent
- Total executions per agent
- Token usage per agent

**System Metrics:**
- Total metrics recorded
- Total traces
- Average memory retrieval time
- Total tokens used

**Recent Traces:**
- Operation name
- Duration
- Status (success/error)
- Error details (if error)

### Implementation

**Current:** Streamlit observability dashboard (see `app/main.py`)

**Future:** Grafana/Prometheus dashboard

---

## Sampling

### Trace Sampling

**Rate:** 10% of traces sampled (for performance)

**Sampling Rules:**
- Always sample errors
- Always sample slow requests (> 5s)
- Random sample 10% of normal requests

### Log Sampling

**Rate:** 100% (all logs sampled)

**Reason:** Logs are lightweight, no sampling needed

---

## Retention

### Logs

**Retention:** 30 days

**Storage:** Local files or cloud logging service

### Metrics

**Retention:** 90 days

**Storage:** Prometheus or cloud metrics service

### Traces

**Retention:** 7 days

**Storage:** Jaeger or cloud tracing service

---

## Privacy and Compliance

### PII Policy

- **User Messages:** Never logged
- **Memory Content:** Never logged (only metadata)
- **User IDs:** Logged (required for debugging)
- **Session IDs:** Logged (required for debugging)

### GDPR Compliance

- **Right to Access:** Users can request their logs
- **Right to Deletion:** Users can request log deletion
- **Data Minimization:** Only log necessary data

---

## Implementation

### Current Implementation

**Service:** `services/observability.py`

**Features:**
- Metrics recording
- Trace management
- Logging integration

### Future Enhancements

- **Prometheus Export:** Export metrics to Prometheus
- **Jaeger Integration:** Export traces to Jaeger
- **Cloud Logging:** Integrate with cloud logging services

---

## Testing Telemetry

### Unit Tests

- Test metric recording
- Test trace creation
- Test log formatting

### Integration Tests

- Test trace propagation
- Test metric aggregation
- Test log redaction

---

**End of Telemetry and Analytics**


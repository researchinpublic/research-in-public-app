# Testing Strategy

**Version:** 1.0.0  
**Last Updated:** 2024-11-19

This document defines the testing strategy for Research In Public, including contract tests, unit tests, integration tests, E2E tests, and accessibility tests.

---

## Testing Pyramid

```
        /\
       /E2E\          (10%)
      /------\
     /Integration\    (20%)
    /------------\
   /    Unit      \   (70%)
  /----------------\
```

**Distribution:**
- **Unit Tests:** 70% of tests
- **Integration Tests:** 20% of tests
- **E2E Tests:** 10% of tests

---

## Contract Tests

### Purpose

Validate that API responses match the OpenAPI contract specification.

### Implementation

**Tool:** `pytest` with `openapi-core` or `schemathesis`

**Location:** `tests/contract/`

**Example:**
```python
import pytest
from openapi_core import validate_request, validate_response
from openapi_spec_validator import validate_spec

def test_message_endpoint_contract(api_client, openapi_spec):
    """Validate message endpoint matches OpenAPI spec."""
    response = api_client.post(
        "/v1/sessions/123/messages",
        json={"content": "Test message"}
    )
    
    # Validate response against spec
    validate_response(
        request=request,
        response=response,
        spec=openapi_spec
    )
```

### Test Coverage

- [ ] All endpoints have contract tests
- [ ] Request validation (required fields, types)
- [ ] Response validation (schema, status codes)
- [ ] Error responses match error model

### Running Contract Tests

```bash
pytest tests/contract/ -v
```

---

## Unit Tests

### Purpose

Test individual components, functions, and classes in isolation.

### Coverage Target

**Minimum:** 80% code coverage

### Test Areas

**Agents:**
- Agent logic (Vent Validator, Matchmaker, Scribe, Guardian, PI Simulator)
- Intent classification
- Memory query classification

**Services:**
- Graph memory operations
- Vector search
- Context compaction
- Observability

**Orchestration:**
- Message routing
- Parallel execution
- Memory retrieval

### Example

```python
def test_vent_validator_empathy():
    """Test Vent Validator generates empathetic response."""
    agent = VentValidatorAgent()
    response = agent.process("I'm frustrated", session, memory_context="")
    
    assert "empathy" in response.lower() or "understand" in response.lower()
    assert len(response) > 50
```

### Running Unit Tests

```bash
pytest tests/unit/ -v --cov=agents --cov=services --cov=orchestration
```

---

## Integration Tests

### Purpose

Test interactions between components and external services.

### Test Areas

**End-to-End Message Processing:**
- User message → Intent classification → Agent routing → Response
- Memory retrieval and saving
- Peer matching flow

**Memory Operations:**
- Memory save → Graph update → Memory retrieval
- Cross-session memory retrieval

**Draft Creation:**
- Shareable moment detection → Draft generation → Guardian scan

### Mocking Strategy

**External Services:**
- Mock Gemini API responses
- Mock vector search (FAISS)
- Mock file system (memory persistence)

**Example:**
```python
@patch('services.gemini_service.gemini_service.generate_text')
def test_message_processing_integration(mock_gemini):
    """Test full message processing flow."""
    mock_gemini.return_value = "Test response"
    
    orchestrator = AgentOrchestrator(vector_store, graph_memory)
    response = orchestrator.process_message(
        "Test message",
        session,
        agent_mode="auto"
    )
    
    assert response["main_response"] == "Test response"
    assert response["agent_used"] == "Vent Validator"
```

### Running Integration Tests

```bash
pytest tests/integration/ -v
```

---

## E2E Tests

### Purpose

Test complete user flows through the application.

### Test Scenarios

**Scenario 1: Emotional Support Flow**
1. User sends emotional message
2. Vent Validator responds
3. Peer matches suggested
4. Memory saved

**Scenario 2: Content Drafting Flow**
1. User has shareable conversation
2. User clicks "Draft Post"
3. Scribe generates draft
4. Guardian scans draft
5. Draft displayed with report

**Scenario 3: Memory Query Flow**
1. User asks "how many times I tried"
2. Memory query classifier detects quantitative query
3. Memory retrieved with expanded search
4. Agent extracts specific numbers

### Tools

**Streamlit E2E:** `pytest` with `streamlit` test client

**Future SPA E2E:** Playwright or Cypress

### Example

```python
def test_emotional_support_flow(test_client):
    """Test complete emotional support user flow."""
    # Send message
    response = test_client.post(
        "/api/v1/sessions/123/messages",
        json={"content": "I'm frustrated with my research"}
    )
    
    assert response.status_code == 200
    assert "main_response" in response.json()
    assert "peer_matches" in response.json()
```

### Running E2E Tests

```bash
pytest tests/e2e/ -v
```

---

## Accessibility Tests

### Purpose

Ensure application meets WCAG 2.1 Level AA standards.

### Tools

**Automated:** `axe-core` (via `pytest-axe`)

**Manual:** Keyboard navigation, screen reader testing

### Test Areas

- **Keyboard Navigation:** All interactive elements accessible
- **Screen Readers:** ARIA labels, semantic HTML
- **Color Contrast:** WCAG AA compliant (4.5:1)
- **Focus Management:** Visible focus indicators
- **Error Messages:** Announced to screen readers

### Example

```python
def test_chat_interface_accessibility(page):
    """Test chat interface accessibility."""
    page.goto("/")
    
    # Run axe-core
    violations = page.run_axe()
    assert len(violations) == 0, f"Accessibility violations: {violations}"
    
    # Test keyboard navigation
    page.keyboard.press("Tab")
    assert page.locator("input").is_focused()
```

### Running Accessibility Tests

```bash
pytest tests/a11y/ -v
```

---

## Mock Strategy

### MSW (Mock Service Worker)

**Purpose:** Mock API responses for frontend development

**Location:** `src/gen/mocks/`

**Example:**
```typescript
import { rest } from 'msw';

export const handlers = [
  rest.post('/api/v1/sessions/:id/messages', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        main_response: "Mock response",
        agent_used: "Vent Validator"
      })
    );
  })
];
```

### Prism (OpenAPI Mock Server)

**Purpose:** Generate mock server from OpenAPI spec

**Usage:**
```bash
prism mock contract/openapi.yaml
```

**Benefits:**
- Automatic mock generation from contract
- Validates against OpenAPI spec
- No manual mock maintenance

---

## Test Data and Fixtures

### Seed Data

**Location:** `tests/fixtures/`

**Files:**
- `sessions.json`: Sample sessions
- `messages.json`: Sample messages
- `memory_graph.json`: Sample memory graph

### Fixtures

```python
@pytest.fixture
def sample_session():
    return ConversationSession(
        session_id="test_session",
        user_id="test_user",
        messages=[],
        created_at=datetime.now()
    )

@pytest.fixture
def mock_graph_memory():
    memory = GraphMemoryService()
    # Add test nodes
    memory.add_memory("test_user", "Test content", "struggle")
    return memory
```

---

## Test Execution

### Local Development

```bash
# Run all tests
pytest tests/ -v

# Run specific test type
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/contract/ -v
pytest tests/e2e/ -v
pytest tests/a11y/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### CI/CD Pipeline

**Steps:**
1. Run unit tests
2. Run integration tests
3. Run contract tests
4. Run E2E tests (if applicable)
5. Run accessibility tests
6. Generate coverage report

**Failure Criteria:**
- Any test failure
- Coverage < 80%
- Accessibility violations

---

## Golden Files

### Purpose

Store expected outputs for visual regression and output comparison.

**Location:** `tests/golden/`

**Examples:**
- Expected API responses
- Expected memory summaries
- Expected error messages

### Usage

```python
def test_memory_summary_format(memory_service):
    """Test memory summary format matches golden file."""
    summary = memory_service.summarize_user_memory("test_user")
    
    golden = load_golden("memory_summary.json")
    assert summary == golden
```

---

## Performance Tests

### Purpose

Ensure system meets performance budgets.

### Test Areas

- **Agent Latency:** < 3s (p95)
- **Memory Retrieval:** < 500ms (p95)
- **API Response:** < 1s (p95)

### Example

```python
def test_agent_latency():
    """Test agent response latency."""
    start = time.time()
    response = agent.process("Test message", session)
    duration = time.time() - start
    
    assert duration < 3.0, f"Latency {duration}s exceeds 3s budget"
```

---

## Test Maintenance

### Best Practices

1. **Keep tests fast:** Unit tests < 100ms each
2. **Keep tests isolated:** No shared state
3. **Use descriptive names:** `test_vent_validator_empathy_response`
4. **Test behavior, not implementation:** Test outputs, not internals
5. **Update tests with code:** Don't let tests get stale

### Test Review Checklist

- [ ] Tests cover happy path
- [ ] Tests cover error cases
- [ ] Tests cover edge cases
- [ ] Tests are fast (< 100ms for unit)
- [ ] Tests are isolated (no dependencies)
- [ ] Tests have clear names
- [ ] Tests have assertions

---

**End of Testing Strategy**


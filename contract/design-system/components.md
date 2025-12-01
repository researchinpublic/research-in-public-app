# Design System Components

**Version:** 1.0.0  
**Last Updated:** 2024-11-19

This document defines the base component library for Research In Public. All components must follow these specifications for consistency and accessibility.

---

## Component Specifications

### Button

**Purpose:** Primary interactive element for user actions.

**Props:**
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `variant` | `"primary" \| "secondary" \| "ghost"` | No | `"primary"` | Visual variant |
| `size` | `"sm" \| "md" \| "lg"` | No | `"md"` | Button size |
| `disabled` | `boolean` | No | `false` | Disabled state |
| `loading` | `boolean` | No | `false` | Loading state |
| `onClick` | `() => void` | Yes | - | Click handler |
| `ariaLabel` | `string` | No | - | ARIA label for screen readers |
| `dataTestId` | `string` | No | - | Test ID for E2E tests |

**Visual Variants:**
- **Primary:** Background `colors.primary[500]`, text white, hover `colors.primary[600]`
- **Secondary:** Background transparent, border `colors.border`, text `colors.text.primary`
- **Ghost:** Background transparent, no border, text `colors.text.primary`

**States:**
- **Default:** Normal appearance
- **Hover:** Slight elevation increase (`elevation[1]`)
- **Active:** Pressed state (slightly darker)
- **Disabled:** Opacity 0.5, cursor not-allowed
- **Loading:** Spinner icon, disabled interaction

**Accessibility:**
- Keyboard accessible (Enter/Space)
- Focus indicator visible (`outline: 2px solid colors.primary[500]`)
- ARIA label required if button text is icon-only
- Disabled state announced to screen readers

**Example:**
```python
# Streamlit
st.button("Submit", key="submit_btn", disabled=False)
```

---

### Input

**Purpose:** Single-line text input.

**Props:**
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `value` | `string` | Yes | - | Input value |
| `onChange` | `(value: string) => void` | Yes | - | Change handler |
| `placeholder` | `string` | No | - | Placeholder text |
| `disabled` | `boolean` | No | `false` | Disabled state |
| `error` | `boolean` | No | `false` | Error state |
| `errorMessage` | `string` | No | - | Error message |
| `ariaLabel` | `string` | Yes | - | ARIA label |
| `dataTestId` | `string` | No | - | Test ID |

**Visual States:**
- **Default:** Border `colors.border`, background `colors.surface.light`
- **Focus:** Border `colors.primary[500]`, outline `2px solid colors.primary[500]`
- **Error:** Border `colors.danger[500]`, error message below
- **Disabled:** Opacity 0.5, cursor not-allowed

**Accessibility:**
- Label associated via `aria-label` or `<label>` element
- Error message announced to screen readers (`aria-describedby`)
- Keyboard navigation (Tab to focus)

**Example:**
```python
# Streamlit
st.text_input("Message", key="message_input", placeholder="Type your message...")
```

---

### TextArea

**Purpose:** Multi-line text input.

**Props:**
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `value` | `string` | Yes | - | Textarea value |
| `onChange` | `(value: string) => void` | Yes | - | Change handler |
| `rows` | `number` | No | `4` | Number of rows |
| `placeholder` | `string` | No | - | Placeholder text |
| `disabled` | `boolean` | No | `false` | Disabled state |
| `error` | `boolean` | No | `false` | Error state |
| `errorMessage` | `string` | No | - | Error message |
| `ariaLabel` | `string` | Yes | - | ARIA label |
| `dataTestId` | `string` | No | - | Test ID |

**Accessibility:** Same as Input component.

---

### Select

**Purpose:** Dropdown selection.

**Props:**
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `value` | `string` | Yes | - | Selected value |
| `onChange` | `(value: string) => void` | Yes | - | Change handler |
| `options` | `Array<{value: string, label: string}>` | Yes | - | Options list |
| `placeholder` | `string` | No | - | Placeholder text |
| `disabled` | `boolean` | No | `false` | Disabled state |
| `ariaLabel` | `string` | Yes | - | ARIA label |
| `dataTestId` | `string` | No | - | Test ID |

**Accessibility:**
- Keyboard navigation (Arrow keys, Enter to select)
- Focus indicator visible
- Selected option announced to screen readers

**Example:**
```python
# Streamlit
st.selectbox("Agent Mode", ["auto", "vent", "pi", "scribe"], key="agent_mode")
```

---

### ChatMessage

**Purpose:** Display user or assistant message in chat interface.

**Props:**
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `role` | `"user" \| "assistant"` | Yes | - | Message role |
| `content` | `string` | Yes | - | Message content |
| `agent` | `string` | No | - | Agent name (for assistant) |
| `timestamp` | `string` | No | - | Timestamp |
| `dataTestId` | `string` | No | - | Test ID |

**Visual Design:**
- **User:** Right-aligned, background `colors.primary[50]`, text `colors.text.primary`
- **Assistant:** Left-aligned, background `colors.surface.lightSecondary`, text `colors.text.primary`
- Agent name shown as caption below assistant messages

**Accessibility:**
- Role announced to screen readers (`role="article"`)
- Agent name announced if present

**Example:**
```python
# Streamlit
with st.chat_message("user"):
    st.markdown(message_content)
```

---

### Card

**Purpose:** Container for content sections.

**Props:**
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `title` | `string` | No | - | Card title |
| `children` | `ReactNode` | Yes | - | Card content |
| `elevation` | `0 \| 1 \| 2 \| 3 \| 4 \| 5` | No | `1` | Elevation level |
| `padding` | `string` | No | `spacing.xl` | Padding |
| `dataTestId` | `string` | No | - | Test ID |

**Visual Design:**
- Background `colors.surface.light`
- Border radius `radii.lg`
- Box shadow from `elevation` token
- Padding from `spacing` scale

---

### Skeleton

**Purpose:** Loading state placeholder.

**Props:**
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `width` | `string` | No | `"100%"` | Width |
| `height` | `string` | No | `"20px"` | Height |
| `variant` | `"text" \| "circular" \| "rectangular"` | No | `"text"` | Variant |

**Visual Design:**
- Background `colors.surface.lightSecondary`
- Animated shimmer effect
- Pulse animation (`motion.duration.normal`)

**Accessibility:**
- `aria-busy="true"` during loading
- `aria-label="Loading..."`

---

### Toast

**Purpose:** Notification/toast messages.

**Props:**
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `message` | `string` | Yes | - | Toast message |
| `variant` | `"success" \| "error" \| "warning" \| "info"` | No | `"info"` | Variant |
| `duration` | `number` | No | `5000` | Auto-dismiss duration (ms) |
| `onDismiss` | `() => void` | No | - | Dismiss handler |

**Visual Design:**
- Background color from `colors[variant][500]`
- Text white
- Position: Top-right corner
- Slide-in animation (`motion.easing.easeOut`)

**Accessibility:**
- `role="alert"` for error toasts
- `role="status"` for info/success toasts
- Auto-dismiss announced to screen readers

**Example:**
```python
# Streamlit
st.success("Graph memory saved!")
st.error("Error saving graph memory")
st.warning("Guardian Alert: MEDIUM risk detected")
```

---

### Expander

**Purpose:** Collapsible content sections.

**Props:**
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `label` | `string` | Yes | - | Expander label |
| `expanded` | `boolean` | No | `false` | Initial expanded state |
| `onToggle` | `(expanded: boolean) => void` | No | - | Toggle handler |
| `children` | `ReactNode` | Yes | - | Content |

**Accessibility:**
- `aria-expanded` attribute
- Keyboard accessible (Enter/Space to toggle)
- Focus indicator visible

**Example:**
```python
# Streamlit
with st.expander("📊 Session Info"):
    st.json(session_data)
```

---

### Spinner

**Purpose:** Loading indicator.

**Props:**
| Prop | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `size` | `"sm" \| "md" \| "lg"` | No | `"md"` | Spinner size |
| `color` | `string` | No | `colors.primary[500]` | Spinner color |

**Visual Design:**
- Circular spinner animation
- Rotate animation (`motion.duration.normal`)

**Accessibility:**
- `aria-busy="true"`
- `aria-label="Loading..."`

**Example:**
```python
# Streamlit
with st.spinner("Processing..."):
    result = process_message()
```

---

## Component Usage Guidelines

### Spacing
- Use spacing scale from tokens (`spacing.xs` to `spacing.5xl`)
- Consistent padding/margins between components

### Colors
- Use semantic color roles (primary, success, danger, warning, info)
- Never use raw color values directly

### Typography
- Use font sizes from `typography.fontSize`
- Use font weights from `typography.fontWeight`
- Line heights from `typography.lineHeight`

### Responsive Design
- Components adapt to breakpoints (`breakpoints.sm`, `md`, `lg`, `xl`)
- Mobile-first approach (stack on mobile, side-by-side on desktop)

### Accessibility Checklist
- [ ] All interactive elements keyboard accessible
- [ ] ARIA labels present for screen readers
- [ ] Focus indicators visible
- [ ] Color contrast meets WCAG AA (4.5:1)
- [ ] Error states announced
- [ ] Loading states announced

---

## Testing Requirements

Each component must have:
1. **Unit Tests:** Props, states, event handlers
2. **Accessibility Tests:** axe-core, keyboard navigation
3. **Visual Regression Tests:** Screenshot comparisons
4. **E2E Tests:** User interaction flows

Test IDs (`dataTestId`) required for E2E test selectors.

---

**End of Component Specifications**


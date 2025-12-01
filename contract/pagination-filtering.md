# Pagination, Filtering, and Sorting

**Version:** 1.0.0  
**Last Updated:** 2025-12-01

This document defines the standard query parameters for pagination, filtering, and sorting across all API endpoints.

---

## Pagination

### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `page` | `integer` | `1` | - | Page number (1-indexed) |
| `per_page` | `integer` | `20` | `100` | Items per page |

### Response Format

All paginated responses include pagination metadata:

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

### Pagination Metadata

| Field | Type | Description |
|-------|------|-------------|
| `page` | `integer` | Current page number |
| `per_page` | `integer` | Items per page |
| `total` | `integer` | Total number of items |
| `total_pages` | `integer` | Total number of pages |
| `has_next` | `boolean` | Whether next page exists |
| `has_prev` | `boolean` | Whether previous page exists |

### Example Request

```
GET /v1/users/demo_user/memory/timeline?page=2&per_page=50
```

### Example Response

```json
{
  "data": [
    {
      "node_id": "node_1",
      "content": "...",
      "node_type": "struggle",
      "timestamp": "2025-12-01T10:00:00Z"
    },
    ...
  ],
  "pagination": {
    "page": 2,
    "per_page": 50,
    "total": 150,
    "total_pages": 3,
    "has_next": true,
    "has_prev": true
  }
}
```

---

## Filtering

### Query Parameter Format

Filters use the format: `filter[field][operator]=value`

**Operators:**
- `eq`: Equal to
- `ne`: Not equal to
- `gt`: Greater than
- `gte`: Greater than or equal to
- `lt`: Less than
- `lte`: Less than or equal to
- `contains`: Contains substring (case-insensitive)
- `in`: Value in array

### Supported Fields

**Memory Nodes:**
- `filter[node_type][eq]=struggle`
- `filter[user_id][eq]=demo_user`
- `filter[created_after][gte]=2025-12-01T00:00:00Z`

**Sessions:**
- `filter[user_id][eq]=demo_user`
- `filter[created_after][gte]=2025-12-01T00:00:00Z`

### Multiple Filters

Multiple filters are combined with AND logic:

```
GET /v1/users/demo_user/memory/timeline?filter[node_type][eq]=struggle&filter[created_after][gte]=2025-12-01T00:00:00Z
```

### Example Request

```
GET /v1/users/demo_user/memory/timeline?filter[node_type][eq]=struggle&filter[created_after][gte]=2025-12-01T00:00:00Z&page=1&per_page=20
```

### Example Response

```json
{
  "data": [
    {
      "node_id": "node_1",
      "content": "I'm struggling with...",
      "node_type": "struggle",
      "timestamp": "2025-12-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 5,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

---

## Sorting

### Query Parameter

**Format:** `sort=field` (ascending) or `sort=-field` (descending)

**Multiple Sorts:** `sort=field1,-field2` (comma-separated)

### Supported Fields

**Memory Nodes:**
- `timestamp` (default)
- `node_type`
- `content` (alphabetical)

**Sessions:**
- `created_at` (default)
- `last_message_at`

### Example Request

```
GET /v1/users/demo_user/memory/timeline?sort=-timestamp&page=1&per_page=20
```

**Response:** Sorted by timestamp descending (newest first)

---

## Combined Example

**Request:**
```
GET /v1/users/demo_user/memory/timeline?filter[node_type][eq]=struggle&filter[created_after][gte]=2025-12-01T00:00:00Z&sort=-timestamp&page=1&per_page=20
```

**Response:**
```json
{
  "data": [
    {
      "node_id": "node_5",
      "content": "Latest struggle...",
      "node_type": "struggle",
      "timestamp": "2025-12-01T15:00:00Z"
    },
    {
      "node_id": "node_3",
      "content": "Earlier struggle...",
      "node_type": "struggle",
      "timestamp": "2025-12-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 2,
    "total_pages": 1,
    "has_next": false,
    "has_prev": false
  }
}
```

---

## Error Handling

### Invalid Parameters

**Invalid page number:**
```json
{
  "type": "https://api.researchinpublic.ai/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Invalid page number. Must be >= 1",
  "code": "VALIDATION_ERROR",
  "errors": [
    {
      "field": "page",
      "message": "Page must be >= 1"
    }
  ]
}
```

**Invalid per_page:**
```json
{
  "type": "https://api.researchinpublic.ai/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Invalid per_page. Maximum is 100",
  "code": "VALIDATION_ERROR",
  "errors": [
    {
      "field": "per_page",
      "message": "per_page must be <= 100"
    }
  ]
}
```

**Invalid filter field:**
```json
{
  "type": "https://api.researchinpublic.ai/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Invalid filter field",
  "code": "VALIDATION_ERROR",
  "errors": [
    {
      "field": "filter[invalid_field]",
      "message": "Field 'invalid_field' is not filterable"
    }
  ]
}
```

---

## Implementation Notes

### Default Behavior

- **No pagination params:** Return first page (20 items)
- **No sort param:** Use default sort (usually `-timestamp` or `-created_at`)
- **No filters:** Return all items (subject to pagination)

### Performance

- **Indexes:** Ensure database indexes on commonly filtered/sorted fields
- **Limit:** Enforce `per_page` maximum (100) to prevent large responses
- **Caching:** Consider caching paginated results for frequently accessed endpoints

---

**End of Pagination, Filtering, and Sorting**


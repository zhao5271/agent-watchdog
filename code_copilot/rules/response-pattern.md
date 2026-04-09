# Response Pattern

Document the repository's stable response and result shapes here.

## Suggested JSON Response Shape

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "requestId": "trace-123"
}
```

## Suggested Pagination Shape

```json
{
  "page": 1,
  "pageSize": 20,
  "total": 200,
  "list": []
}
```

If the repository already has a different stable standard, record that standard instead of forcing this example.

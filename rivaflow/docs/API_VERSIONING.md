# API Versioning Strategy

**Status:** Active
**Current Version:** v1
**Last Updated:** 2026-02-02

---

## Overview

RivaFlow API uses URL-based versioning to provide stable, backwards-compatible interfaces for clients while allowing evolution of the API.

**Current Endpoint Pattern:**
```
https://rivaflow.onrender.com/api/v1/*
```

---

## Versioning Principles

### 1. URL-Based Versioning

**Format:** `/api/v{major}/resource`

**Examples:**
```
/api/v1/sessions
/api/v1/auth/login
/api/v2/sessions  (future)
```

**Why URL-based?**
- ✅ Explicit and visible
- ✅ Easy to route and cache
- ✅ Simple for clients to understand
- ✅ Works with all HTTP clients

### 2. Semantic Versioning (Major Only)

We use **major version numbers only** in URLs:
- `v1`, `v2`, `v3`, etc.

**Major version bump when:**
- Breaking changes to request/response format
- Removing endpoints
- Changing authentication requirements
- Incompatible behavior changes

**NO version bump for:**
- Adding new endpoints
- Adding optional fields to requests
- Adding fields to responses (clients ignore unknown fields)
- Bug fixes
- Performance improvements

### 3. Backwards Compatibility Within Version

**v1 commitments:**
- Existing endpoints won't be removed
- Existing required fields won't change
- Existing response fields won't be removed
- Existing status codes won't change meaning

**We CAN add (without version bump):**
- New optional request fields
- New response fields
- New endpoints
- New query parameters (optional)

---

## Version Lifecycle

### v1 (Current)

**Status:** ✅ Active
**Release:** 2026-01-25
**Support:** Indefinite
**Deprecation:** TBD (at least 12 months notice)

**Endpoints:**
- Authentication (`/api/v1/auth/*`)
- Sessions (`/api/v1/sessions/*`)
- Analytics (`/api/v1/analytics/*`)
- Social (`/api/v1/social/*`)
- Feed (`/api/v1/feed/*`)
- Grapple AI (`/api/v1/grapple/*`)
- See full list: `GET /api/v1/docs`

### v2 (Future)

**Status:** 🔮 Planned
**Triggers for v2:**
- Need to change authentication model
- Major schema redesign
- Breaking changes accumulate

**When to create v2:**
- When breaking changes benefit >50% of users
- When v1 technical debt is unsustainable
- When major new features require redesign

**v2 Planning Process:**
1. Announce v2 development (6 months before release)
2. Publish v2 design document
3. Beta v2 alongside v1
4. Release v2 with migration guide
5. Support v1 for 12+ months

---

## Deprecation Policy

### How We Deprecate

1. **Announce** (12 months before removal)
   - Add to CHANGELOG
   - Add warning headers to deprecated endpoints
   - Email all registered users
   - Update documentation with warnings

2. **Warn** (6 months before removal)
   - Return `Deprecated: true` in response headers
   - Include `sunset` date in headers
   - Add deprecation notices to docs

3. **Sunset** (3 months before removal)
   - Return `410 Gone` for deprecated endpoints
   - Redirect to v2 equivalent if available
   - Final migration reminders

4. **Remove** (after 12 months)
   - Remove deprecated endpoints
   - Update documentation
   - Announce completion

### Example Deprecation Headers

```http
Deprecation: true
Sunset: Sat, 01 Jan 2027 00:00:00 GMT
Link: </api/v2/sessions>; rel="successor-version"
```

---

## Client Migration Guide

### Migrating from v1 to v2 (when available)

**Step 1: Update Base URL**
```python
# Old
BASE_URL = "https://rivaflow.onrender.com/api/v1"

# New
BASE_URL = "https://rivaflow.onrender.com/api/v2"
```

**Step 2: Review Breaking Changes**
- Read v2 migration guide
- Check v2 changelog
- Test with v2 sandbox environment

**Step 3: Run in Parallel**
- Run v1 and v2 clients simultaneously
- Compare responses
- Validate behavior

**Step 4: Switch Over**
- Deploy v2 client
- Monitor for errors
- Keep v1 client as rollback

**Step 5: Cleanup**
- Remove v1 code after successful migration
- Update documentation

---

## Version Negotiation

### Default Version

If no version specified, default to latest stable:
```
/api/sessions  → redirects to /api/v1/sessions
```

### Version in Headers (Optional)

For advanced clients, support version negotiation via headers:
```http
Accept: application/vnd.rivaflow.v1+json
```

**Currently:** Not implemented (use URL versioning)
**Future:** May add header-based versioning for granular control

---

## OpenAPI Specification

Each version has its own OpenAPI spec:

```
/api/v1/openapi.json  → v1 spec
/api/v2/openapi.json  → v2 spec (future)
```

**Swagger UI:**
```
/api/v1/docs  → Interactive v1 docs
/api/v2/docs  → Interactive v2 docs (future)
```

---

## Internal Implementation

### Route Organization

```python
# api/routes/v1/__init__.py
from fastapi import APIRouter

router_v1 = APIRouter(prefix="/v1")

# Add all v1 routes
router_v1.include_router(auth.router, prefix="/auth", tags=["auth"])
router_v1.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
...

# api/main.py
app.include_router(router_v1, prefix="/api")
```

### Shared Business Logic

**Services are version-agnostic:**
```python
# core/services/session_service.py
class SessionService:
    def create_session(...):  # Used by both v1 and v2
        ...
```

**API layers differ:**
```python
# api/routes/v1/sessions.py
@router.post("/")
async def create_session_v1(req: SessionCreateV1):
    # v1-specific validation/transformation
    service.create_session(...)

# api/routes/v2/sessions.py
@router.post("/")
async def create_session_v2(req: SessionCreateV2):
    # v2-specific validation/transformation
    service.create_session(...)
```

---

## Testing Strategy

### Version-Specific Tests

```python
# tests/api/v1/test_sessions.py
def test_v1_create_session():
    response = client.post("/api/v1/sessions", json={...})
    assert response.status_code == 201

# tests/api/v2/test_sessions.py (future)
def test_v2_create_session():
    response = client.post("/api/v2/sessions", json={...})
    assert response.status_code == 201
```

### Cross-Version Compatibility

```python
def test_v1_and_v2_compatible():
    v1_session = create_via_v1()
    v2_session = get_via_v2(v1_session.id)
    assert v1_session.data == v2_session.data  # Same underlying data
```

---

## FAQ

### Q: Do I need to version private/internal APIs?

**A:** No. Only public-facing APIs (`/api/v1/*`) are versioned. Internal services don't need versioning.

### Q: Can I deploy a breaking change without bumping version?

**A:** No. Breaking changes MUST bump major version. Add new endpoint instead.

### Q: How do I add a new field to response?

**A:** Just add it. Clients ignore unknown fields. No version bump needed.

### Q: Can I remove a field from response?

**A:** No. This is a breaking change. Requires new version.

### Q: Can I change a field from optional to required?

**A:** No. This is a breaking change. Requires new version.

### Q: Can I change a field from required to optional?

**A:** Yes. This is backwards compatible (old clients still send it).

### Q: When should I create v2?

**A:** When you have enough breaking changes to justify it. Aim for <1 major version per year.

---

## Summary

✅ **Current:** v1 (stable, supported indefinitely)
📅 **Future:** v2 (TBD, not needed yet)
⏰ **Deprecation:** 12 months notice minimum
🔄 **Migration:** Parallel running, gradual cutover
📚 **Docs:** Auto-generated OpenAPI specs per version

**Key Principle:** Stability over perfection. Don't break clients.

---

**Next Review:** Before v2 planning (or annually)

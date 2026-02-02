# File Upload Security

**Last Updated:** 2026-02-02

---

## Overview

RivaFlow allows users to upload activity photos. This document details the security measures in place to prevent malicious file uploads.

---

## Security Measures

### 1. File Extension Whitelist

**Implementation:** `api/routes/photos.py:19`

Only specific image extensions are allowed:
- `.jpg` / `.jpeg`
- `.png`
- `.webp`
- `.gif`

Any other file extensions are rejected.

### 2. File Size Limit

**Implementation:** `api/routes/photos.py:20`

Maximum file size: **5 MB**

Prevents:
- Denial of Service (DoS) attacks via large files
- Storage exhaustion
- Bandwidth abuse

### 3. Magic Byte Validation

**Implementation:** `api/routes/photos.py:validate_image_content()`

Uses Python's `imghdr` library to verify file content matches claimed type.

**Protection:**
- Detects files disguised as images (e.g., `.exe` renamed to `.jpg`)
- Verifies extension matches actual content
- Prevents executable uploads

**Example:**
```python
# Rejected: malware.exe renamed to photo.jpg
# Magic bytes: 4D 5A (executable) != FF D8 FF (JPEG)
```

### 4. MIME Type Validation

**Implementation:** `api/routes/photos.py:21-26`

Validates HTTP `Content-Type` header against whitelist:
- `image/jpeg`
- `image/png`
- `image/webp`
- `image/gif`

### 5. Authentication Required

**Implementation:** All upload endpoints use `Depends(get_current_user)`

Only authenticated users can upload files.

### 6. User Isolation

**Implementation:** Database queries scoped by `user_id`

Users can only:
- Upload to their own activities
- View their own photos
- Delete their own photos

Cross-user access is prevented.

### 7. Upload Limit per Activity

**Implementation:** `api/routes/photos.py:44-49`

Maximum **3 photos per activity** (session/readiness/rest).

Prevents:
- Storage abuse
- Spam uploads

### 8. Unique Filename Generation

**Implementation:** `api/routes/photos.py:96-98`

Filename format:
```
{activity_type}_{user_id}_{timestamp}_{full_uuid4}{extension}
```

Example: `session_123_20260202_143022_a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg`

**Security benefits:**
- UUID4 prevents filename collisions
- Timestamp adds uniqueness
- User ID prevents cross-user overwrites
- Original filename is NOT used (prevents path traversal)

### 9. Path Traversal Prevention

**Implementation:** `api/routes/photos.py:101-103`

```python
if not file_path.resolve().is_relative_to(UPLOAD_DIR.resolve()):
    raise HTTPException(status_code=400, detail="Invalid filename")
```

Prevents directory traversal attacks like:
- `../../../etc/passwd`
- `..\..\..\windows\system32\config\sam`

### 10. Secure File Permissions

**Implementation:** System-level (upload directory permissions)

Upload directory: `uploads/activities/`
- Created with appropriate permissions
- Not executable
- Web server cannot list directory contents

---

## Threats Mitigated

### ✅ Malware Upload
- **Attack:** Upload malicious executable disguised as image
- **Mitigation:** Magic byte validation detects mismatched content

### ✅ Path Traversal
- **Attack:** Upload file to arbitrary location (`../../../sensitive/file`)
- **Mitigation:** Path validation ensures file stays in upload directory

### ✅ Denial of Service
- **Attack:** Upload massive files to exhaust storage
- **Mitigation:** 5MB size limit + 3 photos per activity

### ✅ Cross-Site Scripting (XSS)
- **Attack:** Upload SVG with embedded JavaScript
- **Mitigation:** SVG not in allowed formats (only raster images)

### ✅ Server-Side Request Forgery (SSRF)
- **Attack:** Upload file with URL to trigger server-side request
- **Mitigation:** No server-side processing of file content beyond validation

### ✅ Storage Exhaustion
- **Attack:** Create many accounts and upload maximum photos
- **Mitigation:** File size limit + photo count limit + authentication

### ✅ Directory Listing
- **Attack:** Browse uploaded files of other users
- **Mitigation:** User ID scoping + no directory listing enabled

---

## Remaining Risks (Accepted)

### ⚠️ Image-Based Steganography
**Risk:** Users could hide data within image files (steganography)
**Likelihood:** Low
**Impact:** Low (hidden data has no execution context)
**Mitigation:** Not implemented (low priority)

### ⚠️ Image Bomb (Decompression DoS)
**Risk:** Upload crafted image that decompresses to huge size
**Likelihood:** Low (5MB compressed limit helps)
**Impact:** Medium (could consume memory during processing)
**Mitigation:** Not implemented (low priority)
**Recommendation:** Add image dimension limits if this becomes an issue

### ⚠️ Metadata Injection
**Risk:** EXIF/metadata contains malicious content
**Likelihood:** Low
**Impact:** Low (metadata not displayed)
**Mitigation:** Not implemented
**Recommendation:** Strip EXIF data if privacy becomes a concern

---

## Future Enhancements

### 1. Image Dimension Limits
Prevent extremely large images (e.g., 10000x10000 pixels)

```python
MAX_IMAGE_WIDTH = 4096
MAX_IMAGE_HEIGHT = 4096
```

### 2. EXIF Stripping
Remove all metadata for privacy:
- GPS coordinates
- Camera model
- Software used
- Timestamps

### 3. Virus Scanning
Integrate with ClamAV or similar for malware detection.

### 4. Image Optimization
- Automatically resize large images
- Convert to WebP for better compression
- Generate thumbnails

### 5. Content Moderation
- AI-based inappropriate content detection
- Hash-based duplicate detection
- Watermarking

---

## Testing

### Manual Tests

**Test 1: Malicious File Upload**
```bash
# Rename executable to .jpg
mv malware.exe test.jpg

# Upload via API
curl -X POST /api/v1/photos/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.jpg" \
  -F "activity_type=session" \
  -F "activity_id=1"

# Expected: 400 Bad Request - "File content does not match image format"
```

**Test 2: Oversized File**
```bash
# Create 10MB file
dd if=/dev/zero of=large.jpg bs=1M count=10

# Upload
curl -X POST /api/v1/photos/upload \
  -F "file=@large.jpg" \
  ...

# Expected: 400 Bad Request - "File too large"
```

**Test 3: Path Traversal**
```bash
# Attempt directory traversal (would fail during validation)
# The filename is auto-generated, so this attack is not possible
# through the API
```

**Test 4: Extension Mismatch**
```bash
# Rename PNG to .jpg
mv image.png test.jpg

# Upload
curl -X POST /api/v1/photos/upload \
  -F "file=@test.jpg" \
  ...

# Expected: 400 Bad Request - "File extension mismatch"
```

---

## Audit Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-02-02 | Added magic byte validation | Prevent malicious file disguise |
| 2026-02-02 | Added MIME type validation | Defense in depth |
| 2026-02-02 | Added path traversal check | Prevent directory escape |
| 2026-02-02 | Use full UUID4 (not truncated) | Prevent collisions |

---

## References

- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [CWE-434: Unrestricted Upload of File with Dangerous Type](https://cwe.mitre.org/data/definitions/434.html)
- [CWE-22: Path Traversal](https://cwe.mitre.org/data/definitions/22.html)

---

**Last reviewed:** 2026-02-02
**Next review:** 2026-05-02 (quarterly)

# Error Messages Guide

**Purpose:** Document user-facing error messages and actionable guidance.

---

## Validation Errors (400 Bad Request)

### Session Creation

#### Future Date Error
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed. Please check your input.",
    "status": 422,
    "details": {
      "errors": [
        {
          "field": "session_date",
          "message": "Session date cannot be in the future. You provided 2026-02-05, but today is 2026-02-02. Please use today's date or an earlier date.",
          "type": "value_error"
        }
      ]
    }
  }
}
```

**User Action:** Use today's date or a past date when logging sessions.

---

#### Empty Gym Name
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed. Please check your input.",
    "details": {
      "errors": [
        {
          "field": "gym_name",
          "message": "Gym name cannot be empty. Please provide the name of your training academy or gym.",
          "type": "value_error"
        }
      ]
    }
  }
}
```

**User Action:** Provide a gym name (e.g., "Gracie Barra Sydney").

---

#### Invalid Intensity
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed. Please check your input.",
    "details": {
      "errors": [
        {
          "field": "intensity",
          "message": "Input should be greater than or equal to 1",
          "type": "greater_than_equal"
        }
      ]
    }
  }
}
```

**Field Description:** Training intensity (1=light, 5=competition pace). Scale of 1-5.

**User Action:** Provide intensity between 1 and 5.

---

#### Invalid Duration
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed. Please check your input.",
    "details": {
      "errors": [
        {
          "field": "duration_mins",
          "message": "Input should be less than or equal to 480",
          "type": "less_than_equal"
        }
      ]
    }
  }
}
```

**Field Description:** Session duration in minutes (1-480). Typical: 60-120 minutes.

**User Action:** Provide duration between 1 and 480 minutes (8 hours max).

---

#### Invalid Class Time Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed. Please check your input.",
    "details": {
      "errors": [
        {
          "field": "class_time",
          "message": "String should match pattern '^([01]\\d|2[0-3]):([0-5]\\d)$'",
          "type": "string_pattern_mismatch"
        }
      ]
    }
  }
}
```

**Field Description:** Start time in 24-hour format (HH:MM). Example: 18:30

**User Action:** Use 24-hour format like "18:30" (not "6:30 PM").

---

### Authentication Errors

#### Invalid Email Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "status": 400,
    "details": {
      "suggested_action": "Please provide a valid email address (e.g., user@example.com)"
    }
  }
}
```

**User Action:** Provide a valid email address with @ sign and domain.

---

#### Disposable Email Blocked
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Disposable email addresses are not allowed. Please use a permanent email address.",
    "status": 400,
    "details": {
      "suggested_action": "Use your personal or work email address instead of temporary email services"
    }
  }
}
```

**Blocked Domains:** 10minutemail.com, guerrillamail.com, tempmail.com, etc.

**User Action:** Use a permanent email address (Gmail, Outlook, work email, etc.).

---

#### Weak Password
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Password must be at least 8 characters long",
    "status": 400,
    "details": {
      "suggested_action": "Choose a password with at least 8 characters. Consider using a mix of letters, numbers, and symbols for better security."
    }
  }
}
```

**User Action:** Create a password with minimum 8 characters.

---

#### Email Already Registered
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email already registered",
    "status": 400,
    "details": {
      "suggested_action": "If you already have an account, please login instead. If you forgot your password, use the 'Forgot Password' link."
    }
  }
}
```

**User Action:** Login with existing account or reset password.

---

## Authentication Errors (401 Unauthorized)

#### Invalid Credentials
```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid email or password",
    "status": 401,
    "details": {
      "suggested_action": "Double-check your email and password. If you forgot your password, click 'Forgot Password' to reset it."
    }
  }
}
```

**User Action:** Verify credentials or reset password.

---

#### Token Expired
```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Token has expired",
    "status": 401,
    "details": {
      "suggested_action": "Your session has expired (tokens last 30 minutes). Please login again."
    }
  }
}
```

**User Action:** Login again to get a new token.

---

## Authorization Errors (403 Forbidden)

#### Access Denied
```json
{
  "error": {
    "code": "AUTHORIZATION_ERROR",
    "message": "You do not have permission to perform this action",
    "status": 403,
    "details": {
      "suggested_action": "You can only access your own data. Make sure you're logged in with the correct account."
    }
  }
}
```

**User Action:** Ensure you're accessing your own resources.

---

## Not Found Errors (404)

#### Session Not Found
```json
{
  "error": {
    "code": "NOT_FOUND_ERROR",
    "message": "Session 123 not found or access denied",
    "status": 404,
    "details": {
      "suggested_action": "This session may have been deleted or doesn't exist. Check your session list to see available sessions."
    }
  }
}
```

**User Action:** Verify session ID or check if it was deleted.

---

## File Upload Errors (400)

#### File Too Large
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "File too large. Maximum size: 5MB",
    "status": 400,
    "details": {
      "suggested_action": "Compress your image or choose a smaller file. Recommended: resize to 1920x1080 or lower before uploading."
    }
  }
}
```

**User Action:** Resize or compress image before uploading.

---

#### Invalid File Type
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "File is not a valid image. File content does not match image format.",
    "status": 400,
    "details": {
      "suggested_action": "Only upload actual image files (JPEG, PNG, WebP, or GIF). Renamed executables or other file types are not allowed."
    }
  }
}
```

**User Action:** Upload only genuine image files.

---

#### Too Many Photos
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Maximum 3 photos per activity",
    "status": 400,
    "details": {
      "suggested_action": "You've reached the photo limit for this session. Delete an existing photo if you want to upload a new one."
    }
  }
}
```

**User Action:** Delete old photo or create new session.

---

## Rate Limit Errors (429)

#### Too Many Requests
```json
{
  "error": {
    "code": "RATE_LIMIT_ERROR",
    "message": "Rate limit exceeded. Try again in 42 seconds.",
    "status": 429,
    "details": {
      "suggested_action": "Please wait before making another request. Rate limits protect the service for all users."
    }
  }
}
```

**User Action:** Wait for the specified time before retrying.

---

#### Too Many Login Attempts
```json
{
  "error": {
    "code": "RATE_LIMIT_ERROR",
    "message": "Too many login attempts. Please try again later.",
    "status": 429,
    "details": {
      "retry_after": 300,
      "suggested_action": "Wait 5 minutes before trying to login again. If you're having trouble, use 'Forgot Password' to reset your credentials."
    }
  }
}
```

**User Action:** Wait or use password reset.

---

## Server Errors (500)

### Development Mode

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "DatabaseError: Connection timeout",
    "status": 500,
    "details": {
      "type": "DatabaseError",
      "hint": "This detailed error is only shown in development mode"
    }
  }
}
```

### Production Mode

```json
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "An unexpected error occurred. Please try again later.",
    "status": 500,
    "details": {
      "suggested_action": "If this persists, please contact support@rivaflow.com with the request ID.",
      "request_id": "abc123-def456"
    }
  }
}
```

**User Action:** Retry or contact support with request ID.

---

## Best Practices for Error Handling

### For Users

1. **Read the error message carefully** - It tells you what went wrong
2. **Check the suggested_action field** - It tells you what to do next
3. **Look at field-specific errors** - Each field error has context
4. **Verify your input** - Double-check dates, formats, and values
5. **Contact support if stuck** - Include request_id if provided

### For Developers

1. **Always include suggested_action** - Guide users to resolution
2. **Be specific** - "Password too short" not "Invalid input"
3. **Show examples** - "Use format: HH:MM (e.g., 18:30)"
4. **Avoid jargon** - "Email already exists" not "Unique constraint violation"
5. **Provide context** - "You provided 2026-02-05, but today is 2026-02-02"
6. **Never expose** - Passwords, tokens, internal paths in errors
7. **Log everything** - Full stack traces server-side, generic message to user

---

## Error Response Format

All errors follow this structure:

```json
{
  "error": {
    "code": "ERROR_TYPE",
    "message": "Human-readable error message",
    "status": 400,
    "details": {
      "errors": [...],  // Field-level errors (validation only)
      "suggested_action": "What to do next",
      "request_id": "abc123"  // For support
    }
  }
}
```

---

**Last Updated:** 2026-02-02

# RivaFlow API Reference

**Version:** v1
**Base URL:** `https://rivaflow.onrender.com/api/v1`
**Authentication:** Bearer Token (JWT)

---

## Table of Contents

- [Authentication](#authentication)
- [Sessions](#sessions)
- [Readiness](#readiness)
- [Rest Days](#rest-days)
- [Analytics](#analytics)
- [Profile](#profile)
- [Social](#social)
- [Feed](#feed)
- [Goals](#goals)
- [Grapple AI](#grapple-ai)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## Authentication

### Register

Create a new user account.

**Endpoint:** `POST /auth/register`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:** `201 Created`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "user_id": 123,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

**Validation:**
- Email must be valid format
- Password minimum 8 characters
- Names required, non-empty

**Rate Limit:** 5 requests/minute

---

### Login

Authenticate existing user.

**Endpoint:** `POST /auth/login`

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Errors:**
- `401 Unauthorized` - Invalid credentials
- `400 Bad Request` - Missing fields

**Rate Limit:** 5 requests/minute

---

### Refresh Token

Get new access token using refresh token.

**Endpoint:** `POST /auth/refresh`

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Token Lifetimes:**
- Access Token: 30 minutes
- Refresh Token: 7 days

---

### Forgot Password

Request password reset email.

**Endpoint:** `POST /auth/forgot-password`

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password reset email sent if account exists"
}
```

**Note:** Always returns 200 (don't leak user existence)

**Rate Limit:** 3 requests/hour

---

### Reset Password

Reset password with token.

**Endpoint:** `POST /auth/reset-password`

**Request:**
```json
{
  "token": "reset_token_from_email",
  "new_password": "NewSecurePassword456!"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password reset successful"
}
```

---

## Sessions

### Create Session

Log a training session.

**Endpoint:** `POST /sessions`
**Auth Required:** Yes

**Request:**
```json
{
  "session_date": "2026-02-01",
  "class_type": "gi",
  "gym_name": "Gracie Barra Sydney",
  "location": "Sydney, NSW",
  "duration_mins": 90,
  "intensity": 4,
  "rolls": 5,
  "submissions_for": 2,
  "submissions_against": 1,
  "partners": ["John Doe", "Jane Smith"],
  "techniques": ["armbar", "triangle", "guard pass"],
  "notes": "Great session, worked on closed guard",
  "visibility_level": "full"
}
```

**Required Fields:**
- `session_date` (date, not in future)
- `class_type` (enum: gi, no-gi, open-mat, drilling, private, competition)
- `gym_name` (string, non-empty)
- `duration_mins` (integer, > 0)
- `intensity` (integer, 1-5)

**Optional Fields:**
- `location` (string)
- `rolls` (integer, >= 0)
- `submissions_for` (integer, >= 0)
- `submissions_against` (integer, >= 0)
- `partners` (array of strings)
- `techniques` (array of strings)
- `notes` (string, max 5000 chars)
- `visibility_level` (enum: private, attendance, summary, full)

**Response:** `201 Created`
```json
{
  "session_id": 456,
  "user_id": 123,
  "session_date": "2026-02-01",
  "class_type": "gi",
  "gym_name": "Gracie Barra Sydney",
  "duration_mins": 90,
  "intensity": 4,
  "rolls": 5,
  "created_at": "2026-02-01T14:30:00Z"
}
```

---

### List Sessions

Get all sessions for authenticated user.

**Endpoint:** `GET /sessions`
**Auth Required:** Yes

**Query Parameters:**
- `limit` (integer, default: 50, max: 100)
- `offset` (integer, default: 0)
- `start_date` (date, optional)
- `end_date` (date, optional)

**Response:** `200 OK`
```json
[
  {
    "session_id": 456,
    "session_date": "2026-02-01",
    "class_type": "gi",
    "gym_name": "Gracie Barra Sydney",
    "duration_mins": 90,
    "intensity": 4,
    "rolls": 5
  },
  ...
]
```

---

### Get Session

Get specific session by ID.

**Endpoint:** `GET /sessions/{session_id}`
**Auth Required:** Yes

**Response:** `200 OK`
```json
{
  "session_id": 456,
  "user_id": 123,
  "session_date": "2026-02-01",
  "class_type": "gi",
  "gym_name": "Gracie Barra Sydney",
  "location": "Sydney, NSW",
  "duration_mins": 90,
  "intensity": 4,
  "rolls": 5,
  "submissions_for": 2,
  "submissions_against": 1,
  "partners": ["John Doe", "Jane Smith"],
  "techniques": ["armbar", "triangle"],
  "notes": "Great session",
  "visibility_level": "full",
  "created_at": "2026-02-01T14:30:00Z"
}
```

**Errors:**
- `404 Not Found` - Session doesn't exist or belongs to another user

---

### Update Session

Update existing session.

**Endpoint:** `PUT /sessions/{session_id}`
**Auth Required:** Yes

**Request:** (all fields optional)
```json
{
  "duration_mins": 120,
  "intensity": 5,
  "notes": "Updated notes"
}
```

**Response:** `200 OK`
```json
{
  "session_id": 456,
  "duration_mins": 120,
  "intensity": 5,
  "notes": "Updated notes",
  ...
}
```

---

### Delete Session

Delete a session.

**Endpoint:** `DELETE /sessions/{session_id}`
**Auth Required:** Yes

**Response:** `200 OK`
```json
{
  "message": "Session deleted successfully"
}
```

---

## Readiness

### Log Readiness

Log daily readiness check-in.

**Endpoint:** `POST /readiness`
**Auth Required:** Yes

**Request:**
```json
{
  "check_date": "2026-02-01",
  "energy": 4,
  "soreness": 3,
  "stress": 2,
  "sleep_hours": 7.5,
  "mood": 4,
  "notes": "Feeling good today",
  "training_planned": true
}
```

**Required Fields:**
- `energy` (integer, 1-5)
- `soreness` (integer, 1-5)
- `stress` (integer, 1-5)
- `sleep_hours` (float, 0-24)
- `mood` (integer, 1-5)

**Response:** `201 Created`
```json
{
  "readiness_id": 789,
  "check_date": "2026-02-01",
  "readiness_score": 78,
  "energy": 4,
  "soreness": 3,
  "stress": 2,
  "sleep_hours": 7.5,
  "mood": 4,
  "created_at": "2026-02-01T08:00:00Z"
}
```

**Readiness Score Calculation:**
- Weighted average of inputs
- Range: 1-100
- Higher = better prepared for training

---

### Get Readiness History

**Endpoint:** `GET /readiness`
**Auth Required:** Yes

**Query Parameters:**
- `limit` (integer, default: 30)
- `start_date` (date, optional)
- `end_date` (date, optional)

**Response:** `200 OK`
```json
[
  {
    "readiness_id": 789,
    "check_date": "2026-02-01",
    "readiness_score": 78,
    "energy": 4,
    "soreness": 3
  },
  ...
]
```

---

## Analytics

### Weekly Summary

**Endpoint:** `GET /analytics/weekly`
**Auth Required:** Yes

**Response:** `200 OK`
```json
{
  "period": "week",
  "start_date": "2026-01-26",
  "end_date": "2026-02-01",
  "sessions_count": 4,
  "total_hours": 6.0,
  "total_rolls": 18,
  "avg_intensity": 4.2,
  "class_breakdown": {
    "gi": 3,
    "no-gi": 1
  },
  "top_gyms": [
    {"gym_name": "Gracie Barra Sydney", "count": 4}
  ]
}
```

---

### Monthly Summary

**Endpoint:** `GET /analytics/monthly`
**Auth Required:** Yes

---

### Readiness Trends

**Endpoint:** `GET /analytics/readiness`
**Auth Required:** Yes

**Query Parameters:**
- `period` (enum: week, month, year, all)

**Response:** `200 OK`
```json
{
  "avg_readiness": 76.5,
  "avg_energy": 4.1,
  "avg_soreness": 3.2,
  "avg_stress": 2.8,
  "avg_sleep": 7.4,
  "avg_mood": 4.0,
  "trend": "improving"
}
```

---

## Profile

### Get Profile

**Endpoint:** `GET /profile/me`
**Auth Required:** Yes

**Response:** `200 OK`
```json
{
  "user_id": 123,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "current_belt": "blue",
  "current_stripe": 2,
  "default_visibility": "full",
  "gym_name": "Gracie Barra Sydney",
  "location": "Sydney, NSW"
}
```

---

### Update Profile

**Endpoint:** `PUT /profile/me`
**Auth Required:** Yes

**Request:** (all optional)
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "current_belt": "blue",
  "current_stripe": 3,
  "default_visibility": "summary",
  "gym_name": "New Gym",
  "location": "New Location"
}
```

---

## Social

### Add Friend

**Endpoint:** `POST /social/friends`
**Auth Required:** Yes

**Request:**
```json
{
  "friend_username": "johndoe"
}
```

**Response:** `201 Created`

---

### List Friends

**Endpoint:** `GET /social/friends`
**Auth Required:** Yes

**Response:** `200 OK`
```json
[
  {
    "user_id": 456,
    "username": "johndoe",
    "first_name": "John",
    "status": "accepted"
  }
]
```

---

## Feed

### Get Feed

**Endpoint:** `GET /feed`
**Auth Required:** Yes

**Query Parameters:**
- `limit` (integer, default: 20)
- `offset` (integer, default: 0)

**Response:** `200 OK`
```json
[
  {
    "activity_id": 999,
    "user_id": 456,
    "username": "johndoe",
    "activity_type": "session",
    "created_at": "2026-02-01T14:00:00Z",
    "content": {
      "gym_name": "Gracie Barra Sydney",
      "duration_mins": 90,
      "intensity": 4
    },
    "likes_count": 5,
    "comments_count": 2
  }
]
```

---

## Error Handling

### Standard Error Response

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "INVALID_INPUT",
  "field": "email"  // Optional, if field-specific
}
```

### HTTP Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required or failed
- `403 Forbidden` - Access denied
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

## Rate Limiting

**Limits:**
- Authentication endpoints: 5 requests/minute
- Password reset: 3 requests/hour
- General API: 100 requests/minute (per user)

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1643723400
```

**Exceeded Response:** `429 Too Many Requests`
```json
{
  "detail": "Rate limit exceeded. Try again in 42 seconds."
}
```

---

## Interactive Documentation

**Swagger UI:** `https://rivaflow.onrender.com/api/v1/docs`
**OpenAPI Spec:** `https://rivaflow.onrender.com/api/v1/openapi.json`

Try endpoints directly in your browser with the interactive documentation.

---

**Questions?** support@rivaflow.com

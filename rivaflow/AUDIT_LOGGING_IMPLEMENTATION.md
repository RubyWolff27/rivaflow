# Audit Logging System Implementation

## Overview
Comprehensive audit logging system for tracking all admin actions in RivaFlow.

## Files Created

### 1. Audit Service
**Location:** `/Users/rubertwolff/scratch/rivaflow/core/services/audit_service.py`

**Methods:**
- `log()` - Log an admin action with details
- `get_logs()` - Retrieve audit logs with filters
- `get_total_count()` - Get count of matching logs
- `get_user_activity_summary()` - Get activity summary for a user

**Features:**
- Automatic JSON serialization of details
- IP address tracking
- Comprehensive filtering (by actor, action, target type/id)
- Pagination support
- Error-resilient (failures don't break operations)

### 2. Database Migration
**Location:** `/Users/rubertwolff/scratch/rivaflow/db/migrations/039_create_audit_logs.sql`

**Schema:**
```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_user_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT,
    target_id INTEGER,
    details TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

**Indexes:**
- `idx_audit_logs_actor` on `actor_user_id`
- `idx_audit_logs_action` on `action`
- `idx_audit_logs_created` on `created_at`
- `idx_audit_logs_target` on `(target_type, target_id)`

## Actions Logged

### User Management
- `user.update` - When is_active or is_admin is changed
  - Details: `{changes: {is_active: bool, is_admin: bool}, email: string}`
- `user.delete` - When a user is deleted
  - Details: `{email: string}`

### Gym Management
- `gym.create` - When a new gym is created
  - Details: `{name: string, verified: bool}`
- `gym.update` - When gym details are updated
  - Details: `{changes: {field: value}, name: string}`
- `gym.delete` - When a gym is deleted
  - Details: `{name: string}`
- `gym.merge` - When gyms are merged
  - Details: `{source_gym_id: int, source_gym_name: string, target_gym_name: string}`

### Content Moderation
- `comment.delete` - When a comment is deleted
  - Details: `{}`
- `technique.delete` - When a technique is deleted
  - Details: `{name: string}`

## Admin Endpoints Updated

All admin endpoints in `/Users/rubertwolff/scratch/rivaflow/api/routes/admin.py` have been updated:

1. **Gym Operations:**
   - `POST /admin/gyms` - Create gym
   - `PUT /admin/gyms/{gym_id}` - Update gym
   - `DELETE /admin/gyms/{gym_id}` - Delete gym
   - `POST /admin/gyms/merge` - Merge gyms

2. **User Management:**
   - `PUT /admin/users/{user_id}` - Update user
   - `DELETE /admin/users/{user_id}` - Delete user

3. **Content Moderation:**
   - `DELETE /admin/comments/{comment_id}` - Delete comment
   - `DELETE /admin/techniques/{technique_id}` - Delete technique

4. **New Endpoint:**
   - `GET /admin/audit-logs` - Retrieve audit logs
     - Query params: `limit`, `offset`, `actor_id`, `action`, `target_type`, `target_id`

## IP Address Tracking

Added helper function `get_client_ip(request)` that:
- Checks `X-Forwarded-For` header for reverse proxy scenarios
- Falls back to direct client IP
- Returns "unknown" if IP cannot be determined

## Integration Notes

- All audit logging calls are non-blocking
- Logging failures are logged but don't interrupt operations
- Details are stored as JSON for flexible querying
- Rate limiting already in place on all admin endpoints
- Migration added to database migrations list

## Database Updates

Updated `/Users/rubertwolff/scratch/rivaflow/db/database.py`:
- Added migration `039_create_audit_logs.sql` to migrations list
- Added `audit_logs` to PostgreSQL sequence reset list

## Next Steps

1. **Run migration:**
   ```bash
   python -m rivaflow.db.database
   ```

2. **Optional enhancements:**
   - Add audit log viewer in admin UI
   - Create audit log export functionality
   - Add retention policy for old logs
   - Add alerting for suspicious patterns

## Testing Recommendations

Test each admin action to verify audit logs are created:
```python
# Example: Check user update logging
response = client.put("/admin/users/1", json={"is_admin": true})
logs = client.get("/admin/audit-logs?action=user.update").json()
assert len(logs["logs"]) > 0
assert logs["logs"][0]["action"] == "user.update"
```

## Security Notes

- Audit logs use CASCADE DELETE with users (cleanup when actor is deleted)
- IP addresses stored for security investigations
- All endpoints require admin access
- Rate limiting prevents abuse

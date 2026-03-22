# `Sessions/` — Runtime Session State

Stores the currently logged-in user's session data.

## Files

| File | Purpose |
|------|---------|
| `session.json` | Written on successful login by `LoginPage.session_creation()`. Read by `MainApp.fetch_session()` and form classes to get the active user's ID, name, and role. |

## Schema

```json
{
    "user": {
        "id": "uuid-string",
        "created_at": "ISO-8601",
        "user_email": "user@example.com",
        "user_password": "$2b$12$...",     // ⚠️ bcrypt hash stored here
        "user_name": "Display Name",
        "user_role": "admin|Regular"
    }
}
```

## Security Note

> ⚠️ The `user_password` field contains the bcrypt hash. While bcrypt is a one-way hash and not reversible, persisting it in an unencrypted JSON file on disk is a security concern. The file is not access-controlled beyond OS-level file permissions.

## Lifecycle

1. **Created/Updated:** `LoginPage.login()` → `session_creation(user_data)` → writes JSON
2. **Read:** `MainApp.fetch_session()` → `HomePage.set_user()` and form `submit_form()` methods
3. **No explicit logout cleanup:** The `logout()` method in `HomePage` navigates back to `LoginPage` but does **not** delete `session.json`. The old session data persists on disk.

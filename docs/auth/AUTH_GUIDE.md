# Authentication Guide - Grammar-LLM-Bridge

## Quick Start for Testers

### 1. Register
```bash
curl -X POST http://your-server:9020/auth/register \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "your_username",
    "email": "you@example.com",
    "password": "your_password"
  }'
```

### 2. Login
```bash
curl -X POST http://your-server:9020/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

Response:
```json
{
  "api_key": "6818a197cb440317...",
  "user": {...},
  "message": "Login successful. Use the api_key in X-API-Key header..."
}
```

**Save your API key!** It's shown only once.

### 3. Use API
```bash
# With authentication (tracked, rate limited per user)
curl -X POST http://your-server:9020/v2/check \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: YOUR_API_KEY_HERE' \
  -d '{"text": "Your text here", "language": "en-GB"}'
```

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ X-API-Key: xxx (optional)
       ▼
┌─────────────────────────┐
│  API Key Middleware     │ ← Validates key, sets user
└──────┬──────────────────┘
       │ request.state.user = User (or None)
       ▼
┌─────────────────────────┐
│   Endpoint Handler      │
│  - Public: anyone       │
│  - Protected: needs key │
└─────────────────────────┘
```

## Current Implementation

### Backward Compatible
- **Without API key**: Works (anonymous access)
- **With invalid key**: 401 Unauthorized
- **With valid key**: Authenticated + tracked

### Temporary Solution
This is a **minimal viable auth system** for closed beta testing.

**Login endpoint** (`/auth/login`):
- Takes username + password
- Returns session API key (expires in 30 days)
- Simple, works now

**Future extensibility** (no breaking changes needed):
- JWT tokens → just another way to get/verify API key
- OAuth2 → external provider creates user + API key
- SSO → redirect creates user + API key
- 2FA → add extra validation before issuing key

The API key is the **stable interface** - any auth method can generate one.

## Endpoints

### Public (no auth required)
- `GET /v2/languages` - List supported languages
- `GET /v2/info` - Server info
- `POST /v2/check` - Grammar check (works with/without auth)
- `POST /auth/register` - Create account
- `POST /auth/login` - Get API key

### Protected (requires X-API-Key header)
- `POST /auth/api-keys` - Create permanent API key
- `GET /auth/api-keys` - List your keys
- `DELETE /auth/api-keys/{id}` - Revoke key
- `GET /auth/rate-limits` - Check your rate limits

## Rate Limiting

**Default limits per user** (in-memory, resets on restart):
- 60 requests/minute
- 1000 requests/hour

Anonymous users: no limits (for now)

## API Key Types

1. **Session key** (from login):
   - Name: "Session key (login)"
   - Expires: 30 days
   - Auto-created on each login

2. **Permanent key** (from /auth/api-keys):
   - Name: custom
   - Expires: never (or custom)
   - Use for integrations, scripts

## Security Notes

- Passwords hashed with bcrypt
- API keys hashed with SHA-256
- Keys transmitted once (on creation)
- Failed login attempts logged
- Inactive users rejected

## Future Extensions (No Refactoring Needed)

This design supports:

### Option 1: JWT Tokens
```python
# New endpoint
@router.post("/auth/token")
async def get_jwt_token(credentials):
    user = verify_credentials(credentials)
    jwt_token = create_jwt(user.id, expires=1h)
    return {"access_token": jwt_token}

# Middleware update (add JWT validation)
if "Authorization: Bearer xxx":
    user = decode_jwt(token)
elif "X-API-Key: xxx":
    user = validate_api_key(key)
```

### Option 2: OAuth2
```python
@router.get("/auth/oauth/google")
async def oauth_google():
    # Redirect to Google

@router.get("/auth/oauth/callback")
async def oauth_callback(code):
    google_user = get_google_user(code)
    user = get_or_create_user(google_user.email)
    api_key = generate_api_key()
    return {"api_key": api_key}
```

### Option 3: Magic Links
```python
@router.post("/auth/magic-link")
async def send_magic_link(email):
    user = get_user_by_email(email)
    token = generate_one_time_token(user.id)
    send_email(f"Login: {BASE_URL}/auth/verify?token={token}")

@router.get("/auth/verify")
async def verify_magic_link(token):
    user = validate_one_time_token(token)
    api_key = generate_api_key()
    return {"api_key": api_key}
```

**Key insight**: All methods end with `generate_api_key()` → no refactoring needed!

## Database

SQLite (async): `grammar_llm_bridge.db`

Tables:
- `users` - id, username, email, hashed_password, is_active, is_admin
- `api_keys` - id, user_id, key (hashed), name, is_active, expires_at

For production: switch to PostgreSQL by changing `DATABASE_URL` env var.

## Testing Checklist

- [ ] Register new user
- [ ] Login with correct password
- [ ] Login with wrong password (should fail)
- [ ] Use API key for /v2/check
- [ ] Create permanent API key
- [ ] List all keys
- [ ] Check rate limits
- [ ] Use grammar check without auth (backward compat)
- [ ] Revoke API key
- [ ] Try revoked key (should fail)

## Admin Operations

### Create admin user (manual, in DB)
```bash
docker exec -it grammar-llm-bridge sqlite3 /app/grammar_llm_bridge.db
sqlite> UPDATE users SET is_admin=1 WHERE username='alice';
```

### View all users
```bash
docker exec -it grammar-llm-bridge sqlite3 /app/grammar_llm_bridge.db \
  "SELECT id, username, email, is_active, is_admin FROM users;"
```

### Revoke user's keys
```bash
docker exec -it grammar-llm-bridge sqlite3 /app/grammar_llm_bridge.db \
  "UPDATE api_keys SET is_active=0 WHERE user_id=1;"
```

## Contact

For issues or questions, contact the project maintainer.

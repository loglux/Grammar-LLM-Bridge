# Authentication & API Key Management Design Discussion

**Date:** 2025-12-19
**Status:** Design phase, awaiting decision on implementation approach

---

## Context

Need to implement authentication for Grammar-LLM-Bridge to:
1. Protect API from unauthorized access
2. Manage LLM provider API keys
3. Support phased rollout: 1-2 personal users → 5-10 team → public service

---

## Original Design (User's Proposal)

### Roles

- **User** — account owner, can see their keys, issue/revoke, view usage
- **Admin** — can activate accounts, change plans, view all users

### Tables

**users**
- `id`
- `email` (unique)
- `password_hash` (for login to dashboard/admin)
- `status`: `PENDING` | `ACTIVE` | `SUSPENDED`
- `plan`: `FREE` | `PRO` | …
- `created_at`, `activated_at`, `suspended_at`
- `email_verified_at` (optional)
- `is_admin` (or separate roles table)

**activation_tokens** (for email confirmation/activation)
- `id`
- `user_id`
- `token_hash`
- `purpose`: `EMAIL_VERIFY` / `ACCOUNT_ACTIVATE`
- `expires_at`, `used_at`

**api_keys**
- `id`
- `user_id`
- `key_hash`
- `prefix` (first 6-10 chars, to show in UI "sk_live_abc123…")
- `label` (e.g., "Prod plugin", "Staging")
- `scopes` (string/JSON: e.g., `["check:read"]`)
- `status`: `ACTIVE` | `REVOKED`
- `created_at`, `last_used_at`, `revoked_at`

**usage_events** (minimal) or aggregates
- either events: `user_id`, `api_key_id`, `ts`, `route`, `units`, `status_code`
- or daily aggregate: `user_id`, `date`, `requests`, `chars_processed`

**payments/subscriptions** (when needed)
- `user_id`, `provider`, `customer_id`, `subscription_id`, `status`, `current_period_end`, etc.

**Key principle:** Store only **hashes** of tokens/keys in DB (like passwords). Show raw keys to user **once** at creation.

---

## Flows

### 1) Account Creation (signup)
1. `POST /auth/signup` (email, password)
2. Create user with status `PENDING`
3. Create `activation_token` (purpose EMAIL_VERIFY or ACTIVATE)
4. Send email with link (or show "check your email")

> If payment required before activation — user remains `PENDING` until payment webhook / manual activation.

### 2) Account Activation (after payment or manually)

Options:
**A. Via payment webhooks (Stripe/etc.)**
- webhook "payment succeeded / subscription active" → `users.status = ACTIVE`

**B. Manual activation by admin**
- `POST /admin/users/{id}/activate` → ACTIVE

**C. Combo**
- email verify → "email confirmed"
- payment → "paid"
- active account = both flags true

### 3) Dashboard/Admin Login
- `POST /auth/login` → issue **session cookie** (for web admin) _or_ JWT for UI
- For simplicity and security, cookie-session is often better (HttpOnly, SameSite)

### 4) API Key Generation

Available only to users with status `ACTIVE`.
- `POST /keys` (label, scopes)
  Server generates key, e.g., `sk_live_<random>`:
  - saves **hash** + prefix + metadata
  - returns user **raw key** once
- `GET /keys` → list (without raw key)
- `POST /keys/{id}/revoke` → revoke

### 5) API Access (`/v2/check`)

Only via:
- client sends `Authorization: Bearer <api_key>`
- server:
  1. hashes and looks up active key
  2. checks user: `ACTIVE`, plan not expired, quotas
  3. applies rate limit / quotas
  4. logs usage

---

## How "Payment/Activation" Ties to API Access

Everything comes down to one function called on each request:

**can_use_api(user, key, request)**
- user.status == ACTIVE
- plan allows route `/v2/check`
- quota/limits not exceeded
- key not revoked

This is convenient: tomorrow you add tariffs and limits — don't change the whole system, only rules.

---

## Endpoints Usually Needed

### Public
- `POST /auth/signup`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/activate?token=...` (or `POST /auth/activate`)

### User (requires login to dashboard)
- `GET /me`
- `POST /keys`
- `GET /keys`
- `POST /keys/{id}/revoke`
- `GET /usage` (by day)

### Admin
- `GET /admin/users?status=pending`
- `POST /admin/users/{id}/activate`
- `POST /admin/users/{id}/suspend`
- `POST /admin/users/{id}/set-plan`

### API (requires API key)
- `POST /v2/check`
- (optional) `GET /v2/info`, `GET /v2/languages` can be left open, but often closed too

---

## Decisions That Will Save You Pain

1. **Separate "login tokens" and "API keys"**
   - login → cookie/JWT for UI
   - API access → separate API keys
   Don't mix them, or it will be hard and dangerous.

2. **Key prefix and "search by prefix"**
   Good practice: keys like `sk_live_xxx...`, store `prefix = "sk_live_xxx"` and `hash`.
   This speeds up lookup and is better for debugging/audit.

3. **Show key once**
   Created → shown → then only "****last4/prefix".

4. **Rate-limit**
   Set limit immediately:
   - on proxy by IP (coarse)
   - in application by user/key (fine)

---

## Phased Implementation Plan (Proposed)

### Phase 1: Basic Auth (1-2 personal users) ✅ Immediate

**Goal:** Close API from public access, minimal changes.

**Implementation:**
- **At Nginx level** (in `lb.conf`):
  ```nginx
  location /v2/check {
      auth_basic "Grammar LLM Bridge";
      auth_basic_user_file /etc/nginx/.htpasswd;
      proxy_pass http://grammar_backend;
  }
  ```
- `.htpasswd` file in docker volume (don't commit!)
- Obsidian plugin configured: `username:password` in settings

**What's NOT needed:**
- ❌ Database
- ❌ Changes in app.py
- ❌ Admin panel

**Advantages:**
- ✅ Works in 10 minutes
- ✅ Don't touch Python code
- ✅ Easy to rollback (remove `auth_basic`)

**Disadvantages:**
- ⚠️ One login/password or static file
- ⚠️ No usage tracking

**Migration to Phase 2:**
- Remove `auth_basic` from nginx
- Create users in DB
- Issue API keys
- Update Obsidian plugin: replace Basic Auth with `Authorization: Bearer <key>`

---

### Phase 2: API Keys + Simple DB (5-10 team) 🎯 Next

**Goal:** API keys per user, usage tracking, minimal admin panel.

**DB Schema (simplified):**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE,
    status TEXT DEFAULT 'ACTIVE',  -- simplified: immediately ACTIVE
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);

CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key_hash TEXT UNIQUE,
    prefix TEXT,
    label TEXT,
    status TEXT DEFAULT 'ACTIVE',
    created_at TIMESTAMP,
    last_used_at TIMESTAMP
);

CREATE TABLE usage_events (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    api_key_id INTEGER,
    ts TIMESTAMP,
    route TEXT,
    chars_processed INTEGER,
    latency_ms INTEGER
);
```

**Changes in app.py:**
1. Middleware for API key validation:
   ```python
   @app.middleware("http")
   async def auth_middleware(request: Request, call_next):
       if request.url.path == "/v2/check":
           api_key = request.headers.get("Authorization", "").replace("Bearer ", "")
           user = await validate_api_key(api_key)  # check DB
           if not user:
               return JSONResponse({"error": "Unauthorized"}, status_code=401)
           request.state.user = user
       return await call_next(request)
   ```

2. Usage logging:
   ```python
   # After request processing
   await log_usage(user_id, key_id, len(text), latency_ms)
   ```

**New endpoints (minimum):**
- `POST /admin/users` — create user (admin only)
- `POST /admin/keys` — create API key for user
- `GET /admin/usage` — statistics

**Admin panel:** Simple HTML + htmx or CLI script.

**Migration from Phase 1:**
- Create 1-2 users in DB
- Issue API keys
- Remove `auth_basic` from nginx
- Obsidian plugin: replace Basic Auth with `Authorization: Bearer <key>`

**Database choice:**
- **SQLite:** Simple, file-based, good for 5-10 users
- **PostgreSQL:** Production-ready, better for scaling

**Admin interface:**
- **CLI scripts:** Fastest to implement, good for initial phase
- **Simple web UI:** HTML + htmx, better UX for non-technical admins

---

### Phase 3: Full System (public service) 🚀 Future

**Add:**
1. **Signup/Login flow** (full schema as above)
2. **Email activation** (`activation_tokens`)
3. **Password hashing** for user login
4. **User self-service** (`POST /keys`, `GET /usage`)
5. **Plans & Quotas** (`FREE`, `PRO`)
6. **Rate limiting** (by user/key)
7. **Payment integration** (Stripe webhooks)

**Migration from Phase 2:**
- Add tables: `activation_tokens`, `subscriptions`
- Add fields: `users.password_hash`, `users.plan`, `users.status=PENDING`
- Existing users: mark as `ACTIVE` with `plan=PRO` (grandfathered)
- New users via signup flow

---

## Open Questions (Awaiting Decision)

### Question 1: Which approach to start with?

**Option A: Quick Start (Phase 1)**
- Implement Basic Auth on Nginx in 15 minutes
- Protect API today
- Move to Phase 2 in 1-2 weeks

**Option B: Straight to Phase 2**
- Add SQLite (or Postgres)
- Write auth middleware in app.py
- Create minimal admin panel (CLI or simple HTML)

### Question 2: If Phase 2, which database?
- **SQLite:** Simpler, file-based, sufficient for 5-10 users
- **PostgreSQL:** Production-ready from the start, easier to scale later

### Question 3: Admin interface preference?
- **CLI scripts:** Faster to implement, sufficient for technical team
- **Web UI:** Better UX, easier for non-technical admins

### Question 4: LLM API Key Management
Separate discussion needed:
- Keep in environment variables (current approach)?
- Admin panel for managing LLM provider keys?
- Per-user LLM keys (advanced)?

---

## Next Steps

**User needs to:**
1. Review phased implementation plan
2. Weigh pros/cons of Phase 1 vs Phase 2 start
3. Decide on database choice (if Phase 2)
4. Decide on admin interface approach (CLI vs Web)
5. Consider timeline and priorities

**When ready, answer:**
- Which phase to start with?
- Database preference?
- Admin interface preference?

---

## Related Files

- ``local/LOCAL_NOTES.md` (gitignored)` — project state and context
- `<this-repo>/deploy/load-balancer/` — current deployment config
- `<this-repo>/app/` — main application code (modular package)

---

**Status:** Waiting for user decision before implementation begins.

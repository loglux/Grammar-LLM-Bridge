# Authentication Customization Guide

## Изменение срока действия session key

### Текущая настройка
**Файл**: `app/api/auth.py`, функция `login()`

**Строка 72-78**:
```python
await create_api_key(
    db,
    user_id=user.id,
    hashed_key=hashed_key,
    name=f"Session key (login)",
    expires_in_days=30  # <-- ЗДЕСЬ
)
```

### Варианты изменения

#### 1. Сделать бессрочным
```python
expires_in_days=None  # Никогда не истекает
```

#### 2. Увеличить срок
```python
expires_in_days=90   # 90 дней
expires_in_days=365  # 1 год
```

#### 3. Уменьшить срок
```python
expires_in_days=7   # 1 неделя
expires_in_days=1   # 1 день
```

#### 4. Сделать через переменную окружения
```python
# app/config.py
SESSION_KEY_EXPIRES_DAYS = int(os.getenv("SESSION_KEY_EXPIRES_DAYS", "30"))

# app/api/auth.py
from app.config import SESSION_KEY_EXPIRES_DAYS

await create_api_key(
    db,
    user_id=user.id,
    hashed_key=hashed_key,
    name=f"Session key (login)",
    expires_in_days=SESSION_KEY_EXPIRES_DAYS
)
```

Тогда в Docker:
```bash
docker run ... -e SESSION_KEY_EXPIRES_DAYS=90 ...
```

---

## Изменение срока по умолчанию для permanent keys

### Текущая настройка
**Файл**: `app/models/auth.py`

**Строка 53-55**:
```python
class APIKeyCreate(BaseModel):
    """Schema for creating a new API key."""
    name: str
    expires_in_days: Optional[int] = None  # <-- ЗДЕСЬ
```

`None` = бессрочный ключ по умолчанию.

### Варианты

#### 1. Сделать обязательным указание срока
```python
expires_in_days: int  # Обязательное поле, без default
```

Тогда пользователь ДОЛЖЕН указать срок при создании.

#### 2. Задать default срок
```python
expires_in_days: Optional[int] = 365  # По умолчанию 1 год
```

---

## Rate limiting настройки

### Текущие лимиты
**Файл**: `app/auth/rate_limiter.py`

**Строка 14-15**:
```python
def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
    self.requests_per_minute = requests_per_minute
    self.requests_per_hour = requests_per_hour
```

### Изменить глобально

**Файл**: `app/auth/rate_limiter.py`, внизу файла

**Строка 106**:
```python
# Global rate limiter instance
rate_limiter = RateLimiter()  # <-- Добавить параметры
```

Например:
```python
rate_limiter = RateLimiter(
    requests_per_minute=120,  # Увеличить до 120/мин
    requests_per_hour=5000    # Увеличить до 5000/час
)
```

### Изменить через env переменные

**app/config.py** (добавить):
```python
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
```

**app/auth/rate_limiter.py** (изменить):
```python
from app.config import RATE_LIMIT_PER_MINUTE, RATE_LIMIT_PER_HOUR

rate_limiter = RateLimiter(
    requests_per_minute=RATE_LIMIT_PER_MINUTE,
    requests_per_hour=RATE_LIMIT_PER_HOUR
)
```

Docker:
```bash
docker run ... \
  -e RATE_LIMIT_PER_MINUTE=120 \
  -e RATE_LIMIT_PER_HOUR=5000 \
  ...
```

### Разные лимиты для разных пользователей

В будущем можно добавить:

**app/db/users.py** (добавить в UserTable):
```python
class UserTable(Base):
    # ... existing fields ...
    rate_limit_minute = Column(Integer, default=60)
    rate_limit_hour = Column(Integer, default=1000)
```

**app/auth/rate_limiter.py** (использовать):
```python
def check_rate_limit(self, user: User):
    minute_limit = user.rate_limit_minute or 60
    hour_limit = user.rate_limit_hour or 1000
    # ... проверка с кастомными лимитами
```

---

## Middleware настройки

### Добавить публичные пути (без auth)

**Файл**: `app/auth/middleware.py`

**Строка 24-27**:
```python
# Skip auth for public endpoints
public_paths = ["/docs", "/openapi.json", "/redoc", "/health"]
if request.url.path in public_paths:
    return await call_next(request)
```

Добавить свои:
```python
public_paths = [
    "/docs",
    "/openapi.json",
    "/redoc",
    "/health",
    "/public/*",        # Все /public/* пути
    "/webhooks/stripe"  # Конкретный webhook
]
```

Для wildcard паттернов:
```python
import fnmatch

public_patterns = ["/docs", "/openapi.json", "/public/*", "/webhooks/*"]

if any(fnmatch.fnmatch(request.url.path, pattern) for pattern in public_patterns):
    return await call_next(request)
```

### Требовать auth для всех запросов (убрать backward compatibility)

**Файл**: `app/auth/middleware.py`

**Строка 29-36** (УДАЛИТЬ):
```python
# Check for API key in headers
api_key = request.headers.get("X-API-Key")

if not api_key:
    # Allow requests without API key for now (backward compatibility)
    # In production, you might want to require API keys for all endpoints
    request.state.user = None
    return await call_next(request)
```

**ЗАМЕНИТЬ на**:
```python
api_key = request.headers.get("X-API-Key")

if not api_key:
    logger.warning("Missing API key from %s", request.client.host)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "API key required"}
    )
```

Тогда ВСЕ запросы будут требовать X-API-Key header.

---

## Логирование auth событий

### Добавить детальное логирование

**app/auth/middleware.py** (добавить):
```python
# После успешной аутентификации
logger.info(
    "Authenticated request: user=%s endpoint=%s",
    user.username,
    request.url.path
)
```

### Логировать неудачные попытки в файл

**app/config.py** (добавить):
```python
import logging

# Setup separate logger for auth failures
auth_failures_handler = logging.FileHandler("auth_failures.log")
auth_failures_handler.setLevel(logging.WARNING)
auth_failures_logger = logging.getLogger("auth_failures")
auth_failures_logger.addHandler(auth_failures_handler)
```

**app/auth/middleware.py** (использовать):
```python
from app.config import auth_failures_logger

if not db_api_key:
    auth_failures_logger.warning(
        "Invalid API key attempt: key=%s ip=%s path=%s",
        api_key[:10] + "...",
        request.client.host,
        request.url.path
    )
```

---

## Быстрые команды

### Пересобрать контейнер после изменений
```bash
cd <repo-root>
docker stop grammar-test-refactored
docker rm grammar-test-refactored
docker build -t grammar-llm-bridge:refactored .
docker run -d --name grammar-test-refactored -p 9020:8000 \
  -e OPENAI_API_KEY=... \
  -e OPENAI_BASE_URL=... \
  -e LLM_MODEL=... \
  grammar-llm-bridge:refactored
```

### Проверить логи
```bash
docker logs grammar-test-refactored | tail -50
docker logs -f grammar-test-refactored  # follow mode
```

### Проверить БД
```bash
docker exec -it grammar-test-refactored sqlite3 /app/grammar_llm_bridge.db

# В sqlite3:
.tables
SELECT * FROM users;
SELECT id, name, is_active, expires_at FROM api_keys;
```

---

## Примеры кастомизации

### Пример 1: Короткие session keys для тестирования
```python
# app/api/auth.py, login()
expires_in_days=1  # 1 день для быстрого тестирования expiration
```

### Пример 2: Строгий production mode
```python
# app/auth/middleware.py
if not api_key:
    return JSONResponse(401, {"detail": "API key required"})

# app/auth/rate_limiter.py
rate_limiter = RateLimiter(
    requests_per_minute=30,   # Строже
    requests_per_hour=500     # Строже
)

# app/api/auth.py, login()
expires_in_days=7  # Короткие session keys
```

### Пример 3: Relaxed testing mode
```python
# app/auth/rate_limiter.py
rate_limiter = RateLimiter(
    requests_per_minute=1000,  # Почти без лимитов
    requests_per_hour=100000
)

# app/api/auth.py, login()
expires_in_days=365  # Длинные session keys
```

---

Документ создан: 2025-12-28
Версия: 1.0

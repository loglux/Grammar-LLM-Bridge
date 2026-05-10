# Структура модулей Grammar-LLM-Bridge

## Обзор архитектуры

```
Request → Middleware → Router → Handler → LLM → Response
   ↓         ↓          ↓         ↓        ↓        ↓
  Auth   Validation  Route   Process   API    Build
                    Match    Text     Call   Result
```

---

## Модули по назначению

### 🔌 Точка входа

#### `app/main.py` (77 строк)
**Назначение**: Инициализация FastAPI приложения.

**Компоненты**:
- FastAPI app instance
- CORS middleware
- Auth middleware
- Router registration
- Startup events (DB init)
- Custom OpenAPI schema

**Импорты**:
```python
from app.config import MODEL
from app.models import CheckRequest
from app.api import v2_router, auth_router
from app.auth.middleware import api_key_auth_middleware
```

**Не содержит**: бизнес-логику (вынесена в handlers)

---

### ⚙️ Конфигурация

#### `app/config.py`
**Назначение**: Централизованная конфигурация через env variables.

**Переменные**:
```python
# LLM settings
OPENAI_API_KEY
OPENAI_BASE_URL
MODEL
LLM_TIMEOUT

# Feature flags
GRAMMAR_ONLY
TYPOGRAPHY_CHECK

# Chunking
LLM_CHUNKING
LLM_CHUNK_SIZE
LLM_CHUNK_OVERLAP
LLM_CHUNK_THRESHOLD
```

**Используется**: всеми модулями для настроек.

---

### 📝 Промпты

#### `app/prompts.py`
**Назначение**: LLM промпты и их компоненты.

**Структура**:
- Модульные блоки (SYSTEM_INTRO, MODE_BLOCK, SVA_BLOCK и т.д.)
- Финальный SYSTEM_MESSAGE (собран из блоков)
- JSON schema для structured output

**Преимущество**: Легко изменять отдельные части промпта без переписывания всего.

---

### 📦 Модели данных (`app/models/`)

#### `app/models/grammar_api.py`
**Назначение**: Pydantic модели для LanguageTool-compatible API.

**Модели**:
- `LTResponse` - главный ответ
- `Match` - найденная ошибка
- `Replacement` - вариант исправления
- `Rule`, `RuleCategory` - категоризация
- `Context` - контекст ошибки
- `Software`, `Warnings`, `LanguageInfo` - метаданные
- `CheckRequest` - запрос на проверку

#### `app/models/auth.py`
**Назначение**: Модели аутентификации.

**Модели**:
- `User`, `UserCreate`, `UserResponse`
- `APIKey`, `APIKeyCreate`, `APIKeyResponse`
- `UsageRecord` - трекинг использования

---

### 🤖 LLM провайдеры (`app/llm/`)

#### `app/llm/client.py`
**Назначение**: HTTP клиент с retry логикой.

**Функции**:
- `get_http_client()` - shared AsyncClient
- `post_chat_completion()` - отправка запроса с retry
- `extract_message_content()` - безопасный парсинг

**Особенности**:
- Exponential backoff на 429/5xx
- Connection pooling
- Timeout handling

#### `app/llm/providers.py`
**Назначение**: Определение провайдера и роутинг.

**Функции**:
- `detect_provider()` - определяет по model/base_url
- `analyze_with_provider()` - выбирает правильный метод

**Поддерживаемые провайдеры**:
- OpenAI (JSON Schema mode)
- DeepSeek (json_object mode)
- Ollama (JSON Schema mode)
- Grok, OpenRouter (fallback mode)

#### `app/llm/openai.py`
**Назначение**: OpenAI/Ollama JSON Schema режим.

**Особенность**: `response_format.json_schema.strict = true`

#### `app/llm/deepseek.py`
**Назначение**: DeepSeek json_object режим.

**Особенности**:
- Empty content retry (DeepSeek bug workaround)
- JSON sanitization (escape sequences)

#### `app/llm/fallback.py`
**Назначение**: Универсальный парсер для любых LLM.

**Метод**: Manual JSON extraction из markdown code blocks.

---

### 🗃️ База данных (`app/db/`)

#### `app/db/connection.py`
**Назначение**: SQLAlchemy async setup.

**Компоненты**:
- `engine` - async SQLAlchemy engine
- `async_session_maker` - session factory
- `Base` - declarative base для ORM
- `get_db()` - dependency для FastAPI
- `init_db()` - создание таблиц

**Поддержка**:
- SQLite (aiosqlite) - по умолчанию
- PostgreSQL (asyncpg) - для production
- MySQL (aiomysql) - опционально

#### `app/db/users.py`
**Назначение**: User CRUD операции.

**ORM**:
```python
class UserTable(Base):
    id, username, email, hashed_password,
    is_active, is_admin, created_at, updated_at
```

**Функции**:
- `create_user()`
- `get_user_by_id()`
- `get_user_by_username()`
- `get_user_by_email()`

#### `app/db/api_keys.py`
**Назначение**: API key CRUD операции.

**ORM**:
```python
class APIKeyTable(Base):
    id, user_id, key (hashed), name,
    is_active, created_at, last_used_at, expires_at
```

**Функции**:
- `create_api_key()`
- `get_api_key_by_key()`
- `get_user_api_keys()`
- `update_api_key_last_used()`
- `revoke_api_key()`

---

### 🔐 Аутентификация (`app/auth/`)

#### `app/auth/middleware.py`
**Назначение**: Middleware для валидации API ключей.

**Функция**: `api_key_auth_middleware()`
- Проверяет `X-API-Key` header
- Валидирует в БД
- Устанавливает `request.state.user`
- Обновляет `last_used_at`

**Backward compatible**: без ключа тоже пропускает (user=None).

#### `app/auth/dependencies.py`
**Назначение**: FastAPI dependencies для защиты endpoints.

**Functions**:
- `get_optional_user()` - User | None
- `get_current_user()` - User (требует auth, 401 если нет)
- `require_admin()` - Admin user (требует admin, 403 если нет)

**Использование**:
```python
@router.get("/protected")
async def endpoint(user: User = Depends(get_current_user)):
    # user гарантированно есть
```

#### `app/auth/utils.py`
**Назначение**: Утилиты для паролей и ключей.

**Функции**:
- `hash_password()` - bcrypt hash
- `verify_password()` - bcrypt verify
- `generate_api_key()` - secure random 64-char hex
- `hash_api_key()` - SHA-256 hash для хранения

#### `app/auth/rate_limiter.py`
**Назначение**: Rate limiting per user.

**Класс**: `RateLimiter`
- Sliding window algorithm
- In-memory хранилище (сбрасывается на restart)
- Дефолт: 60/min, 1000/hour

**Глобальный инстанс**: `rate_limiter`

---

### 🌐 API endpoints (`app/api/`)

#### `app/api/v2.py`
**Назначение**: LanguageTool-compatible v2 API.

**Endpoints**:
- `GET /v2/languages` - список языков
- `GET /v2/info` - информация о сервере
- `POST /v2/check` - проверка грамматики

**Особенность**: Поддерживает form-urlencoded и JSON.

#### `app/api/auth.py`
**Назначение**: Authentication endpoints.

**Endpoints**:
- `POST /auth/login` - логин (получить API key)
- `POST /auth/register` - регистрация
- `POST /auth/api-keys` - создать постоянный ключ
- `GET /auth/api-keys` - список ключей
- `DELETE /auth/api-keys/{id}` - отозвать ключ
- `GET /auth/rate-limits` - проверить лимиты

---

### 📄 Обработка текста

#### `app/text_processing.py`
**Назначение**: Извлечение, маскирование, chunking текста.

**Главные функции**:
- `extract_texts_and_mapping()` - original, logical, mapping
- `mask_math_blocks()` - маскирование LaTeX
- `split_into_chunks()` - paragraph-aware chunking
- `retry_missing_on_sentences()` - sentence-level retry

**Ключевая концепция**:
```
Original text (с markup)
    ↓ extract
Logical text (без markup) + mapping
    ↓ mask
Masked text + math_ranges
    ↓ chunk
Chunks with overlap + anchors
```

#### `app/error_finder.py`
**Назначение**: Поиск позиций ошибок в тексте + фильтры.

**Главная функция**: `find_error_positions_in_logical()`

**Heuristics (15+ фильтров)**:
- Word boundary checks
- Token connector handling (don't, well-being)
- Capital letter guards
- Redundant article filtering
- No-op replacement filtering
- Punctuation existence checks
- Style/typography filtering

**Сложность**: ~340 строк (самый сложный модуль).

#### `app/position_mapper.py`
**Назначение**: Mapping позиций между версиями текста.

**Функции**:
- `map_to_original_positions()` - logical → original
- `convert_to_utf16_positions()` - Python → UTF-16 code units
- `deduplicate_by_span()` - удаление дубликатов

**Критичность**: Обеспечивает корректность offsets для клиентов.

#### `app/response_builder.py`
**Назначение**: Сборка LanguageTool-compatible ответов.

**Функция**: `build_lt_response()`

**Создаёт**:
- `LTResponse` с matches
- Software metadata
- Language detection info
- Sentence ranges

---

### 🎯 Главный orchestrator

#### `app/handlers.py`
**Назначение**: Главная логика проверки (orchestrator).

**Функция**: `handle_check()`

**Пайплайн** (8 шагов):
1. Parse input (text or data)
2. Extract texts and mapping
3. Mask math blocks
4. Run LLM (chunked or single)
5. Find error positions in logical text
6. Retry missing on sentences
7. Map to original positions
8. Deduplicate + convert to UTF-16
9. Build LT response

**Timing**: Опциональный tracking latency.

---

## Граф зависимостей

```
main.py
  ├─→ config
  ├─→ models (grammar_api, auth)
  ├─→ api (v2, auth)
  │    └─→ handlers
  │         ├─→ text_processing
  │         ├─→ error_finder
  │         ├─→ position_mapper
  │         ├─→ response_builder
  │         └─→ llm (providers, client, openai, deepseek, fallback)
  └─→ auth (middleware, dependencies, utils, rate_limiter)
       └─→ db (connection, users, api_keys)
```

**Направление**: main → api → handlers → processing/llm

**Циклических зависимостей**: нет ✅

---

## Принципы организации

### 1. Separation of Concerns
- Каждый модуль отвечает за одну задачу
- Чёткие границы ответственности

### 2. Single Source of Truth
- Config - единственный источник настроек
- Prompts - единственный источник промптов

### 3. Dependency Injection
- FastAPI Depends() для DB sessions
- Middleware для user context

### 4. Async by Default
- Все IO операции async
- SQLAlchemy async mode
- httpx AsyncClient

### 5. Type Safety
- Pydantic модели везде
- Type hints в функциях

---

## Файловая структура (summary)

```
app/
├── main.py                 # FastAPI app
├── config.py               # Env config
├── prompts.py              # LLM prompts
│
├── models/                 # Data models
│   ├── grammar_api.py
│   └── auth.py
│
├── llm/                    # LLM providers
│   ├── client.py
│   ├── providers.py
│   ├── openai.py
│   ├── deepseek.py
│   └── fallback.py
│
├── db/                     # Database
│   ├── connection.py
│   ├── users.py
│   └── api_keys.py
│
├── auth/                   # Authentication
│   ├── middleware.py
│   ├── dependencies.py
│   ├── utils.py
│   └── rate_limiter.py
│
├── api/                    # API routers
│   ├── v2.py
│   └── auth.py
│
├── text_processing.py      # Text extraction/chunking
├── error_finder.py         # Position finding + filters
├── position_mapper.py      # Position mapping
├── response_builder.py     # Response building
└── handlers.py             # Main orchestrator
```

**Всего**: ~18 файлов, ~3000 строк (vs 2067 в монолите).

---

Документ создан: 2025-12-28
Версия: 1.0

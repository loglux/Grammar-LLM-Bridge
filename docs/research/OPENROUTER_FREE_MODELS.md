# Quick Check: OpenRouter Free Models (Dec 2025)

Goal: увидеть, какие бесплатные модели OpenRouter можно использовать для грамматических проверок, в каком формате они отвечают, и насколько они шумят на текстах с LaTeX.

## Тестовый сценарий
- Основной пример: формула в блоке `$$...$$` и предложение после блока.
- Формат запроса (варианты):
  - **JSON Schema**: `response_format={'type': 'json_schema', ...}` с обёрткой `{ "errors": [...] }`.
  - **JSON Object**: `response_format={'type': 'json_object'}`.
  - **Fallback**: без `response_format`, ожидание массива в тексте.
- Ключ: OpenRouter (локальный), base_url: `https://openrouter.ai/api/v1`.

## Результаты по моделям

### meta-llama/llama-3.1-405b-instruct:free
- **JSON Schema**: работает, форматы соблюдены. Даёт стилистические/артиклевые правки (например, “the initial height of the ball” → с артиклем/уточнением). Формулы не ломает.
- **JSON Object**: 400 (“Value error”) — не использовать.
- **Fallback (без response_format)**: возвращает markdown + массив; можно распарсить вручную, но есть стилистика/артикли.
- Базовая грамматика на простых кейсах: SVA, опечатки, запятая — ок; корректное предложение → пустой список.

### openai/gpt-oss-20b:free
- **JSON Schema**: работает, вернул минимальный шум (в тесте только `for → of` в “graph for the function”), LaTeX не трогает, регистр после блока не меняет.
- JSON Object и fallback не проверялись отдельно, т.к. Schema уже дала корректный ответ.
- **Rate limits**: free endpoint возвращает 429 при bursts ~20 запросов (см. `X-RateLimit-Limit: 20`, `Remaining: 0`), так что параллельные тесты нужно дозировать.

### google/gemini-2.0-flash-exp:free
- 429 (rate-limited upstream) — сейчас недоступна.

### google/gemma-3-27b-it:free
- 429 (rate-limited upstream) — сейчас недоступна.

### openai/gpt-oss-120b:free
- 404 (“No endpoints found matching your data policy (Free model publication)”) — недоступна с бесплатным ключом.

## Выводы и рекомендации
- Из доступных бесплатных моделей на практике работают только:
  - **openai/gpt-oss-20b:free** — самый “тихий” на нашем примере.
  - **meta-llama/llama-3.1-405b-instruct:free** — работает, но даёт стили/артикли; JSON Object не поддерживает.
- Gemini/Gemma free — упираются в rate-limit; 120b — недоступна.
- Для стабильного парсинга используйте **JSON Schema** (учесть, что ответ обёрнут в `{errors: [...]}`).

## Интеграционные заметки
- Наш текущий сервер ожидает “голый” массив (DeepSeek/OpenAI json_object). Если подключать OpenRouter + JSON Schema, потребуется:
  - Обработать обёртку `{errors: [...]}`.
  - Или переключить провайдер только на модели, которые отдают чистый массив (но среди free это не гарантировано).
- Запуск контейнера с OpenRouter:
  - `OPENAI_API_KEY=<sk-or-...>`
  - `OPENAI_BASE_URL=https://openrouter.ai/api/v1`
  - `LLM_MODEL=openai/gpt-oss-20b:free` (или llama-3.1-405b:free)

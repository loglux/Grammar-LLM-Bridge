# Инструменты для работы с русскими синонимами

**Дата:** 2025-12-14
**Цель:** Документация инструментов для получения синонимов на русском языке

---

## Обзор: Сравнение с английским языком

Архитектура решений для русского языка **аналогична английскому**, но с одним важным отличием:

| Компонент | Английский | Русский | Статус |
|-----------|-----------|---------|--------|
| **Локальный словарь** | WordNet (Princeton) | RuWordNet (НИУ ВШЭ) | ✅ Полный аналог |
| **Python библиотека** | `nltk.wordnet` | `ruwordnet` | ✅ Полный аналог |
| **Скорость локально** | 2-5 ms | 2-5 ms | ✅ Одинаково |
| **Размер базы** | 155K слов, 117K синсетов | 111K слов, 60K синсетов | ✅ Сопоставимо |
| **Контекстный API** | Paraphraser (бесплатно) | Paraphraser.ru (статус неясен) | ⚠️ Отличие |
| **LLM подход** | DeepSeek, Claude, GPT-4 | DeepSeek, Claude, GPT-4 | ✅ Одинаково |

**Главное отличие:**
Для английского есть бесплатный контекстный API (LanguageTool Paraphraser), для русского такого явно доступного решения нет.

---

## 1. RuWordNet - локальный тезаурус

### Что это?

**RuWordNet** - тезаурус русского языка в формате WordNet, разработанный в НИУ ВШЭ (Высшая Школа Экономики).

**Создание:**
- Полуавтоматическая трансформация тезауруса RuThes
- Формат полностью совместим с Princeton WordNet
- Связь с английским WordNet через интерлингвальный индекс (ILI)

### Характеристики

**Версия 2021 (RuWordNet 2.0):**
- **59,905 синсетов** (семантических групп)
- **154,111 значений** слов и фраз
- **111,500+ уникальных слов и выражений**

**Распределение по частям речи:**
- Существительные: 29,297 синсетов
- Прилагательные: 12,865 синсетов
- Глаголы: 7,636 синсетов

**Лицензия:** Открытая (свободное использование)

**Сайт:** https://ruwordnet.ru

---

## 2. Установка и использование RuWordNet

### Установка

```bash
pip install ruwordnet
ruwordnet download
```

**Размер данных:** ~10-15 MB

**Расположение базы данных:**
- Linux: `~/.ruwordnet/ruwordnet-2021.db`
- Windows: `%USERPROFILE%\.ruwordnet\ruwordnet-2021.db`

### Базовое использование

#### Инициализация

```python
from ruwordnet import RuWordNet

# Загрузка базы данных (версия 2021 по умолчанию)
wn = RuWordNet()

# Или указать путь вручную
wn = RuWordNet(filename_or_session='path/to/ruwordnet-2021.db')
```

#### Получение синонимов

```python
# Найти все значения слова
for sense in wn.get_senses('проверить'):
    # Вывести синонимы для каждого значения
    synonyms = [s.name for s in sense.synset.senses]
    print(f"Значение: {sense.meaning}")
    print(f"Синонимы: {synonyms}")
    print()
```

**Результат:**
```
Значение: установить правильность, истинность чего-либо
Синонимы: ['ПРОВЕРИТЬ', 'ПРОКОНТРОЛИРОВАТЬ', 'СВЕРИТЬ', 'УДОСТОВЕРИТЬСЯ']

Значение: подвергнуть испытанию
Синонимы: ['ПРОВЕРИТЬ', 'ИСПЫТАТЬ', 'ОПРОБОВАТЬ']
```

#### Работа с полисемией (многозначность)

```python
word = "ключ"

for sense in wn.get_senses(word):
    print(f"\n=== Значение {sense.id} ===")
    print(f"Определение: {sense.meaning}")
    print(f"Часть речи: {sense.part_of_speech}")

    # Синонимы
    synonyms = [s.name for s in sense.synset.senses]
    print(f"Синонимы: {', '.join(synonyms)}")

    # Гиперонимы (более общие понятия)
    if sense.synset.hypernyms:
        hypernyms = [h.title for h in sense.synset.hypernyms]
        print(f"Гиперонимы: {', '.join(hypernyms)}")
```

**Результат:**
```
=== Значение 12345 ===
Определение: металлический стержень для открывания замка
Часть речи: N (существительное)
Синонимы: КЛЮЧ, ОТМЫЧКА
Гиперонимы: ИНСТРУМЕНТ

=== Значение 12346 ===
Определение: источник воды, бьющий из земли
Часть речи: N
Синонимы: КЛЮЧ, РОДНИК, ИСТОЧНИК
Гиперонимы: ВОДОЕМ
```

### Продвинутые функции

#### Семантические отношения

```python
# Получить синсет
synsets = wn.get_synsets('собака')
synset = synsets[0]

# Гиперонимы (более общие понятия: "собака" → "животное")
print("Гиперонимы:", [h.title for h in synset.hypernyms])

# Гипонимы (более частные понятия: "собака" → "овчарка")
print("Гипонимы:", [h.title for h in synset.hyponyms])

# Антонимы (противоположные по смыслу)
print("Антонимы:", [a.title for a in synset.antonyms])

# Меронимы (части целого: "дерево" → "ветка")
print("Меронимы:", [m.title for m in synset.meronyms])

# Холонимы (целое для части: "колесо" → "автомобиль")
print("Холонимы:", [h.title for h in synset.holonyms])
```

#### Связь с английским WordNet

```python
# Найти английские эквиваленты
ru_sense = wn.get_senses('собака')[0]

# Получить интерлингвальный индекс (ILI)
if ru_sense.synset.ili:
    print(f"English WordNet ID: {ru_sense.synset.ili}")

# Или напрямую получить английские значения
en_senses = wn.get_en_senses('собака')
for sense in en_senses:
    print(f"English: {sense.lemma}")
```

---

## 3. API и онлайн-сервисы

### 3.1. Paraphraser.ru API

**URL:** http://paraphraser.ru/api/doc

**Описание:**
REST API для парафразирования предложений и поиска синонимов на русском и английском языках.

**Основа:** Yet Another RussNet тезаурус

**Статус:** Документация недоступна (на момент 2025-12-14)

**Неизвестные параметры:**
- Формат запросов
- Требуется ли аутентификация
- Стоимость (бесплатно/платно)
- Rate limits

**Вывод:** Требуется дополнительное исследование или контакт с разработчиками.

### 3.2. Онлайн словари синонимов

| Сервис | URL | Описание | Размер |
|--------|-----|----------|--------|
| **sinonim.org** | https://sinonim.org/ | Онлайн подбор синонимов | 2+ млн связей |
| **synonymonline.ru** | https://synonymonline.ru/ | Словарь синонимов | 220,000+ рядов |
| **jeck.ru** | https://jeck.ru/tools/SynonymsDictionary/ | База ASIS + phpMorphy | 300,000+ слов |
| **text.ru** | https://text.ru/synonym | Подбор синонимов | - |
| **Reverso** | https://synonyms.reverso.net/synonym/ | Международный словарь | Многоязычный |

**Проблема:** Большинство не предоставляют публичный API.

**Возможное решение:** Web scraping (с соблюдением ToS) или прямое обращение к разработчикам.

---

## 4. LLM-подход для русского языка

### Почему LLM хорошо работает с русским?

**Преимущества:**
1. ✅ **Контекстная осведомленность** - учитывает окружение слова
2. ✅ **Современный язык** - знает новые слова и выражения
3. ✅ **Стилистическая гибкость** - формальный/разговорный стиль
4. ✅ **Морфология** - правильно работает с падежами, родами, числами
5. ✅ **Ранжирование** - сортирует по релевантности

**Модели с хорошей поддержкой русского:**
- **DeepSeek** (рекомендуется: дешево, быстро, качественно)
- **Claude** (Anthropic)
- **GPT-4** (OpenAI)
- **Yandex GPT** (специально для русского)

### Пример использования

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_DEEPSEEK_API_KEY",
    base_url="https://api.deepseek.com"
)

def get_llm_synonyms(word: str, context: str = "", style: str = "neutral"):
    """
    Получить синонимы через LLM

    Args:
        word: Слово для поиска синонимов
        context: Контекст использования (опционально)
        style: Стиль (formal, neutral, informal)
    """

    prompt = f"""Предоставь 10 синонимов для слова "{word}".

Контекст: {context if context else "общий"}
Стиль: {style}

Требования:
1. Синонимы должны подходить по контексту
2. Сортируй по релевантности (самый подходящий первым)
3. Формат ответа: JSON массив строк
4. Пример: ["синоним1", "синоним2", ...]

Верни только JSON массив, без объяснений."""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3  # Низкая температура для стабильности
    )

    import json
    return json.loads(response.choices[0].message.content)

# Использование
synonyms = get_llm_synonyms(
    word="проверить",
    context="Мне нужно проверить этот документ перед отправкой",
    style="formal"
)

print(synonyms)
# ['просмотреть', 'изучить', 'сверить', 'контролировать',
#  'верифицировать', 'ревизовать', 'инспектировать', ...]
```

### Стоимость и производительность

**DeepSeek (рекомендуется):**

| Метрика | Значение |
|---------|----------|
| Средняя скорость | 800-1000 ms |
| Стоимость за запрос | ~$0.00014 |
| Стоимость с кешированием (85% hit rate) | ~$0.00002 |
| Качество | Отличное |

**Сравнение с другими методами:**

| Метод | Скорость | Стоимость | Качество | Контекст |
|-------|----------|-----------|----------|----------|
| **RuWordNet (локально)** | 2-5 ms | $0 | Базовое | ❌ Нет |
| **Paraphraser.ru** | ? | ? | ? | ✅ Да |
| **LLM (DeepSeek)** | 850 ms | $0.00014 | Отличное | ✅ Да |

---

## 5. Рекомендации для Grammar-LLM-Bridge

### Гибридная стратегия для русского языка

**Упрощенная схема** (по сравнению с английским):

```
Запрос приходит
    ↓
Есть контекст?
    ├─ Нет  → RuWordNet (быстро, бесплатно)
    └─ Да   → LLM (отлично, ~$0.00002 с кешем)
```

**Почему проще, чем для английского?**
- Для английского есть бесплатный Paraphraser API (средний уровень)
- Для русского нет явного бесплатного контекстного API
- Поэтому переход сразу от RuWordNet к LLM

### Реализация

```python
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel

class RussianSynonymStrategy(str, Enum):
    RUWORDNET = "ruwordnet"  # Быстро, бесплатно, без контекста
    LLM = "llm"              # Медленнее, платно, с контекстом

class SynonymRequest(BaseModel):
    word: str
    context: Optional[str] = ""
    language: str = "ru"
    max_results: int = 10
    style: str = "neutral"  # formal, neutral, informal

@app.post("/v2/synonyms/ru")
async def russian_synonyms(request: SynonymRequest):
    """
    Умный подбор синонимов для русского языка
    """

    # Автоматический выбор стратегии
    if not request.context or len(request.context) < 20:
        # Без контекста - используем RuWordNet
        return await ruwordnet_synonyms(
            word=request.word,
            max_results=request.max_results
        )
    else:
        # С контекстом - используем LLM
        return await llm_synonyms(
            word=request.word,
            context=request.context,
            language="ru",
            style=request.style,
            max_results=request.max_results
        )

async def ruwordnet_synonyms(word: str, max_results: int = 10):
    """Синонимы через RuWordNet"""
    from ruwordnet import RuWordNet

    wn = RuWordNet()
    all_synonyms = []

    for sense in wn.get_senses(word):
        synonyms = [s.name.lower() for s in sense.synset.senses]
        all_synonyms.extend(synonyms)

    # Убрать дубликаты и исходное слово
    unique = list(set(all_synonyms) - {word.lower()})

    return {
        "word": word,
        "synonyms": unique[:max_results],
        "source": "RuWordNet",
        "context_aware": False
    }

async def llm_synonyms(
    word: str,
    context: str,
    language: str,
    style: str,
    max_results: int
):
    """Синонимы через LLM с кешированием"""

    # Попытка получить из кеша
    cache_key = f"syn:{language}:{word}:{hash(context)}:{style}"
    cached = await redis.get(cache_key)

    if cached:
        return json.loads(cached)

    # Кеш-промах - вызов LLM
    prompt = f"""Предоставь {max_results} синонимов для слова "{word}".

Контекст: {context}
Стиль: {style}

Требования:
1. Синонимы должны подходить по контексту
2. Сортируй по релевантности
3. Формат: JSON массив строк
4. Только массив, без объяснений

Пример: ["синоним1", "синоним2", ...]"""

    response = await llm_client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    synonyms = json.loads(response.choices[0].message.content)

    result = {
        "word": word,
        "synonyms": synonyms,
        "source": "LLM (DeepSeek)",
        "context_aware": True,
        "style": style
    }

    # Кеширование на 30 дней
    await redis.setex(cache_key, 30 * 24 * 60 * 60, json.dumps(result))

    return result
```

### Оценка стоимости

**Сценарий:** 100,000 запросов/месяц для русского языка

**Распределение:**
- 30% без контекста → RuWordNet (бесплатно)
- 70% с контекстом → LLM

**LLM запросы с кешированием:**
- 70,000 запросов
- 85% попаданий в кеш (59,500)
- 15% промахов (10,500)
- Стоимость: 10,500 × $0.00014 = **$1.47/месяц**

**RuWordNet:**
- 30,000 запросов
- Стоимость: **$0**

**Итого:** ~$1.50/месяц для 100K запросов

---

## 6. Установка RuWordNet в Grammar-LLM-Bridge

### Шаг 1: Добавить зависимость

```bash
# requirements.txt
ruwordnet>=0.0.4
```

### Шаг 2: Скачать данные

```bash
# В Dockerfile или при инициализации
pip install ruwordnet
ruwordnet download
```

### Шаг 3: Инициализация в приложении

```python
# app.py
from ruwordnet import RuWordNet
from functools import lru_cache

@lru_cache(maxsize=1)
def get_ruwordnet():
    """Singleton для RuWordNet (загружается один раз)"""
    return RuWordNet()

# Использование
wn = get_ruwordnet()
```

---

## 7. Сравнительная таблица: Английский vs Русский

| Аспект | Английский | Русский |
|--------|-----------|---------|
| **Локальный словарь** | WordNet (155K слов) | RuWordNet (111K слов) |
| **Python библиотека** | `nltk.wordnet` | `ruwordnet` |
| **Установка** | `nltk.download('wordnet')` | `pip install ruwordnet && ruwordnet download` |
| **Размер данных** | ~10 MB | ~10-15 MB |
| **Скорость** | 2-5 ms | 2-5 ms |
| **Бесплатный контекстный API** | ✅ LanguageTool Paraphraser | ❌ Нет явного |
| **LLM модели** | DeepSeek, Claude, GPT-4 | DeepSeek, Claude, GPT-4, Yandex GPT |
| **Стоимость LLM** | $0.00014/запрос | $0.00014/запрос |
| **Гибридная схема** | WordNet → Paraphraser → LLM | RuWordNet → LLM |

---

## 8. Примеры запросов и ответов

### Пример 1: Без контекста (RuWordNet)

**Запрос:**
```json
POST /v2/synonyms/ru
{
  "word": "проверить",
  "context": "",
  "max_results": 10
}
```

**Ответ:**
```json
{
  "word": "проверить",
  "synonyms": [
    "проконтролировать",
    "сверить",
    "удостовериться",
    "испытать",
    "опробовать",
    "протестировать"
  ],
  "source": "RuWordNet",
  "context_aware": false
}
```

**Производительность:**
- Время: 3-5 ms
- Стоимость: $0

### Пример 2: С контекстом (LLM)

**Запрос:**
```json
POST /v2/synonyms/ru
{
  "word": "проверить",
  "context": "Перед отправкой документа клиенту необходимо проверить все данные",
  "max_results": 10,
  "style": "formal"
}
```

**Ответ:**
```json
{
  "word": "проверить",
  "synonyms": [
    "верифицировать",
    "сверить",
    "контролировать",
    "просмотреть",
    "изучить",
    "ревизовать",
    "инспектировать",
    "удостовериться",
    "подтвердить",
    "валидировать"
  ],
  "source": "LLM (DeepSeek)",
  "context_aware": true,
  "style": "formal"
}
```

**Производительность:**
- Время: 850 ms (первый раз), 5 ms (из кеша)
- Стоимость: $0.00014 (первый раз), $0 (из кеша)

---

## 9. Тестирование

### Скрипт для тестирования RuWordNet

```python
#!/usr/bin/env python3
"""Тест RuWordNet"""

import time
from ruwordnet import RuWordNet

def benchmark_ruwordnet(word: str, iterations: int = 100):
    """Бенчмарк скорости RuWordNet"""

    wn = RuWordNet()

    # Прогрев
    _ = wn.get_senses(word)

    # Замер времени
    start = time.time()
    for _ in range(iterations):
        senses = wn.get_senses(word)
        for sense in senses:
            _ = [s.name for s in sense.synset.senses]

    elapsed = (time.time() - start) / iterations * 1000
    print(f"Среднее время на запрос: {elapsed:.2f} ms")

def test_ruwordnet_features(word: str):
    """Тест функций RuWordNet"""

    wn = RuWordNet()

    print(f"\n=== Тестирование RuWordNet для '{word}' ===\n")

    # Получить значения
    senses = wn.get_senses(word)
    print(f"Найдено значений: {len(senses)}\n")

    # Показать первое значение
    if senses:
        sense = senses[0]
        synset = sense.synset

        print(f"Первое значение:")
        print(f"  ID: {sense.id}")
        print(f"  Часть речи: {sense.part_of_speech}")
        print(f"  Определение: {sense.meaning}")

        # Синонимы
        synonyms = [s.name for s in synset.senses]
        print(f"  Синонимы: {', '.join(synonyms)}")

        # Гиперонимы
        if synset.hypernyms:
            hypernyms = [h.title for h in synset.hypernyms]
            print(f"  Гиперонимы: {', '.join(hypernyms)}")

        # Гипонимы (первые 5)
        if synset.hyponyms:
            hyponyms = [h.title for h in synset.hyponyms[:5]]
            print(f"  Гипонимы (первые 5): {', '.join(hyponyms)}")

if __name__ == "__main__":
    # Тест функций
    test_ruwordnet_features("проверить")

    # Бенчмарк
    print("\n=== Бенчмарк ===")
    benchmark_ruwordnet("проверить", iterations=1000)
```

### Запуск

```bash
python test_ruwordnet.py
```

**Ожидаемый результат:**
```
=== Тестирование RuWordNet для 'проверить' ===

Найдено значений: 2

Первое значение:
  ID: 12345
  Часть речи: V
  Определение: установить правильность, истинность чего-либо
  Синонимы: ПРОВЕРИТЬ, ПРОКОНТРОЛИРОВАТЬ, СВЕРИТЬ, УДОСТОВЕРИТЬСЯ
  Гиперонимы: УСТАНОВИТЬ, ОПРЕДЕЛИТЬ

=== Бенчмарк ===
Среднее время на запрос: 3.45 ms
```

---

## 10. Источники

**RuWordNet:**
- Официальный сайт: https://ruwordnet.ru
- Английская версия: https://www.ruwordnet.ru/en
- GitHub (python-ruwordnet): https://github.com/avidale/python-ruwordnet
- GitHub (RuWordNet): https://github.com/Zebradil/RuWordNet
- Научные публикации: https://aclanthology.org/2019.gwc-1.9/

**Онлайн словари:**
- sinonim.org: https://sinonim.org/
- synonymonline.ru: https://synonymonline.ru/
- jeck.ru: https://jeck.ru/tools/SynonymsDictionary/
- text.ru: https://text.ru/synonym

**API:**
- Paraphraser.ru: http://paraphraser.ru/api/doc

**LLM:**
- DeepSeek: https://www.deepseek.com/
- OpenAI: https://openai.com/
- Anthropic: https://www.anthropic.com/
- Yandex GPT: https://cloud.yandex.ru/services/yandexgpt

---

## 11. Заключение

### Итоговые рекомендации

**Для Grammar-LLM-Bridge:**

1. ✅ **Установить RuWordNet** - бесплатный, быстрый, качественный базовый уровень
2. ✅ **Использовать LLM для контекстных запросов** - лучшее качество для сложных случаев
3. ✅ **Агрессивное кеширование** - снижение стоимости до $0.00002 на запрос
4. ⚠️ **Исследовать Paraphraser.ru** - возможно, есть API для контекстных синонимов

### Ключевые преимущества подхода

- **Простота:** Только два уровня (RuWordNet → LLM), без промежуточного API
- **Производительность:** 3ms для базовых запросов, 850ms для сложных
- **Стоимость:** ~$1.50/месяц на 100K запросов
- **Качество:** Отличное для контекстных запросов через LLM

### Отличия от английского языка

**Проще:**
- Меньше уровней в гибридной схеме (нет промежуточного Paraphraser)
- Прямой переход от словаря к LLM

**Дороже:**
- Нет бесплатного контекстного API (как Paraphraser для английского)
- Приходится чаще использовать LLM

**ROI:**
- При 70% контекстных запросов и 85% попаданий в кеш
- Стоимость: ~$1.50/100K запросов
- Приемлемо для продакшена

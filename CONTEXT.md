# Контекст проекта (для разработчика)

Bankrot Parser Pro — система парсинга и анализа данных о банкротствах. Парсит лоты, анализирует через DeepSeek API, предоставляет REST API, веб-интерфейс и CLI. Использует SQLite с persistent disk на Render.

**Ключевые модули:**
- `parser.py` — парсинг с проверкой даты, запрос подтверждения
- `analyzer.py` — анализ лотов через DeepSeek API с кешированием в `analysis_cache`
- `database.py` — SQLite с таблицами `trades` и `analysis_cache`, функции фильтрации
- `app.py` — FastAPI с эндпоинтами для данных, анализа, статистики, экспорта
- `cli.py` — CLI команды: parse, show, stats, analyze
- `templates/index.html` — веб-интерфейс с фильтрами, таблицей, графиками Chart.js

**Архитектура:** Python 3.10, FastAPI, SQLite, Bootstrap, Chart.js. Деплой на Render с Docker. Переменные окружения: `DEEPSEEK_API_KEY`, `DATABASE_PATH`. Persistent disk для `/data`.

**Основные потоки:** парсинг → сохранение в БД → анализ через API → кеширование → отображение в UI. Весь код в одном репозитории, документация в DOCS.md, роадмап в ROADMAP.md.
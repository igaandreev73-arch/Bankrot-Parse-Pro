# Bankrot Parser Pro - Документация

## О проекте

Bankrot Parser Pro — это система для парсинга, анализа и визуализации данных о банкротствах. Проект предоставляет REST API, веб-интерфейс и CLI для работы с данными о лотах банкротства.

**Основные возможности:**
- Парсинг данных о банкротствах с проверкой даты
- Анализ лотов с использованием DeepSeek API
- Кеширование результатов анализа в SQLite
- Веб-интерфейс с графиками и фильтрами
- REST API для интеграции с другими системами
- CLI для командной строки

## Технологический стек

- **Backend:** Python 3.10, FastAPI, SQLite
- **Frontend:** HTML/CSS/JavaScript, Bootstrap 5, Chart.js
- **База данных:** SQLite с persistent disk для Render
- **Контейнеризация:** Docker, Docker Compose
- **Деплой:** Render (с поддержкой persistent disk)
- **Аналитика:** DeepSeek API для оценки лотов

## Архитектура

```
bankrot-parser-pro/
├── app.py              # FastAPI приложение (REST API)
├── parser.py           # Модуль парсинга данных
├── analyzer.py         # Модуль анализа лотов (DeepSeek API)
├── database.py         # Работа с SQLite (trades + analysis_cache)
├── cli.py              # CLI интерфейс
├── templates/          # HTML шаблоны
│   └── index.html      # Веб-интерфейс
├── requirements.txt    # Зависимости Python
├── Dockerfile          # Конфигурация Docker
├── docker-compose.yml  # Локальное развёртывание
└── render.yaml         # Конфигурация для Render
```

## Установка и запуск

### Локальная установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/ваш-username/bankrot-parser-pro.git
cd bankrot-parser-pro
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env, добавьте DEEPSEEK_API_KEY
```

4. Инициализируйте базу данных:
```bash
python -c "from database import init_database; init_database()"
```

5. Запустите приложение:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Запуск через Docker Compose

```bash
docker-compose up --build
```

Приложение будет доступно по адресу: http://localhost:8000

### Деплой на Render

1. Создайте репозиторий на GitHub
2. Создайте новый Web Service на Render
3. Подключите репозиторий
4. Настройте persistent disk для `/data`
5. Установите переменные окружения:
   - `DEEPSEEK_API_KEY` (обязательно)
   - `DATABASE_PATH=/data/bankrot.db`

## API эндпоинты

| Метод | Эндпоинт | Описание | Параметры |
|-------|----------|----------|-----------|
| GET | `/api/trades` | Получить список лотов | `limit`, `offset`, `region`, `min_discount` |
| GET | `/api/analyze/{lot_id}` | Анализ конкретного лота | `lot_id` (в пути) |
| POST | `/api/analyze/batch` | Пакетный анализ лотов | `lot_ids` (массив) |
| GET | `/api/stats/advanced` | Расширенная статистика | - |
| GET | `/api/regions` | Список уникальных регионов | - |
| GET | `/api/export` | Экспорт данных в CSV | `region`, `min_discount` |
| GET | `/api/run-parser` | Запуск парсера вручную | - |
| GET | `/` | Веб-интерфейс | - |

## Структура базы данных

### Таблица `trades`
| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PRIMARY KEY | Уникальный идентификатор |
| lot_id | TEXT NOT NULL | ID лота |
| lot_name | TEXT | Название лота |
| initial_price | REAL | Начальная цена |
| discount_percent | REAL | Процент скидки |
| final_price | REAL | Финальная цена |
| region | TEXT | Регион |
| property_type | TEXT | Тип имущества |
| participants_count | INTEGER | Количество участников |
| trade_end_date | TEXT | Дата окончания торгов |
| parsed_at | TEXT NOT NULL | Дата парсинга |
| UNIQUE(lot_id, DATE(parsed_at)) | | Защита от дублирования |

### Таблица `analysis_cache`
| Поле | Тип | Описание |
|------|-----|----------|
| id | INTEGER PRIMARY KEY | Уникальный идентификатор |
| lot_id | TEXT NOT NULL UNIQUE | ID лота |
| lot_name | TEXT | Название лота |
| property_type | TEXT | Тип имущества |
| region | TEXT | Регион |
| initial_price | REAL | Начальная цена |
| liquidity_score | INTEGER | Оценка ликвидности (0-100) |
| risk_level | TEXT | Уровень риска |
| recommendation | TEXT | Рекомендация |
| max_reasonable_price | REAL | Макс. разумная цена |
| key_factors | TEXT | JSON массив ключевых факторов |
| created_at | TEXT NOT NULL | Дата создания |
| updated_at | TEXT NOT NULL | Дата обновления |

## Переменные окружения

| Переменная | Обязательно | Значение по умолчанию | Описание |
|------------|-------------|----------------------|----------|
| `DEEPSEEK_API_KEY` | Да | - | API ключ DeepSeek |
| `DATABASE_PATH` | Нет | `database/bankrot.db` | Путь к файлу SQLite |
| `PORT` | Нет | `8000` | Порт для FastAPI |
| `LOG_LEVEL` | Нет | `INFO` | Уровень логирования |

## CLI команды

```bash
# Запуск парсера
python cli.py parse

# Показать последние лоты
python cli.py show --limit 10 --region Москва

# Статистика
python cli.py stats --json

# Анализ лота
python cli.py analyze --lot-id 12345
```

## Лицензия

MIT License
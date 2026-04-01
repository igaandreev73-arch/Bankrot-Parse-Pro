# Bankrot Parser Pro

Проект для парсинга и анализа данных о банкротствах с веб-интерфейсом.


## Функциональность

- **Парсинг данных**: Сбор информации о лотах банкротства из различных источников (синтетические данные)
- **Фильтрация при парсинге**: Возможность задать регион, минимальную скидку и лимит записей
- **Анализ лотов**: Оценка ликвидности, рисков и рекомендаций с использованием DeepSeek API
- **Кеширование**: Сохранение результатов анализа в SQLite базе данных
- **Веб-интерфейс**: Полноценный веб-интерфейс с таблицей лотов, графиками и фильтрами
- **Управление базой данных**: Очистка всей базы данных одной кнопкой
- **Экспорт данных**: Выгрузка данных в CSV формате

## Скриншот
![1](https://github.com/user-attachments/assets/0484af52-1705-4a63-9d9a-dc28edffe9cc)


## Структура проекта

```
bankrot-parse-pro/
├── app.py              # FastAPI приложение с REST API
├── parser.py           # Основной модуль парсинга с поддержкой фильтров
├── analyzer.py         # Модуль анализа лотов с DeepSeek API
├── database.py         # Работа с SQLite базой данных
├── cli.py              # Командный интерфейс
├── requirements.txt    # Зависимости Python
├── Dockerfile          # Конфигурация Docker
├── docker-compose.yml  # Docker Compose для развёртывания
├── templates/          # HTML шаблоны (веб-интерфейс)
│   └── index.html
├── static/             # Статические файлы (CSS, JS)
├── .gitignore          # Игнорируемые файлы
├── README.md           # Документация
└── DOCS.md             # Подробная документация
```

## Установка

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
# Создайте файл .env
echo "DEEPSEEK_API_KEY=ваш_ключ_api" > .env
```

4. Инициализируйте базу данных:
```bash
python -c "from database import init_database; init_database()"
```

## Использование

### Запуск веб-интерфейса

1. Запустите FastAPI сервер:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

2. Откройте в браузере: http://localhost:8000

### Веб-интерфейс

- **Таблица лотов**: Просмотр всех записей с фильтрами по региону и скидке
- **Графики**: Визуализация средних скидок по регионам и динамики по дням
- **Топ рекомендации**: Автоматический отбор лотов с высокой скидкой
- **Управление парсером**: Кнопки "Запустить парсер", "Анализ всех новых", "Очистить базу", "Экспорт CSV"

### Парсинг данных с фильтрами

Парсер можно запустить через веб-интерфейс или программно:

```python
from parser import run_parser

# Без фильтров (генерирует 20 случайных записей)
run_parser()

# С фильтрами (только Москва, скидка >=30%, максимум 5 записей)
run_parser(region="Москва", min_discount=30, limit=5)
```

### Анализ лота

```python
from analyzer import analyze_lot

result = analyze_lot(
    lot_id="12345",
    lot_name="Офисное помещение",
    initial_price=15000000.0,
    property_type="Недвижимость",
    region="Москва"
)
print(result)
```

## Конфигурация API

Для работы анализатора требуется API ключ DeepSeek. Получите ключ на [platform.deepseek.com](https://platform.deepseek.com) и добавьте в переменную окружения `DEEPSEEK_API_KEY`.

## Запуск через Docker

### Сборка и запуск контейнера

```bash
docker build -t bankrot-parser-pro .
docker run -p 8000:8000 --env-file .env bankrot-parser-pro
```

### Docker Compose

```bash
docker-compose up -d
```

Приложение будет доступно по адресу http://localhost:8000

## Деплой на Render

Проект готов к деплою на Render.com:

1. Создайте новый Web Service на Render
2. Подключите репозиторий GitHub
3. Укажите следующие настройки:
   - **Build Command**: `docker build -t bankrot-parser-pro .`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**: Добавьте `DEEPSEEK_API_KEY` (если нужен анализ)
4. Нажмите Deploy

## Лицензия

MIT

## Деплой на Render

Проект готов к деплою на Render с использованием SQLite и persistent disk.

1. Создайте новый Web Service на Render
2. Подключите репозиторий GitHub
3. Используйте Dockerfile из проекта
4. Настройте persistent disk для `/data`
5. Установите переменные окружения

## Лицензия

MIT

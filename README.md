# Bankrot Parser Pro

Проект для парсинга и анализа данных о банкротствах.

## Функциональность

- **Парсинг данных**: Сбор информации о лотах банкротства из различных источников
- **Анализ лотов**: Оценка ликвидности, рисков и рекомендаций с использованием DeepSeek API
- **Кеширование**: Сохранение результатов анализа в SQLite базе данных
- **Веб-интерфейс**: REST API для доступа к данным (в разработке)

## Структура проекта

```
bankrot-parse-pro/
├── parser.py          # Основной модуль парсинга
├── analyzer.py        # Модуль анализа лотов с DeepSeek API
├── database.py        # Работа с SQLite базой данных
├── requirements.txt   # Зависимости Python
├── .gitignore         # Игнорируемые файлы
└── README.md          # Документация
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

### Парсинг данных
```python
from parser import run_parser
run_parser()
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

## Деплой на Render

Проект готов к деплою на Render с использованием SQLite и persistent disk.

1. Создайте новый Web Service на Render
2. Подключите репозиторий GitHub
3. Используйте Dockerfile из проекта
4. Настройте persistent disk для `/data`
5. Установите переменные окружения

## Лицензия

MIT
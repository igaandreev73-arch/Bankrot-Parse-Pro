"""
Модуль для работы с SQLite базой данных проекта Bankrot Parser Pro.
Содержит таблицу trades, функции сохранения и выборки данных с защитой от дублирования.
"""

import sqlite3
import pandas as pd
from datetime import datetime, date
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

DB_PATH = "database/bankrot.db"


@contextmanager
def db_connection():
    """Контекстный менеджер для работы с подключением к SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()


def init_database():
    """Инициализация базы данных: создание таблицы и индексов."""
    with db_connection() as conn:
        cursor = conn.cursor()
        
        # Создание таблицы trades
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT NOT NULL,
                lot_name TEXT,
                initial_price REAL,
                discount_percent REAL,
                final_price REAL,
                region TEXT,
                property_type TEXT,
                participants_count INTEGER,
                trade_end_date TEXT,
                parsed_at TEXT NOT NULL,
                UNIQUE(lot_id, DATE(parsed_at))
            )
        """)
        
        # Создание индексов
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_region ON trades (region)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_parsed_at ON trades (parsed_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lot_id ON trades (lot_id)")
        
        logger.info("Database initialized: table 'trades' created with indexes")


def save_trades_to_db(df: pd.DataFrame) -> int:
    """
    Сохраняет DataFrame с лотами в базу данных.
    Защита от дублирования: один lot_id не добавляется дважды за день.
    
    Args:
        df: DataFrame с колонками, соответствующими таблице trades
        
    Returns:
        Количество успешно сохранённых записей
    """
    if df.empty:
        logger.warning("Empty DataFrame provided to save_trades_to_db")
        return 0
    
    # Приводим названия колонок к ожидаемым
    required_columns = [
        'lot_id', 'lot_name', 'initial_price', 'discount_percent', 
        'final_price', 'region', 'property_type', 'participants_count', 
        'trade_end_date'
    ]
    
    # Проверяем наличие необходимых колонок
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            raise ValueError(f"DataFrame must contain column: {col}")
    
    # Добавляем timestamp парсинга
    df = df.copy()
    parsed_at = datetime.now().isoformat()
    df['parsed_at'] = parsed_at
    
    saved_count = 0
    with db_connection() as conn:
        cursor = conn.cursor()
        
        for _, row in df.iterrows():
            try:
                # Проверяем, существует ли уже запись с таким lot_id за сегодня
                today = date.today().isoformat()
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM trades 
                    WHERE lot_id = ? AND DATE(parsed_at) = DATE(?)
                    """,
                    (row['lot_id'], parsed_at)
                )
                exists = cursor.fetchone()[0]
                
                if exists > 0:
                    logger.debug(f"Lot {row['lot_id']} already exists today, skipping")
                    continue
                
                # Вставляем новую запись
                cursor.execute(
                    """
                    INSERT INTO trades (
                        lot_id, lot_name, initial_price, discount_percent,
                        final_price, region, property_type, participants_count,
                        trade_end_date, parsed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row['lot_id'], row['lot_name'], row['initial_price'],
                        row['discount_percent'], row['final_price'], row['region'],
                        row['property_type'], row['participants_count'],
                        row['trade_end_date'], parsed_at
                    )
                )
                saved_count += 1
                
            except sqlite3.IntegrityError as e:
                logger.warning(f"Integrity error for lot {row['lot_id']}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error saving lot {row['lot_id']}: {e}")
                continue
    
    logger.info(f"Saved {saved_count} new trades to database")
    return saved_count


def get_trades_from_db(
    limit: int = 100,
    offset: int = 0,
    region: Optional[str] = None,
    min_discount: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Получает лоты из базы данных с фильтрацией.
    
    Args:
        limit: Максимальное количество записей
        offset: Смещение для пагинации
        region: Фильтр по региону (регион содержит подстроку)
        min_discount: Минимальный процент скидки
        
    Returns:
        Список словарей с данными лотов
    """
    query = "SELECT * FROM trades WHERE 1=1"
    params = []
    
    if region:
        query += " AND region LIKE ?"
        params.append(f"%{region}%")
    
    if min_discount is not None:
        query += " AND discount_percent >= ?"
        params.append(min_discount)
    
    query += " ORDER BY parsed_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
    
    # Преобразуем sqlite3.Row в словари
    result = [dict(row) for row in rows]
    return result


def get_last_parse_date() -> Optional[str]:
    """
    Возвращает дату последнего парсинга (самую свежую parsed_at).
    
    Returns:
        Строка с датой в формате ISO или None если данных нет
    """
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(parsed_at) FROM trades")
        result = cursor.fetchone()[0]
    
    return result


def get_trades_count() -> int:
    """Возвращает общее количество записей в таблице trades."""
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM trades")
        result = cursor.fetchone()[0]
    
    return result


def cleanup_old_data(days_to_keep: int = 30):
    """
    Удаляет старые данные, оставляя только указанное количество дней.
    
    Args:
        days_to_keep: Количество дней для хранения данных
    """
    cutoff_date = (datetime.now() - pd.Timedelta(days=days_to_keep)).isoformat()
    
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM trades WHERE parsed_at < ?", (cutoff_date,))
        deleted = cursor.rowcount
    
    logger.info(f"Cleaned up {deleted} old records (older than {days_to_keep} days)")
    return deleted


# Инициализация базы при импорте модуля
if __name__ != "__main__":
    import os
    os.makedirs("database", exist_ok=True)
    init_database()
    logger.info("Database module initialized")


if __name__ == "__main__":
    # Тестирование модуля
    import logging
    logging.basicConfig(level=logging.INFO)
    
    init_database()
    
    # Создаем тестовый DataFrame
    test_data = pd.DataFrame([{
        'lot_id': 'TEST-001',
        'lot_name': 'Тестовый лот',
        'initial_price': 1000000.0,
        'discount_percent': 15.5,
        'final_price': 845000.0,
        'region': 'Московская область',
        'property_type': 'Недвижимость',
        'participants_count': 3,
        'trade_end_date': '2024-12-31'
    }])
    
    saved = save_trades_to_db(test_data)
    print(f"Saved {saved} test records")
    
    trades = get_trades_from_db(limit=5)
    print(f"Retrieved {len(trades)} trades")
    
    last_date = get_last_parse_date()
    print(f"Last parse date: {last_date}")
    
    count = get_trades_count()
    print(f"Total records in database: {count}")
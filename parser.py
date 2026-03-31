"""
Модуль парсера данных о банкротствах для проекта Bankrot Parser Pro.
Содержит функцию run_parser() для запуска процесса парсинга.
"""

import pandas as pd
from datetime import datetime, date
from typing import Optional
import logging

from database import get_last_parse_date, save_trades_to_db, init_database

logger = logging.getLogger(__name__)


def parse_source() -> pd.DataFrame:
    """
    Заглушка для реального парсинга.
    В реальном проекте здесь будет код для получения данных с сайта.
    
    Returns:
        DataFrame с данными о лотах
    """
    # Пример данных для демонстрации
    data = {
        'lot_id': ['12345', '67890'],
        'lot_name': ['Лот 1', 'Лот 2'],
        'initial_price': [1000000.0, 2000000.0],
        'discount_percent': [15.5, 20.0],
        'final_price': [845000.0, 1600000.0],
        'region': ['Москва', 'Санкт-Петербург'],
        'property_type': ['Недвижимость', 'Транспорт'],
        'participants_count': [5, 3],
        'trade_end_date': ['2026-04-15', '2026-04-20']
    }
    return pd.DataFrame(data)


def run_parser(force: bool = False) -> None:
    """
    Основная функция запуска парсера.
    Выполняет проверку даты последнего парсинга и запрашивает подтверждение у пользователя.
    
    Args:
        force: Если True, пропускает подтверждение и обновляет данные даже если парсинг уже был сегодня
    """
    # Инициализация базы данных
    init_database()
    
    # Проверяем дату последнего парсинга
    last_parse = get_last_parse_date()
    
    if last_parse:
        last_date = datetime.fromisoformat(last_parse).date()
        today = date.today()
        
        if last_date == today and not force:
            # Парсинг уже был сегодня, но force=False - пропускаем
            print("Парсинг уже был сегодня. Используйте force=True для принудительного обновления.")
            return
    
    print("Запуск парсинга...")
    
    # Получаем данные
    df = parse_source()
    
    if df.empty:
        print("Нет данных для сохранения.")
        return
    
    # Сохраняем в базу данных
    saved_count = save_trades_to_db(df)
    
    # Выводим количество новых записей
    print(f"Сохранено новых записей: {saved_count}")
    
    if saved_count > 0:
        print("Парсинг успешно завершён.")
    else:
        print("Нет новых записей для сохранения.")


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    run_parser()
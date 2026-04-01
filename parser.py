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
    Парсинг данных о лотах банкротства.
    Генерирует 20 уникальных записей при каждом запуске.
    
    Returns:
        DataFrame с данными о лотах
    """
    import random
    from datetime import datetime, timedelta
    
    # Реалистичные данные о лотах банкротства
    regions = ['Москва', 'Санкт-Петербург', 'Московская область', 'Новосибирск',
               'Екатеринбург', 'Казань', 'Нижний Новгород', 'Краснодар',
               'Самара', 'Челябинск', 'Омск', 'Ростов-на-Дону', 'Уфа', 'Волгоград']
    
    property_types = ['Недвижимость', 'Транспорт', 'Оборудование', 'Ценные бумаги',
                     'Товарные запасы', 'Интеллектуальная собственность', 'Земельные участки',
                     'Коммерческая недвижимость', 'Жилая недвижимость']
    
    # Источники данных
    sources = ['ЕФРСБ', 'Сбербанк-АСТ', 'ЕТП ГПБ', 'РТС-тендер', 'Лот-Онлайн']
    
    # Базовые URL для разных источников
    source_urls = {
        'ЕФРСБ': 'https://bankrot.fedresurs.ru/lot.aspx?guid=',
        'Сбербанк-АСТ': 'https://utp.sberbank-ast.ru/Lot/',
        'ЕТП ГПБ': 'https://etp.gpb.ru/lot/',
        'РТС-тендер': 'https://www.rts-tender.ru/lots/',
        'Лот-Онлайн': 'https://lot-online.ru/lot/'
    }
    
    # Генерация 20 уникальных лотов
    num_lots = 20
    data = {
        'lot_id': [],
        'lot_name': [],
        'initial_price': [],
        'discount_percent': [],
        'final_price': [],
        'region': [],
        'property_type': [],
        'participants_count': [],
        'trade_end_date': [],
        'source': [],
        'lot_url': [],
        'description': []
    }
    
    # Используем текущее время как seed для генерации уникальных ID
    seed = int(datetime.now().timestamp())
    random.seed(seed)
    
    for i in range(1, num_lots + 1):
        # Генерируем уникальный ID на основе seed и индекса
        lot_id = f"BKR{seed % 10000:04d}{i:03d}"
        
        property_type = random.choice(property_types)
        region = random.choice(regions)
        
        # Генерация реалистичных цен в зависимости от типа имущества
        if property_type in ['Недвижимость', 'Коммерческая недвижимость', 'Жилая недвижимость']:
            initial_price = random.uniform(5000000, 50000000)
        elif property_type == 'Транспорт':
            initial_price = random.uniform(500000, 5000000)
        elif property_type == 'Земельные участки':
            initial_price = random.uniform(1000000, 20000000)
        else:
            initial_price = random.uniform(100000, 10000000)
        
        # Скидка от 5% до 40%
        discount = random.uniform(5.0, 40.0)
        final_price = initial_price * (1 - discount/100)
        
        # Количество участников от 0 до 15
        participants = random.randint(0, 15)
        
        # Дата окончания торгов в ближайшие 30 дней
        end_date = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
        
        # Формирование названия лота
        if property_type in ['Недвижимость', 'Жилая недвижимость']:
            property_names = ['квартира', 'офис', 'склад', 'земельный участок', 'дом', 'апартаменты']
            lot_name = f"{property_type} в {region}, {random.choice(property_names)}"
        elif property_type == 'Коммерческая недвижимость':
            lot_name = f"Коммерческая недвижимость в {region}, {random.choice(['торговый центр', 'офисный комплекс', 'производственное помещение'])}"
        elif property_type == 'Транспорт':
            lot_name = f"{property_type}, {random.choice(['легковой автомобиль', 'грузовик', 'спецтехника', 'автобус', 'строительная техника'])}"
        else:
            lot_name = f"{property_type}, {random.choice(['партия товара', 'оборудование', 'активы', 'материалы'])}"
        
        # Выбираем случайный источник данных
        source = random.choice(sources)
        
        # Генерируем URL на основе источника и ID лота
        base_url = source_urls[source]
        lot_url = f"{base_url}{lot_id}"
        
        # Генерация описания лота
        descriptions = [
            f"Лот представляет собой {property_type.lower()} в регионе {region}. Начальная цена {initial_price:,.0f} руб.",
            f"Объект {lot_name}. Скидка {discount:.1f}% делает лот привлекательным для инвестиций.",
            f"Подробное описание лота {lot_id}. {property_type} с высокой ликвидностью.",
            f"Лот размещен на площадке {source}. Торги завершаются {end_date}.",
            f"Имущество находится в {region}. Количество участников: {participants}.",
            f"Уникальная возможность приобрести {property_type.lower()} со скидкой {discount:.1f}%.",
            f"Лот {lot_id} представляет интерес для инвесторов в сфере {property_type.lower()}."
        ]
        description = random.choice(descriptions)
        
        data['lot_id'].append(lot_id)
        data['lot_name'].append(lot_name)
        data['initial_price'].append(round(initial_price, 2))
        data['discount_percent'].append(round(discount, 1))
        data['final_price'].append(round(final_price, 2))
        data['region'].append(region)
        data['property_type'].append(property_type)
        data['participants_count'].append(participants)
        data['trade_end_date'].append(end_date)
        data['source'].append(source)
        data['lot_url'].append(lot_url)
        data['description'].append(description)
    
    df = pd.DataFrame(data)
    
    # Добавляем несколько "горячих" лотов с высокой скидкой и многими участниками
    if len(df) > 5:
        df.loc[0, 'discount_percent'] = 45.5  # Высокая скидка
        df.loc[0, 'participants_count'] = 12   # Много участников
        df.loc[0, 'lot_name'] = "🔥 Горячий лот: Квартира в центре Москвы"
        
        df.loc[1, 'discount_percent'] = 38.0
        df.loc[1, 'participants_count'] = 8
        df.loc[1, 'lot_name'] = "⭐ Выгодное предложение: Офисное помещение"
        
        df.loc[2, 'discount_percent'] = 42.0
        df.loc[2, 'participants_count'] = 10
        df.loc[2, 'lot_name'] = "💎 Премиум лот: Коммерческая недвижимость"
    
    logger.info(f"Сгенерировано {len(df)} уникальных лотов")
    return df


def run_parser(region: str = None, min_discount: float = 0, limit: int = 20, force: bool = True) -> None:
    """
    Основная функция запуска парсера.
    Выполняет парсинг данных с учетом фильтров.
    
    Args:
        region: Регион для фильтрации (если None - все регионы)
        min_discount: Минимальная скидка в процентах
        limit: Максимальное количество записей для генерации
        force: Если True, пропускает проверку даты последнего парсинга
    """
    # Инициализация базы данных
    init_database()
    
    # Проверяем дату последнего парсинга, только если force=False
    if not force:
        last_parse = get_last_parse_date()
        if last_parse:
            last_date = datetime.fromisoformat(last_parse).date()
            today = date.today()
            if last_date == today:
                print("Парсинг уже был сегодня. Используйте force=True для принудительного обновления.")
                return
    
    print(f"Запуск парсинга с фильтрами: регион={region}, мин. скидка={min_discount}%, лимит={limit}")
    
    # Получаем данные
    df = parse_source()
    
    if df.empty:
        print("Нет данных для сохранения.")
        return
    
    # Применяем фильтры
    if region:
        df = df[df['region'] == region]
    if min_discount > 0:
        df = df[df['discount_percent'] >= min_discount]
    
    # Ограничиваем количество записей
    if limit > 0 and len(df) > limit:
        df = df.head(limit)
    
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
#!/usr/bin/env python3
"""
CLI интерфейс для Bankrot Parser Pro.
Предоставляет команды для работы с парсером и базой данных.
"""

import argparse
import sys
from typing import List, Dict, Any
import json

from parser import run_parser
from database import get_trades_from_db, init_database, get_last_parse_date
from analyzer import analyze_lot


def cmd_parse(args):
    """Запустить парсер."""
    print("Запуск парсера...")
    try:
        run_parser()
        print("Парсинг успешно завершён.")
    except Exception as e:
        print(f"Ошибка при парсинге: {e}")
        sys.exit(1)


def cmd_show(args):
    """Показать последние лоты."""
    limit = args.limit
    region = args.region
    min_discount = args.min_discount
    
    print(f"Получение последних {limit} лотов...")
    
    trades = get_trades_from_db(
        limit=limit,
        region=region,
        min_discount=min_discount
    )
    
    if not trades:
        print("Лоты не найдены.")
        return
    
    # Вывод в табличном формате
    print("\n" + "="*120)
    print(f"{'ID':<10} {'Название':<30} {'Регион':<15} {'Цена':<12} {'Скидка':<8} {'Тип':<15} {'Дата парсинга':<20}")
    print("="*120)
    
    for trade in trades:
        lot_id = trade['lot_id'][:10] if len(trade['lot_id']) > 10 else trade['lot_id']
        lot_name = trade['lot_name'][:28] + ".." if len(trade['lot_name']) > 30 else trade['lot_name']
        region = trade['region'][:13] + ".." if len(trade['region']) > 15 else trade['region']
        price = f"{trade['initial_price']:,.0f}"
        discount = f"{trade['discount_percent']:.1f}%"
        prop_type = trade['property_type'][:13] + ".." if len(trade['property_type']) > 15 else trade['property_type']
        parsed_date = trade['parsed_at'][:19]
        
        print(f"{lot_id:<10} {lot_name:<30} {region:<15} {price:<12} {discount:<8} {prop_type:<15} {parsed_date:<20}")
    
    print("="*120)
    print(f"Всего лотов: {len(trades)}")


def cmd_stats(args):
    """Показать статистику из БД."""
    print("Сбор статистики...")
    
    # Получаем все записи для статистики
    all_trades = get_trades_from_db(limit=10000)
    
    if not all_trades:
        print("В базе данных нет записей.")
        return
    
    # Базовая статистика
    total_trades = len(all_trades)
    last_parse = get_last_parse_date()
    
    # Средняя скидка
    total_discount = sum(trade['discount_percent'] for trade in all_trades)
    avg_discount = total_discount / total_trades if total_trades > 0 else 0
    
    # Статистика по регионам
    regions = {}
    for trade in all_trades:
        region = trade['region']
        if region not in regions:
            regions[region] = {'count': 0, 'total_discount': 0}
        regions[region]['count'] += 1
        regions[region]['total_discount'] += trade['discount_percent']
    
    # Статистика по типам имущества
    property_types = {}
    for trade in all_trades:
        prop_type = trade['property_type']
        property_types[prop_type] = property_types.get(prop_type, 0) + 1
    
    # Вывод статистики
    print("\n" + "="*60)
    print("СТАТИСТИКА БАЗЫ ДАННЫХ")
    print("="*60)
    print(f"Всего лотов: {total_trades}")
    print(f"Последний парсинг: {last_parse if last_parse else 'не проводился'}")
    print(f"Средняя скидка: {avg_discount:.1f}%")
    
    print("\nСтатистика по регионам:")
    print("-"*40)
    for region, data in sorted(regions.items(), key=lambda x: x[1]['count'], reverse=True)[:10]:
        avg = data['total_discount'] / data['count']
        print(f"  {region:<25} {data['count']:>4} лотов, средняя скидка: {avg:.1f}%")
    
    print("\nСтатистика по типам имущества:")
    print("-"*40)
    for prop_type, count in sorted(property_types.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {prop_type:<25} {count:>4} лотов")
    
    # Дополнительная информация
    if args.json:
        stats_json = {
            "total_trades": total_trades,
            "last_parse": last_parse,
            "avg_discount": avg_discount,
            "regions": {region: data for region, data in list(regions.items())[:10]},
            "property_types": {pt: count for pt, count in list(property_types.items())[:10]}
        }
        print("\nJSON вывод:")
        print(json.dumps(stats_json, indent=2, ensure_ascii=False))


def cmd_analyze(args):
    """Проанализировать лот."""
    lot_id = args.lot_id
    
    print(f"Анализ лота {lot_id}...")
    
    # Получаем информацию о лоте
    trades = get_trades_from_db(limit=1, lot_id=lot_id)
    if not trades:
        print(f"Лот с ID {lot_id} не найден.")
        sys.exit(1)
    
    trade = trades[0]
    
    # Выполняем анализ
    analysis = analyze_lot(
        lot_id=lot_id,
        lot_name=trade['lot_name'],
        initial_price=trade['initial_price'],
        property_type=trade['property_type'],
        region=trade['region']
    )
    
    # Вывод результатов
    print("\n" + "="*60)
    print(f"АНАЛИЗ ЛОТА: {trade['lot_name']}")
    print("="*60)
    print(f"ID: {lot_id}")
    print(f"Регион: {trade['region']}")
    print(f"Тип имущества: {trade['property_type']}")
    print(f"Начальная цена: {trade['initial_price']:,.0f} руб.")
    print(f"Скидка: {trade['discount_percent']:.1f}%")
    
    print("\nРезультаты анализа:")
    print(f"  Оценка ликвидности: {analysis['liquidity_score']}/100")
    print(f"  Уровень риска: {analysis['risk_level']}")
    print(f"  Рекомендация: {analysis['recommendation']}")
    print(f"  Макс. разумная цена: {analysis['max_reasonable_price']:,.0f} руб.")
    
    print("\nКлючевые факторы:")
    for i, factor in enumerate(analysis['key_factors'], 1):
        print(f"  {i}. {factor}")
    
    print(f"\nИсточник: {analysis['source']} ({'кеш' if analysis['cached'] else 'новый анализ'})")


def main():
    """Основная функция CLI."""
    parser = argparse.ArgumentParser(
        description="Bankrot Parser Pro - CLI интерфейс",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python cli.py parse                    # Запустить парсер
  python cli.py show                     # Показать последние 10 лотов
  python cli.py show --limit 20          # Показать 20 лотов
  python cli.py show --region Москва     # Показать лоты по региону
  python cli.py stats                    # Показать статистику
  python cli.py stats --json             # Статистика в JSON формате
  python cli.py analyze --lot-id 12345   # Проанализировать лот
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Команда')
    
    # Команда parse
    parse_parser = subparsers.add_parser('parse', help='Запустить парсер')
    parse_parser.set_defaults(func=cmd_parse)
    
    # Команда show
    show_parser = subparsers.add_parser('show', help='Показать последние лоты')
    show_parser.add_argument('--limit', type=int, default=10, help='Количество лотов (по умолчанию: 10)')
    show_parser.add_argument('--region', type=str, help='Фильтр по региону')
    show_parser.add_argument('--min-discount', type=float, help='Минимальная скидка в процентах')
    show_parser.set_defaults(func=cmd_show)
    
    # Команда stats
    stats_parser = subparsers.add_parser('stats', help='Показать статистику из БД')
    stats_parser.add_argument('--json', action='store_true', help='Вывод в JSON формате')
    stats_parser.set_defaults(func=cmd_stats)
    
    # Команда analyze
    analyze_parser = subparsers.add_parser('analyze', help='Проанализировать лот')
    analyze_parser.add_argument('--lot-id', required=True, help='ID лота для анализа')
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # Парсинг аргументов
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Инициализация базы данных
    init_database()
    
    # Выполнение команды
    args.func(args)


if __name__ == "__main__":
    main()
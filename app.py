"""
FastAPI приложение для Bankrot Parser Pro.
Предоставляет REST API и веб-интерфейс для работы с данными о банкротствах.
"""

import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from database import (
    get_trades_from_db,
    get_last_parse_date,
    init_database,
    cleanup_old_records
)
from analyzer import analyze_lot

app = FastAPI(
    title="Bankrot Parser Pro API",
    description="API для парсинга и анализа данных о банкротствах",
    version="1.0.0"
)

# Создаём папки для статики и шаблонов
import os
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Инициализация базы данных при запуске
@app.on_event("startup")
def startup_event():
    init_database()
    # Очистка старых записей (старше 30 дней)
    # Временно отключено для отладки
    # cleanup_old_records(days_to_keep=30)


# Модели запросов/ответов
class BatchAnalyzeRequest(BaseModel):
    lot_ids: List[str]


class TradeResponse(BaseModel):
    id: int
    lot_id: str
    lot_name: str
    initial_price: float
    discount_percent: float
    final_price: float
    region: str
    property_type: str
    participants_count: int
    trade_end_date: str
    parsed_at: str
    parsed_date: str = ""
    source: str = ""
    lot_url: str = ""
    description: str = ""


class AnalysisResponse(BaseModel):
    liquidity_score: int
    risk_level: str
    recommendation: str
    max_reasonable_price: float
    key_factors: List[str]
    cached: bool
    source: str


class StatsResponse(BaseModel):
    total_trades: int
    avg_discount_by_region: Dict[str, float]
    trades_by_day: Dict[str, int]


# Эндпоинты API
@app.get("/api/trades", response_model=List[TradeResponse], response_model_exclude_none=False)
async def get_trades(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    region: Optional[str] = None,
    min_discount: Optional[float] = Query(None, ge=0, le=100)
):
    """
    Получить список лотов с фильтрацией.
    """
    trades = get_trades_from_db(
        limit=limit,
        offset=offset,
        region=region,
        min_discount=min_discount
    )
    return trades


@app.get("/api/analyze/{lot_id}", response_model=AnalysisResponse)
async def analyze_single(lot_id: str):
    """
    Получить анализ конкретного лота.
    """
    # Сначала получаем информацию о лоте
    trades = get_trades_from_db(limit=1, lot_id=lot_id)
    if not trades:
        raise HTTPException(status_code=404, detail="Лот не найден")
    
    trade = trades[0]
    
    # Выполняем анализ
    analysis = analyze_lot(
        lot_id=lot_id,
        lot_name=trade['lot_name'],
        initial_price=trade['initial_price'],
        property_type=trade['property_type'],
        region=trade['region']
    )
    
    return analysis


@app.post("/api/analyze/batch")
async def analyze_batch(request: BatchAnalyzeRequest):
    """
    Анализ нескольких лотов.
    """
    results = []
    
    for lot_id in request.lot_ids:
        trades = get_trades_from_db(limit=1, lot_id=lot_id)
        if trades:
            trade = trades[0]
            analysis = analyze_lot(
                lot_id=lot_id,
                lot_name=trade['lot_name'],
                initial_price=trade['initial_price'],
                property_type=trade['property_type'],
                region=trade['region']
            )
            results.append({
                "lot_id": lot_id,
                "analysis": analysis
            })
        else:
            results.append({
                "lot_id": lot_id,
                "error": "Лот не найден"
            })
    
    return {"results": results}


@app.get("/api/stats/advanced", response_model=StatsResponse)
async def get_advanced_stats():
    """
    Расширенная статистика по данным.
    """
    # Получаем все записи для статистики
    all_trades = get_trades_from_db(limit=10000)
    
    # Общее количество
    total_trades = len(all_trades)
    
    # Средняя скидка по регионам
    region_discounts = {}
    region_counts = {}
    
    for trade in all_trades:
        region = trade['region']
        discount = trade['discount_percent']
        
        if region not in region_discounts:
            region_discounts[region] = 0
            region_counts[region] = 0
        
        region_discounts[region] += discount
        region_counts[region] += 1
    
    avg_discount_by_region = {
        region: region_discounts[region] / region_counts[region]
        for region in region_discounts
    }
    
    # Количество лотов по дням
    trades_by_day = {}
    for trade in all_trades:
        parsed_date = trade['parsed_at'][:10]  # YYYY-MM-DD
        trades_by_day[parsed_date] = trades_by_day.get(parsed_date, 0) + 1
    
    return StatsResponse(
        total_trades=total_trades,
        avg_discount_by_region=avg_discount_by_region,
        trades_by_day=trades_by_day
    )


@app.get("/api/regions")
async def get_regions():
    """
    Получить список уникальных регионов.
    """
    all_trades = get_trades_from_db(limit=10000)
    regions = set(trade['region'] for trade in all_trades if trade['region'])
    return {"regions": sorted(list(regions))}


@app.get("/api/export")
async def export_csv(
    region: Optional[str] = None,
    min_discount: Optional[float] = None
):
    """
    Экспорт данных в CSV.
    """
    # Получаем данные с фильтрами
    trades = get_trades_from_db(
        limit=10000,
        region=region,
        min_discount=min_discount
    )
    
    if not trades:
        raise HTTPException(status_code=404, detail="Нет данных для экспорта")
    
    # Создаём CSV в памяти
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=trades[0].keys())
    writer.writeheader()
    writer.writerows(trades)
    
    # Возвращаем файл
    response = StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=trades_export.csv"
        }
    )
    
    return response


@app.get("/api/run-parser")
async def run_parser(force: bool = False):
    """
    Запустить парсер вручную.
    
    Args:
        force: Принудительно обновить данные, даже если парсинг уже был сегодня
    """
    try:
        from parser import run_parser as run_parser_func
        run_parser_func(force=force)
        return {"status": "success", "message": "Парсер успешно запущен"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Веб-интерфейс
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Главная страница веб-интерфейса.
    """
    with open("templates/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
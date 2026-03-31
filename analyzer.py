"""
Модуль анализа лотов для проекта Bankrot Parser Pro.
Использует DeepSeek API для оценки лотов с кешированием результатов.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import requests

from database import get_cached_analysis, save_analysis_to_cache

logger = logging.getLogger(__name__)

# Конфигурация API (в реальном проекте вынести в переменные окружения)
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY = ""  # Должен быть установлен в переменных окружения


def call_deepseek_api(prompt: str) -> Optional[Dict[str, Any]]:
    """
    Вызывает DeepSeek API с заданным промптом.
    
    Args:
        prompt: Текст промпта
        
    Returns:
        Словарь с ответом API или None при ошибке
    """
    if not DEEPSEEK_API_KEY:
        logger.warning("DeepSeek API key not configured")
        return None
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ты финансовый аналитик, специализирующийся на оценке лотов банкротства. Отвечай строго в формате JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 500
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Извлекаем JSON из ответа (может быть обёрнут в markdown)
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            logger.error(f"Failed to extract JSON from API response: {content}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Failed to parse API response: {e}")
        return None


def generate_fallback_analysis(
    lot_name: str, 
    property_type: str, 
    region: str, 
    initial_price: float
) -> Dict[str, Any]:
    """
    Генерирует fallback-анализ при недоступности API.
    
    Args:
        Параметры лота
        
    Returns:
        Стандартный анализ
    """
    # Простая эвристика для fallback
    liquidity_score = 50  # средняя ликвидность
    risk_level = "средний"
    recommendation = "стоит рассмотреть"
    max_reasonable_price = initial_price * 0.8  # 80% от начальной цены
    
    # Факторы в зависимости от типа имущества и региона
    key_factors = []
    
    if "недвижимость" in property_type.lower():
        key_factors.append("Недвижимость имеет стабильный спрос")
        liquidity_score = 60
    elif "транспорт" in property_type.lower():
        key_factors.append("Транспортные средства быстро теряют стоимость")
        risk_level = "высокий"
        liquidity_score = 40
    
    if "москва" in region.lower() or "санкт-петербург" in region.lower():
        key_factors.append("Столичный регион повышает ликвидность")
        liquidity_score += 10
        risk_level = "низкий"
    else:
        key_factors.append("Региональный рынок может быть менее ликвиден")
    
    if initial_price > 10000000:
        key_factors.append("Высокая цена снижает круг покупателей")
        liquidity_score -= 10
        risk_level = "высокий"
    
    # Ограничиваем score в диапазоне 0-100
    liquidity_score = max(0, min(100, liquidity_score))
    
    # Корректируем рекомендацию на основе score
    if liquidity_score >= 70:
        recommendation = "стоит участвовать"
    elif liquidity_score <= 30:
        recommendation = "не рекомендуется"
    
    return {
        "liquidity_score": liquidity_score,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "max_reasonable_price": max_reasonable_price,
        "key_factors": key_factors[:3]  # максимум 3 фактора
    }


def analyze_lot(
    lot_id: str,
    lot_name: str,
    initial_price: float,
    property_type: str,
    region: str
) -> Dict[str, Any]:
    """
    Основная функция анализа лота.
    
    Шаги:
    1. Проверяет кеш в таблице analysis_cache
    2. Если есть — возвращает из кеша
    3. Если нет — вызывает DeepSeek API
    4. Сохраняет результат в кеш
    5. Обрабатывает ошибки (fallback-ответ)
    
    Args:
        lot_id: Уникальный идентификатор лота
        lot_name: Название лота
        initial_price: Начальная цена
        property_type: Тип имущества
        region: Регион
        
    Returns:
        Словарь с результатами анализа:
        {
            "liquidity_score": 0-100,
            "risk_level": "низкий"/"средний"/"высокий",
            "recommendation": "стоит участвовать"/"стоит рассмотреть"/"не рекомендуется",
            "max_reasonable_price": число,
            "key_factors": ["фактор1", "фактор2", "фактор3"],
            "cached": True/False,
            "source": "cache"/"api"/"fallback"
        }
    """
    logger.info(f"Analyzing lot {lot_id}: {lot_name}")
    
    # 1. Проверка кеша
    cached = get_cached_analysis(lot_id)
    if cached:
        logger.info(f"Cache hit for lot {lot_id}")
        return {
            **cached,
            "cached": True,
            "source": "cache"
        }
    
    logger.info(f"Cache miss for lot {lot_id}, calling API")
    
    # 2. Подготовка промпта для API
    prompt = f"""
Оцени лот банкротства:
Название: {lot_name}
Тип имущества: {property_type}
Регион: {region}
Начальная цена: {initial_price:,.2f} руб.

Верни ответ в формате JSON со следующими полями:
- liquidity_score (целое число от 0 до 100, где 100 максимальная ликвидность)
- risk_level (строка: "низкий", "средний" или "высокий")
- recommendation (строка: "стоит участвовать", "стоит рассмотреть" или "не рекомендуется")
- max_reasonable_price (число, максимальная разумная цена для участия в торгах)
- key_factors (массив из 3 строк, ключевые факторы влияющие на оценку)

Будь объективным и учитывай специфику рынка банкротства.
"""
    
    # 3. Вызов API
    api_result = call_deepseek_api(prompt)
    
    if api_result:
        # Валидация результата API
        try:
            liquidity_score = int(api_result.get("liquidity_score", 50))
            risk_level = api_result.get("risk_level", "средний")
            recommendation = api_result.get("recommendation", "стоит рассмотреть")
            max_reasonable_price = float(api_result.get("max_reasonable_price", initial_price * 0.8))
            key_factors = api_result.get("key_factors", [])
            
            # Нормализация значений
            liquidity_score = max(0, min(100, liquidity_score))
            risk_level = risk_level.lower()
            if risk_level not in ["низкий", "средний", "высокий"]:
                risk_level = "средний"
            
            if recommendation not in ["стоит участвовать", "стоит рассмотреть", "не рекомендуется"]:
                recommendation = "стоит рассмотреть"
            
            # Ограничиваем количество факторов
            if isinstance(key_factors, list):
                key_factors = key_factors[:3]
            else:
                key_factors = []
            
            # 4. Сохранение в кеш
            save_analysis_to_cache(
                lot_id=lot_id,
                lot_name=lot_name,
                property_type=property_type,
                region=region,
                initial_price=initial_price,
                liquidity_score=liquidity_score,
                risk_level=risk_level,
                recommendation=recommendation,
                max_reasonable_price=max_reasonable_price,
                key_factors=key_factors
            )
            
            logger.info(f"API analysis successful for lot {lot_id}")
            
            return {
                "liquidity_score": liquidity_score,
                "risk_level": risk_level,
                "recommendation": recommendation,
                "max_reasonable_price": max_reasonable_price,
                "key_factors": key_factors,
                "cached": False,
                "source": "api"
            }
            
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid API response format: {e}, using fallback")
    
    # 5. Fallback-анализ при ошибках
    logger.info(f"Using fallback analysis for lot {lot_id}")
    fallback_result = generate_fallback_analysis(lot_name, property_type, region, initial_price)
    
    # Сохраняем fallback в кеш, чтобы не вызывать API повторно
    save_analysis_to_cache(
        lot_id=lot_id,
        lot_name=lot_name,
        property_type=property_type,
        region=region,
        initial_price=initial_price,
        liquidity_score=fallback_result["liquidity_score"],
        risk_level=fallback_result["risk_level"],
        recommendation=fallback_result["recommendation"],
        max_reasonable_price=fallback_result["max_reasonable_price"],
        key_factors=fallback_result["key_factors"]
    )
    
    return {
        **fallback_result,
        "cached": False,
        "source": "fallback"
    }


if __name__ == "__main__":
    # Тестирование модуля
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Тестовый вызов
    result = analyze_lot(
        lot_id="TEST-001",
        lot_name="Офисное помещение в бизнес-центре",
        initial_price=15000000.0,
        property_type="Недвижимость",
        region="Москва"
    )
    
    print("Результат анализа:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
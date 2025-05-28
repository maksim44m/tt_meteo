from datetime import datetime
from typing import Optional, List

from fastapi import HTTPException
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import db
from app.models.weather import City, WeatherForecast, WeatherData

from app.log_conf import logging


logger = logging.getLogger(__name__)


async def get_city_coordinates(
    city_name: str, limit: int = 5, session: AsyncSession = None
) -> List[City]:
    """Получение координат города по названию"""
    # Поиск города в базе данных
    if session:
        db_city = await db.find_city_by_name(city_name, session)
        if db_city:
            return [City(id=db_city.city_id,
                         name=db_city.name,
                         latitude=db_city.latitude,
                         longitude=db_city.longitude,
                         country=db_city.country,
                         admin1=db_city.admin1)]

    # Если город не найден в БД, запрашиваем API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city_name,
                        "count": limit,
                        "language": "ru",
                        "format": "json"}
            )
            response.raise_for_status()
            data = response.json()

            if "results" not in data:
                return []

            cities = [City(id=item.get("id"),
                           name=item.get("name"),
                           latitude=item.get("latitude"),
                           longitude=item.get("longitude"),
                           country=item.get("country"),
                           admin1=item.get("admin1"))
                      for item in data["results"]]

            # Сохраняем найденные города в БД
            if session and cities:
                for city_data in data["results"]:
                    await db.save_city(city_data, session)

            return cities
    except httpx.HTTPError as e:
        logger.error(f"Ошибка при получении координат города: {e}")
        raise HTTPException(
            status_code=503,
            detail="Не удалось получить данные о координатах города. API недоступен."
        )


async def get_weather_forecast(
    city: City, forecast_days: int = 1
) -> Optional[WeatherForecast]:
    """Получение прогноза погоды по координатам"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={"latitude": city.latitude,
                        "longitude": city.longitude,
                        "hourly": "temperature_2m",
                        "forecast_days": forecast_days,
                        "format": "json",
                        "timeformat": "unixtime"}
            )
            response.raise_for_status()
            data = response.json()

            if "hourly" not in data:
                return None

            # Создаем объект прогноза погоды
            weather_data = WeatherData(
                time=data["hourly"]["time"],
                temperature_2m=data["hourly"]["temperature_2m"]
            )

            return WeatherForecast(
                city=city,
                hourly=weather_data,
                hourly_units=data["hourly_units"]
            )
    except httpx.HTTPError as e:
        logger.error(f"Ошибка при получении прогноза погоды: {e}")
        raise HTTPException(
            status_code=503,
            detail="Не удалось получить данные о координатах города. API недоступен."
        )


async def forecast_handler(
        city: str, user_id: str, session: AsyncSession
    ) -> dict:
    """Обработчик прогноза погоды"""

    # Получаем координаты города
    cities = await get_city_coordinates(city, limit=1, session=session)
    city_info = cities[0]

    # Получаем прогноз погоды по координатам
    forecast = await get_weather_forecast(city_info)

    # Добавляем поиск в историю
    await db.add_search_history(user_id, city_info.name, session)

    # Форматируем данные для отображения
    formatted_data = []
    for i in range(len(forecast.hourly.time)):
        timestamp = forecast.hourly.time[i]
        if timestamp < int(datetime.now().timestamp()):
            continue
        time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M')
        temp = forecast.hourly.temperature_2m[i]
        formatted_data.append({
            "time": time_str,
            "temperature": temp,
            "unit": forecast.hourly_units.get("temperature_2m", "°C")
        })

    return {"city": forecast.city, "forecast": formatted_data}

from fastapi import APIRouter, Cookie, Response, Query, Depends
from typing import Dict, List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import services
from app.db.base import db
from app.models.weather import City

router = APIRouter()

@router.get("/search")
async def search_city(
    q: str = Query(..., min_length=2, description="Название города"),
    session: AsyncSession = Depends(db.get_session)
) -> Dict[str, List[City]]:
    """Поиск города по названию (для автодополнения)"""
    cities = await services.get_city_coordinates(q, session=session)
    return {"cities": cities}

@router.get("/forecast")
async def get_forecast(
    city: str = Query(..., description="Название города"),
    user_id: Optional[str] = Cookie(None),
    response: Response = None,
    session: AsyncSession = Depends(db.get_session)
):
    """Получение прогноза погоды для города"""
    # Если пользователь не имеет ID
    if not user_id:
        user_id = str(uuid.uuid4())
        response.set_cookie(key="user_id", value=user_id, max_age=3600*24*30)
    
    return await services.forecast_handler(city, user_id, session)

@router.get("/history")
async def get_history(
    user_id: Optional[str] = Cookie(None), 
    session: AsyncSession = Depends(db.get_session)
):
    """Получение истории поиска для пользователя"""
    if not user_id:
        return {"history": []}
    
    history = await db.get_user_history(user_id, session)
    return {"history": history}

@router.get("/stats")
async def get_statistics(
    session: AsyncSession = Depends(db.get_session)
):
    """Получение статистики поиска городов"""
    return await db.get_city_stats(session)

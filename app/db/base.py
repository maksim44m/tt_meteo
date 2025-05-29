import os
import time
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)

from app.db.models import Base, SearchHistoryDB, CityDB


DATABASE_URL = os.getenv(
    'DATABASE_URL', 'postgresql+asyncpg://postgres:postgres@localhost:5432/weather_db')


class DB:
    def __init__(self):
        self.engine = create_async_engine(os.getenv('db_url', DATABASE_URL),
                                          echo=True,
                                          future=True)
        self.Session = async_sessionmaker(bind=self.engine,
                                          expire_on_commit=False)  # данными можно пользоваться после комита

        self.all_tables = Base.metadata.tables

    async def get_session(self):
        async with self.Session() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise e

    async def add_search_history(
            self, 
            user_id: str, 
            city_name: str, 
            session=None
        ):
        """Добавление записи в историю поиска"""
        history_entry = SearchHistoryDB(
            user_id=user_id,
            city_name=city_name,
            timestamp=int(time.time())
        )
        session.add(history_entry)
        await session.commit()
        await session.refresh(history_entry)
        return history_entry

    async def get_user_history(
            self, user_id: str, session: AsyncSession
        ) -> List[str]:
        """Получение истории поиска для пользователя"""
        query = (
            select(SearchHistoryDB.city_name)
            .filter(SearchHistoryDB.user_id == user_id)
            .order_by(SearchHistoryDB.timestamp.desc())
        )

        result = await session.execute(query)
        history_query = result.all()

        # Извлечение уникальных названий городов с сохранением порядка
        unique_cities = []
        seen = set()
        for item in history_query:
            if item[0] not in seen:
                seen.add(item[0])
                unique_cities.append(item[0])

        return unique_cities

    async def get_city_stats(
            self, session: AsyncSession
        ) -> List[Dict[str, int]]:
        """Получение статистики поиска городов"""
        query = (
            select(
                SearchHistoryDB.city_name,
                func.count(SearchHistoryDB.id).label('count')
            )
            .group_by(SearchHistoryDB.city_name)
        )

        result = await session.execute(query)
        stats_query = result.all()

        stats = {city: count for city, count in stats_query}

        # Сортировка города по частоте запросов (по убыванию)
        return [{"city": city, "count": stats[city]} 
                for city in sorted(stats, key=stats.get, reverse=True)]

        
    async def find_city_by_name(
            self, city_name: str, session: AsyncSession
        ) -> Optional[CityDB]:
        """Поиск города в базе данных по имени"""
        query = select(CityDB).filter(func.lower(CityDB.name) == func.lower(city_name))
        result = await session.execute(query)
        city = result.scalars().first()
        return city
        
    async def save_city(
            self, city_data: dict, session: AsyncSession
        ) -> CityDB:
        """Сохранение города в базу данных"""
        # Проверка существования города с таким же city_id
        city_id = city_data.get('id')
        if city_id:
            query = select(CityDB).filter(CityDB.city_id == city_id)
            result = await session.execute(query)
            existing_city = result.scalars().first()
            
            if existing_city:
                return existing_city
        
        # Если город не найден, добавляем новый
        city = CityDB(
            city_id=city_id,
            name=city_data.get('name'),
            latitude=city_data.get('latitude'),
            longitude=city_data.get('longitude'),
            country=city_data.get('country'),
            admin1=city_data.get('admin1')
        )
        session.add(city)
        await session.commit()
        await session.refresh(city)
        return city


# Создание экземпляра БД
db = DB()

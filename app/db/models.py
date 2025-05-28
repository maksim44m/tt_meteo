from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class CityDB(Base):
    """Модель города"""
    __tablename__ = 'cities'
    
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(Integer, unique=True, index=True, nullable=True)  # ID города из API
    name = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    country = Column(String, nullable=True)
    admin1 = Column(String, nullable=True)

class SearchHistoryDB(Base):
    """Модель истории поиска"""
    __tablename__ = 'search_history'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    city_name = Column(String)
    timestamp = Column(Integer) 
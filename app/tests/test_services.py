import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from fastapi import HTTPException

from app.api.services import get_city_coordinates, get_weather_forecast, forecast_handler
from app.models.weather import City, WeatherData, WeatherForecast


@pytest.fixture
def mock_city():
    """Фикстура для создания тестового города"""
    return City(
        id=1,
        name='Москва',
        latitude=55.7558,
        longitude=37.6173,
        country='Россия',
        admin1='Москва'
    )


@pytest.fixture
def mock_weather_forecast(mock_city):
    """Фикстура для создания тестового прогноза погоды"""
    current_time = int(datetime.now().timestamp())
    weather_data = WeatherData(
        time=[current_time, current_time + 3600, current_time + 7200],
        temperature_2m=[20.5, 21.0, 19.5]
    )
    
    return WeatherForecast(
        city=mock_city,
        hourly=weather_data,
        hourly_units={'temperature_2m': '°C'}
    )


@pytest.mark.asyncio
async def test_get_city_coordinates_from_db(db_session):
    """Тест получения координат города из базы данных"""
    # Получение сессии из генератора
    session = await anext(db_session)
    
    # Мок результата запроса к БД
    db_city = MagicMock()
    db_city.city_id = 1
    db_city.name = 'Москва'
    db_city.latitude = 55.7558
    db_city.longitude = 37.6173
    db_city.country = 'Россия'
    db_city.admin1 = 'Москва'
    
    with patch('app.db.base.db.find_city_by_name', 
               AsyncMock(return_value=db_city)):
        result = await get_city_coordinates('Москва', session=session)
    
    # Проверка результата
    assert len(result) == 1
    assert result[0].name == 'Москва'
    assert result[0].latitude == 55.7558
    assert result[0].longitude == 37.6173


@pytest.mark.asyncio
async def test_get_city_coordinates_from_api(db_session):
    """Тест получения координат города через API"""
    # Получение сессии из генератора
    session = await anext(db_session)
    
    # Мок для httpx.AsyncClient
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'results': [
            {
                'id': 1,
                'name': 'Москва',
                'latitude': 55.7558,
                'longitude': 37.6173,
                'country': 'Россия',
                'admin1': 'Москва'
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()
    
    # Настройка мока для поиска города в БД (возвращаем None)
    with patch('app.db.base.db.find_city_by_name', AsyncMock(return_value=None)), \
         patch('httpx.AsyncClient.get', AsyncMock(return_value=mock_response)), \
         patch('app.db.base.db.save_city', AsyncMock()):
        result = await get_city_coordinates('Москва', session=session)
    
    # Проверка результата
    assert len(result) == 1
    assert result[0].name == 'Москва'
    assert result[0].latitude == 55.7558
    assert result[0].longitude == 37.6173


@pytest.mark.asyncio
async def test_get_weather_forecast(mock_city):
    """Тест получения прогноза погоды"""
    # Мок для httpx.AsyncClient
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'hourly': {
            'time': [1625097600, 1625101200, 1625104800],
            'temperature_2m': [20.5, 21.0, 19.5]
        },
        'hourly_units': {'temperature_2m': '°C'}
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient.get', AsyncMock(return_value=mock_response)):
        result = await get_weather_forecast(mock_city)
    
    # Проверка результата
    assert result is not None
    assert result.city.name == 'Москва'
    assert len(result.hourly.time) == 3
    assert len(result.hourly.temperature_2m) == 3
    assert result.hourly_units['temperature_2m'] == '°C'


@pytest.mark.asyncio
async def test_forecast_handler(mock_city, mock_weather_forecast, db_session):
    """Тест обработчика прогноза погоды"""
    # Получение сессии из генератора
    session = await anext(db_session)
    
    # Настройка моков
    with patch('app.api.services.get_city_coordinates', 
               AsyncMock(return_value=[mock_city])), \
         patch('app.api.services.get_weather_forecast', 
               AsyncMock(return_value=mock_weather_forecast)), \
         patch('app.db.base.db.add_search_history', AsyncMock()):
        
        result = await forecast_handler('Москва', 'test_user', session)
    
    # Проверка результата
    assert result['city'].name == 'Москва'
    assert 'forecast' in result
    assert len(result['forecast']) > 0
    # Проверяем структуру данных в прогнозе
    for item in result['forecast']:
        assert 'time' in item
        assert 'temperature' in item
        assert 'unit' in item


@pytest.mark.asyncio
async def test_forecast_handler_city_not_found(db_session):
    """Тест обработчика когда город не найден"""
    # Получение сессии из генератора
    session = await anext(db_session)
    
    # Настройка моков
    with patch('app.api.services.get_city_coordinates', AsyncMock(return_value=[])):
        try:
            await forecast_handler('НесуществующийГород', 'test_user', session)
            assert False, "Исключение не было выброшено"
        except HTTPException as exc:
            assert exc.status_code == 404
            assert f"Город 'НесуществующийГород' не найден" == exc.detail


@pytest.mark.asyncio
async def test_forecast_handler_forecast_not_available(mock_city, db_session):
    """Тест обработчика когда прогноз недоступен"""
    # Получение сессии из генератора
    session = await anext(db_session)
    
    # Настройка моков
    with patch('app.api.services.get_city_coordinates', 
               AsyncMock(return_value=[mock_city])), \
         patch('app.api.services.get_weather_forecast', 
               AsyncMock(return_value=None)):
        try:
            await forecast_handler('Москва', 'test_user', session)
            assert False, "Исключение не было выброшено"
        except HTTPException as exc:
            assert exc.status_code == 404
            assert "Не удалось получить прогноз погоды" == exc.detail 
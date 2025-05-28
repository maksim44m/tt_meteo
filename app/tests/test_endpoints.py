import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.weather import City


@pytest.fixture
def test_client():
    """Фикстура для тестового клиента FastAPI"""
    return TestClient(app)


@pytest.fixture
def mock_city():
    """Фикстура с тестовым городом"""
    return City(
        id=123,
        name='Москва',
        latitude=55.7558,
        longitude=37.6173,
        country='Россия',
        admin1='Московская область'
    )


@pytest.fixture
def override_get_session():
    """Переопределение зависимости get_session"""
    async def _override_get_session():
        mock_session = AsyncMock(spec=AsyncSession)
        yield mock_session
    
    # Сохраняем оригинальную зависимость
    original_get_session = app.dependency_overrides.get('app.db.base.db.get_session')
    
    # Переопределяем зависимость
    app.dependency_overrides['app.db.base.db.get_session'] = _override_get_session
    
    # Восстанавливаем оригинальную зависимость после выполнения теста
    yield
    
    if original_get_session:
        app.dependency_overrides['app.db.base.db.get_session'] = original_get_session
    else:
        del app.dependency_overrides['app.db.base.db.get_session']


def test_search_city(test_client, mock_city, override_get_session):
    """Тест эндпоинта поиска города"""
    # Мокируем функцию сервиса
    with patch('app.api.services.get_city_coordinates') as mock_get_coords:
        mock_get_coords.return_value = [mock_city]
        
        # Выполняем запрос
        response = test_client.get("/api/weather/search?q=Москва")
        
        # Проверяем ответ
        assert response.status_code == 200
        data = response.json()
        assert "cities" in data
        assert len(data["cities"]) == 1
        assert data["cities"][0]["name"] == "Москва"
        assert data["cities"][0]["latitude"] == 55.7558
        assert data["cities"][0]["longitude"] == 37.6173


def test_search_city_empty_result(test_client, override_get_session):
    """Тест эндпоинта поиска города без результатов"""
    # Мокируем функцию сервиса
    with patch('app.api.services.get_city_coordinates') as mock_get_coords:
        mock_get_coords.return_value = []
        
        # Выполняем запрос
        response = test_client.get("/api/weather/search?q=НесуществующийГород")
        
        # Проверяем ответ
        assert response.status_code == 200
        data = response.json()
        assert "cities" in data
        assert len(data["cities"]) == 0


def test_get_forecast(test_client, mock_city, override_get_session):
    """Тест эндпоинта получения прогноза погоды"""
    # Преобразуем объект City в словарь
    city_dict = {
        "id": mock_city.id,
        "name": mock_city.name,
        "latitude": mock_city.latitude,
        "longitude": mock_city.longitude,
        "country": mock_city.country,
        "admin1": mock_city.admin1
    }
    
    # Мокируем функцию обработчика прогноза
    mock_forecast_result = {
        "city": city_dict,
        "forecast": [
            {"time": "12:00", "temperature": 15.5, "unit": "°C"},
            {"time": "13:00", "temperature": 16.2, "unit": "°C"}
        ]
    }
    
    with patch('app.api.services.forecast_handler') as mock_forecast_handler:
        mock_forecast_handler.return_value = mock_forecast_result
        
        # Выполняем запрос
        response = test_client.get("/api/weather/forecast?city=Москва")
        
        # Проверяем ответ
        assert response.status_code == 200
        data = response.json()
        assert "city" in data
        assert "forecast" in data
        assert data["city"]["name"] == "Москва"
        assert len(data["forecast"]) == 2
        assert data["forecast"][0]["temperature"] == 15.5


def test_get_forecast_sets_cookie(test_client, mock_city, override_get_session):
    """Тест установки cookie при первом запросе прогноза"""
    # Преобразуем объект City в словарь
    city_dict = {
        "id": mock_city.id,
        "name": mock_city.name,
        "latitude": mock_city.latitude,
        "longitude": mock_city.longitude,
        "country": mock_city.country,
        "admin1": mock_city.admin1
    }
    
    # Мокируем функцию обработчика прогноза
    mock_forecast_result = {
        "city": city_dict,
        "forecast": [
            {"time": "12:00", "temperature": 15.5, "unit": "°C"}
        ]
    }
    
    with patch('app.api.services.forecast_handler') as mock_forecast_handler:
        mock_forecast_handler.return_value = mock_forecast_result
        
        # Выполняем запрос без cookie
        response = test_client.get("/api/weather/forecast?city=Москва")
        
        # Проверяем ответ и наличие cookie
        assert response.status_code == 200
        assert "user_id" in response.cookies
        assert response.cookies["user_id"] != ""


def test_get_history_empty(test_client, override_get_session):
    """Тест получения пустой истории без cookie"""
    # Выполняем запрос без cookie
    response = test_client.get("/api/weather/history")
    
    # Проверяем ответ
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert len(data["history"]) == 0


def test_get_history_with_data(test_client, override_get_session):
    """Тест получения истории поиска"""
    # Мокируем функцию получения истории
    history = ["Москва", "Санкт-Петербург"]
    
    with patch('app.db.base.db.get_user_history') as mock_history:
        mock_history.return_value = history
        
        # Устанавливаем cookie непосредственно на клиенте
        test_client.cookies.set("user_id", "test_user_id")
        
        # Выполняем запрос
        response = test_client.get("/api/weather/history")
        
        # Проверяем ответ
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) == 2
        assert data["history"][0] == "Москва"
        assert data["history"][1] == "Санкт-Петербург"


def test_get_statistics(test_client, override_get_session):
    """Тест получения статистики"""
    # Мокируем функцию получения статистики
    stats = [
        {"city": "Москва", "count": 10},
        {"city": "Санкт-Петербург", "count": 5}
    ]
    
    with patch('app.db.base.db.get_city_stats') as mock_stats:
        mock_stats.return_value = stats
        
        # Выполняем запрос
        response = test_client.get("/api/weather/stats")
        
        # Проверяем ответ
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["city"] == "Москва"
        assert data[0]["count"] == 10
        assert data[1]["city"] == "Санкт-Петербург"
        assert data[1]["count"] == 5


def test_main_page(test_client):
    """Тест главной страницы"""
    response = test_client.get("/")
    
    # Проверяем ответ
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_stats_page(test_client, override_get_session):
    """Тест страницы статистики"""
    # Мокируем функцию получения статистики
    stats = [
        {"city": "Москва", "count": 10},
        {"city": "Санкт-Петербург", "count": 5}
    ]
    
    with patch('app.db.base.db.get_city_stats') as mock_stats:
        mock_stats.return_value = stats
        
        # Выполняем запрос
        response = test_client.get("/stats")
        
        # Проверяем ответ
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"] 
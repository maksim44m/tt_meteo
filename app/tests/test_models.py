import pytest
from app.models.weather import City, WeatherData, WeatherForecast, SearchHistory


def test_city_model():
    """Тест модели City"""
    city = City(
        id=1, 
        name='Москва', 
        latitude=55.7558, 
        longitude=37.6173, 
        country='Россия',
        admin1='Московская область'
    )
    
    assert city.id == 1
    assert city.name == 'Москва'
    assert city.latitude == 55.7558
    assert city.longitude == 37.6173
    assert city.country == 'Россия'
    assert city.admin1 == 'Московская область'


def test_city_model_minimal():
    """Тест модели City с минимальными данными"""
    city = City(name='Москва', latitude=55.7558, longitude=37.6173)
    
    assert city.name == 'Москва'
    assert city.latitude == 55.7558
    assert city.longitude == 37.6173
    assert city.id is None
    assert city.country is None
    assert city.admin1 is None


def test_weather_data_model():
    """Тест модели WeatherData"""
    weather_data = WeatherData(
        time=[1698764400, 1698768000, 1698771600],
        temperature_2m=[10.5, 11.2, 12.0]
    )
    
    assert len(weather_data.time) == 3
    assert weather_data.time[0] == 1698764400
    assert len(weather_data.temperature_2m) == 3
    assert weather_data.temperature_2m[1] == 11.2


def test_weather_forecast_model():
    """Тест модели WeatherForecast"""
    city = City(name='Москва', latitude=55.7558, longitude=37.6173)
    weather_data = WeatherData(
        time=[1698764400, 1698768000],
        temperature_2m=[10.5, 11.2]
    )
    
    forecast = WeatherForecast(
        city=city,
        hourly=weather_data,
        hourly_units={'temperature_2m': '°C'}
    )
    
    assert forecast.city.name == 'Москва'
    assert len(forecast.hourly.time) == 2
    assert forecast.hourly.temperature_2m[0] == 10.5
    assert forecast.hourly_units['temperature_2m'] == '°C'


def test_search_history_model():
    """Тест модели SearchHistory"""
    history = SearchHistory(
        user_id='user123',
        city_name='Москва',
        timestamp=1698764400
    )
    
    assert history.user_id == 'user123'
    assert history.city_name == 'Москва'
    assert history.timestamp == 1698764400 
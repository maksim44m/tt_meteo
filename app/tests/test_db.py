import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.db.base import DB
from app.db.models import CityDB, SearchHistoryDB


@pytest.fixture
def db_instance():
    """Фикстура для экземпляра DB"""
    with patch('sqlalchemy.ext.asyncio.create_async_engine'), \
         patch('sqlalchemy.ext.asyncio.async_sessionmaker'):
        db = DB()
        return db


@pytest.fixture
def mock_session():
    """Фикстура для мока сессии базы данных"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.mark.asyncio
async def test_add_search_history(db_instance, mock_session):
    """Тест добавления записи в историю поиска"""
    user_id = 'test_user'
    city_name = 'Москва'
    
    # Вызываем тестируемый метод
    result = await db_instance.add_search_history(user_id, city_name, mock_session)
    
    # Проверяем, что был вызван метод add с правильным объектом
    assert mock_session.add.called
    
    # Получаем аргумент, который был передан в метод add
    added_obj = mock_session.add.call_args[0][0]
    assert isinstance(added_obj, SearchHistoryDB)
    assert added_obj.user_id == 'test_user'
    assert added_obj.city_name == 'Москва'
    
    # Проверяем, что был вызван коммит
    assert mock_session.commit.called
    
    # Проверяем, что был вызван refresh
    assert mock_session.refresh.called


@pytest.mark.asyncio
async def test_get_user_history(db_instance, mock_session):
    """Тест получения истории поиска пользователя"""
    user_id = 'test_user'
    
    # Мок для результата запроса
    mock_result = MagicMock()
    mock_result.all.return_value = [('Москва',), ('Санкт-Петербург',), ('Москва',)]
    
    # Настраиваем мок для метода execute
    mock_session.execute.return_value = mock_result
    
    # Вызываем тестируемый метод
    result = await db_instance.get_user_history(user_id, mock_session)
    
    # Проверяем результат
    assert len(result) == 2  # Уникальные города
    assert result[0] == 'Москва'
    assert result[1] == 'Санкт-Петербург'
    
    # Проверяем, что был вызван метод execute
    assert mock_session.execute.called


@pytest.mark.asyncio
async def test_get_city_stats(db_instance, mock_session):
    """Тест получения статистики поиска городов"""
    # Мок для результата запроса
    mock_result = MagicMock()
    mock_result.all.return_value = [('Москва', 10), ('Санкт-Петербург', 5)]
    
    # Настраиваем мок для метода execute
    mock_session.execute.return_value = mock_result
    
    # Вызываем тестируемый метод
    result = await db_instance.get_city_stats(mock_session)
    
    # Проверяем результат
    assert len(result) == 2
    assert result[0]['city'] == 'Москва'
    assert result[0]['count'] == 10
    assert result[1]['city'] == 'Санкт-Петербург'
    assert result[1]['count'] == 5
    
    # Проверяем, что был вызван метод execute
    assert mock_session.execute.called


@pytest.mark.asyncio
async def test_find_city_by_name(db_instance, mock_session):
    """Тест поиска города по имени"""
    city_name = 'Москва'
    
    # Создаем моковый город
    mock_city = CityDB(
        id=1,
        city_id=123,
        name='Москва',
        latitude=55.7558,
        longitude=37.6173,
        country='Россия',
        admin1='Московская область'
    )
    
    # Мок для результата запроса
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = mock_city
    mock_result.scalars.return_value = mock_scalars
    
    # Настраиваем мок для метода execute
    mock_session.execute.return_value = mock_result
    
    # Вызываем тестируемый метод
    result = await db_instance.find_city_by_name(city_name, mock_session)
    
    # Проверяем результат
    assert result is not None
    assert result.name == 'Москва'
    assert result.latitude == 55.7558
    assert result.longitude == 37.6173
    
    # Проверяем, что был вызван метод execute
    assert mock_session.execute.called


@pytest.mark.asyncio
async def test_save_city(db_instance, mock_session):
    """Тест сохранения города в базу данных"""
    city_data = {
        'id': 123,
        'name': 'Москва',
        'latitude': 55.7558,
        'longitude': 37.6173,
        'country': 'Россия',
        'admin1': 'Московская область'
    }
    
    # Мок для результата запроса проверки существования города
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None  # Город не существует
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    
    # Вызываем тестируемый метод
    result = await db_instance.save_city(city_data, mock_session)
    
    # Проверяем, что был вызван метод execute для проверки существования
    assert mock_session.execute.called
    
    # Проверяем, что был вызван метод add с правильным объектом
    assert mock_session.add.called
    
    # Получаем аргумент, который был передан в метод add
    added_obj = mock_session.add.call_args[0][0]
    assert isinstance(added_obj, CityDB)
    assert added_obj.city_id == 123
    assert added_obj.name == 'Москва'
    assert added_obj.latitude == 55.7558
    assert added_obj.longitude == 37.6173
    
    # Проверяем, что был вызван коммит
    assert mock_session.commit.called
    
    # Проверяем, что был вызван refresh
    assert mock_session.refresh.called


@pytest.mark.asyncio
async def test_save_city_existing(db_instance, mock_session):
    """Тест сохранения города, который уже существует в базе данных"""
    city_data = {
        'id': 123,
        'name': 'Москва',
        'latitude': 55.7558,
        'longitude': 37.6173,
        'country': 'Россия',
        'admin1': 'Московская область'
    }
    
    # Создаем существующий город
    existing_city = CityDB(
        id=1,
        city_id=123,
        name='Москва',
        latitude=55.7558,
        longitude=37.6173,
        country='Россия',
        admin1='Московская область'
    )
    
    # Мок для результата запроса проверки существования города
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = existing_city  # Город существует
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_result
    
    # Вызываем тестируемый метод
    result = await db_instance.save_city(city_data, mock_session)
    
    # Проверяем, что был вызван метод execute для проверки существования
    assert mock_session.execute.called
    
    # Проверяем, что метод add НЕ был вызван (т.к. город уже существует)
    assert not mock_session.add.called
    
    # Проверяем, что методы commit и refresh НЕ были вызваны
    assert not mock_session.commit.called
    assert not mock_session.refresh.called
    
    # Проверяем, что функция вернула существующий город
    assert result == existing_city 
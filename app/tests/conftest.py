import pytest
import asyncio
from unittest.mock import AsyncMock, patch

# Настройка pytest-asyncio для тестирования асинхронных функций
@pytest.fixture(scope="session")
def event_loop():
    """Создание нового цикла событий для каждой тестовой сессии"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Мок для сессии базы данных
@pytest.fixture
async def db_session():
    """Фикстура для создания мока сессии базы данных"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    
    # Использование контекстного менеджера для yield сессии в тестах
    async def _get_test_session():
        yield session
    
    # Патчим функцию получения сессии
    with patch('app.db.base.db.get_session', _get_test_session):
        yield session 
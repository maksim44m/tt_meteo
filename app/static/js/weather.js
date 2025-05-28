// Получение элементов DOM
document.addEventListener('DOMContentLoaded', function() {
    const cityInput = document.getElementById('city-input');
    const searchBtn = document.getElementById('search-btn');
    const suggestionsDiv = document.getElementById('suggestions');
    const weatherResults = document.getElementById('weather-results');
    const cityInfo = document.getElementById('city-info');
    const forecastContainer = document.getElementById('forecast-container');
    const historyContainer = document.getElementById('history-container');
    const historyItems = document.getElementById('history-items');
    
    // Получение истории поиска при загрузке страницы
    window.addEventListener('load', async () => {
        await loadHistory();
    });
    
    // Обработчик ввода в поле поиска (для автодополнения)
    let timeout = null;
    if (cityInput) {
        cityInput.addEventListener('input', function() {
            clearTimeout(timeout);
            
            // Если поле пустое, скрываем подсказки
            if (this.value.trim().length < 2) {
                suggestionsDiv.style.display = 'none';
                return;
            }
            
            // Задержка запроса для уменьшения количества обращений к API
            timeout = setTimeout(async function() {
                const value = cityInput.value.trim();
                try {
                    const response = await fetch(`/api/weather/search?q=${encodeURIComponent(value)}`);
                    const data = await response.json();
                    
                    if (data.cities && data.cities.length > 0) {
                        // Отображаем подсказки
                        suggestionsDiv.innerHTML = '';
                        data.cities.forEach(city => {
                            const div = document.createElement('div');
                            let cityText = city.name;
                            if (city.admin1) cityText += `, ${city.admin1}`;
                            if (city.country) cityText += `, ${city.country}`;
                            
                            div.textContent = cityText;
                            div.addEventListener('click', function() {
                                cityInput.value = city.name;
                                suggestionsDiv.style.display = 'none';
                                searchWeather(city.name);
                            });
                            suggestionsDiv.appendChild(div);
                        });
                        suggestionsDiv.style.display = 'block';
                    } else {
                        suggestionsDiv.style.display = 'none';
                    }
                } catch (error) {
                    console.error('Ошибка при получении подсказок:', error);
                }
            }, 300);
        });
    }
    
    // Обработчик нажатия на кнопку поиска
    if (searchBtn) {
        searchBtn.addEventListener('click', function() {
            const city = cityInput.value.trim();
            if (city) {
                searchWeather(city);
            }
        });
    }
    
    // Обработчик нажатия Enter в поле ввода
    if (cityInput) {
        cityInput.addEventListener('keyup', function(event) {
            if (event.key === 'Enter') {
                const city = cityInput.value.trim();
                if (city) {
                    searchWeather(city);
                }
            }
        });
    }
    
    // Функция для поиска погоды
    async function searchWeather(city) {
        try {
            const response = await fetch(`/api/weather/forecast?city=${encodeURIComponent(city)}`);
            
            if (!response.ok) {
                const error = await response.json();
                alert(error.detail || 'Не удалось получить прогноз погоды');
                return;
            }
            
            const data = await response.json();
            displayWeather(data);
            
            // Обновляем историю после успешного поиска
            await loadHistory();
        } catch (error) {
            console.error('Ошибка при получении прогноза погоды:', error);
            alert('Произошла ошибка при получении прогноза погоды');
        }
    }
    
    // Функция для отображения погоды
    function displayWeather(data) {
        // Отображаем информацию о городе
        let cityText = data.city.name;
        if (data.city.admin1) cityText += `, ${data.city.admin1}`;
        if (data.city.country) cityText += `, ${data.city.country}`;
        cityInfo.textContent = cityText;
        
        // Отображаем прогноз погоды
        forecastContainer.innerHTML = '';
        
        data.forecast.forEach(item => {
            const forecastItem = document.createElement('div');
            forecastItem.className = 'forecast-item';
            
            const timeDiv = document.createElement('div');
            timeDiv.className = 'forecast-time';
            timeDiv.textContent = item.time;
            
            const tempDiv = document.createElement('div');
            tempDiv.className = 'forecast-temp';
            tempDiv.textContent = `${item.temperature}${item.unit}`;
            
            forecastItem.appendChild(timeDiv);
            forecastItem.appendChild(tempDiv);
            
            forecastContainer.appendChild(forecastItem);
        });
        
        // Показываем результаты
        weatherResults.style.display = 'block';
    }
    
    // Функция для загрузки истории поиска
    async function loadHistory() {
        try {
            const response = await fetch('/api/weather/history');
            const data = await response.json();
            
            if (data.history && data.history.length > 0) {
                historyItems.innerHTML = '';
                
                data.history.forEach(city => {
                    const item = document.createElement('div');
                    item.className = 'history-item';
                    item.textContent = city;
                    item.addEventListener('click', function() {
                        cityInput.value = city;
                        searchWeather(city);
                    });
                    historyItems.appendChild(item);
                });
                
                historyContainer.style.display = 'block';
            } else {
                historyContainer.style.display = 'none';
            }
        } catch (error) {
            console.error('Ошибка при получении истории:', error);
        }
    }
    
    // Закрытие выпадающего списка при клике вне его
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.suggestions-container')) {
            suggestionsDiv.style.display = 'none';
        }
    });
}); 
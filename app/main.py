from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.endpoints import router as weather_router
from app.db.base import db

app = FastAPI(title="Погодный сервис")

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Настройка шаблонов
templates = Jinja2Templates(directory="app/templates")

# Подключение маршрутов API
app.include_router(weather_router, prefix="/api/weather", tags=["weather"])

@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    """Главная страница"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/stats", response_class=HTMLResponse)
async def stats_page(
    request: Request, 
    session: AsyncSession = Depends(db.get_session)
) -> HTMLResponse:
    """Страница статистики поиска городов"""
    stats = await db.get_city_stats(session)

    return templates.TemplateResponse(
        "stats.html", 
        {"request": request, "stats": stats}
    )

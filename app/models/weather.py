from pydantic import BaseModel
from typing import List, Dict, Optional

class City(BaseModel):
    id: Optional[int] = None
    name: str
    latitude: float
    longitude: float
    country: Optional[str] = None
    admin1: Optional[str] = None

class WeatherData(BaseModel):
    time: List[int]
    temperature_2m: List[float]

class WeatherForecast(BaseModel):
    city: City
    hourly: WeatherData
    hourly_units: Dict[str, str]
    
class SearchHistory(BaseModel):
    user_id: str
    city_name: str
    timestamp: int 
# weatherapitest.py
import os
import requests

# Optional: load from .env if you prefer that workflow
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

API_KEY = os.getenv("6998c995bdc891add712737369e24063")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

def get_current_weather_by_city(city: str, units: str = "metric", lang: str = "en"):
    if not API_KEY:
        raise RuntimeError("OPENWEATHER_API_KEY is not set")
    params = {"q": city, "appid": API_KEY, "units": units, "lang": lang}
    # Optional: print the final URL once for debugging
    # print("Requesting:", requests.Request("GET", BASE_URL, params=params).prepare().url)
    r = requests.get(BASE_URL, params=params, timeout=15)
    if r.status_code == 401:
        raise RuntimeError(f"401 Unauthorized from OpenWeather. Response: {r.text}")
    r.raise_for_status()
    data = r.json()
    return {
        "city": data.get("name"),
        "country": data.get("sys", {}).get("country"),
        "temp": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "description": data["weather"]["description"],
        "wind_speed": data["wind"]["speed"],
    }

if __name__ == "__main__":
    print(get_current_weather_by_city("London", units="metric", lang="en"))

import requests
from datetime import date

# NYC coordinates
LAT = 40.7128
LON = -74.0060

WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Heavy drizzle",
    56: "Light freezing drizzle",
    57: "Heavy freezing drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Light snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Moderate showers",
    82: "Heavy showers",
    85: "Light snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with light hail",
    99: "Thunderstorm with heavy hail",
}


def fetch_weather():
    today = date.today().isoformat()
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "relativehumidity_2m",
            "precipitation",
            "rain",
            "snowfall",
            "weathercode",
            "windspeed_10m",
        ]),
        "temperature_unit": "fahrenheit",
        "windspeed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "America/New_York",
        "start_date": today,
        "end_date": today,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    hourly = data["hourly"]
    hours = []
    for i, time_str in enumerate(hourly["time"]):
        hour = int(time_str[11:13])
        code = hourly["weathercode"][i]
        hours.append({
            "hour": hour,
            "time": time_str,
            "temp": hourly["temperature_2m"][i],
            "feels_like": hourly["apparent_temperature"][i],
            "humidity": hourly["relativehumidity_2m"][i],
            "precipitation": hourly["precipitation"][i],
            "rain": hourly["rain"][i],
            "snowfall": hourly["snowfall"][i],
            "weathercode": code,
            "condition": WMO_CODES.get(code, "Unknown"),
            "windspeed": hourly["windspeed_10m"][i],
        })
    return hours

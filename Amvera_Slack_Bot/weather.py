import requests
from config import WEATHER_API_KEY

def fetch_weather(city="Москва"):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    response = requests.get(url)
    data = response.json()
    if response.status_code == 200:
        weather = data['weather'][0]['description']
        temperature = data['main']['temp']
        return f"Погода в {city}: {weather}, {temperature}°C"
    else:
        return "Не удалось получить данные о погоде."

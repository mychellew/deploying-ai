import os
import requests
from openai import OpenAI

client = OpenAI(
    base_url = 'https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1',
    api_key='any value',
    default_headers={"x-api-key": os.getenv('API_GATEWAY_KEY')}
)

def extract_location(user_input: str) -> str:
    # If the input is just one word, assume it's the city
    if len(user_input.split()) == 1:
        return user_input.strip().replace(".", "")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract ONLY the city name. If no city is found, respond with 'None'."},
                {"role": "user", "content": user_input}
            ],
            temperature=0
        )
        city = response.choices[0].message.content.strip()
        return None if city.lower() == "none" else city.replace(".", "")
    except Exception:
        return None


def get_coordinates(city: str):
    # Added .lower() check to handle the 'None' string case
    if not city or city.lower() == "none":
        return None, None
        
    url = f"https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1}
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "results" in data and data["results"]:
            return data["results"][0]["latitude"], data["results"][0]["longitude"]
    except:
        return None, None
    return None, None

def get_weather(user_input: str):
    location = extract_location(user_input)

    restricted_topics = ["cats", "dogs", "horoscope", "zodiac", "taylor swift"]

    for topic in restricted_topics:
        if topic in user_input.lower():
            return "Sorry, I cannot discuss that topic. Let's plan your trip to Canada instead!"
    
    # Check for the string "None" specifically
    if not location or location.lower() == "none":
        return "Please specify a city name so I can check the weather for you!"
    
    lat, long = get_coordinates(location)

    if lat is None or long is None:
        return f"Sorry, I couldn't find the coordinates for '{location}'."

    url = f"https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": long,
        "current_weather": True
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        current = data.get("current_weather")

        if not current:
            return f"Weather data for {location} is currently unavailable."
        
        temp = current.get("temperature")
        return (
            f"The current temperature in {location} is {temp}°C. "
            f"(Weather code: {current.get('weathercode')})"
        )
    except requests.RequestException as e:
        return f"Error fetching weather: {str(e)}"
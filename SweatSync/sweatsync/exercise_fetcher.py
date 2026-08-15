import os
import requests
from pymongo import MongoClient

# Use synchronous PyMongo for curator scripts (which are synchronous)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["sweatsync"]
exercises_cache = db["exercises_cache"]

RAPIDAPI_HOST = "exercisedb.p.rapidapi.com"

def get_headers():
    rapid_key = os.getenv("RAPIDAPI_KEY")
    if not rapid_key:
        raise ValueError("RAPIDAPI_KEY is not set.")
    return {
        "X-RapidAPI-Key": rapid_key,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }

def _fetch_and_cache(url: str) -> list:
    """Helper to fetch from url, cache the detailed results, and return them."""
    try:
        headers = get_headers()
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        # Cache each returned exercise for ultra-fast lookup later
        if isinstance(data, list):
            for ex in data:
                ex_copy = ex.copy()
                ex_copy["name_lower"] = ex.get("name", "").lower()
                ex_copy.pop("_id", None)
                exercises_cache.update_one(
                    {"id": ex["id"]}, 
                    {"$set": ex_copy}, 
                    upsert=True
                )
            return data
        elif isinstance(data, dict):
            # Fallback for single item endpoints
            data_copy = data.copy()
            data_copy["name_lower"] = data.get("name", "").lower()
            data_copy.pop("_id", None)
            exercises_cache.update_one(
                {"id": data["id"]}, 
                {"$set": data_copy}, 
                upsert=True
            )
            return [data]
        return []
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

def fetch_exercises_by_body_part(body_part: str, limit: int = 15) -> list:
    """Gets exercises targeted to a specific body part (e.g. 'chest', 'upper arms')"""
    bp_encode = body_part.replace(' ', '%20')
    url = f"https://{RAPIDAPI_HOST}/exercises/bodyPart/{bp_encode}?limit={limit}"
    return _fetch_and_cache(url)

def fetch_exercises_by_target(target: str, limit: int = 15) -> list:
    """Gets exercises targeted to a specific muscle (e.g. 'pectorals')"""
    target_encode = target.replace(' ', '%20')
    url = f"https://{RAPIDAPI_HOST}/exercises/target/{target_encode}?limit={limit}"
    return _fetch_and_cache(url)

def fetch_exercises_by_equipment(equipment: str, limit: int = 20) -> list:
    """Gets exercises matching specific equipment (e.g. 'dumbbell')"""
    eq_encode = equipment.replace(' ', '%20')
    url = f"https://{RAPIDAPI_HOST}/exercises/equipment/{eq_encode}?limit={limit}"
    return _fetch_and_cache(url)

def get_cached_exercise_by_id(exercise_id: str) -> dict:
    """Reads directly from mongo cache"""
    cached = exercises_cache.find_one({"id": exercise_id})
    if cached:
        cached.pop("_id", None)
        return cached
    return None

def get_cached_exercise_by_name(name: str) -> dict:
    """Reads directly from mongo cache by name"""
    cached = exercises_cache.find_one({"name_lower": name.lower()})
    if cached:
        cached.pop("_id", None)
        return cached
    return None

"""
Weather Context Service for AquaForensics using Open-Meteo API.
Fetches recent 24h rainfall data for location coordinates.
Provides graceful fallbacks if weather API is unreachable or returns invalid data.
"""
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger("aquaforensics.weather")

def fetch_weather_context(latitude: float, longitude: float, timeout_seconds: float = 3.0) -> Dict[str, Any]:
    """
    Fetches 24-hour total rainfall (mm) and hours since last rain from Open-Meteo API.
    Returns context dictionary formatted for the AquaForensics reasoning engine:
    {
        "rain_mm_24h": float | None,
        "hours_since_rain": float | None,
        "n_independent_reports": 1,
        "weather_status": "ok" | "unavailable"
    }
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=rain&past_days=1&forecast_days=1"
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.get(url)
            if response.status_code == 200:
                data = response.json()
                hourly_rain = data.get("hourly", {}).get("rain", [])
                if hourly_rain:
                    # Sum past 24 hours of rain (take last 24 slots up to current hour)
                    past_24h = hourly_rain[:24] if len(hourly_rain) >= 24 else hourly_rain
                    rain_sum = float(sum(past_24h))
                    
                    # Calculate hours since last non-zero rain in past_24h
                    hours_since = None
                    for idx, val in enumerate(reversed(past_24h)):
                        if val > 0.1:
                            hours_since = float(idx)
                            break
                            
                    return {
                        "rain_mm_24h": round(rain_sum, 2),
                        "hours_since_rain": hours_since,
                        "n_independent_reports": 1,
                        "weather_status": "ok"
                    }
    except Exception as e:
        logger.warning(f"Open-Meteo weather fetch failed for ({latitude}, {longitude}): {e}")

    # Graceful fallback when weather is unavailable
    return {
        "rain_mm_24h": None,
        "hours_since_rain": None,
        "n_independent_reports": 1,
        "weather_status": "unavailable"
    }

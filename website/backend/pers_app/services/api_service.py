import requests
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

API_ENDPOINTS = {
    "temperature": "https://api-open.data.gov.sg/v2/real-time/api/air-temperature",
    "rainfall": "https://api-open.data.gov.sg/v2/real-time/api/rainfall",
    "humidity": "https://api-open.data.gov.sg/v2/real-time/api/relative-humidity",
    "wind_direction": "https://api-open.data.gov.sg/v2/real-time/api/wind-direction",
    "wind_speed": "https://api-open.data.gov.sg/v2/real-time/api/wind-speed",
}

def fetch_api_data(api_type, date_time, max_retries=3, delay=1):
    """
    Fetch data from the specified API with retry logic
    
    Parameters:
    - api_type: Type of weather data (temperature, rainfall, etc.)
    - date_time: ISO format datetime string (YYYY-MM-DDTHH:MM:SS)
    - max_retries: Maximum number of retry attempts
    - delay: Delay between retries in seconds
    
    Returns:
    - JSON response or None if all retries fail
    """
    url = API_ENDPOINTS[api_type]
    params = {
        "date": date_time
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"No {api_type} data available for {date_time}")
                return None
            else:
                logger.warning(f"Error fetching {api_type} data: HTTP {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
        except Exception as e:
            logger.error(f"Exception fetching {api_type} data: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    return None

def extract_stations(api_response):
    """
    Extract station information from API response
    
    Parameters:
    - api_response: JSON response from API
    
    Returns:
    - Dictionary mapping station IDs to station info
    """
    stations = {}
    
    if not api_response or 'data' not in api_response or 'stations' not in api_response['data']:
        return stations
    
    for station in api_response['data']['stations']:
        if 'id' in station:
            station_id = station['id']
            stations[station_id] = {
                'id': station_id,
                'name': station.get('name', 'Unknown'),
                'latitude': station.get('location', {}).get('latitude', None),
                'longitude': station.get('location', {}).get('longitude', None)
            }
    
    return stations

def extract_readings(api_response, timestamp, api_type):
    """
    Extract readings for all stations from API response
    
    Parameters:
    - api_response: JSON response from API
    - timestamp: Timestamp for the reading
    - api_type: Type of weather data
    
    Returns:
    - Dictionary mapping station IDs to values
    """
    readings = {}
    
    if not api_response or 'data' not in api_response or 'readings' not in api_response['data']:
        return readings
    
    api_readings = api_response['data']['readings']
    if not api_readings:
        return readings
    
    # Get the latest reading
    latest_reading = api_readings[-1]
    
    if 'data' not in latest_reading:
        return readings
    
    for item in latest_reading['data']:
        station_id = item.get('stationId')
        if not station_id:
            # Try alternative key if stationId is not present
            station_id = item.get('id')
        
        if station_id and 'value' in item:
            readings[station_id] = {
                'timestamp': timestamp,
                api_type: item['value']
            }
    
    return readings

def fetch_and_store_weather_data(datetime_str=None):
    """
    Fetch and store weather data for all API endpoints
    
    Parameters:
    - datetime_str: ISO format datetime string (YYYY-MM-DDTHH:MM:SS)
                   If None, use current time
    
    Returns:
    - Dictionary with summary of operations
    """
    from weather_app.models import WeatherStation, WeatherReading
    
    if not datetime_str:
        # Format current time as ISO 8601
        datetime_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    # Parse the timestamp
    timestamp = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    
    # Store results
    results = {
        "timestamp": datetime_str,
        "stations_added": 0,
        "readings_added": 0,
        "errors": []
    }
    
    # Get stations and readings for each API type
    for api_type in API_ENDPOINTS.keys():
        try:
            api_response = fetch_api_data(api_type, datetime_str)
            
            if not api_response:
                results["errors"].append(f"No response from {api_type} API")
                continue
            
            # Extract and store stations
            stations = extract_stations(api_response)
            for station_data in stations.values():
                station, created = WeatherStation.objects.update_or_create(
                    station_id=station_data['id'],
                    defaults={
                        'name': station_data['name'],
                        'latitude': station_data['latitude'],
                        'longitude': station_data['longitude']
                    }
                )
                if created:
                    results["stations_added"] += 1
            
            # Extract and store readings
            readings = extract_readings(api_response, timestamp, api_type)
            for station_id, reading_data in readings.items():
                try:
                    station = WeatherStation.objects.get(station_id=station_id)
                    reading, created = WeatherReading.objects.update_or_create(
                        station=station,
                        timestamp=timestamp,
                        defaults={
                            api_type: reading_data[api_type]
                        }
                    )
                    if created:
                        results["readings_added"] += 1
                except WeatherStation.DoesNotExist:
                    results["errors"].append(f"Station {station_id} not found")
        
        except Exception as e:
            results["errors"].append(f"Error processing {api_type}: {str(e)}")
    
    return results
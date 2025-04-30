import requests
import time
import logging
from datetime import datetime, timedelta
from django.utils import timezone
import pytz

logger = logging.getLogger(__name__)

API_ENDPOINTS = {
    "temperature": "https://api-open.data.gov.sg/v2/real-time/api/air-temperature",
    "rainfall": "https://api-open.data.gov.sg/v2/real-time/api/rainfall",
    "humidity": "https://api-open.data.gov.sg/v2/real-time/api/relative-humidity",
    "wind_direction": "https://api-open.data.gov.sg/v2/real-time/api/wind-direction",
    "wind_speed": "https://api-open.data.gov.sg/v2/real-time/api/wind-speed",
}

def round_down_to_hour(dt=None):
    """
    Round down a datetime to the nearest hour (00:00)
    If dt is None, use current time
    Returns a timezone-aware datetime
    """
    if dt is None:
        dt = timezone.now()
    
    # Ensure datetime is timezone-aware
    if dt.tzinfo is None:
        dt = timezone.make_aware(dt)
    
    # Round down to nearest hour
    rounded = dt.replace(minute=0, second=0, microsecond=0)
    return rounded

def get_singapore_time(dt=None, include_timezone=False):
    """
    Convert a datetime to Singapore time
    If dt is None, use current time
    
    Parameters:
    - dt: datetime object or None
    - include_timezone: Whether to include +08:00 in the output
    
    Returns:
    - Formatted string in Singapore timezone
    """
    if dt is None:
        dt = timezone.now()
    
    # Ensure datetime is timezone-aware
    if dt.tzinfo is None:
        dt = timezone.make_aware(dt)
    
    # Convert to Singapore timezone
    singapore_tz = pytz.timezone('Asia/Singapore')
    singapore_time = dt.astimezone(singapore_tz)
    
    # Format as ISO 8601 with or without timezone info
    if include_timezone:
        return singapore_time.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    else:
        return singapore_time.strftime("%Y-%m-%dT%H:%M:%S")

def get_hourly_timestamp(dt=None):
    """
    Get the most recent completed hour timestamp in Singapore time
    """
    # Round down to hour
    rounded = round_down_to_hour(dt)
    
    # Convert to Singapore time string
    return get_singapore_time(rounded)

def get_last_n_hours(hours=24):
    """
    Get a list of the last N hourly timestamps in Singapore time
    Returns oldest first (ascending order)
    """
    current = round_down_to_hour()
    timestamps = []
    
    for i in range(hours, 0, -1):  # Count backwards from hours to 1
        timestamp = current - timedelta(hours=i)
        timestamps.append(get_singapore_time(timestamp))
    
    return timestamps

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
    
    logger.info(f"Fetching {api_type} data for {date_time}")
    
    for attempt in range(max_retries):
        try:
            logger.info(f'Parameters: {params}')
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                logger.info(f"Successfully fetched {api_type} data")
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
                   If None, use current time rounded to the hour
    
    Returns:
    - Dictionary with summary of operations
    """
    from pers_app.models import WeatherStation, WeatherReading
    
    if not datetime_str:
        # Use the most recent completed hour
        datetime_str = get_hourly_timestamp()
    
    # Parse the timestamp
    try:
        # Ensure timestamp is timezone-aware
        timestamp = timezone.datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        if timestamp.tzinfo is None:
            # If it's naive, make it aware
            timestamp = timezone.make_aware(timestamp)
    except Exception as e:
        logger.error(f"Error parsing timestamp: {e}")
        # Fallback to current hour
        timestamp = round_down_to_hour()
    
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

def backfill_weather_data(hours=24):
    """
    Backfill weather data for the specified number of hours
    
    Parameters:
    - hours: Number of hours to backfill
    
    Returns:
    - Dictionary with summary of operations
    """
    results = {
        "hours_requested": hours,
        "hours_processed": 0,
        "successful_fetches": 0,
        "failed_fetches": 0,
        "errors": []
    }
    
    # Get hourly timestamps for the last N hours
    timestamps = get_last_n_hours(hours)
    
    for timestamp in timestamps:
        try:
            hour_result = fetch_and_store_weather_data(timestamp)
            results["hours_processed"] += 1
            
            if hour_result and not any(hour_result.get("errors", [])):
                results["successful_fetches"] += 1
            else:
                results["failed_fetches"] += 1
                if hour_result and hour_result.get("errors"):
                    results["errors"].extend(hour_result.get("errors"))
                    
            # Add a small delay to avoid overwhelming the API
            time.sleep(1)
            
        except Exception as e:
            results["failed_fetches"] += 1
            results["errors"].append(f"Exception for {timestamp}: {str(e)}")
    
    return results
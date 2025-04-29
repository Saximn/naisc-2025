import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime
import time
import logging
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API endpoints
API_ENDPOINTS = {
    "temperature": "https://api-open.data.gov.sg/v2/real-time/api/air-temperature",
    "rainfall": "https://api-open.data.gov.sg/v2/real-time/api/rainfall",
    "humidity": "https://api-open.data.gov.sg/v2/real-time/api/relative-humidity",
    "wind_direction": "https://api-open.data.gov.sg/v2/real-time/api/wind-direction",
    "wind_speed": "https://api-open.data.gov.sg/v2/real-time/api/wind-speed",
}

# Initialize geocoder
geolocator = Nominatim(user_agent="flood_prediction_sg")

# Cache for geocoded locations
geocode_cache = {}

# Common Singapore locations for fallback
COMMON_LOCATIONS = {
    "orchard": (1.3036, 103.8318),
    "yishun": (1.4304, 103.8354),
    "tampines": (1.3546, 103.9450),
    "jurong": (1.3329, 103.7436),
    "bukit timah": (1.3294, 103.8021),
    "toa payoh": (1.3340, 103.8471),
    "changi": (1.3644, 103.9915),
    "bedok": (1.3236, 103.9273),
    "serangoon": (1.3554, 103.8679),
    "woodlands": (1.4382, 103.7891),
    "ang mo kio": (1.3691, 103.8454),
    "punggol": (1.3984, 103.9072),
    "bukit batok": (1.3590, 103.7637),
    "clementi": (1.3162, 103.7649),
    "hougang": (1.3719, 103.8930),
    "pasir ris": (1.3721, 103.9474),
    "novena": (1.3203, 103.8438),
    "paya lebar": (1.3178, 103.8918),
    "bishan": (1.3526, 103.8352),
    "buona vista": (1.3066, 103.7901),
    "boon lay": (1.3246, 103.7055),
    "choa chu kang": (1.3840, 103.7470),
    "marine parade": (1.3020, 103.9069),
    "kallang": (1.3100, 103.8716),
    "sengkang": (1.3868, 103.8914),
    "singapore": (1.3521, 103.8198)  # Center of Singapore as fallback
}

def geocode_location(location_text):
    """
    Convert location text to coordinates with multiple fallback methods
    
    Parameters:
    - location_text: Text description of the location
    
    Returns:
    - Dictionary with latitude and longitude
    """
    # Check cache first
    if location_text in geocode_cache:
        return geocode_cache[location_text]
    
    # Try to match with common locations first (faster than geocoding)
    location_lower = location_text.lower()
    for name, coords in COMMON_LOCATIONS.items():
        if name in location_lower:
            result = {'latitude': coords[0], 'longitude': coords[1]}
            geocode_cache[location_text] = result
            logger.info(f"Matched '{location_text}' to common location '{name}'")
            return result
    
    # Try geocoding
    try:
        location = geolocator.geocode(f"{location_text}, Singapore", timeout=10)
        if location:
            result = {'latitude': location.latitude, 'longitude': location.longitude}
            geocode_cache[location_text] = result
            logger.info(f"Successfully geocoded '{location_text}'")
            return result
    except Exception as e:
        logger.warning(f"Error geocoding '{location_text}': {e}")
    
    # If geocoding fails, try to extract parts of the address
    try:
        # Try with main road or area name
        parts = location_text.split('(')[0].strip()  # Remove anything in parentheses
        if parts != location_text:
            location = geolocator.geocode(f"{parts}, Singapore", timeout=10)
            if location:
                result = {'latitude': location.latitude, 'longitude': location.longitude}
                geocode_cache[location_text] = result
                logger.info(f"Successfully geocoded simplified '{parts}'")
                return result
    except Exception:
        pass
    
    # Final fallback: use center of Singapore
    logger.warning(f"Could not geocode '{location_text}', using center of Singapore")
    result = {'latitude': 1.3521, 'longitude': 103.8198}
    geocode_cache[location_text] = result
    return result

def fetch_api_data(api_type, date_time, max_retries=3):
    """
    Fetch data from the specified API
    
    Parameters:
    - api_type: Type of weather data (temperature, rainfall, etc.)
    - date_time: ISO format datetime string (YYYY-MM-DDTHH:MM:SS)
    
    Returns:
    - JSON response or None if error
    """
    url = API_ENDPOINTS[api_type]
    params = {
        "date": date_time
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"No {api_type} data available for {date_time}")
                return None
            else:
                logger.warning(f"Error fetching {api_type} data: HTTP {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(1)
        except Exception as e:
            logger.warning(f"Exception fetching {api_type} data: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
    
    return None

def extract_stations_from_api(api_response):
    """
    Extract station information from API response
    
    Parameters:
    - api_response: JSON response from API
    
    Returns:
    - List of dictionaries with station info including coordinates
    """
    if not api_response or 'data' not in api_response or 'stations' not in api_response['data']:
        return []
    
    stations = []
    for station in api_response['data']['stations']:
        # Check if station has required data
        if 'id' in station and 'name' in station and 'labelLocation' in station:
            try:
                stations.append({
                    'id': station['id'],
                    'name': station['name'],
                    'latitude': station['labelLocation']['latitude'],
                    'longitude': station['labelLocation']['longitude']
                })
            except KeyError:
                continue
    
    return stations

def find_nearest_station(stations, location_coords):
    """
    Find the nearest weather station to a specific location
    
    Parameters:
    - stations: List of station dictionaries with coordinates
    - location_coords: Dictionary with latitude and longitude
    
    Returns:
    - Dictionary with nearest station info or None if no stations
    """
    if not stations or not location_coords:
        return None
    
    nearest_station = None
    min_distance = float('inf')
    
    for station in stations:
        try:
            station_coords = (station['latitude'], station['longitude'])
            loc_coords = (location_coords['latitude'], location_coords['longitude'])
            
            # Calculate distance
            distance = geodesic(station_coords, loc_coords).kilometers
            
            if distance < min_distance:
                min_distance = distance
                nearest_station = {
                    'id': station['id'],
                    'name': station['name'],
                    'distance': distance
                }
        except (KeyError, ValueError):
            continue
    
    return nearest_station

def get_station_value(api_response, station_id):
    """
    Get the value for a specific station from API response
    
    Parameters:
    - api_response: JSON response from API
    - station_id: ID of the station to find
    
    Returns:
    - Value from the station or None if not found
    """
    if not api_response or 'data' not in api_response or 'readings' not in api_response['data']:
        return None
    
    # Get the latest reading
    readings = api_response['data']['readings']
    if not readings:
        return None
    
    latest_reading = readings[-1]
    
    # Find the station in the data
    if 'data' in latest_reading:
        for item in latest_reading['data']:
            if item.get('stationId') == station_id and 'value' in item:
                return item['value']
    
    return None

def create_flood_dataset_with_nearest_stations(flood_data_file, output_file="flood_data_nearest_stations_2.csv"):
    """
    Create dataset with nearest station data for each flood event
    
    Parameters:
    - flood_data_file: Path to JSON file with flood warning data
    - output_file: Path to output CSV file
    
    Returns:
    - DataFrame with flood events and nearest station data
    """
    # Load flood data
    try:
        with open(flood_data_file, 'r') as f:
            flood_data = json.load(f)
        logger.info(f"Loaded {len(flood_data)} flood events from {flood_data_file}")
    except Exception as e:
        logger.error(f"Error loading flood data: {e}")
        return None
    
    # Prepare list for data points
    data_points = []
    
    # Cache stations for each API
    api_stations_cache = {}
    
    # Process each flood event
    for i, flood in enumerate(flood_data):
        try:
            # Extract flood event details
            flood_datetime = flood['datetime']
            flood_location = flood['location']
            
            logger.info(f"Processing event {i+1}/{len(flood_data)}: {flood_location} at {flood_datetime}")
            
            # Geocode the flood location
            location_coords = geocode_location(flood_location)
            
            # Create data point with flood details
            data_point = {
                'datetime': flood_datetime,
                'location': flood_location,
                'latitude': location_coords['latitude'],
                'longitude': location_coords['longitude'],
                'flood': 1  # This is a flood event
            }
            
            # Process each API
            for api_type in API_ENDPOINTS.keys():
                # Get API data
                api_data = fetch_api_data(api_type, flood_datetime)
                print(api_data)
                
                if not api_data:
                    # No data available for this API
                    data_point[f"{api_type}_nearest_value"] = None
                    data_point[f"{api_type}_nearest_distance"] = None
                    data_point[f"{api_type}_nearest_station"] = None
                    continue
                
                # Extract stations if not already cached
                if api_type not in api_stations_cache:
                    stations = extract_stations_from_api(api_data)
                    api_stations_cache[api_type] = stations
                else:
                    stations = api_stations_cache[api_type]
                
                # Find nearest station
                nearest = find_nearest_station(stations, location_coords)
                
                if nearest:
                    # Get value from nearest station
                    value = get_station_value(api_data, nearest['id'])
                    
                    # Add to data point
                    data_point[f"{api_type}_nearest_value"] = value
                    data_point[f"{api_type}_nearest_distance"] = nearest['distance']
                    data_point[f"{api_type}_nearest_station"] = nearest['name']
                else:
                    # No nearest station found
                    data_point[f"{api_type}_nearest_value"] = None
                    data_point[f"{api_type}_nearest_distance"] = None
                    data_point[f"{api_type}_nearest_station"] = None
            
            # Add data point
            data_points.append(data_point)
            
            # Progress update
            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{len(flood_data)} flood events")
            
            # Small delay to avoid API rate limits
            time.sleep(0.5)
        
        except Exception as e:
            logger.error(f"Error processing event {i+1}: {e}")
            continue  # Skip this event and continue
    
    # Convert to DataFrame
    if not data_points:
        logger.error("No data points collected")
        return None
    
    df = pd.DataFrame(data_points)
    
    # Clean up missing values
    df = df.fillna(0)
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    logger.info(f"Dataset with nearest station data saved to {output_file}")
    
    return df

def create_ml_ready_dataset(flood_dataset, output_file="flood_ml_dataset.csv"):
    """
    Create a machine learning ready dataset from the flood dataset
    
    Parameters:
    - flood_dataset: DataFrame with flood events and nearest station data
    - output_file: Path to output CSV file
    
    Returns:
    - DataFrame with ML-ready features
    """
    if flood_dataset is None or len(flood_dataset) == 0:
        logger.error("No flood data available")
        return None
    
    # Create a copy of the dataset
    df = flood_dataset.copy()
    
    # Create balanced dataset (add non-flood examples)
    non_flood_rows = []
    for _, row in df.iterrows():
        # Create non-flood version with modified weather values
        non_flood = row.copy()
        non_flood['flood'] = 0
        
        # Reduce rainfall by 40-70%
        if 'rainfall_nearest_value' in non_flood and non_flood['rainfall_nearest_value'] > 0:
            non_flood['rainfall_nearest_value'] *= np.random.uniform(0.3, 0.6)
        
        # Reduce humidity slightly (5-15%)
        if 'humidity_nearest_value' in non_flood and non_flood['humidity_nearest_value'] > 0:
            non_flood['humidity_nearest_value'] *= np.random.uniform(0.85, 0.95)
        
        non_flood_rows.append(non_flood)
    
    # Add non-flood examples to dataset
    balanced_df = pd.concat([df, pd.DataFrame(non_flood_rows)])
    
    # Drop columns not needed for ML
    drop_columns = ['datetime', 'location']
    drop_columns.extend([col for col in balanced_df.columns if 'nearest_station' in col])
    
    ml_df = balanced_df.drop(columns=[col for col in drop_columns if col in balanced_df.columns])
    
    # Shuffle the dataset
    ml_df = ml_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Save to CSV
    ml_df.to_csv(output_file, index=False)
    logger.info(f"ML-ready dataset saved to {output_file}")
    
    return ml_df

# Main execution
if __name__ == "__main__":
    flood_data_file = "flood_warnings_clean_small.json"  # Path to cleaned flood warning data
    
    # Create dataset with nearest station data
    flood_df = create_flood_dataset_with_nearest_stations(flood_data_file)
    
    if flood_df is not None:
        # Create ML-ready dataset
        ml_df = create_ml_ready_dataset(flood_df)
        
        print("\nDataset creation complete!")
        print(f"Flood dataset with nearest stations: {len(flood_df)} rows")
        if ml_df is not None:
            print(f"ML-ready dataset: {len(ml_df)} rows")
            print(f"Number of features: {len(ml_df.columns) - 1}")  # Excluding the target variable
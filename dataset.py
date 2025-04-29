import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime
import time
import logging

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

def fetch_api_data_with_retry(api_type, date_time, max_retries=3, delay=1):
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
            logger.info(f"Fetching {api_type} data for {date_time} (attempt {attempt+1}/{max_retries})")
            response = requests.get(url, params=params, timeout=10)
            
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

def extract_weather_data(api_response):
    """
    Extract weather data values from API response
    
    Parameters:
    - api_response: JSON response from API
    
    Returns:
    - Dictionary with weather statistics
    """
    if not api_response or 'data' not in api_response:
        return {
            'mean': 0,
            'min': 0,
            'max': 0,
            'count': 0
        }
    
    # Check if readings exist
    if 'readings' not in api_response['data'] or not api_response['data']['readings']:
        return {
            'mean': 0,
            'min': 0,
            'max': 0,
            'count': 0
        }
    
    # Get the last reading
    latest_reading = api_response['data']['readings'][-1]
    
    # Check if data exists in the reading
    if 'data' not in latest_reading or not latest_reading['data']:
        return {
            'mean': 0,
            'min': 0,
            'max': 0,
            'count': 0
        }
    
    # Extract values from all stations
    values = [item['value'] for item in latest_reading['data'] if 'value' in item]
    
    if not values:
        return {
            'mean': 0,
            'min': 0,
            'max': 0,
            'count': 0
        }
    
    return {
        'mean': np.mean(values),
        'min': np.min(values),
        'max': np.max(values),
        'count': len(values)
    }

def create_flood_event_dataset(flood_data_file, output_file="flood_events_data.csv"):
    """
    Create dataset with weather data at each flood event time
    
    Parameters:
    - flood_data_file: Path to JSON file with flood warning data
    - output_file: Path to output CSV file
    
    Returns:
    - DataFrame with flood events and weather data
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
    
    # Process each flood event
    for i, flood in enumerate(flood_data):
        try:
            # Extract flood event details
            flood_datetime = flood['datetime']
            flood_location = flood['location']
            
            logger.info(f"Processing event {i+1}/{len(flood_data)}: {flood_location} at {flood_datetime}")
            
            # Create data point with flood details
            data_point = {
                'datetime': flood_datetime,
                'location': flood_location,
                'flood': 1  # This is a flood event
            }
            
            # Collect data from each API
            api_success = False  # Track if any API call succeeds
            
            for api_type in API_ENDPOINTS.keys():
                # Get API data
                api_data = fetch_api_data_with_retry(api_type, flood_datetime)
                
                if api_data:
                    api_success = True
                    
                    # Extract weather data
                    weather_stats = extract_weather_data(api_data)
                    
                    # Add to data point
                    data_point[f"{api_type}_mean"] = weather_stats['mean']
                    data_point[f"{api_type}_min"] = weather_stats['min']
                    data_point[f"{api_type}_max"] = weather_stats['max']
                    data_point[f"{api_type}_stations"] = weather_stats['count']
                else:
                    # No data available
                    data_point[f"{api_type}_mean"] = 0
                    data_point[f"{api_type}_min"] = 0
                    data_point[f"{api_type}_max"] = 0
                    data_point[f"{api_type}_stations"] = 0
            
            # Only add data point if at least one API call succeeded
            if api_success:
                data_points.append(data_point)
                logger.info(f"Successfully added data for event {i+1}")
            else:
                logger.warning(f"No weather data available for event {i+1}, skipping")
            
            # Add small delay to avoid rate limiting
            time.sleep(1)
        
        except Exception as e:
            logger.error(f"Error processing event {i+1}: {e}")
            continue  # Skip this event and continue
    
    # Check if we have any data points
    if not data_points:
        logger.error("No data points collected for any flood events")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(data_points)
    logger.info(f"Created dataset with {len(df)} flood events")
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    logger.info(f"Dataset saved to {output_file}")
    
    return df

def create_balanced_dataset(flood_dataset, output_file="flood_prediction_dataset.csv"):
    """
    Create a balanced dataset with equal flood and non-flood examples
    
    Parameters:
    - flood_dataset: DataFrame with flood events and weather data
    - output_file: Path to output CSV file
    
    Returns:
    - DataFrame with balanced flood and non-flood examples
    """
    if flood_dataset is None or len(flood_dataset) == 0:
        logger.error("No flood data available to create balanced dataset")
        return None
    
    # Get number of flood events
    num_flood = len(flood_dataset)
    logger.info(f"Creating balanced dataset with {num_flood} non-flood examples")
    
    # Create non-flood examples by altering the weather data slightly
    non_flood_data = []
    
    for _, row in flood_dataset.iterrows():
        # Create a non-flood example by decreasing rainfall and/or humidity
        non_flood = row.copy()
        non_flood['flood'] = 0  # This is not a flood event
        
        # Reduce rainfall by a random percentage (40-60%)
        if 'rainfall_mean' in non_flood:
            reduction = np.random.uniform(0.4, 0.6)
            non_flood['rainfall_mean'] *= reduction
            non_flood['rainfall_max'] *= reduction
            non_flood['rainfall_min'] *= reduction
        
        # Reduce humidity slightly (by 5-15%)
        if 'humidity_mean' in non_flood:
            reduction = np.random.uniform(0.05, 0.15)
            non_flood['humidity_mean'] = max(0, non_flood['humidity_mean'] * (1 - reduction))
            non_flood['humidity_max'] = max(0, non_flood['humidity_max'] * (1 - reduction))
            non_flood['humidity_min'] = max(0, non_flood['humidity_min'] * (1 - reduction))
        
        non_flood_data.append(non_flood)
    
    # Create balanced dataset
    non_flood_df = pd.DataFrame(non_flood_data)
    balanced_df = pd.concat([flood_dataset, non_flood_df])
    
    # Shuffle the dataset
    balanced_df = balanced_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Save to CSV
    balanced_df.to_csv(output_file, index=False)
    logger.info(f"Balanced dataset with {len(balanced_df)} examples saved to {output_file}")
    
    return balanced_df

# Main execution
if __name__ == "__main__":
    flood_data_file = "flood_warnings_clean.json"  # Path to cleaned flood warning data
    
    # Create dataset with flood events and weather data
    flood_events_df = create_flood_event_dataset(flood_data_file)
    
    if flood_events_df is not None:
        # Create balanced dataset with flood and non-flood examples
        balanced_df = create_balanced_dataset(flood_events_df)
        
        print("\nDataset creation complete!")
        print(f"Flood events dataset: {len(flood_events_df)} examples")
        if balanced_df is not None:
            print(f"Balanced dataset: {len(balanced_df)} examples")
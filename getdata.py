import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
import logging
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("weather_data_collection.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API endpoints
API_ENDPOINTS = {
    "temperature": "https://api-open.data.gov.sg/v2/real-time/api/air-temperature",
    "rainfall": "https://api-open.data.gov.sg/v2/real-time/api/rainfall",
    "humidity": "https://api-open.data.gov.sg/v2/real-time/api/relative-humidity",
    "wind_direction": "https://api-open.data.gov.sg/v2/real-time/api/wind-direction",
    "wind_speed": "https://api-open.data.gov.sg/v2/real-time/api/wind-speed",
}

def create_date_range(start_date, end_date, hour_interval=1):
    """
    Create a range of datetime objects at hourly intervals
    
    Parameters:
    - start_date: Start date string (YYYY-MM-DD)
    - end_date: End date string (YYYY-MM-DD)
    - hour_interval: Interval in hours (default: 1)
    
    Returns:
    - List of datetime strings in ISO format
    """
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)  # Include end date
    
    date_range = []
    current_dt = start_dt
    
    while current_dt < end_dt:
        date_range.append(current_dt.strftime("%Y-%m-%dT%H:%M:%S"))
        current_dt += timedelta(hours=hour_interval)
    
    return date_range

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

def create_directory(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def collect_monthly_data(start_date, end_date, output_dir="weather_data"):
    """
    Collect weather data for a month, combining all parameters by station
    
    Parameters:
    - start_date: Start date string (YYYY-MM-DD)
    - end_date: End date string (YYYY-MM-DD)
    - output_dir: Directory to save CSV files
    """
    # Create output directory
    create_directory(output_dir)
    
    # Create date range
    logger.info(f"Creating date range from {start_date} to {end_date}")
    date_range = create_date_range(start_date, end_date)
    logger.info(f"Generated {len(date_range)} timestamps")
    
    # Dictionary to store station metadata
    station_metadata = {}
    
    # Dictionary to store combined data for each station
    # Structure: station_data[station_id][timestamp] = {param1: value1, param2: value2, ...}
    station_data = {}
    
    # Process each timestamp
    for timestamp in tqdm(date_range, desc=f"Collecting data for {start_date} to {end_date}"):
        # Process each API type
        for api_type in API_ENDPOINTS.keys():
            # Fetch data
            api_data = fetch_api_data(api_type, timestamp)
            
            if not api_data:
                continue
            
            # Extract stations
            stations = extract_stations(api_data)
            
            # Update station metadata
            for station_id, station_info in stations.items():
                if station_id not in station_metadata:
                    station_metadata[station_id] = station_info
            
            # Extract readings
            readings = extract_readings(api_data, timestamp, api_type)
            
            # Update station data
            for station_id, reading in readings.items():
                if station_id not in station_data:
                    station_data[station_id] = {}
                
                timestamp_str = reading['timestamp']
                
                if timestamp_str not in station_data[station_id]:
                    station_data[station_id][timestamp_str] = {'timestamp': timestamp_str}
                
                # Add parameter value
                station_data[station_id][timestamp_str][api_type] = reading.get(api_type)
        
        # Add short delay to avoid rate limiting
        time.sleep(0.1)
    
    # Save data for each station
    for station_id, timestamps in station_data.items():
        # Create DataFrame from station data
        rows = list(timestamps.values())
        df = pd.DataFrame(rows)
        
        # Ensure timestamp column is first
        if 'timestamp' in df.columns:
            cols = ['timestamp'] + [col for col in df.columns if col != 'timestamp']
            df = df[cols]
        
        # Get station info
        station_info = station_metadata.get(station_id, {'name': 'Unknown'})
        station_name = station_info.get('name', 'Unknown').replace(" ", "_")
        
        # Sort by timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Create filename
        filename = f"{station_id}_{station_name}.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Save to CSV
        df.to_csv(filepath, index=False)
        logger.info(f"Saved {len(df)} records to {filepath}")
    
    # Save station metadata
    metadata_df = pd.DataFrame.from_dict(station_metadata, orient='index')
    metadata_filepath = os.path.join(output_dir, "station_metadata.csv")
    metadata_df.to_csv(metadata_filepath, index=True)
    logger.info(f"Saved metadata for {len(metadata_df)} stations to {metadata_filepath}")
    
    return station_metadata

def collect_data_by_month(start_date, end_date, output_dir="weather_data"):
    """
    Collect data month by month to avoid memory issues
    
    Parameters:
    - start_date: Start date string (YYYY-MM-DD)
    - end_date: End date string (YYYY-MM-DD)
    - output_dir: Directory to save CSV files
    
    Returns:
    - Dictionary of all station metadata
    """
    # Create output directory
    create_directory(output_dir)
    
    # Parse start and end dates
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Dictionary to store all station metadata
    all_station_metadata = {}
    
    # Process month by month
    current_start = start_dt
    
    while current_start <= end_dt:
        # Calculate end of month (or end_date if earlier)
        if current_start.month == 12:
            next_month = datetime(current_start.year + 1, 1, 1)
        else:
            next_month = datetime(current_start.year, current_start.month + 1, 1)
        
        current_end = min(next_month - timedelta(days=1), end_dt)
        
        # Format dates
        month_start_str = current_start.strftime("%Y-%m-%d")
        month_end_str = current_end.strftime("%Y-%m-%d")
        month_name = current_start.strftime("%Y_%m")
        
        # Create month directory
        month_dir = os.path.join(output_dir, month_name)
        create_directory(month_dir)
        
        # Collect data for this month
        logger.info(f"Collecting data for {month_name}: {month_start_str} to {month_end_str}")
        station_metadata = collect_monthly_data(month_start_str, month_end_str, month_dir)
        
        # Update all station metadata
        all_station_metadata.update(station_metadata)
        
        # Move to next month
        current_start = next_month
    
    return all_station_metadata

def merge_monthly_data(output_dir="weather_data", final_dir="all_stations"):
    """
    Merge monthly data into single files for each station
    
    Parameters:
    - output_dir: Directory containing monthly data
    - final_dir: Directory to save merged files
    """
    # Create output directory
    create_directory(final_dir)
    
    # Dictionary to store data for each station
    station_files = {}
    
    # List all month directories
    month_dirs = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d)) and d.startswith("20")]
    
    # Find all station files
    for month_dir in month_dirs:
        month_path = os.path.join(output_dir, month_dir)
        
        for filename in os.listdir(month_path):
            if not filename.endswith(".csv") or filename == "station_metadata.csv":
                continue
            
            # Extract station ID from filename
            station_id = filename.split("_")[0]
            
            if station_id not in station_files:
                station_files[station_id] = []
            
            filepath = os.path.join(month_path, filename)
            station_files[station_id].append(filepath)
    
    # Merge data for each station
    for station_id, file_paths in tqdm(station_files.items(), desc="Merging station data"):
        # Read and concatenate all files
        dfs = []
        station_name = None
        
        for filepath in file_paths:
            try:
                df = pd.read_csv(filepath)
                dfs.append(df)
                
                # Extract station name from filename if not already set
                if station_name is None:
                    filename = os.path.basename(filepath)
                    parts = filename.split("_")
                    station_name = "_".join(parts[1:]).replace(".csv", "")
            except Exception as e:
                logger.error(f"Error reading {filepath}: {e}")
        
        if not dfs:
            logger.warning(f"No valid data files for station {station_id}")
            continue
        
        # Concatenate all dataframes
        merged_df = pd.concat(dfs, ignore_index=True)
        
        # Convert timestamp to datetime for sorting
        merged_df['timestamp'] = pd.to_datetime(merged_df['timestamp'])
        
        # Sort by timestamp
        merged_df = merged_df.sort_values('timestamp')
        
        # Remove duplicates
        merged_df = merged_df.drop_duplicates(subset=['timestamp'])
        
        # Create output filename
        filename = f"{station_id}_{station_name}.csv"
        filepath = os.path.join(final_dir, filename)
        
        # Save to CSV
        merged_df.to_csv(filepath, index=False)
        logger.info(f"Saved merged data with {len(merged_df)} records to {filepath}")

# Main execution
if __name__ == "__main__":
    # Define date range
    start_date = "2024-05-01"
    end_date = "2024-11-21"
    
    # Create output directories
    monthly_dir = "singapore_weather_monthly"
    final_dir = "singapore_weather_stations"
    
    # Collect data month by month
    all_station_metadata = collect_data_by_month(start_date, end_date, monthly_dir)
    
    # Save complete station metadata
    metadata_df = pd.DataFrame.from_dict(all_station_metadata, orient='index')
    metadata_filepath = os.path.join(final_dir, "all_station_metadata.csv")
    create_directory(final_dir)
    metadata_df.to_csv(metadata_filepath, index=True)
    logger.info(f"Saved complete metadata for {len(metadata_df)} stations to {metadata_filepath}")
    
    # Merge monthly data
    merge_monthly_data(monthly_dir, final_dir)
    
    logger.info("Data collection complete!")
    print("\nWeather data collection complete!")
    print(f"Monthly data is saved in: {monthly_dir}")
    print(f"Merged data by station is saved in: {final_dir}")
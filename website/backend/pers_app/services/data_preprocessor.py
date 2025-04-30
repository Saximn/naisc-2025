import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from math import radians, sin, cos, sqrt, atan2
from tqdm import tqdm

logger = logging.getLogger(__name__)

# Singapore bounds for grid creation
SG_LAT_MIN, SG_LAT_MAX = 1.15, 1.50  # Latitude bounds
SG_LON_MIN, SG_LON_MAX = 103.6, 104.1  # Longitude bounds

# Required station coordinates
STATION_COORDS = {
    'S109': {'latitude': 1.3764, 'longitude': 103.8492},
    'S117': {'latitude': 1.256, 'longitude': 103.679},
    'S50': {'latitude': 1.3337, 'longitude': 103.7768},
    'S107': {'latitude': 1.3135, 'longitude': 103.9625},
    'S43': {'latitude': 1.3399, 'longitude': 103.8878},
    'S44': {'latitude': 1.34583, 'longitude': 103.68166},
    'S121': {'latitude': 1.37288, 'longitude': 103.72244},
    'S111': {'latitude': 1.31055, 'longitude': 103.8365},
    'S60': {'latitude': 1.25, 'longitude': 103.8279},
    'S115': {'latitude': 1.29377, 'longitude': 103.61843},
    'S24': {'latitude': 1.3678, 'longitude': 103.9826},
    'S116': {'latitude': 1.281, 'longitude': 103.754},
    'S104': {'latitude': 1.44387, 'longitude': 103.78538},
    'S77': {'latitude': 1.2937, 'longitude': 103.8125},
    'S64': {'latitude': 1.3824, 'longitude': 103.7603},
    'S90': {'latitude': 1.3191, 'longitude': 103.8191},
    'S114': {'latitude': 1.38, 'longitude': 103.73},
    'S215': {'latitude': 1.32785, 'longitude': 103.88899},
    'S118': {'latitude': 1.2994, 'longitude': 103.8461},
    'S120': {'latitude': 1.30874, 'longitude': 103.818},
    'S33': {'latitude': 1.3081, 'longitude': 103.71},
    'S71': {'latitude': 1.2923, 'longitude': 103.7815},
    'S66': {'latitude': 1.4387, 'longitude': 103.7363},
    'S112': {'latitude': 1.43854, 'longitude': 103.70131},
    'S07': {'latitude': 1.3415, 'longitude': 103.8334},
    'S40': {'latitude': 1.4044, 'longitude': 103.78962},
    'S113': {'latitude': 1.30648, 'longitude': 103.9104},
    'S119': {'latitude': 1.30105, 'longitude': 103.8666},
    'S35': {'latitude': 1.3329, 'longitude': 103.7556},
    'S94': {'latitude': 1.3662, 'longitude': 103.9528},
    'S78': {'latitude': 1.30703, 'longitude': 103.89067},
    'S81': {'latitude': 1.4029, 'longitude': 103.9092},
    'S201': {'latitude': 1.32311, 'longitude': 103.76714},
    'S203': {'latitude': 1.29164, 'longitude': 103.7702},
    'S207': {'latitude': 1.32485, 'longitude': 103.95836},
    'S208': {'latitude': 1.3136, 'longitude': 104.00317},
    'S209': {'latitude': 1.42111, 'longitude': 103.84472},
    'S210': {'latitude': 1.44003, 'longitude': 103.76904},
    'S211': {'latitude': 1.42918, 'longitude': 103.75711},
    'S212': {'latitude': 1.31835, 'longitude': 103.93574},
    'S213': {'latitude': 1.32427, 'longitude': 103.8097},
    'S214': {'latitude': 1.29911, 'longitude': 103.88289},
    'S216': {'latitude': 1.36019, 'longitude': 103.85335},
    'S217': {'latitude': 1.35041, 'longitude': 103.85526},
    'S218': {'latitude': 1.36491, 'longitude': 103.75065},
    'S219': {'latitude': 1.37999, 'longitude': 103.87643},
    'S220': {'latitude': 1.38666, 'longitude': 103.89797},
    'S221': {'latitude': 1.35691, 'longitude': 103.89088},
    'S222': {'latitude': 1.28987, 'longitude': 103.82364},
    'S223': {'latitude': 1.29984, 'longitude': 103.80264},
    'S224': {'latitude': 1.34392, 'longitude': 103.98409},
    'S226': {'latitude': 1.27472, 'longitude': 103.80389},
    'S227': {'latitude': 1.43944, 'longitude': 103.80389},
    'S228': {'latitude': 1.34703, 'longitude': 103.70073},
    'S229': {'latitude': 1.35167, 'longitude': 103.72195},
    'S230': {'latitude': 1.30167, 'longitude': 103.76444},
    'S900': {'latitude': 1.41284, 'longitude': 103.86922},
    'S84': {'latitude': 1.3437, 'longitude': 103.9444},
    'S79': {'latitude': 1.3004, 'longitude': 103.8372},
    'S88': {'latitude': 1.3427, 'longitude': 103.8482},
    'S123': {'latitude': 1.3214, 'longitude': 103.8577},
    'S89': {'latitude': 1.31985, 'longitude': 103.66162},
    'S69': {'latitude': 1.37, 'longitude': 103.805},
    'S08': {'latitude': 1.3701, 'longitude': 103.8271},
    'S108': {'latitude': 1.2799, 'longitude': 103.8703},
    'S102': {'latitude': 1.189, 'longitude': 103.768},
    'S106': {'latitude': 1.4168, 'longitude': 103.9673},
    'S92': {'latitude': 1.2841, 'longitude': 103.7886},
    'S29': {'latitude': 1.387, 'longitude': 103.935},
    'S06': {'latitude': 1.3524, 'longitude': 103.9007}
}

def get_last_24_hours_data():
    """
    Get weather data for the last 24 hours from the database
    
    Returns:
    - Pandas DataFrame with weather data
    """
    from pers_app.models import WeatherReading
    from django.utils import timezone

    end_time = timezone.now()
    start_time = end_time - timedelta(hours=24)
    
    # Query readings for the last 24 hours
    readings = WeatherReading.objects.filter(
        timestamp__gte=start_time,
        timestamp__lte=end_time
    ).select_related('station').order_by('timestamp')
    
    # Convert to DataFrame
    data = []
    for reading in readings:
        data.append({
            'station_id': reading.station.station_id,
            'station_name': reading.station.name,
            'latitude': reading.station.latitude,
            'longitude': reading.station.longitude,
            'timestamp': reading.timestamp,
            'temperature': reading.temperature,
            'rainfall': reading.rainfall,
            'humidity': reading.humidity,
            'wind_direction': reading.wind_direction,
            'wind_speed': reading.wind_speed
        })
    
    return pd.DataFrame(data)

def standardize_and_convert_wind_vectors(df):
    """
    Standardize columns and convert wind direction and speed to u, v components
    
    Parameters:
    - df: Pandas DataFrame with weather data
    
    Returns:
    - Standardized DataFrame with wind vectors in u,v format
    """
    logger.info("Standardizing data and converting wind vectors")
    
    # Ensure all required columns exist
    required_cols = ['timestamp', 'temperature', 'rainfall', 'humidity', 'wind_direction', 'wind_speed']
    for col in required_cols:
        if col not in df.columns:
            df[col] = pd.NA
    
    # Reorder columns
    df = df[required_cols + [col for col in df.columns if col not in required_cols]]
    
    # Convert wind direction and speed to u, v components
    theta = np.deg2rad(df['wind_direction'])
    df = df.copy()  # Avoid SettingWithCopyWarning
    df['wind_u'] = df['wind_speed'] * np.sin(theta)
    df['wind_v'] = df['wind_speed'] * np.cos(theta)
    
    # Drop the old columns
    df.drop(columns=['wind_direction', 'wind_speed'], inplace=True)
    
    return df

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    
    Returns distance in meters
    """
    R = 6371000  # Earth radius in meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))

def haversine_vectorized(lat1, lon1, lat2_array, lon2_array):
    """
    Vectorized haversine distance calculation
    
    Parameters:
    -----------
    lat1, lon1 : float
        Latitude and longitude of single point
    lat2_array, lon2_array : np.ndarray
        Arrays of latitudes and longitudes for multiple points
        
    Returns:
    --------
    distances : np.ndarray
        Array of distances in meters
    """
    R = 6371000  # Earth radius in meters
    
    # Convert to radians
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = np.radians(lat2_array)
    lon2_rad = np.radians(lon2_array)
    
    # Haversine formula components
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    
    return R * c

def prepare_station_data(df):
    """
    Prepare station data for interpolation
    
    Parameters:
    - df: Pandas DataFrame with weather data
    
    Returns:
    - station_data: numpy array with shape (n_stations, n_features)
    - station_coords: numpy array with shape (n_stations, 2)
    - station_ids: list of station IDs
    """
    logger.info("Preparing station data for interpolation")
    
    # Get unique timestamps (we're only using the latest timestamp)
    latest_timestamp = df['timestamp'].max()
    df_latest = df[df['timestamp'] == latest_timestamp].copy()
    
    # Get unique stations
    stations = df_latest[['station_id', 'latitude', 'longitude']].drop_duplicates()
    station_ids = stations['station_id'].tolist()
    
    # Create a mapping from station ID to index
    station_index = {sid: i for i, sid in enumerate(station_ids)}
    
    # Prepare coordinates array
    n_stations = len(station_ids)
    station_coords = np.zeros((n_stations, 2))
    
    # Fill coordinates from stations DataFrame
    for i, (_, row) in enumerate(stations.iterrows()):
        station_coords[i, 0] = row['latitude']
        station_coords[i, 1] = row['longitude']
    
    # Add missing stations from STATION_COORDS
    missing_stations = set(STATION_COORDS.keys()) - set(station_ids)
    for station_id in missing_stations:
        station_ids.append(station_id)
        idx = len(station_coords)
        station_index[station_id] = idx
        
        # Add new row to coordinates array
        coords = STATION_COORDS[station_id]
        new_coord = np.array([[coords['latitude'], coords['longitude']]])
        station_coords = np.vstack((station_coords, new_coord))
    
    # Features we're interested in
    features = ['temperature', 'humidity', 'rainfall', 'wind_u', 'wind_v']
    
    # Prepare data array
    n_stations = len(station_ids)
    n_features = len(features)
    station_data = np.full((n_stations, n_features), np.nan)
    
    # Fill in data
    for _, row in df_latest.iterrows():
        sid = row['station_id']
        if sid in station_index:
            i = station_index[sid]
            for j, feat in enumerate(features):
                if feat in row and not pd.isna(row[feat]):
                    station_data[i, j] = row[feat]
    
    return station_data, station_coords, station_ids

def impute_missing_values(station_data, station_coords, power=2):
    """
    Impute missing values using IDW (Inverse Distance Weighting)
    
    Parameters:
    - station_data: numpy array with shape (n_stations, n_features)
    - station_coords: numpy array with shape (n_stations, 2)
    - power: power parameter for IDW
    
    Returns:
    - completed: numpy array with shape (n_stations, n_features)
    """
    logger.info("Imputing missing values using IDW")
    
    n_stations = station_data.shape[0]
    
    # Compute pairwise distances
    dist = np.full((n_stations, n_stations), np.inf)
    for i in range(n_stations):
        for j in range(n_stations):
            if i != j:
                dist[i, j] = haversine(
                    station_coords[i, 0], station_coords[i, 1],
                    station_coords[j, 0], station_coords[j, 1]
                )
    
    # Compute global IDW weights
    W_glob = 1.0 / (dist ** power)
    # Avoid division by zero by setting diagonal to 0
    np.fill_diagonal(W_glob, 0)
    # Normalize weights
    W_glob = W_glob / W_glob.sum(axis=1, keepdims=True)
    
    # Build mask of missing entries
    mask = np.isnan(station_data)
    
    # Prepare array to hold imputed values
    add = np.zeros_like(station_data)
    
    # For each feature, compute the global IDW filled values
    for f in range(station_data.shape[1]):
        feat = station_data[:, f]
        # Numerator: weighted sum, treating NaN as zero
        num = W_glob.dot(np.nan_to_num(feat, nan=0.0))
        # Denominator: sum of weights where data exists
        valid = (~np.isnan(feat)).astype(float)
        den = W_glob.dot(valid)
        den[den == 0] = np.nan  # Avoid division by zero
        filled = num / den
        add[:, f] = filled
    
    # Compute the completed array
    completed = np.array(station_data, copy=True)
    completed[mask] = add[mask]
    
    return completed

def create_singapore_grid(resolution=500):
    """
    Create a grid covering Singapore with specified resolution in meters
    
    Parameters:
    - resolution: Grid cell size in meters
    
    Returns:
    - grid_coords: numpy array with shape (n_grid_points, 2)
    - lat_grid: numpy array with latitudes
    - lon_grid: numpy array with longitudes
    """
    logger.info(f"Creating Singapore grid with {resolution}m resolution")
    
    # Calculate grid size in degrees
    LAT_STEP = resolution / 111000  # Convert meters to degrees latitude
    LON_STEP = resolution / 110000  # Convert meters to degrees longitude
    
    # Create grid coordinates
    lat_grid = np.arange(SG_LAT_MIN, SG_LAT_MAX, LAT_STEP)
    lon_grid = np.arange(SG_LON_MIN, SG_LON_MAX, LON_STEP)
    lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
    
    # Flatten grid for interpolation
    grid_coords = np.column_stack((lat_mesh.flatten(), lon_mesh.flatten()))
    
    return grid_coords, lat_grid, lon_grid

def idw_interpolation_5_nearest(station_data, station_coords, grid_coords, p=2, batch_size=1000):
    """
    Inverse Distance Weighting interpolation using 5 nearest stations
    
    Parameters:
    - station_data: numpy array with shape (n_stations, n_features)
    - station_coords: numpy array with shape (n_stations, 2)
    - grid_coords: numpy array with shape (n_grid_points, 2)
    - p: power parameter for IDW
    - batch_size: number of grid points to process at once
    
    Returns:
    - grid_data: numpy array with shape (n_grid_points, n_features)
    """
    logger.info("Performing IDW interpolation with 5 nearest stations")
    
    n_stations, n_features = station_data.shape
    n_grid_points = grid_coords.shape[0]
    
    # Extract station coordinates
    station_lats = station_coords[:, 0]
    station_lons = station_coords[:, 1]
    
    # Initialize result array
    grid_data = np.zeros((n_grid_points, n_features))
    
    # Process grid points in batches to manage memory
    for start_idx in range(0, n_grid_points, batch_size):
        end_idx = min(start_idx + batch_size, n_grid_points)
        batch_grid_coords = grid_coords[start_idx:end_idx]
        batch_size_actual = end_idx - start_idx
        
        # Calculate Haversine distances for this batch
        batch_distances = np.zeros((batch_size_actual, n_stations))
        
        for i in range(batch_size_actual):
            grid_lat = batch_grid_coords[i, 0]
            grid_lon = batch_grid_coords[i, 1]
            batch_distances[i] = haversine_vectorized(grid_lat, grid_lon, station_lats, station_lons)
        
        # Find 5 nearest stations for each grid point in batch
        nearest_indices = np.argsort(batch_distances, axis=1)[:, :5]
        
        # For each grid point in this batch
        for i in range(batch_size_actual):
            # Get the 5 nearest station indices
            idx = nearest_indices[i]
            
            # Get the distances to these 5 nearest stations
            dist = batch_distances[i, idx]
            
            # Avoid division by zero for exact matches
            dist = np.where(dist == 0, 1e-10, dist)
            
            # Calculate weights using IDW formula
            weights = 1.0 / (dist ** p)
            weights = weights / np.sum(weights)
            
            # Reshape weights for broadcasting
            weights_reshaped = weights.reshape(-1, 1)
            
            # Get data for 5 nearest stations
            station_subset = station_data[idx]
            
            # Apply weights and store result
            grid_data[start_idx + i] = np.sum(weights_reshaped * station_subset, axis=0)
    
    return grid_data

def interpolate_to_grid(station_data, station_coords, resolution=500, p=2):
    """
    Interpolate station data to a regular grid
    
    Parameters:
    - station_data: numpy array with shape (n_stations, n_features)
    - station_coords: numpy array with shape (n_stations, 2)
    - resolution: Grid cell size in meters
    - p: power parameter for IDW
    
    Returns:
    - grid_data_reshaped: numpy array with shape (78, 110, 5)
    """
    # Create grid
    grid_coords, lat_grid, lon_grid = create_singapore_grid(resolution)
    
    # Perform interpolation
    flat_grid_data = idw_interpolation_5_nearest(
        station_data, station_coords, grid_coords, p=p
    )
    
    # Get dimensions
    n_features = station_data.shape[1]
    
    # Reshape to grid
    grid_data = flat_grid_data.reshape(len(lat_grid), len(lon_grid), n_features)
    
    # Resize to exact 78x110 grid using simple interpolation
    # This ensures the grid is exactly 78x110 regardless of the resolution
    target_shape = (78, 110, n_features)
    grid_data_reshaped = np.zeros(target_shape)
    
    # Simple bilinear interpolation
    src_height, src_width = len(lat_grid), len(lon_grid)
    for i in range(78):
        for j in range(110):
            # Map indices to source grid
            src_i = i / 78 * src_height
            src_j = j / 110 * src_width
            
            # Get indices of four nearest neighbors
            i0, j0 = int(src_i), int(src_j)
            i1, j1 = min(i0 + 1, src_height - 1), min(j0 + 1, src_width - 1)
            
            # Get weights
            wi, wj = src_i - i0, src_j - j0
            
            # Bilinear interpolation
            grid_data_reshaped[i, j] = (
                (1 - wi) * (1 - wj) * grid_data[i0, j0] +
                wi * (1 - wj) * grid_data[i1, j0] +
                (1 - wi) * wj * grid_data[i0, j1] +
                wi * wj * grid_data[i1, j1]
            )
    
    logger.info(f"Final grid data shape: {grid_data_reshaped.shape}")
    return grid_data_reshaped

def preprocess_to_grid(df, grid_height=78, grid_width=110):
    """
    Preprocess weather data to a grid format required by the ModelArts API
    
    Parameters:
    - df: Pandas DataFrame with weather data
    - grid_height: Height of the grid (default: 78)
    - grid_width: Width of the grid (default: 110)
    
    Returns:
    - Numpy array with shape (grid_height, grid_width, 24, 5)
      where 24 is the number of hourly readings and 5 is the number of features
    """
    logger.info("Preprocessing data to grid format")
    
    # Standardize data and convert wind vectors
    df = standardize_and_convert_wind_vectors(df)
    
    # Group by timestamp
    grouped = df.groupby('timestamp')
    
    # Get list of all timestamps, sorted
    timestamps = sorted(grouped.groups.keys())
    
    # We need exactly 24 hours of data
    if len(timestamps) < 24:
        logger.warning(f"Only {len(timestamps)} hours of data available, padding with zeros")
        # Use what we have (will be padded later)
    elif len(timestamps) > 24:
        # Use most recent 24 hours
        timestamps = timestamps[-24:]
    
    # Initialize the output array
    output = np.zeros((grid_height, grid_width, 24, 5))
    
    # Process each timestamp
    for t, timestamp in enumerate(timestamps):
        logger.info(f"Processing timestamp {t+1}/{len(timestamps)}: {timestamp}")
        
        # Get data for this timestamp
        df_t = grouped.get_group(timestamp)
        
        # Prepare station data
        station_data, station_coords, station_ids = prepare_station_data(df_t)
        
        # Impute missing values
        completed = impute_missing_values(station_data, station_coords)
        
        # Interpolate to grid
        grid_data = interpolate_to_grid(completed, station_coords)
        
        # Store in output array
        output[:, :, t, :] = grid_data
    
    # If we have fewer than 24 hours, pad with zeros
    if len(timestamps) < 24:
        logger.warning("Padding missing timestamps with zeros")
        # The unprocessed timestamps are already zero because we initialized the array with zeros
    
    logger.info(f"Final output shape: {output.shape}")
    return output

def get_model_input_data():
    """
    Get the last 24 hours of weather data, preprocessed to the format required by the model
    
    Returns:
    - Numpy array with shape (78, 110, 24, 5)
    """
    logger.info("Getting input data for model")
    
    # Get raw data from database
    df = get_last_24_hours_data()
    
    if df.empty:
        logger.error("No data available for the last 24 hours")
        return None
    
    # Preprocess to grid format
    grid_data = preprocess_to_grid(df)
    
    return grid_data
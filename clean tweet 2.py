import re
import json
import pandas as pd
from datetime import datetime
import time
import logging
from geopy.geocoders import Nominatim

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_pub_flood_data(raw_text):
    """
    Parse flood warning data from PUB tweets text format
    
    Parameters:
    - raw_text: Raw text containing PUB flood warnings
    
    Returns:
    - List of dictionaries with flood warning details
    """
    # Regular expression pattern to extract information
    pattern = r'PUB\n@PUBsingapore\n·\n([A-Za-z]+ \d+(?:, \d+)?)\n\[Risk of Flash Floods\]\s*\n\nDue to heavy rain, please avoid this location for the next 1 hour: (.*?)\s*\[(\d+:\d+) hours\]'
    
    matches = re.findall(pattern, raw_text, re.DOTALL)
    
    flood_warnings = []
    
    for match in matches:
        date_str, location, time_str = match
        
        # Handle date format (convert to YYYY-MM-DD)
        if ',' in date_str:
            date_obj = datetime.strptime(date_str, '%b %d, %Y')
        else:
            # For entries without year, assume current year (2025)
            date_obj = datetime.strptime(f"{date_str} 2025", '%b %d %Y')
        
        formatted_date = date_obj.strftime('%Y-%m-%d')
        
        # Clean and normalize location strings
        location = location.strip()
        
        # Split multiple locations if separated by semicolons
        locations = [loc.strip() for loc in location.split(';') if loc.strip()]
        
        # Create entry for each location
        for loc in locations:
            flood_warnings.append({
                'date': formatted_date,
                'time': time_str,
                'location': loc,
                'datetime': f"{formatted_date}T{time_str}:00"
            })
    
    return flood_warnings

def geocode_location(location_name, max_retries=3, delay=1):
    """
    Geocode a location name to get latitude and longitude
    
    Parameters:
    - location_name: Name of the location to geocode
    - max_retries: Maximum number of retry attempts
    - delay: Delay between retries in seconds
    
    Returns:
    - Tuple of (latitude, longitude) or (None, None) if geocoding fails
    """
    # Initialize geocoder with a user agent
    geolocator = Nominatim(user_agent="flood_data_geocoder")
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Geocoding location: {location_name} (attempt {attempt+1}/{max_retries})")
            location = geolocator.geocode(f"{location_name}, Singapore")
            
            if location:
                logger.info(f"Successfully geocoded {location_name}: {location.latitude}, {location.longitude}")
                return (location.latitude, location.longitude)
            else:
                logger.warning(f"No geocoding results for {location_name}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
        except Exception as e:
            logger.error(f"Exception geocoding {location_name}: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    logger.error(f"Failed to geocode {location_name} after {max_retries} attempts")
    return (None, None)

def add_geocoding_to_flood_data(flood_warnings):
    """
    Add latitude and longitude to flood warnings data
    
    Parameters:
    - flood_warnings: List of dictionaries with flood warning details
    
    Returns:
    - List of dictionaries with added geocoding information
    """
    geocoded_warnings = []
    
    for i, warning in enumerate(flood_warnings):
        try:
            location = warning['location']
            logger.info(f"Processing event {i+1}/{len(flood_warnings)}: {location}")
            
            # Geocode the location
            latitude, longitude = geocode_location(location)
            
            # Create new warning with geocoding
            geocoded_warning = warning.copy()
            geocoded_warning['latitude'] = latitude
            geocoded_warning['longitude'] = longitude
            
            geocoded_warnings.append(geocoded_warning)
            logger.info(f"Successfully added data for event {i+1}")
            
            # Add small delay to avoid rate limiting on geocoding service
            time.sleep(1)
        
        except Exception as e:
            logger.error(f"Error processing event {i+1}: {e}")
            # Still add the warning without geocoding
            warning['latitude'] = None
            warning['longitude'] = None
            geocoded_warnings.append(warning)
            continue
    
    return geocoded_warnings

def process_flood_data_from_file(input_file="data.txt", output_file="flood_data_geocoded.csv"):
    """
    Process flood data from data.txt file, add geocoding, and save to CSV/JSON
    
    Parameters:
    - input_file: Path to raw text file (default: data.txt)
    - output_file: Path to output CSV file
    
    Returns:
    - DataFrame with processed flood data
    """
    # Read raw text from file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_text = f.read()
        logger.info(f"Loaded raw text from {input_file}")
    except Exception as e:
        logger.error(f"Error loading raw text file: {e}")
        return None
    
    # Clean and parse the data
    flood_warnings = clean_pub_flood_data(raw_text)
    logger.info(f"Extracted {len(flood_warnings)} flood warnings")
    
    # Remove duplicates
    df = pd.DataFrame(flood_warnings)
    df = df.drop_duplicates(subset=['date', 'time', 'location'])
    logger.info(f"Found {len(df)} unique flood warnings after removing duplicates")
    
    # Convert back to list for geocoding
    unique_warnings = df.to_dict('records')
    
    # Add geocoding
    geocoded_warnings = add_geocoding_to_flood_data(unique_warnings)
    
    # Convert to DataFrame and save
    geocoded_df = pd.DataFrame(geocoded_warnings)
    
    # Save to CSV
    geocoded_df.to_csv(output_file, index=False)
    logger.info(f"Geocoded dataset saved to {output_file}")
    
    # Save to JSON
    json_output_file = output_file.replace('.csv', '.json')
    with open(json_output_file, 'w') as f:
        json.dump(geocoded_warnings, f, indent=2)
    logger.info(f"Geocoded dataset also saved to {json_output_file}")
    
    return geocoded_df

# Main execution
if __name__ == "__main__":
    # Process the data from data.txt
    geocoded_df = process_flood_data_from_file(input_file="data 2.txt")
    
    if geocoded_df is not None:
        print("\nProcessing complete!")
        print(f"Processed {len(geocoded_df)} flood warnings with geocoding")
        
        # Display a sample
        print("\nSample data:")
        print(geocoded_df.head())
        
        # Print statistics
        print("\nData statistics:")
        print(f"Date range: {geocoded_df['date'].min()} to {geocoded_df['date'].max()}")
        print(f"Number of unique locations: {geocoded_df['location'].nunique()}")
        print(f"Number of locations with successful geocoding: {geocoded_df['latitude'].count()}")
        print(f"Number of locations with failed geocoding: {geocoded_df['latitude'].isna().sum()}")
import csv
import requests
import os
import time
import sys
import urllib.parse
import math

# Define Singapore's approximate bounding box
SINGAPORE_BOUNDS = {
    'min_lat': 1.1304,
    'max_lat': 1.4705,
    'min_lng': 103.5520,
    'max_lng': 104.1220
}

def is_in_singapore(lat, lng):
    """
    Check if a location is within Singapore's bounding box.
    
    Args:
        lat (float): Latitude
        lng (float): Longitude
        
    Returns:
        bool: True if in Singapore, False otherwise
    """
    # Handle None values
    if lat is None or lng is None:
        return False
        
    # Handle non-numeric values
    try:
        lat_float = float(lat)
        lng_float = float(lng)
    except (ValueError, TypeError):
        return False
        
    return (SINGAPORE_BOUNDS['min_lat'] <= lat_float <= SINGAPORE_BOUNDS['max_lat'] and
            SINGAPORE_BOUNDS['min_lng'] <= lng_float <= SINGAPORE_BOUNDS['max_lng'])

def geocode_location(location, api_key):
    """
    Call the Google Maps Geocoding API to get the latitude and longitude for a location in Singapore.
    
    Args:
        location (str): The location to geocode
        api_key (str): Google Maps API key
        
    Returns:
        tuple: (latitude, longitude) or (None, None) if geocoding fails
    """
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    # Handle empty or None location
    if not location or location.strip() == '':
        print("Empty location provided, skipping geocoding")
        return None, None
    
    # Prepare parameters with component filtering for Singapore
    params = {
        "address": location,
        "components": "country:SG",  # Filter for Singapore
        "key": api_key
    }
    
    try:
        # Make the API request
        response = requests.get(base_url, params=params)
        data = response.json()
        
        # Check if the API returned a successful response
        if data["status"] == "OK":
            # Extract the latitude and longitude from the first result
            lat = data["results"][0]["geometry"]["location"]["lat"]
            lng = data["results"][0]["geometry"]["location"]["lng"]
            return lat, lng
        else:
            print(f"Geocoding failed for location '{location}'. Status: {data['status']}")
            if "error_message" in data:
                print(f"Error message: {data['error_message']}")
            return None, None
    except Exception as e:
        print(f"Error geocoding location '{location}': {e}")
        return None, None

def process_csv(input_file, output_file, api_key):
    """
    Process the input CSV file to fix locations that are missing or outside Singapore.
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file
        api_key (str): Google Maps API key
    """
    try:
        # Read the input CSV and get header
        with open(input_file, 'r', newline='', encoding='utf-8') as csvfile:
            sample = csvfile.read(2048)
            csvfile.seek(0)  # Go back to beginning of file
            
            # Check if the CSV has a BOM (Byte Order Mark)
            has_bom = sample.startswith('\ufeff')
            
            # Use the appropriate reader
            if has_bom:
                reader = csv.DictReader(csvfile, encoding='utf-8-sig')
            else:
                reader = csv.DictReader(csvfile)
            
            # Get the fieldnames from the reader and ensure latitude and longitude are included
            fieldnames = list(reader.fieldnames) if reader.fieldnames else []
            
            # Create a copy of fieldnames to avoid modifying the original
            fieldnames_copy = fieldnames.copy()
            
            # Ensure latitude and longitude fields are in fieldnames
            if 'latitude' not in fieldnames_copy:
                fieldnames_copy.append('latitude')
            if 'longitude' not in fieldnames_copy:
                fieldnames_copy.append('longitude')
            
            # Store all rows
            rows = []
            locations_to_geocode = []
            
            print("Analyzing locations in CSV...")
            for i, row in enumerate(reader, 1):
                # Create a new row dictionary with all fields
                new_row = {field: '' for field in fieldnames_copy}
                
                # Copy existing values
                for field in row:
                    if field in fieldnames_copy:
                        new_row[field] = row[field]
                
                # Check if latitude and longitude are valid
                lat_str = new_row.get('latitude', '').strip()
                lng_str = new_row.get('longitude', '').strip()
                
                try:
                    lat = float(lat_str) if lat_str else None
                    lng = float(lng_str) if lng_str else None
                except ValueError:
                    # Handle cases where lat/lng are not valid numbers
                    lat, lng = None, None
                
                # If coordinates are missing or not in Singapore, mark for geocoding
                needs_geocoding = False
                
                if lat is None or lng is None:
                    print(f"[{i}] Missing coordinates: {new_row.get('location', 'UNKNOWN')}")
                    needs_geocoding = True
                elif not is_in_singapore(lat, lng):
                    print(f"[{i}] Outside Singapore: {new_row.get('location', 'UNKNOWN')} ({lat}, {lng})")
                    needs_geocoding = True
                
                if needs_geocoding:
                    locations_to_geocode.append((i, new_row))
                
                # Update the row with the current lat/lng (may be updated later)
                new_row['latitude'] = str(lat) if lat is not None else ''
                new_row['longitude'] = str(lng) if lng is not None else ''
                
                # Add the row to our list
                rows.append(new_row)
            
            # Now geocode the locations that need it
            print(f"\nGeocode {len(locations_to_geocode)} locations with Singapore filter...")
            for i, (row_idx, row) in enumerate(locations_to_geocode, 1):
                location = row.get('location', '')
                print(f"[{i}/{len(locations_to_geocode)}] Geocoding: {location}")
                
                # Call the geocoding API with Singapore filter
                lat, lng = geocode_location(location, api_key)
                
                # Update the row with new lat/lng
                rows[row_idx-1]['latitude'] = str(lat) if lat is not None else ''
                rows[row_idx-1]['longitude'] = str(lng) if lng is not None else ''
                
                # Add a small delay to avoid hitting API rate limits
                time.sleep(0.5)
        
        # Write to the output CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames_copy)
            writer.writeheader()
            writer.writerows(rows)
            
        print(f"\nProcessed {len(rows)} locations and wrote results to {output_file}")
        
        # Print summary
        locations_with_coords = sum(1 for row in rows if row.get('latitude') and row.get('longitude'))
        print(f"Summary: {locations_with_coords} locations with coordinates, {len(rows) - locations_with_coords} without coordinates")
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    except FileNotFoundError:
        print(f"Error: The input file '{input_file}' was not found.")
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied when accessing '{input_file}' or '{output_file}'.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

def main():
    print("Singapore Location Data Cleanup")
    print("-" * 40)
    
    # Check if the API key is provided as an environment variable
    api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    
    # If not, ask for it
    if not api_key:
        api_key = input("Please enter your Google Maps API key: ")
        if not api_key:
            print("Error: API key is required.")
            sys.exit(1)
    
    # Check for input and output file arguments
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    else:
        input_file = input("Enter the input CSV file path: ")
        output_file = input("Enter the output CSV file path: ")
        
        if not input_file or not output_file:
            print("Error: Both input and output file paths are required.")
            sys.exit(1)
    
    # Process the CSV
    process_csv(input_file, output_file, api_key)

if __name__ == "__main__":
    main()
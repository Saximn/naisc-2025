import csv
import requests
import os
import time
import sys

def geocode_location(location, api_key):
    """
    Call the Google Maps Geocoding API to get the latitude and longitude for a location.
    
    Args:
        location (str): The location to geocode
        api_key (str): Google Maps API key
        
    Returns:
        tuple: (latitude, longitude) or (None, None) if geocoding fails
    """
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    # Prepare parameters
    params = {
        "address": location,
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
    Process the input CSV file, add latitude and longitude, and write to output CSV.
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file
        api_key (str): Google Maps API key
    """
    try:
        # Read the input CSV
        with open(input_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            # Get the fieldnames from the reader
            fieldnames = reader.fieldnames
            
            # Store all rows
            rows = []
            for i, row in enumerate(reader, 1):
                # Get the location
                location = row['location']
                print(f"[{i}] Geocoding: {location}")
                
                # Call the geocoding API
                lat, lng = geocode_location(location, api_key)
                
                # Update the row with latitude and longitude
                row['latitude'] = lat if lat is not None else ''
                row['longitude'] = lng if lng is not None else ''
                
                # Add the row to our list
                rows.append(row)
                
                # Add a small delay to avoid hitting API rate limits
                time.sleep(0.5)
        
        # Write to the output CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            
        print(f"Processed {len(rows)} locations and wrote results to {output_file}")
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
    print("Google Maps Geocoding CSV Processor")
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
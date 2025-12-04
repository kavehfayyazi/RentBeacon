import os
import requests
from dotenv import load_dotenv
from geopy.geocoders import Nominatim

load_dotenv()

RENTCAST_API_KEY = os.getenv("RENTCAST_API_KEY")
RENTCAST_API_URL = os.getenv("RENTCAST_API_URL")

geolocator = Nominatim(user_agent="RentBeacon")

def fetch_rentals(latitude: float, longitude: float, radius: float, status="Active"):
    if RENTCAST_API_KEY is None or RENTCAST_API_URL is None:
        raise RuntimeError("RENTCAST_API_KEY or RENTCAST_API_URL not set in .env")

    headers = {
        'Accept': 'application/json',
        'X-Api-Key': RENTCAST_API_KEY,
    }

    params = {
        'latitude': latitude,
        'longitude': longitude,
        'radius': radius,
        'status': status
    }

    response = requests.get(RENTCAST_API_URL, params=params, headers=headers)

    if response.status_code != 200:
        print("Error from RentCast:", response.status_code, response.text)
        return []

    try:
        data = response.json()
    except ValueError:
        print("Could not decode JSON from RentCast")
        return []

    # Expecting a list of listings
    if not isinstance(data, list):
        print("Unexpected response format from RentCast:", data)
        return []

    return data

def normalize_listing(listing: dict) -> dict:
    return {
        "provider_id": listing.get("id"),
        "provider": "rentcast",

        "address": listing.get("formattedAddress"),
        "address_line1": listing.get("addressLine1"),
        "address_line2": listing.get("addressLine2"),
        "city": listing.get("city"),
        "state": listing.get("state"),
        "zip_code": listing.get("zipCode"),
        "county": listing.get("county"),

        "latitude": listing.get("latitude"),
        "longitude": listing.get("longitude"),

        "property_type": listing.get("propertyType"),
        "status": listing.get("status"),  # Active, etc.

        "price": listing.get("price"),
        "bedrooms": listing.get("bedrooms"),
        "bathrooms": listing.get("bathrooms"),
        "square_feet": listing.get("squareFootage"),
        "lot_size": listing.get("lotSize"),
        "year_built": listing.get("yearBuilt"),

        "listed_date": listing.get("listedDate"),
        "removed_date": listing.get("removedDate"),
        "created_date": listing.get("createdDate"),
        "last_seen_date": listing.get("lastSeenDate"),
        "days_on_market": listing.get("daysOnMarket"),
    }

def main():
    choice = input("Enter 'a' to input an address OR 'c' for coordinates: ").strip().lower()

    address = None
    latitude = None
    longitude = None

    if choice == "a":
        address = input("Enter an address (e.g., '5000 Forbes Ave, Pittsburgh PA'): ").strip()
        location = geolocator.geocode(address)

        if location is None:
            print("Invalid address. Please try again.")


        latitude, longitude = location.latitude, location.longitude
        print(f"Using address: {address}")
        print(f"Resolved to: ({latitude:.5f}, {longitude:.5f})")

    elif choice == "c":
        try:
            latitude = float(input("Enter latitude: ").strip())
            longitude = float(input("Enter longitude: ").strip())
        except ValueError:
            print("Latitude and longitude must be numbers.")
            return
        
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            print("Invalid coordinates. Please try again.")
            return

        print(f"Using coordinates: ({latitude:.5f}, {longitude:.5f})")
        
    else:
        print("Invalid choice. Please try again.")
        return
    try:
        radius = float(input("Proximity radius in miles (e.g., 5): ").strip())
    except ValueError:
        print("Radius must be a number.")
        return
    
    if address:
        print(f"\nFetching rentals within {radius:.2f} miles of '{address}' "
              f"at ({latitude:.5f}, {longitude:.5f}) ...\n")
    else:
        print(f"\nFetching rentals within {radius} miles of "
              f"({latitude:.5f}, {longitude:.5f}) ...\n")

    listings = fetch_rentals(latitude, longitude, radius)

    if not listings:
        print("No listings found or error occurred.")
        return

    print(f"Found {len(listings)} raw listings.\n")

    normalized_listings = [normalize_listing(l) for l in listings]

if __name__ == "__main__":
    main()
import os
import requests
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from mock_data import mock_listings
from sqlalchemy import String, Integer, Float, create_engine
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, sessionmaker


load_dotenv()
USE_MOCK = True

RENTCAST_API_KEY = os.getenv("RENTCAST_API_KEY")
RENTCAST_API_URL = os.getenv("RENTCAST_API_URL")
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL not set in .env")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

geolocator = Nominatim(user_agent="RentBeacon")

def init_db():
    Base.metadata.create_all(bind=engine)

class Base(DeclarativeBase):
    pass

class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    provider_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    provider: Mapped[str] = mapped_column(String)

    address: Mapped[str] = mapped_column(String, nullable=True)
    address_line1: Mapped[str] = mapped_column(String, nullable=True)
    address_line2: Mapped[str] = mapped_column(String, nullable=True)
    city: Mapped[str] = mapped_column(String, index=True, nullable=True)
    state: Mapped[str] = mapped_column(String, index=True, nullable=True)
    zip_code: Mapped[str] = mapped_column(String, index=True, nullable=True)
    county: Mapped[str] = mapped_column(String, nullable=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)

    property_type: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=True)

    price: Mapped[int] = mapped_column(Integer, nullable=True)
    bedrooms: Mapped[float] = mapped_column(Float, nullable=True)   # fractional ok
    bathrooms: Mapped[float] = mapped_column(Float, nullable=True)
    square_feet: Mapped[int] = mapped_column(Integer, nullable=True)
    lot_size: Mapped[int] = mapped_column(Integer, nullable=True)
    year_built: Mapped[int] = mapped_column(Integer, nullable=True)

    listed_date: Mapped[str] = mapped_column(String, nullable=True)
    removed_date: Mapped[str] = mapped_column(String, nullable=True)
    created_date: Mapped[str] = mapped_column(String, nullable=True)
    last_seen_date: Mapped[str] = mapped_column(String, nullable=True)
    days_on_market: Mapped[int] = mapped_column(Integer, nullable=True)

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

def upsert_listings(normalized_listings: list[dict]):
    session = SessionLocal()
    new_count = 0
    updated_count = 0

    try:
        for data in normalized_listings:
            provider_id = data.get("provider_id")
            if not provider_id:
                continue

            existing = (
                session.query(Listing)
                .filter_by(provider_id=provider_id)
                .one_or_none()
            )

            if existing is None:
                # create new Listing row
                listing_obj = Listing(**data)
                session.add(listing_obj)
                new_count += 1
            else:
                # update existing row fields
                for key, value in data.items():
                    setattr(existing, key, value)
                updated_count += 1

        session.commit()
        print(f"Upsert complete: {new_count} new, {updated_count} updated.")
    except Exception as e:
        session.rollback()
        print("Error during upsert:", e)
    finally:
        session.close()

def main():
    init_db()

    if USE_MOCK:
        listings = mock_listings
    else:
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
    upsert_listings(normalized_listings)

if __name__ == "__main__":
    main()
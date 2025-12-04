import os
from dotenv import load_dotenv
from sqlalchemy import String, Integer, Float, create_engine
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, sessionmaker

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL not set in .env")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

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
    bedrooms: Mapped[float] = mapped_column(Float, nullable=True)
    bathrooms: Mapped[float] = mapped_column(Float, nullable=True)
    square_feet: Mapped[int] = mapped_column(Integer, nullable=True)
    lot_size: Mapped[int] = mapped_column(Integer, nullable=True)
    year_built: Mapped[int] = mapped_column(Integer, nullable=True)

    listed_date: Mapped[str] = mapped_column(String, nullable=True)
    removed_date: Mapped[str] = mapped_column(String, nullable=True)
    created_date: Mapped[str] = mapped_column(String, nullable=True)
    last_seen_date: Mapped[str] = mapped_column(String, nullable=True)
    days_on_market: Mapped[int] = mapped_column(Integer, nullable=True)

def init_db():
    """Create tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    print("Database initialized.")
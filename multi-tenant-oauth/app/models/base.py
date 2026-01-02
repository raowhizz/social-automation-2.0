"""Database base configuration and session management."""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    echo=os.getenv("DEBUG", "False").lower() == "true",  # Log SQL queries in debug mode
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.

    Yields:
        Database session

    Usage:
        from fastapi import Depends
        from app.models.base import get_db

        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database (create all tables).

    Note: In production, use Alembic migrations instead.
    """
    from app.models import (
        Tenant,
        TenantUser,
        SocialAccount,
        OAuthToken,
        TokenRefreshHistory,
        PostHistory,
        WebhookEvent,
        OAuthState,
        AssetFolder,
        BrandAsset,
        RestaurantProfile,
        MenuItem,
        SalesData,
    )

    Base.metadata.create_all(bind=engine)

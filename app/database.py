"""Database models and setup for health insurance carrier data"""
import os
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Carrier(Base):
    """Health insurance carrier (Krankenkasse) model"""
    __tablename__ = 'carriers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ik_number = Column(String(9), nullable=False, index=True)
    carrier_type = Column(String(10))
    name = Column(String(200), nullable=False)
    bkk_code = Column(String(20))
    valid_from = Column(DateTime)
    function_code = Column(String(2))  # 01=new, 02=changed, 03=deleted
    acceptance_center_ik = Column(String(9), index=True)  # IK of data acceptance center
    processing_code = Column(String(10))
    address_type = Column(String(10))
    postal_code = Column(String(10))
    city = Column(String(100))
    street = Column(String(200))
    message_number = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Carrier(ik={self.ik_number}, name={self.name})>"


# Database setup
# Use environment variable if available, otherwise use default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kk_info.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

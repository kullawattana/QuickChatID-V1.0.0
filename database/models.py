"""
KYC Database Models
SQLAlchemy models for storing KYC verification data
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# Bangkok timezone (UTC+7)
BANGKOK_TZ = ZoneInfo("Asia/Bangkok")

def get_bangkok_time():
    """Get current time in Bangkok timezone"""
    return datetime.now(BANGKOK_TZ)

Base = declarative_base()


class KYCVerification(Base):
    """KYC Verification Record"""
    __tablename__ = 'kyc_verifications'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # User identification
    user_id = Column(String(100), nullable=False, index=True)  # LINE user ID
    session_id = Column(String(100), nullable=True)  # ADK session ID

    # Personal information from ID card
    id_number = Column(String(20), nullable=True, index=True)  # Thai ID number
    prefix = Column(String(20), nullable=True)  # Mr., Mrs., Miss, etc.
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    date_of_birth = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)

    # ID card OCR details
    id_card_data = Column(JSON, nullable=True)  # Full OCR data

    # Face analysis
    face_similarity_score = Column(Float, nullable=True)  # 0-100
    face_confidence = Column(Float, nullable=True)  # 0-100
    rekognition_data = Column(JSON, nullable=True)  # Full Rekognition response

    # Image storage
    id_card_image_path = Column(String(500), nullable=True)
    id_card_s3_url = Column(String(500), nullable=True)
    selfie_image_path = Column(String(500), nullable=True)
    selfie_s3_url = Column(String(500), nullable=True)

    # Verification status
    status = Column(String(20), default='pending')  # pending, approved, rejected, failed
    verification_result = Column(Text, nullable=True)  # Detailed result message
    is_verified = Column(Boolean, default=False)

    # Metadata (using Bangkok timezone)
    created_at = Column(DateTime, default=get_bangkok_time, nullable=False)
    updated_at = Column(DateTime, default=get_bangkok_time, onupdate=get_bangkok_time, nullable=False)
    verified_at = Column(DateTime, nullable=True)

    # Additional notes
    notes = Column(Text, nullable=True)

    # Role: 'seller' | 'buyer' | None
    role = Column(String(20), nullable=True)

    # Platform: 'line' | 'messenger' | 'web' | None
    platform = Column(String(20), nullable=True)

    # Trust scoring (dedicated columns for fast query/display)
    risk_score = Column(Float, nullable=True)         # 0-100
    trust_level = Column(String(20), nullable=True)   # bronze | silver | gold | platinum

    def __repr__(self):
        return f"<KYCVerification(id={self.id}, user_id={self.user_id}, status={self.status})>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'id_number': self.id_number,
            'prefix': self.prefix,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'date_of_birth': self.date_of_birth,
            'address': self.address,
            'face_similarity_score': self.face_similarity_score,
            'face_confidence': self.face_confidence,
            'id_card_s3_url': self.id_card_s3_url,
            'selfie_s3_url': self.selfie_s3_url,
            'status': self.status,
            'verification_result': self.verification_result,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'notes': self.notes,
            'role': self.role,
            'platform': self.platform,
            'risk_score': self.risk_score,
            'trust_level': self.trust_level
        }


# Database connection
DB_PATH = Path(__file__).parent / 'kyc_data.db'
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{DB_PATH}')

# Create engine and session
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    print(f"✓ Database initialized at: {DB_PATH}")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database on import
if not DB_PATH.exists():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    init_db()

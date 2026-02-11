"""
KYC Repository
Database operations for KYC verification records
"""

from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from .models import KYCVerification, SessionLocal, get_bangkok_time


class KYCRepository:
    """Repository for KYC verification data"""

    @staticmethod
    def create_kyc_record(
        user_id: str,
        session_id: Optional[str] = None,
        **kwargs
    ) -> KYCVerification:
        """Create new KYC verification record"""
        db = SessionLocal()
        try:
            record = KYCVerification(
                user_id=user_id,
                session_id=session_id,
                **kwargs
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            print(f"✓ Created KYC record ID: {record.id} for user: {user_id}")
            return record
        except Exception as e:
            db.rollback()
            print(f"❌ Error creating KYC record: {e}")
            raise
        finally:
            db.close()

    @staticmethod
    def update_kyc_record(
        record_id: int,
        **kwargs
    ) -> Optional[KYCVerification]:
        """Update existing KYC record"""
        db = SessionLocal()
        try:
            record = db.query(KYCVerification).filter(KYCVerification.id == record_id).first()
            if record:
                for key, value in kwargs.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                record.updated_at = get_bangkok_time()
                db.commit()
                db.refresh(record)
                print(f"✓ Updated KYC record ID: {record_id}")
                return record
            return None
        except Exception as e:
            db.rollback()
            print(f"❌ Error updating KYC record: {e}")
            raise
        finally:
            db.close()

    @staticmethod
    def get_by_user_id(user_id: str) -> Optional[KYCVerification]:
        """Get most recent KYC record for user"""
        db = SessionLocal()
        try:
            return db.query(KYCVerification)\
                .filter(KYCVerification.user_id == user_id)\
                .order_by(desc(KYCVerification.created_at))\
                .first()
        finally:
            db.close()

    @staticmethod
    def get_by_id(record_id: int) -> Optional[KYCVerification]:
        """Get KYC record by ID"""
        db = SessionLocal()
        try:
            return db.query(KYCVerification).filter(KYCVerification.id == record_id).first()
        finally:
            db.close()

    @staticmethod
    def get_all_records(
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[KYCVerification]:
        """Get all KYC records with pagination"""
        db = SessionLocal()
        try:
            query = db.query(KYCVerification)

            if status:
                query = query.filter(KYCVerification.status == status)

            return query.order_by(desc(KYCVerification.created_at))\
                .limit(limit)\
                .offset(offset)\
                .all()
        finally:
            db.close()

    @staticmethod
    def get_statistics() -> Dict:
        """Get KYC statistics"""
        db = SessionLocal()
        try:
            total = db.query(func.count(KYCVerification.id)).scalar()
            approved = db.query(func.count(KYCVerification.id))\
                .filter(KYCVerification.status == 'approved').scalar()
            pending = db.query(func.count(KYCVerification.id))\
                .filter(KYCVerification.status == 'pending').scalar()
            rejected = db.query(func.count(KYCVerification.id))\
                .filter(KYCVerification.status == 'rejected').scalar()

            return {
                'total': total or 0,
                'approved': approved or 0,
                'pending': pending or 0,
                'rejected': rejected or 0,
                'failed': (total or 0) - (approved or 0) - (pending or 0) - (rejected or 0)
            }
        finally:
            db.close()

    @staticmethod
    def search_by_id_number(id_number: str) -> Optional[KYCVerification]:
        """Search KYC record by Thai ID number"""
        db = SessionLocal()
        try:
            return db.query(KYCVerification)\
                .filter(KYCVerification.id_number == id_number)\
                .order_by(desc(KYCVerification.created_at))\
                .first()
        finally:
            db.close()

    @staticmethod
    def search_by_name(name: str) -> List[KYCVerification]:
        """Search KYC records by name (first or last)"""
        db = SessionLocal()
        try:
            search_pattern = f"%{name}%"
            return db.query(KYCVerification)\
                .filter(
                    (KYCVerification.first_name.like(search_pattern)) |
                    (KYCVerification.last_name.like(search_pattern))
                )\
                .order_by(desc(KYCVerification.created_at))\
                .all()
        finally:
            db.close()

    @staticmethod
    def delete_record(record_id: int) -> bool:
        """Delete KYC record"""
        db = SessionLocal()
        try:
            record = db.query(KYCVerification).filter(KYCVerification.id == record_id).first()
            if record:
                db.delete(record)
                db.commit()
                print(f"✓ Deleted KYC record ID: {record_id}")
                return True
            return False
        except Exception as e:
            db.rollback()
            print(f"❌ Error deleting KYC record: {e}")
            return False
        finally:
            db.close()

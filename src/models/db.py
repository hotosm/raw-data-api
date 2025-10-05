from datetime import datetime
from enum import Enum as PyEnum

from croniter import croniter
from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ARRAY, Date, Index, DDL, event, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates

Base = declarative_base()

UserRoleEnum = Enum('admin', 'staff', 'guest', name='user_role', create_type=True)


class UserRole(str, PyEnum):
    ADMIN = "admin"
    STAFF = "staff"
    GUEST = "guest"


class UserRoles(Base):
    __tablename__ = 'userroles'
    
    osm_id = Column(Integer, primary_key=True)
    role = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class CronJob(Base):
    __tablename__ = 'cron'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    hdx_upload = Column(Boolean, default=False, nullable=False)
    dataset = Column(JSONB, nullable=True)
    queue = Column(String, default='raw_ondemand', nullable=False)
    meta = Column(Boolean, default=False, nullable=False)
    categories = Column(JSONB, nullable=True)
    geometry = Column(Geometry(geometry_type='GEOMETRY', srid=4326, spatial_index=False), nullable=True)
    h3_indexes = Column(ARRAY(String), nullable=True)
    
    schedule = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    
    @validates('schedule')
    def validate_schedule(self, key, value):
        if value and not croniter.is_valid(value):
            raise ValueError(f"Invalid cron expression: {value}")
        return value
    
    __table_args__ = (
        Index('idx_cron_h3_indexes', 'h3_indexes', postgresql_using='gin'),
        Index('idx_cron_dataset', 'dataset', postgresql_using='gin'),
        Index('idx_cron_categories', 'categories', postgresql_using='gin'),
        Index('idx_cron_geometry', 'geometry', postgresql_using='gist'),
        Index('idx_cron_is_active', 'is_active'),
        Index('idx_cron_schedule', 'schedule'),
    )


class Metrics(Base):
    __tablename__ = 'metrics'
    
    date = Column(Date, primary_key=True)
    summary = Column(JSONB, nullable=True)
    folders = Column(JSONB, nullable=True)
    meta_downloads = Column(JSONB, nullable=True)
    
    __table_args__ = (
        Index('idx_metrics_summary', 'summary', postgresql_using='gin'),
        Index('idx_metrics_folders', 'folders', postgresql_using='gin'),
        Index('idx_metrics_meta_downloads', 'meta_downloads', postgresql_using='gin'),
    )

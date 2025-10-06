from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import HTTPException, Depends
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_AsGeoJSON
from geoalchemy2.shape import from_shape
from shapely.geometry import shape
import orjson

from src.models.db import CronJob
from src.db_session import get_db


def create_cron(cron_data: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, bool]:
    geometry = None
    if cron_data.get("geometry"):
        geom_shape = shape(cron_data["geometry"])
        geometry = from_shape(geom_shape, srid=4326)
    
    cron_job = CronJob(
        hdx_upload=cron_data.get("hdx_upload", False),
        dataset=cron_data.get("dataset"),
        queue=cron_data.get("queue", "raw_ondemand"),
        meta=cron_data.get("meta", False),
        categories=cron_data.get("categories"),
        geometry=geometry,
        schedule=cron_data.get("schedule"),
        is_active=cron_data.get("is_active", True)
    )
    
    db.add(cron_job)
    db.commit()
    db.refresh(cron_job)
    
    return {"create": True}


def get_cron_list(
    skip: int = 0,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    query = db.query(CronJob)
    
    if filters:
        conditions = []
        for key, value in filters.items():
            if hasattr(CronJob, key):
                conditions.append(getattr(CronJob, key) == value)
        if conditions:
            query = query.filter(and_(*conditions))
    
    results = query.offset(skip).limit(limit).all()
    
    return [_serialize_cron(cron) for cron in results]


def search_cron_by_dataset_title(
    dataset_title: str,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    query = db.query(CronJob).filter(
        CronJob.dataset["dataset_title"].astext.ilike(f"%{dataset_title}%")
    )
    
    results = query.offset(skip).limit(limit).all()
    
    return [_serialize_cron(cron) for cron in results]


def get_cron_by_id(cron_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    cron = db.query(CronJob).filter(CronJob.id == cron_id).first()
    
    if not cron:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return _serialize_cron(cron)


def update_cron(
    cron_id: int,
    cron_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, bool]:
    cron = db.query(CronJob).filter(CronJob.id == cron_id).first()
    
    if not cron:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if cron_data.get("geometry"):
        geom_shape = shape(cron_data["geometry"])
        cron.geometry = from_shape(geom_shape, srid=4326)
    
    cron.hdx_upload = cron_data.get("hdx_upload", False)
    cron.dataset = cron_data.get("dataset")
    cron.queue = cron_data.get("queue", "raw_ondemand")
    cron.meta = cron_data.get("meta", False)
    cron.categories = cron_data.get("categories")
    cron.schedule = cron_data.get("schedule")
    cron.is_active = cron_data.get("is_active", True)
    
    db.commit()
    db.refresh(cron)
    
    return {"update": True}


def patch_cron(
    cron_id: int,
    cron_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, bool]:
    if not cron_data:
        raise ValueError("No data provided for update")
    
    cron = db.query(CronJob).filter(CronJob.id == cron_id).first()
    
    if not cron:
        raise HTTPException(status_code=404, detail="Item not found")
    
    for field, value in cron_data.items():
        if field == "geometry" and value:
            geom_shape = shape(value)
            setattr(cron, field, from_shape(geom_shape, srid=4326))
        elif hasattr(cron, field):
            setattr(cron, field, value)
    
    db.commit()
    db.refresh(cron)
    
    return {"update": True}


def delete_cron(cron_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    cron = db.query(CronJob).filter(CronJob.id == cron_id).first()
    
    if not cron:
        raise HTTPException(status_code=404, detail="Cron item not found")
    
    result = _serialize_cron(cron)
    db.delete(cron)
    db.commit()
    
    return result


def get_active_scheduled_jobs(db: Session = Depends(get_db)) -> List[CronJob]:
    return db.query(CronJob).filter(
        and_(
            CronJob.is_active == True,
            CronJob.schedule.isnot(None)
        )
    ).all()


def update_last_run(cron_id: int, db: Session = Depends(get_db)) -> None:
    cron = db.query(CronJob).filter(CronJob.id == cron_id).first()
    if cron:
        cron.last_run_at = datetime.utcnow()
        db.commit()


def _serialize_cron(cron: CronJob) -> Dict[str, Any]:
    from geoalchemy2.shape import to_shape
    from shapely.geometry import mapping
    
    data = {
        "id": cron.id,
        "hdx_upload": cron.hdx_upload,
        "dataset": cron.dataset,
        "queue": cron.queue,
        "meta": cron.meta,
        "categories": cron.categories,
        "h3_indexes": cron.h3_indexes,
        "schedule": cron.schedule,
        "is_active": cron.is_active,
        "created_at": cron.created_at.isoformat() if cron.created_at else None,
        "updated_at": cron.updated_at.isoformat() if cron.updated_at else None,
        "last_run_at": cron.last_run_at.isoformat() if cron.last_run_at else None,
    }
    
    if cron.geometry:
        geom_shape = to_shape(cron.geometry)
        data["geometry"] = mapping(geom_shape)
    
    return data

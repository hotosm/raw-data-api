from datetime import datetime, timezone

from celery import Task
from croniter import croniter

from API.api_worker import celery
from src.db_session import SessionLocal
from src.models.cron import get_active_scheduled_jobs, update_last_run
from src.validation.models import DynamicCategoriesModel


@celery.task(name="check_scheduled_jobs", bind=True)
def check_scheduled_jobs(self: Task):
    from geoalchemy2.shape import to_shape
    from shapely.geometry import mapping
    
    db = SessionLocal()
    try:
        active_jobs = get_active_scheduled_jobs(db)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        for job in active_jobs:
            if not job.schedule:
                continue
            
            cron = croniter(job.schedule, job.last_run_at or job.created_at)
            next_run = cron.get_next(datetime)
            
            if next_run <= now:
                try:
                    geometry = None
                    if job.geometry:
                        geom_shape = to_shape(job.geometry)
                        geometry = mapping(geom_shape)
                    
                    categories_data = {
                        "hdx_upload": job.hdx_upload,
                        "dataset": job.dataset,
                        "categories": job.categories,
                        "geometry": geometry,
                        "meta": job.meta
                    }
                    
                    categories_model = DynamicCategoriesModel(**categories_data)
                    
                    from API.api_worker import process_custom_request
                    process_custom_request.apply_async(
                        args=(categories_model.model_dump(),),
                        queue=job.queue,
                        track_started=True
                    )
                    
                    update_last_run(job.id, db)
                    
                except Exception as ex:
                    continue
                    
    finally:
        db.close()


@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(60.0, check_scheduled_jobs.s(), name='check_scheduled_jobs_every_minute')

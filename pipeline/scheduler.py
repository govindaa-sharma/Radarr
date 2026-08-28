from celery import Celery
from celery.schedules import crontab
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    "radarr",
    broker=os.getenv("REDIS_URL", "redis://127.0.0.1:6379"),
    backend=os.getenv("REDIS_URL", "redis://127.0.0.1:6379")
)

celery_app.conf.beat_schedule = {
    "run-pipeline-every-night": {
        "task": "pipeline.scheduler.run_pipeline_task",
        "schedule": crontab(hour=7, minute=0),
    }
}

celery_app.conf.timezone = "Asia/Kolkata"

@celery_app.task
def run_pipeline_task():
    from pipeline.graph import run_pipeline
    asyncio.run(run_pipeline())
    print("Nightly pipeline completed.")
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# from datetime import datetime
import atexit
from zoneinfo import ZoneInfo

from app.ptu_utils import fetch_ptu_notices


def start_scheduler():
    scheduler = BackgroundScheduler(timezone=ZoneInfo("Asia/Kolkata"))

    # Add job to update notices every 6 hours
    scheduler.add_job(
        func=fetch_ptu_notices,
        trigger=IntervalTrigger(hours=6),
        id="update_notices_job",
        name="Update notices from PTU website",
        replace_existing=True,
    )

    # Start the scheduler
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

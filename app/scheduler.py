from apscheduler.schedulers.background import BackgroundScheduler
from app.storage import save_df

def build_scheduler(job_fn):
    s=BackgroundScheduler(timezone="Europe/Rome")
    s.add_job(job_fn, "cron", day_of_week="sun", hour=23, minute=0, id="weekly_scan", replace_existing=True)
    return s

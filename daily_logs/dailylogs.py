from fastapi import APIRouter
from core.db import logs_collection
from menstrual_tracker.menstrual_tracker_schema import DailyLog
from datetime import datetime
daily_logs=APIRouter()

@daily_logs.post('/logs-daily')
async def logs_daily(log:DailyLog):
        data = {
        **log.dict(),
        "createdAt": datetime.utcnow()
        }

        logs_collection.insert_one(data)
        return {"message": "Log saved"}
    
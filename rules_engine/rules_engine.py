from core.db import cycles_collection, logs_collection
from datetime import datetime

def analyze_user(userId):
    cycles = list(cycles_collection.find({"userId": userId}))
    logs = list(logs_collection.find({"userId": userId}))

    insights = []

    # 🔹 Rule 1: Irregular cycles
    lengths = [c.get("cycleLength", 28) for c in cycles]
    if len(lengths) >= 3:
        if max(lengths) - min(lengths) > 7:
            insights.append("⚠️ Your cycle appears irregular")

    # 🔹 Rule 2: Heavy bleeding detection
    heavy_days = [l for l in logs if l.get("flow") == "heavy"]
    if len(heavy_days) >= 3:
        insights.append("⚠️ Frequent heavy flow detected")

    # 🔹 Rule 3: Low sleep pattern
    low_sleep = [l for l in logs if l.get("sleep", 8) < 5]
    if len(low_sleep) >= 3:
        insights.append("😴 You are getting low sleep during cycles")

    # 🔹 Rule 4: Pain tracking
    pain_logs = [l for l in logs if "cramps" in l.get("symptoms", [])]
    if len(pain_logs) >= 3:
        insights.append("🤕 Repeated cramps observed")

    return insights
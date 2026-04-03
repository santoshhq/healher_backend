from fastapi import APIRouter
from rules_engine.rules_engine import analyze_user
from core.db import insights_collection
from datetime import datetime

router = APIRouter()

@router.post("/generate-insights/{userId}")
async def generate_insights(userId: str):
    results = await analyze_user(userId)

    for r in results:
        insights_collection.insert_one({
            "userId": userId,
            "message": r,
            "createdAt": datetime.utcnow()
        })

    return {"insights": results}

@router.get("/get-insights/{userId}")
async def get_insights(userId: str):
    insights = await insights_collection.find({"userId": userId}).to_list(length=None)
    # Convert ObjectId to string for JSON serialization
    for insight in insights:
        insight["_id"] = str(insight["_id"])
    return {"insights": insights, "count": len(insights)}
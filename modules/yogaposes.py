from db import yoga_poses_collection
from schemas.yogaposes_schema import YogaPoses
from fastapi import APIRouter
import random

yogapose = APIRouter()


# 🔹 CREATE POSE (same as yours)
@yogapose.post('/create-pose')
async def create_pose(yoga: YogaPoses):
    result = await yoga_poses_collection.insert_one({
        "video_id": yoga.video_id,
        "name": yoga.name,
        "benefits": yoga.benefits,
        "difficulty": yoga.difficulty,
        "video_url": str(yoga.video_url),
        "tags": yoga.tags,
        "duration": getattr(yoga, "duration", 5),          # default if not present
        "category": getattr(yoga, "category", "main")      # warmup/main/relaxation
    })
    return {"message": "Successfully Inserted!", "id": str(result.inserted_id)}


# 🔹 HELPER: BUILD 3 PLANS
def build_three_plans(poses):
    random.shuffle(poses)

    warmup = [p for p in poses if p.get("category") == "warmup"]
    main = [p for p in poses if p.get("category") == "main"]
    relax = [p for p in poses if p.get("category") == "relaxation"]

    plans = []

    for _ in range(3):
        plan = []
        total_time = 0

        selected = (
            random.sample(warmup, min(2, len(warmup))) +
            random.sample(main, min(3, len(main))) +
            random.sample(relax, min(1, len(relax)))
        )

        for p in selected:
            if total_time + p.get("duration", 5) <= 20:
                plan.append(p)
                total_time += p.get("duration", 5)

        plans.append(plan)

    return plans


# 🔥 MAIN GET API (PRODUCT LEVEL)
@yogapose.get('/get-plans')
async def get_plans():

    cursor = yoga_poses_collection.find(
        {"tags": {"$in": ["pcos"]}},
        {
            "name": 1,
            "benefits": 1,
            "video_url": 1,
            "duration": 1,
            "category": 1,
            "_id": 0
        }
    ).limit(50)   # ✅ important optimization

    poses = []
    async for doc in cursor:
        poses.append(doc)

    if not poses:
        return {"error": "No yoga poses found"}

    plans = build_three_plans(poses)

    return {
        "plans_count": 3,
        "plans": plans
    }


# 🧘 GET 3 RANDOM POSES (by userId)
@yogapose.get('/get-random-poses/{userId}')
async def get_random_poses(userId: str):
    """
    Get 3 random yoga poses for a user:
    1st from warmup category
    2nd from main category
    3rd from relaxation category
    """
    try:
        # Fetch warmup pose
        warmup_pose = await yoga_poses_collection.find_one(
            {"category": "warmup"},
            {"name": 1, "video_url": 1, "category": 1, "duration": 1, "benefits": 1, "_id": 0}
        )

        # Fetch main pose
        main_pose = await yoga_poses_collection.find_one(
            {"category": "main"},
            {"name": 1, "video_url": 1, "category": 1, "duration": 1, "benefits": 1, "_id": 0}
        )

        # Fetch relaxation pose
        relax_pose = await yoga_poses_collection.find_one(
            {"category": "relaxation"},
            {"name": 1, "video_url": 1, "category": 1, "duration": 1, "benefits": 1, "_id": 0}
        )

        # Check if all poses exist
        if not warmup_pose or not main_pose or not relax_pose:
            return {"error": "Not enough poses in all categories"}

        return {
            "message": f"Random poses for user {userId}",
            "userId": userId,
            "poses": [
                {
                    "position": "1st (Warmup)",
                    "name": warmup_pose.get("name"),
                    "category": warmup_pose.get("category"),
                    "video_url": warmup_pose.get("video_url"),
                    "duration": warmup_pose.get("duration"),
                    "benefits": warmup_pose.get("benefits")
                },
                {
                    "position": "2nd (Main)",
                    "name": main_pose.get("name"),
                    "category": main_pose.get("category"),
                    "video_url": main_pose.get("video_url"),
                    "duration": main_pose.get("duration"),
                    "benefits": main_pose.get("benefits")
                },
                {
                    "position": "3rd (Relaxation)",
                    "name": relax_pose.get("name"),
                    "category": relax_pose.get("category"),
                    "video_url": relax_pose.get("video_url"),
                    "duration": relax_pose.get("duration"),
                    "benefits": relax_pose.get("benefits")
                }
            ]
        }

    except Exception as e:
        return {"error": f"Failed to fetch poses: {str(e)}"}


# 💪 GET CUSTOM POSES BY CATEGORY AND COUNT
@yogapose.get('/get-custom-poses')
async def get_custom_poses(
    warmup_count: int = 0,
    main_count: int = 0,
    relaxation_count: int = 0
):
    """
    Get custom number of yoga poses by category.
    
    Query Parameters:
    - warmup_count: Number of warmup poses (default: 0)
    - main_count: Number of main poses (default: 0)
    - relaxation_count: Number of relaxation poses (default: 0)
    
    Example: /get-custom-poses?warmup_count=2&main_count=3&relaxation_count=1
    """
    try:
        # Validate at least one category is requested
        total_requested = warmup_count + main_count + relaxation_count
        if total_requested == 0:
            return {"error": "Please specify at least one pose count"}

        # Fetch warmup poses
        warmup_poses = []
        if warmup_count > 0:
            cursor = yoga_poses_collection.find(
                {"category": "warmup"},
                {"name": 1, "video_url": 1, "category": 1, "duration": 1, "benefits": 1, "_id": 0}
            ).limit(warmup_count)
            async for doc in cursor:
                warmup_poses.append(doc)

        # Fetch main poses
        main_poses = []
        if main_count > 0:
            cursor = yoga_poses_collection.find(
                {"category": "main"},
                {"name": 1, "video_url": 1, "category": 1, "duration": 1, "benefits": 1, "_id": 0}
            ).limit(main_count)
            async for doc in cursor:
                main_poses.append(doc)

        # Fetch relaxation poses
        relax_poses = []
        if relaxation_count > 0:
            cursor = yoga_poses_collection.find(
                {"category": "relaxation"},
                {"name": 1, "video_url": 1, "category": 1, "duration": 1, "benefits": 1, "_id": 0}
            ).limit(relaxation_count)
            async for doc in cursor:
                relax_poses.append(doc)

        # Check if we got expected poses
        available_warmup = len(warmup_poses)
        available_main = len(main_poses)
        available_relax = len(relax_poses)

        # Build response
        all_poses = warmup_poses + main_poses + relax_poses

        if not all_poses:
            return {"error": "No poses found in requested categories"}

        return {
            "poses": all_poses
        }

    except Exception as e:
        return {"error": f"Failed to fetch custom poses: {str(e)}"}
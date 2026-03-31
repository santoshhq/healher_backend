"""
MongoDB Index Creation Script
Run this once to create necessary indexes for user_workout_plans collection
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import certifi


async def create_indexes():
    """Create indexes for user_workout_plans collection"""
    load_dotenv()
    MONGO_URL = os.getenv("MONGO_URL")

    client = AsyncIOMotorClient(MONGO_URL, tlsCAFile=certifi.where())
    db = client["healherai"]
    user_workout_plans = db["user_workout_plans"]

    try:
        # Create unique index on (userId, date)
        # This ensures only one plan per user per day
        index_result = await user_workout_plans.create_index(
            [("userId", 1), ("date", 1)],
            unique=True,
            name="userId_date_unique"
        )
        print(f"✅ Index created successfully: {index_result}")

        # Optional: Create index on userId for faster queries
        index_result2 = await user_workout_plans.create_index(
            [("userId", 1), ("date", -1)],
            name="userId_date_sort"
        )
        print(f"✅ Index created successfully: {index_result2}")

        print("✅ All indexes created!")

    except Exception as e:
        print(f"❌ Error creating indexes: {str(e)}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(create_indexes())

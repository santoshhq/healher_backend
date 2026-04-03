from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os,certifi
load_dotenv()
MONGO_URL=os.getenv("MONGO_URL")
client=AsyncIOMotorClient(MONGO_URL,tlsCAFile=certifi.where())
db=client["healherai"]
students_collection = db["students"]
yoga_poses_collection=db["yoga_poses"]
auth_collection=db["users"]
pending_auth_collection=db["pending_users"]
cycles_collection = db["cycles"]
logs_collection = db["daily_logs"]
insights_collection = db["ai_insights"]
print("Successfully Connected !")
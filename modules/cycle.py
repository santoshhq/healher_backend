from fastapi import APIRouter
from schemas.menstrual_tracker_schema import Cycle
from datetime import datetime,timedelta
from db import cycles_collection
from statistics import mean
cycle_router=APIRouter()

async def calculate_prediction(userId, new_cycle_length):
    previous_cycles = await cycles_collection.find({"userId": userId}).to_list(length=None)
    
    lengths = [c.get("cycleLength", 28) for c in previous_cycles]
    lengths.append(new_cycle_length)
    
    avg_cycle = int(mean(lengths))
    
    return avg_cycle

@cycle_router.post('/add-cycle')
async def add_cycle(cycle:Cycle):
        start = datetime.fromisoformat(cycle.startDate)
        
        avg_cycle_length = await calculate_prediction(cycle.userId, cycle.cycleLength)
        
        predicted_next = start + timedelta(days=avg_cycle_length)
        ovulation = start + timedelta(days=avg_cycle_length - 14)

        data = {
            **cycle.dict(),
            "predictedNext": predicted_next.isoformat(),
            "ovulationDate": ovulation.isoformat(),
            "createdAt": datetime.utcnow()
        }
        cycles_collection.insert_one(data)
        return {"message":"Cycle Added"}

@cycle_router.get('/cycles/{userId}')
async def get_cycles(userId: str):
        cycles = await cycles_collection.find({"userId": userId}).to_list(length=None)
        # Convert ObjectId to string for JSON serialization
        for cycle in cycles:
            cycle["_id"] = str(cycle["_id"])
        return {"cycles": cycles, "count": len(cycles)}
# User-Specific Workout Planning Module

## 📋 Overview

Complete FastAPI + MongoDB async system for generating personalized daily yoga workout plans.

---

## 📁 Files Created/Modified

### 1. **schemas/workout.py** ✅
Pydantic schemas for workout data:
- `YogaPoseItem` - Single pose in workout
- `WorkoutPlan` - List of poses as a plan
- `UserWorkoutPlanResponse` - API response format
- `UserWorkoutPlanDB` - Database storage format

### 2. **modules/workout.py** ✅
FastAPI routes for workout planning:
- `GET /get-user-plans/{userId}` - Main endpoint

**Key Functions:**
- `get_available_poses()` - Fetch PCOS-tagged poses with exclusion logic
- `build_three_plans()` - Generate 3 workout plans with structure:
  - Plan 1: 2 warmup + 3 main + 1 relaxation
  - Plan 2: 2 warmup + 3 main + 1 relaxation
  - Plan 3: 2 warmup + 3 main + 1 relaxation

### 3. **db.py** ✅
Added collection reference:
```python
user_workout_plans_collection = db["user_workout_plans"]
```

### 4. **main.py** ✅
Added router:
```python
from modules.workout import workout
app.include_router(workout)
```

### 5. **scripts/create_indexes.py** ✅
MongoDB index creation:
- Unique index on `(userId, date)`
- Composite index on `(userId, date DESC)`

---

## 🚀 Setup Instructions

### Step 1: Create Indexes
```bash
python scripts/create_indexes.py
```

**Expected Output:**
```
✅ Index created successfully: userId_date_unique
✅ Index created successfully: userId_date_sort
✅ All indexes created!
```

### Step 2: Test Endpoint
```bash
curl -X GET "http://127.0.0.1:8585/get-user-plans/user123"
```

---

## 📊 Database Schema

### Collection: `user_workout_plans`

```json
{
  "_id": ObjectId,
  "userId": "user123",
  "date": "2026-03-30",
  "plans": [
    [
      {
        "name": "Tadasana",
        "video_url": "https://...",
        "category": "warmup",
        "duration": 5
      },
      ...
    ],
    [...],
    [...]
  ],
  "used_pose_names": ["Tadasana", "Vrikshasana", ...],
  "created_at": ISODate("2026-03-30T10:30:00Z")
}
```

---

## 🎯 Algorithm Logic

### Step 1: Check Today's Plan
- Query: `{userId, date: "2026-03-30"}`
- If exists → Return immediately (no regeneration)

### Step 2: Fetch Last 3 Days
- Query: `{userId, date: {$gte: "2026-03-27", $lt: "2026-03-30"}}`
- Extract all `used_pose_names`

### Step 3: Fetch Available Poses
**Primary Query:**
```javascript
{
  tags: "pcos",
  name: {$nin: [used_pose_names]}
}
```
Limit: 50, Projection: name, video_url, category, duration

**Fallback Query** (if < 6 poses found):
```javascript
{tags: "pcos"}
```

### Step 4: Generate 3 Plans
For each of 3 plans:
- Randomly select 2 warmup poses
- Randomly select 3 main poses
- Randomly select 1 relaxation pose
- Total: 6 poses per plan, 18 poses total

### Step 5: Store Plan
Insert document with:
- userId
- date (YYYY-MM-DD)
- plans (3 arrays of poses)
- used_pose_names (all unique names)
- created_at

---

## 📞 API Reference

### Endpoint: `GET /get-user-plans/{userId}`

**Path Parameters:**
- `userId` (string, required) - User ID

**Response (200):**
```json
{
  "message": "New plan generated",
  "date": "2026-03-30",
  "plans": [
    {
      "poses": [
        {
          "name": "Tadasana",
          "video_url": "https://...",
          "category": "warmup",
          "duration": 5
        },
        ...
      ]
    },
    {...},
    {...}
  ]
}
```

**Response (existing plan):**
```json
{
  "message": "Plan already exists for today",
  "date": "2026-03-30",
  "plans": [...]
}
```

**Error Responses:**
- `404` - No yoga poses available
- `400` - Not enough poses in categories
- `500` - Server error

---

## 🔐 Important Rules Implemented

✅ Async/await throughout  
✅ Motor MongoDB driver  
✅ HTTP exceptions with proper codes  
✅ No MongoDB `_id` in responses  
✅ UTC datetime with YYYY-MM-DD format  
✅ Random selection with `random.sample()`  
✅ Fallback logic for insufficient data  
✅ Unique index on (userId, date)  
✅ Prevents duplicate plans per day  

---

## 📝 Example Usage

### First Request (Today)
```bash
curl -X GET "http://127.0.0.1:8585/get-user-plans/user_001"
```
→ Generates and stores new plan

### Second Request (Same Day)
```bash
curl -X GET "http://127.0.0.1:8585/get-user-plans/user_001"
```
→ Returns cached plan (no regeneration)

### Next Day Request
```bash
curl -X GET "http://127.0.0.1:8585/get-user-plans/user_001"
```
→ Generates new plan (avoids last 3 days' poses)

---

## 🐛 Error Handling

| Scenario | Response |
|----------|----------|
| No PCOS poses in DB | 404 - No yoga poses available |
| Insufficient category coverage | 400 - Not enough poses in all categories |
| Database error | 500 - Error generating plans |

---

## 🎨 Key Features

✨ **Smart Repetition Avoidance** - Tracks last 3-7 days  
✨ **Plan Caching** - Returns same plan if already generated today  
✨ **Structured Workouts** - Warm-up → Main → Relaxation flow  
✨ **Graceful Degradation** - Fallback if exclusion filter insufficient  
✨ **Async Performance** - Non-blocking database operations  

---

## 🚦 Next Steps

1. ✅ Run `python scripts/create_indexes.py` to create indexes
2. ✅ Test endpoint with sample userId
3. ✅ Verify response format and pose data
4. ✅ Monitor performance with large datasets
5. ✅ Add authentication checks if needed

---

## 📌 Notes

- Yoga poses must have `tags: "pcos"` to be included
- Date format is always `YYYY-MM-DD` (UTC)
- Each user gets exactly 3 plans per day (all generated together)
- Plans are immutable after creation
- Old plans can be archived or deleted manually


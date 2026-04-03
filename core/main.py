from fastapi import FastAPI
from yoga_poses.yogaposes import yogapose
from authentication.authentication import auth
from chatbot.chatbot_module import chat
from food_scanner.food_scanner_module import scanner
from menstrual_tracker.cycle import cycle_router
from daily_logs.dailylogs import daily_logs
app=FastAPI()


@app.get('/')
async def default():
  return {"message":"Welcome"}
app.include_router(chat)
app.include_router(scanner)
app.include_router(yogapose)
app.include_router(auth)
app.include_router(cycle_router)
app.include_router(daily_logs)

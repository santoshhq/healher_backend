from fastapi import FastAPI
from modules.yogaposes import yogapose
from modules.authentication import auth
from modules.chatbot_module import chat
from modules.food_scanner_module import scanner
from modules.cycle import cycle_router
from modules.dailylogs import daily_logs
from pcos_prediction import pcos_router
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
app.include_router(pcos_router)

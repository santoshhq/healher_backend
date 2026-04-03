from fastapi import APIRouter
from .chatbot_schema import chatbot
from langgraph.checkpoint.redis import RedisSaver
from langchain_core.messages import HumanMessage
from chatbot import build_graph,DB_URL
chat=APIRouter()

@chat.post('/question')
async def ask_question(chat:chatbot) -> dict:
    try:
        with RedisSaver.from_conn_string(DB_URL) as saver:
            saver.setup()
            tf = {"configurable": {"thread_id": chat.thread_id}}
            inpt = {"question": chat.question, "messages": HumanMessage(content=chat.question)}
            res = build_graph().compile()
            wk = await res.ainvoke(inpt, tf)
            # Extract only the chatbot message
            return {
                "response": wk.get("res", ""),
                
            }
    except Exception as e:
        return {"error": str(e)}
    
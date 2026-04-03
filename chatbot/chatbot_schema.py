from pydantic import BaseModel,Field

class chatbot(BaseModel):
    question:str=Field(...,description="User input query")
    thread_id:str=Field(...,description="User thread_id or userId")

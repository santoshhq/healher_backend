from typing import Optional, Dict
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
import os
import asyncio
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv()

pcos_router = APIRouter()

# -----------------------------
# 1. LLM Setup (with safety)
# -----------------------------
llm = ChatNVIDIA(
    model="google/gemma-3-27b-it",
    api_key=os.getenv("NVIDIA_API_KEY"),
    max_completion_tokens=100,
)

LLM_TIMEOUT = 80  # seconds

# -----------------------------
# 2. Models
# -----------------------------
class PCOSState(BaseModel):
    answers: Dict[str, str] = Field(default_factory=dict)
    score: int = 0
    risk_level: Optional[str] = None
    final_response: Optional[str] = None


class UserInput(BaseModel):
    irregular_periods: str
    skipped_periods: str
    hair_growth: str
    acne: str
    weight_gain: str
    low_energy: str
    body_changes: str
    medical_history: str


# -----------------------------
# 3. Helper: Normalize Input
# -----------------------------
def normalize_answers(data: UserInput) -> Dict[str, str]:
    raw = data.model_dump()

    return {
        k: (v.strip().lower() if isinstance(v, str) else "")
        for k, v in raw.items()
    }


# -----------------------------
# 4. Score Node
# -----------------------------
def compute_score(state: PCOSState) -> PCOSState:
    ans = state.answers
    score = 0

    score += 3 if ans.get("irregular_periods") == "yes" else 0
    score += 3 if ans.get("skipped_periods") == "yes" else 0
    score += 2 if ans.get("hair_growth") == "yes" else 0
    score += 1 if ans.get("acne") == "yes" else 0
    score += 1 if ans.get("weight_gain") == "yes" else 0

    state.score = score

    if score <= 2:
        state.risk_level = "Low"
    elif score <= 6:
        state.risk_level = "Moderate"
    else:
        state.risk_level = "High"

    return state


# -----------------------------
# 5. LLM Node (Robust + Timeout)
# -----------------------------
async def generate_response(state: PCOSState) -> PCOSState:
    prompt = f"""
You are a women's health assistant (NOT a doctor).

User Answers:
{state.answers}

Risk Score: {state.score}
Risk Level: {state.risk_level}

Respond in this format:
1. Simple explanation of risk
2. Key observed symptoms
3. Next steps (lifestyle + doctor visit)
4. Add disclaimer: "This is not a medical diagnosis"
"""

    try:
        print("⚡ LLM start...")

        response = await asyncio.wait_for(
            asyncio.to_thread(
                llm.invoke,
                [
                    SystemMessage(content="You are a safe and helpful health assistant."),
                    HumanMessage(content=prompt),
                ],
            ),
            timeout=LLM_TIMEOUT,
        )

        print("✅ LLM done")

        state.final_response = response.content

    except asyncio.TimeoutError:
        print("⏱️ LLM timeout")
        state.final_response = "Response took too long. Please try again."

    except Exception as e:
        print("❌ LLM error:", str(e))
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

    return state


# -----------------------------
# 6. Graph
# -----------------------------
builder = StateGraph(PCOSState)

builder.add_node("score", compute_score)
builder.add_node("llm", generate_response)

builder.set_entry_point("score")

builder.add_edge("score", "llm")
builder.add_edge("llm", END)

graph = builder.compile()


# -----------------------------
# 7. API Endpoint
# -----------------------------
@pcos_router.post("/assess")
async def assess_pcos(data: UserInput):

    print("📥 Incoming request")

    try:
        state = PCOSState(
            answers=normalize_answers(data)
        )

        result = await graph.ainvoke(state)

        # Convert dict → model (safe)
        final_state = PCOSState(**result)

        print("✅ Completed")

        return {
            "score": final_state.score,
            "risk_level": final_state.risk_level,
            "analysis": final_state.final_response,
        }

    except Exception as e:
        print("❌ API error:", str(e))
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# 8. Health Check
# -----------------------------
@pcos_router.get("/health")
def health():
    return {"status": "ok"}
from fastapi import FastAPI
from app.schemas import WellnessRequest, HistoryResponse
from app.agents.orchestrator import run_wellness_flow
from app.memory import get_memory
from app.db import get_user_history  # <-- SQL history retrieval

from datetime import datetime

app = FastAPI(title="Digital Wellness Assistant - Multi-Agent")


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================
# POST: Wellness Endpoint
# ============================
@app.post("/api/wellness")
def wellness_endpoint(payload: WellnessRequest):
    """
    Accepts a user message and returns the final combined JSON:

    {
        "user_id": "...",
        "final_output": { ... }
    }
    """
    result = run_wellness_flow(user_id=payload.user_id, user_input=payload.message)

    return {"user_id": payload.user_id, "final_output": result}


# ============================
# GET: LangChain Memory History
# ============================
@app.get("/api/history/{user_id}", response_model=HistoryResponse)
def get_user_history_memory(user_id: str):
    """
    Returns conversation history stored in LangChain memory.

    Tags extracted:
    [SymptomAgent]
    [DietAgent]
    [FitnessAgent]
    [LifestyleAgent]
    [FinalAdviceJSON]
    """
    memory = get_memory(user_id)
    vars = memory.load_memory_variables({})
    messages = vars.get("history", [])

    history_items = []

    for m in messages:
        raw = m.content.strip()

        # USER
        if m.type == "human":
            role = "user"
            text = raw

        # AGENT TAGS
        elif raw.startswith("[SymptomAgent]"):
            role = "SymptomAgent"
            text = raw.replace("[SymptomAgent]", "").strip()

        elif raw.startswith("[DietAgent]"):
            role = "DietAgent"
            text = raw.replace("[DietAgent]", "").strip()

        elif raw.startswith("[FitnessAgent]"):
            role = "FitnessAgent"
            text = raw.replace("[FitnessAgent]", "").strip()

        elif raw.startswith("[LifestyleAgent]"):
            role = "LifestyleAgent"
            text = raw.replace("[LifestyleAgent]", "").strip()

        elif raw.startswith("[FinalAdviceJSON]"):
            role = "system"
            text = raw.replace("[FinalAdviceJSON]", "").strip()

        elif raw.startswith("[Synthesized]"):
            continue

        else:
            role = "system"
            text = raw

        history_items.append(
            {
                "timestamp": datetime.now().isoformat(),
                "role": role,
                "content": text,
            }
        )

    return HistoryResponse(user_id=user_id, messages=history_items)


# ============================
# GET: SQL History Retrieval
# ============================
@app.get("/api/db-history/{user_id}")
def get_sql_history(user_id: str):
    """
    Returns ALL recorded interactions stored in MySQL.
    Useful for audit, UI history, analytics.
    """
    return get_user_history(user_id)


# ============================
# Health Check
# ============================
@app.get("/health")
def health():
    return {"status": "ok"}

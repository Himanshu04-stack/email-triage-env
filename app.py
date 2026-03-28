from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn

from environment import EmailTriageEnv, TriageAction, TASKS, EMAILS

app = FastAPI(
    title="Email Triage OpenEnv",
    description="An OpenEnv environment where an AI agent triages support emails by priority, category, and team assignment.",
    version="1.0.0"
)

# ── Global environment instances (one per task) ───────────────────────────────
envs: dict[str, EmailTriageEnv] = {
    "task_easy":   EmailTriageEnv(task_id="task_easy",   seed=42),
    "task_medium": EmailTriageEnv(task_id="task_medium", seed=42),
    "task_hard":   EmailTriageEnv(task_id="task_hard",   seed=42),
}
_active_task = "task_easy"

def get_env() -> EmailTriageEnv:
    return envs[_active_task]


# ── Request / Response schemas ────────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_id: Optional[str] = "task_easy"
    seed: Optional[int] = 42

class StepRequest(BaseModel):
    priority: str
    category: str
    assigned_team: str
    summary: str = ""

class GraderRequest(BaseModel):
    task_id: str
    email_id: str
    priority: str
    category: str
    assigned_team: str
    summary: str = ""


# ── Core OpenEnv endpoints ────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "environment": "EmailTriageEnv", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/reset")
def reset(req: ResetRequest = ResetRequest()):
    global _active_task
    if req.task_id not in TASKS:
        raise HTTPException(400, f"task_id must be one of {list(TASKS.keys())}")
    _active_task = req.task_id
    env = envs[req.task_id]
    env.seed = req.seed
    obs = env.reset()
    return {"observation": obs.model_dump(), "task": TASKS[req.task_id]}

@app.post("/step")
def step(req: StepRequest):
    env = get_env()
    if env._done:
        raise HTTPException(400, "Episode is done. Call /reset first.")
    action = TriageAction(
        priority=req.priority,
        category=req.category,
        assigned_team=req.assigned_team,
        summary=req.summary
    )
    obs, reward, done, info = env.step(action)
    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info
    }

@app.get("/state")
def state():
    env = get_env()
    return env.state()


# ── Task listing endpoint ─────────────────────────────────────────────────────

@app.get("/tasks")
def list_tasks():
    return {
        "tasks": list(TASKS.values()),
        "action_schema": {
            "priority": {"type": "string", "enum": ["urgent", "normal", "low"], "description": "Email urgency level"},
            "category": {"type": "string", "enum": ["bug", "feature_request", "billing", "spam", "support", "other"], "description": "Email topic category"},
            "assigned_team": {"type": "string", "enum": ["engineering", "billing", "support", "sales", "ignore"], "description": "Team to handle this email"},
            "summary": {"type": "string", "description": "One-sentence summary of the key issue (required for task_hard)"}
        }
    }


# ── Grader endpoint ───────────────────────────────────────────────────────────

@app.post("/grader")
def grader(req: GraderRequest):
    if req.task_id not in TASKS:
        raise HTTPException(400, f"task_id must be one of {list(TASKS.keys())}")
    # Find the email
    email = next((e for e in EMAILS if e["email_id"] == req.email_id), None)
    if not email:
        raise HTTPException(404, f"email_id '{req.email_id}' not found")
    env = EmailTriageEnv(task_id=req.task_id)
    action = TriageAction(
        priority=req.priority,
        category=req.category,
        assigned_team=req.assigned_team,
        summary=req.summary
    )
    score = env.grade(action, email)
    return {
        "task_id": req.task_id,
        "email_id": req.email_id,
        "score": score,
        "score_range": "0.0 to 1.0"
    }


# ── Baseline endpoint ─────────────────────────────────────────────────────────

@app.post("/baseline")
def run_baseline():
    """Trigger the baseline inference script and return scores for all 3 tasks."""
    try:
        import baseline
        scores = baseline.run_baseline()
        return {"status": "success", "baseline_scores": scores}
    except Exception as e:
        raise HTTPException(500, f"Baseline failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=7860, reload=False)

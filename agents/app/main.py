from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agents import IncidentWorkflow
from .models import IncidentInput, IncidentRunResult

app = FastAPI(title="Incident Commander Agents", version="0.1.0")
workflow = IncidentWorkflow()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/incidents/run", response_model=IncidentRunResult)
def run_incident(incident: IncidentInput) -> IncidentRunResult:
    return workflow.run(incident)

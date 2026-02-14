from fastapi import FastAPI

from .agents import IncidentWorkflow
from .models import IncidentInput, IncidentRunResult

app = FastAPI(title="Incident Commander Agents", version="0.1.0")
workflow = IncidentWorkflow()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/incidents/run", response_model=IncidentRunResult)
def run_incident(incident: IncidentInput) -> IncidentRunResult:
    return workflow.run(incident)

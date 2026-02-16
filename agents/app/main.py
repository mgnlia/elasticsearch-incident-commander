from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agent_builder_client import AgentBuilderService
from .agents import IncidentWorkflow
from .config import Settings
from .elasticsearch_client import ElasticsearchService
from .models import IncidentInput, IncidentRunResult

settings = Settings.from_env()
app = FastAPI(title="Incident Commander Agents", version="0.2.0")
workflow = IncidentWorkflow()
elastic_service = ElasticsearchService(settings)
agent_builder_service = AgentBuilderService(settings)

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
    result = workflow.run(incident)
    result.elastic = elastic_service.record_incident_and_analyze(incident, result)
    result.agent_builder = agent_builder_service.dispatch_incident(incident, result)
    return result

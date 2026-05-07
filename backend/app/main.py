from fastapi import FastAPI

from .database import Base, engine
from .routers import model_configs, prompt_test_runs, prompt_versions, test_cases, test_runs, test_targets

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Agent Test Platform API", version="0.1.0")

app.include_router(test_targets.router, prefix="/api", tags=["test-targets"])
app.include_router(test_cases.router, prefix="/api", tags=["test-cases"])
app.include_router(test_runs.router, prefix="/api", tags=["test-runs"])
app.include_router(prompt_versions.router, prefix="/api", tags=["prompt-versions"])
app.include_router(model_configs.router, prefix="/api", tags=["model-configs"])
app.include_router(prompt_test_runs.router, prefix="/api", tags=["prompt-test-runs"])


@app.get("/")
def root() -> dict:
    return {"message": "AI Agent Test Platform backend is running."}

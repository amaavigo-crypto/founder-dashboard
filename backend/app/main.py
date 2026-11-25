from fastapi import FastAPI

from . import models  # noqa: F401  (registers tables)
from .api import internal, router
from .db import Base, engine


Base.metadata.create_all(engine)  # no-op once the tables exist; runs per cold start

app = FastAPI(title="Founders Dashboard API")
app.include_router(router)
app.include_router(internal)


@app.get("/health")
def health():
    return {"ok": True}

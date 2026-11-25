from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import models  # noqa: F401  (registers tables)
from .api import internal, router
from .db import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Founders Dashboard API", lifespan=lifespan)
app.include_router(router)
app.include_router(internal)


@app.get("/health")
def health():
    return {"ok": True}

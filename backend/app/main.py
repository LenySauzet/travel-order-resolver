from fastapi import FastAPI

from .api.v1 import user
from .core.config import config
from .core.logging import setup_logging
from .db.schema import Base, engine

setup_logging()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=config.app_name,
    description=config.app_description,
    version=config.app_version,
)


app.include_router(user.router, prefix="/api/v1", tags=["users"])
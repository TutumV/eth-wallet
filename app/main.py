from fastapi import FastAPI

from app.config import settings
from app.core.database import engine
from app.handlers import router
from app.model import Base

app = FastAPI(title=settings.project_name)
app.include_router(router=router)


@app.on_event("startup")
async def init_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

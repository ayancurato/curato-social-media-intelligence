import asyncio
from app.core.database import Base, engine
from app.models import agent_run, content_draft, generation_session, workflow_log

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())

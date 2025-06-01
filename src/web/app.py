"""Web application for the MCP client."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from src.utilities.settings import Settings
from src.web.routes import prompts, schedules
from src.web.scheduler import scheduler, schedule_async_job
from src.web.database import async_session, DBSchedule
from src.web.routes.schedules import execute_prompt_sync, parse_cron_expression

settings = Settings()

async def load_existing_schedules():
  """Load existing schedules from database into scheduler."""
  # Clear any existing jobs first
  scheduler.remove_all_jobs()

  async with async_session() as db:
    result = await db.execute(select(DBSchedule))
    existing_schedules = result.scalars().all()

    for schedule in existing_schedules:
      if schedule.schedule_type == "one_time" and schedule.run_at:
        schedule_async_job(
          execute_prompt_sync,
          "date",
          run_date=schedule.run_at,
          args=[schedule.prompt_id, schedule.id],
          id=f"one_time_{schedule.id}",  # Unique job ID
          replace_existing=True  # Replace if exists
        )
      elif schedule.schedule_type == "recurring" and schedule.cron_expression:
        schedule_async_job(
          execute_prompt_sync,
          "cron",
          args=[schedule.prompt_id, schedule.id],
          id=f"recurring_{schedule.id}",  # Unique job ID
          replace_existing=True,  # Replace if exists
          **parse_cron_expression(schedule.cron_expression)
        )

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
  """Lifespan context manager for the web application."""
  await load_existing_schedules()
  scheduler.start()
  yield
  scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

app.include_router(prompts.router)
app.include_router(schedules.router)

@app.get("/")
async def root():
  """Redirect root to chats page."""
  return RedirectResponse(url="/prompts", status_code=303)

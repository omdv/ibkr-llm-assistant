"""Scheduler module for the web application."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from src.utilities.settings import Settings

settings = Settings()

# Configure the scheduler to use AsyncIOExecutor
executors = {
  'default': AsyncIOExecutor()
}

# Configure job stores to use PostgreSQL with synchronous connection
# Convert async URL to sync URL by removing +asyncpg
database_url = f"postgresql://postgres:postgres@{settings.database_host}:{settings.database_port}/ibkr_mcp"
jobstores = {
  'default': SQLAlchemyJobStore(url=database_url)
}

# Create the scheduler with our configuration
scheduler = AsyncIOScheduler(
  jobstores=jobstores,
  executors=executors,
  timezone='UTC'
)

async def run_async_job(func, *args, **kwargs):
  """Run an async job in the scheduler."""
  try:
    await func(*args, **kwargs)
  except Exception as e:
    # Log the error but don't let it crash the scheduler
    print(f"Error running job: {str(e)}")

def schedule_async_job(func, trigger, **kwargs):
  """Schedule an async job with proper error handling."""
  return scheduler.add_job(
    run_async_job,
    trigger=trigger,
    args=[func] + list(kwargs.pop('args', [])),
    **kwargs
  )

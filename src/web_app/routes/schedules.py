"""Routes for the schedules."""
import asyncio
from croniter import croniter
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, text, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from mcp_client import MCPClient
from src.web.database import DBSchedule, DBPrompt, DBScheduleExecution, async_session, get_db, Base
from src.web.scheduler import scheduler
from src.web.templating import templates
from src.utilities.settings import Settings

settings = Settings()

router = APIRouter()

def parse_cron_expression(cron_expr: str) -> dict:
  """Convert cron expression to APScheduler kwargs"""
  if not croniter.is_valid(cron_expr):
    raise ValueError("Invalid cron expression")

  parts = cron_expr.split()
  return {
    "minute": parts[0],
    "hour": parts[1],
    "day": parts[2],
    "month": parts[3],
    "day_of_week": parts[4],
  }


async def execute_prompt_sync(prompt_id: int, schedule_id: int | None = None):
  """Asynchronous version of execute_prompt_sync for scheduler jobs."""
  max_retries = 3
  retry_delay = 1  # seconds

  for attempt in range(max_retries):
    try:
      async with async_session() as db:
        # Get the prompt
        prompt = await db.get(DBPrompt, prompt_id)
        if not prompt:
          return

        # Get the schedule if schedule_id is provided
        schedule = None
        if schedule_id:
          query = select(DBSchedule).filter(DBSchedule.id == schedule_id)
          result = await db.execute(query)
          schedule = result.scalar_one_or_none()

        # Create execution record with initial status
        execution = DBScheduleExecution(
          schedule_id=schedule.id if schedule else None,
          prompt=prompt,
          status="pending"  # Set initial status
        )
        db.add(execution)
        await db.flush()

        try:
          mcp_client = MCPClient(settings)
          try:
            await mcp_client.connect_to_server()
            result = await mcp_client.process_query(prompt.content)
            execution.status = "success"
            execution.result = str(result)
          except Exception as e:
            execution.status = "error"
            execution.error = str(e)
            raise
          finally:
            await mcp_client.cleanup()
        except Exception as e:
          execution.status = "error"
          execution.error = str(e)
          raise
        finally:
          await db.commit()
          return  # Success - exit the retry loop

    except Exception as e:
      if attempt < max_retries - 1:
        await asyncio.sleep(retry_delay)
        continue
      raise  # Re-raise the exception if all retries failed


@router.get("/schedules", response_class=HTMLResponse)
async def list_schedules(request: Request, db: AsyncSession = Depends(get_db)):
  """List all schedules."""
  # Load schedules with their prompts
  result = await db.execute(select(DBSchedule).options(selectinload(DBSchedule.prompt)))
  schedules = result.scalars().all()

  # Get all prompts for the form
  prompt_result = await db.execute(select(DBPrompt))
  prompts = prompt_result.scalars().all()

  return templates.TemplateResponse(
    "schedules.html", {"request": request, "schedules": schedules, "prompts": prompts}
  )


@router.get("/schedules/new", response_class=HTMLResponse)
async def new_schedule(
  request: Request, prompt_id: int | None = None, db: AsyncSession = Depends(get_db)
):
  """Show the new schedule form, optionally pre-selecting a prompt."""
  # Get all prompts for the form
  prompt_result = await db.execute(select(DBPrompt))
  prompts = prompt_result.scalars().all()

  return templates.TemplateResponse(
    "schedules.html",
    {
      "request": request,
      "schedules": [],
      "prompts": prompts,
      "selected_prompt_id": prompt_id,
    },
  )


@router.post("/schedules/")
async def create_schedule_form(
  prompt_id: int = Form(...),
  schedule_type: str = Form(...),
  run_at: str | None = Form(None),
  cron_expression: str | None = Form(None),
  db: AsyncSession = Depends(get_db),
):
  """Create a new schedule from form data."""
  # Convert run_at string to datetime if provided
  run_at_datetime = None
  if run_at and run_at.strip():
    try:
      # Parse the UTC time received from frontend directly as naive datetime
      run_at_datetime = datetime.fromisoformat(run_at)
    except ValueError:
      raise HTTPException(status_code=400, detail="Invalid datetime format for run_at")

  # Validate schedule parameters
  if schedule_type == "one_time" and not run_at_datetime:
    raise HTTPException(
      status_code=400, detail="run_at is required for one-time schedules"
    )
  if schedule_type == "recurring" and not cron_expression:
    raise HTTPException(
      status_code=400, detail="cron_expression is required for recurring schedules"
    )

  # Validate prompt exists
  prompt = await db.get(DBPrompt, prompt_id)
  if not prompt:
    raise HTTPException(status_code=404, detail="Prompt not found")

  # Create the database model directly from form data
  db_schedule = DBSchedule(
    prompt_id=prompt_id,
    schedule_type=schedule_type,
    run_at=run_at_datetime,
    cron_expression=cron_expression,
  )

  db.add(db_schedule)
  await db.commit()
  await db.refresh(db_schedule)

  # Add to scheduler
  if schedule_type == "one_time":
    scheduler.add_job(
      execute_prompt_sync,
      "date",
      run_date=run_at_datetime,
      args=[db_schedule.prompt_id, db_schedule.id],
      id=f"one_time_{db_schedule.id}",  # Unique job ID
      replace_existing=True  # Replace if exists
    )
  else:
    scheduler.add_job(
      execute_prompt_sync,
      "cron",
      args=[db_schedule.prompt_id, db_schedule.id],
      id=f"recurring_{db_schedule.id}",  # Unique job ID
      replace_existing=True,  # Replace if exists
      **parse_cron_expression(cron_expression)
    )

  return RedirectResponse("/schedules", status_code=303)


@router.post("/schedules/{schedule_id}/delete")
async def delete_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
  """Delete a schedule by ID."""
  max_retries = 3
  retry_delay = 1  # seconds

  for attempt in range(max_retries):
    try:
      # Get the schedule first to check if it exists
      schedule = await db.get(DBSchedule, schedule_id)
      if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")

      # Remove from scheduler
      job_id = f"{schedule.schedule_type}_{schedule.id}"
      job = scheduler.get_job(job_id)
      if job:
        job.remove()

      # Delete the schedule (executions will be kept with schedule_id set to NULL)
      await db.delete(schedule)
      await db.commit()

      return RedirectResponse("/schedules", status_code=303)

    except Exception as e:
      await db.rollback()
      if attempt < max_retries - 1:
        await asyncio.sleep(retry_delay)
        continue
      raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedules/{schedule_id}/executions", response_class=HTMLResponse)
async def list_schedule_executions(
  request: Request,
  schedule_id: int,
  db: AsyncSession = Depends(get_db)
):
  """List execution history for a schedule."""
  # Load schedule with its executions
  result = await db.execute(
    select(DBSchedule)
    .filter(DBSchedule.id == schedule_id)
    .options(selectinload(DBSchedule.executions))
  )
  schedule = result.scalar_one_or_none()

  if not schedule:
    raise HTTPException(status_code=404, detail="Schedule not found")

  # Get all prompts for the filter dropdown
  prompt_result = await db.execute(select(DBPrompt))
  prompts = prompt_result.scalars().all()

  # Get unique statuses for the filter dropdown
  status_result = await db.execute(
    select(DBScheduleExecution.status).distinct()
  )
  statuses = [row[0] for row in status_result.all()]

  return templates.TemplateResponse(
    "executions.html",
    {
      "request": request,
      "executions": schedule.executions,
      "prompts": prompts,
      "current_prompt_id": str(schedule.prompt_id),  # Convert to string to match the form value
      "current_status": None,
      "current_start_date": None,
      "current_end_date": None,
      "current_sort_by": "executed_at",
      "current_sort_order": "desc",
      "statuses": statuses,
      "schedule": schedule,  # Pass the schedule for context
    }
  )


@router.get("/executions", response_class=HTMLResponse)
async def list_all_executions(
  request: Request,
  prompt_id: str | None = Query(None),
  status: str | None = Query(None),
  start_date: str | None = Query(None),
  end_date: str | None = Query(None),
  sort_by: str = Query("executed_at", description="Field to sort by (executed_at, status, prompt_id)"),
  sort_order: str = Query("desc", description="Sort order (asc or desc)"),
  db: AsyncSession = Depends(get_db)
):
  """List all executions with filtering and sorting options."""
  # Build the base query
  query = select(DBScheduleExecution).options(
    joinedload(DBScheduleExecution.schedule).joinedload(DBSchedule.prompt)
  )

  # Apply filters
  if prompt_id and prompt_id.strip():  # Only apply filter if prompt_id is not empty
    try:
      prompt_id_int = int(prompt_id)
      query = query.join(DBSchedule).filter(DBSchedule.prompt_id == prompt_id_int)
    except ValueError:
      # If prompt_id is not a valid integer, ignore the filter
      pass
  if status:
    query = query.filter(DBScheduleExecution.status == status)
  if start_date:
    try:
      start_datetime = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
      query = query.filter(DBScheduleExecution.executed_at >= start_datetime)
    except ValueError:
      raise HTTPException(status_code=400, detail="Invalid start_date format")
  if end_date:
    try:
      end_datetime = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
      query = query.filter(DBScheduleExecution.executed_at <= end_datetime)
    except ValueError:
      raise HTTPException(status_code=400, detail="Invalid end_date format")

  # Apply sorting
  sort_field = getattr(DBScheduleExecution, sort_by, DBScheduleExecution.executed_at)
  if sort_order.lower() == "asc":
    query = query.order_by(asc(sort_field))
  else:
    query = query.order_by(desc(sort_field))

  # Execute query
  result = await db.execute(query)
  executions = result.unique().scalars().all()

  # Get all prompts for the filter dropdown
  prompt_result = await db.execute(select(DBPrompt))
  prompts = prompt_result.scalars().all()

  # Get unique statuses for the filter dropdown
  status_result = await db.execute(
    select(DBScheduleExecution.status).distinct()
  )
  statuses = [row[0] for row in status_result.all()]

  return templates.TemplateResponse(
    "executions.html",
    {
      "request": request,
      "executions": executions,
      "prompts": prompts,
      "current_prompt_id": prompt_id,
      "current_status": status,
      "current_start_date": start_date,
      "current_end_date": end_date,
      "current_sort_by": sort_by,
      "current_sort_order": sort_order,
      "statuses": statuses,
    }
  )


@router.get("/executions/{execution_id}", response_class=HTMLResponse)
async def get_execution(
  execution_id: int,
  request: Request,
  db: AsyncSession = Depends(get_db)
):
  """Get execution details by ID."""
  # Build the query with joined relationships
  query = select(DBScheduleExecution).options(
    joinedload(DBScheduleExecution.schedule).joinedload(DBSchedule.prompt)
  ).filter(DBScheduleExecution.id == execution_id)

  result = await db.execute(query)
  execution = result.unique().scalar_one_or_none()

  if execution is None:
    raise HTTPException(status_code=404, detail="Execution not found")

  # Convert to dict for template
  execution_dict = {
    "id": execution.id,
    "executed_at": execution.executed_at.strftime("%Y-%m-%d %H:%M:%S") if execution.executed_at else "N/A",
    "status": execution.status,
    "result": execution.result,
    "error": execution.error,
    "schedule": execution.schedule
  }

  return templates.TemplateResponse(
    "execution_detail.html",
    {"request": request, "execution": execution_dict}
  )

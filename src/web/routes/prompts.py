"""Routes for the prompts."""
from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.web.database import DBPrompt, DBSchedule, get_db
from src.web.templating import templates
from src.web.routes.schedules import execute_prompt_sync
import asyncio

router = APIRouter()

@router.get("/prompts", response_class=HTMLResponse)
async def list_prompts(request: Request, db: AsyncSession = Depends(get_db)):
  """List all prompts."""
  try:
    # Use select() with schedule count
    result = await db.execute(
      select(DBPrompt)
      .options(selectinload(DBPrompt.schedules))
      .order_by(DBPrompt.created_at.desc())
    )
    prompts = result.scalars().all()
    logger.info(f"Found {len(prompts)} prompts")

    # Convert SQLAlchemy models to dictionaries with schedule count
    serialized_prompts = [
      {
        "id": prompt.id,
        "content": prompt.content,
        "created_at": prompt.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schedule_count": len(prompt.schedules),
      }
      for prompt in prompts
    ]
    return templates.TemplateResponse(
      "prompts.html",
      {
        "request": request,
        "prompts": serialized_prompts,
        "error": request.query_params.get("error"),
      },
    )
  except Exception as e:
    logger.error(f"Error listing prompts: {str(e)}")
    raise


@router.post("/prompts/form", response_class=RedirectResponse)
async def create_prompt_form(
  content: str = Form(...), db: AsyncSession = Depends(get_db)
):
  """Create a new prompt from form data."""
  try:
    logger.info(f"Creating new prompt with content length: {len(content)}")

    # Create the database model directly from form data
    db_prompt = DBPrompt(content=content)
    db.add(db_prompt)
    await db.flush()  # Flush to get the ID
    logger.info(f"Created prompt with ID: {db_prompt.id}")

    await db.commit()
    logger.info("Committed prompt to database")

    # Force a new database session for the redirect
    await db.close()
    return RedirectResponse(url="/prompts", status_code=303)
  except Exception as e:
    logger.error(f"Error creating prompt: {str(e)}")
    await db.rollback()
    raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/{prompt_id}", response_class=HTMLResponse)
async def get_prompt(prompt_id: int, request: Request, db: AsyncSession = Depends(get_db)):
  """Get a prompt by ID."""
  prompt = await db.get(DBPrompt, prompt_id)
  if prompt is None:
    raise HTTPException(status_code=404, detail="Prompt not found")

  # Get schedule count
  result = await db.execute(select(DBSchedule).filter(DBSchedule.prompt_id == prompt_id))
  schedule_count = len(result.scalars().all())

  # Convert to dict with schedule count
  prompt_dict = {
    "id": prompt.id,
    "content": prompt.content,
    "created_at": prompt.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "schedule_count": schedule_count
  }

  return templates.TemplateResponse(
    "prompt_detail.html",
    {"request": request, "prompt": prompt_dict}
  )


@router.post("/prompts/{prompt_id}/delete")
async def delete_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
  """Delete a prompt by ID."""
  try:
    logger.info(f"Attempting to delete prompt {prompt_id}")

    # Load prompt with its schedules
    result = await db.execute(
      select(DBPrompt)
      .options(selectinload(DBPrompt.schedules))
      .where(DBPrompt.id == prompt_id)
    )
    prompt = result.scalar_one_or_none()

    if prompt is None:
      logger.warning(f"Prompt {prompt_id} not found")
      raise HTTPException(status_code=404, detail="Prompt not found")

    # Check if prompt has any schedules
    if prompt.schedules:
      schedule_count = len(prompt.schedules)
      logger.warning(
        f"Cannot delete prompt {prompt_id} - it has {schedule_count} attached schedules"
      )
      error_msg = f"Cannot delete prompt - it has {schedule_count} attached schedule(s). Please delete the schedules first."
      return RedirectResponse(url=f"/prompts?error={error_msg}", status_code=303)

    logger.info(f"Found prompt {prompt_id}, deleting...")
    await db.delete(prompt)
    await db.commit()
    logger.info(f"Successfully deleted prompt {prompt_id}")
    return RedirectResponse(url="/prompts", status_code=303)
  except Exception as e:
    logger.error(f"Error deleting prompt {prompt_id}: {str(e)}")
    await db.rollback()
    error_msg = str(e)
    return RedirectResponse(url=f"/prompts?error={error_msg}", status_code=303)

@router.post("/prompts/{prompt_id}/run")
async def run_prompt_once(prompt_id: int, db: AsyncSession = Depends(get_db)):
  """Run a prompt once immediately."""
  try:
    logger.info(f"Running prompt {prompt_id} once")

    # Get the prompt
    prompt = await db.get(DBPrompt, prompt_id)
    if prompt is None:
      raise HTTPException(status_code=404, detail="Prompt not found")

    # Run the execution in the background
    asyncio.create_task(execute_prompt_sync(prompt_id))

    return RedirectResponse(url="/executions", status_code=303)
  except Exception as e:
    logger.error(f"Error running prompt {prompt_id}: {str(e)}")
    error_msg = str(e)
    return RedirectResponse(url=f"/prompts?error={error_msg}", status_code=303)

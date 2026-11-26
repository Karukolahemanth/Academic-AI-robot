from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date
from database import get_db
from models.models import ToDoTask
from auth import get_current_user

router = APIRouter(prefix="/api/todo", tags=["ToDo"])

class TaskCreate(BaseModel):
    title: str
    priority: Optional[str] = "medium"
    due_date: Optional[date] = None

    @field_validator("due_date", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    is_completed: Optional[bool] = None

    @field_validator("due_date", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

# ── GET /api/todo/ ────────────────────────────────────────────────────────────
@router.get("/")
@router.get("", include_in_schema=False)
def get_tasks(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    tasks = db.query(ToDoTask).filter(ToDoTask.user_id == current_user["user_id"]).order_by(
        asc(ToDoTask.is_completed), desc(ToDoTask.task_id)
    ).all()
    return tasks

# ── POST /api/todo/ ───────────────────────────────────────────────────────────
@router.post("/", status_code=201)
@router.post("", status_code=201, include_in_schema=False)
def add_task(payload: TaskCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    task = ToDoTask(
        user_id=current_user["user_id"],
        title=payload.title,
        priority=payload.priority or "medium",
        due_date=payload.due_date,
        is_completed=False,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

# ── PUT /api/todo/{task_id} ───────────────────────────────────────────────────
@router.put("/{task_id}")
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    task = db.query(ToDoTask).filter(ToDoTask.task_id == task_id, ToDoTask.user_id == current_user["user_id"]).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if payload.title is not None:
        task.title = payload.title
    if payload.priority is not None:
        task.priority = payload.priority
    if "due_date" in payload.model_fields_set:
        task.due_date = payload.due_date
    if payload.is_completed is not None:
        task.is_completed = payload.is_completed
    db.commit()
    db.refresh(task)
    return task

# ── DELETE /api/todo/{task_id} ────────────────────────────────────────────────
@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    task = db.query(ToDoTask).filter(ToDoTask.task_id == task_id, ToDoTask.user_id == current_user["user_id"]).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}

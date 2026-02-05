from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.crud import tasks as crud_tasks
from app.schemas.tasks import TaskCreate, TaskOut, TaskUpdate
from app.db.models import User

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_tasks.create_task(db, user_id=current_user.id, task_in=task_in)

@router.get("", response_model=list[TaskOut])
def list_tasks(
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
    priority: int | None = None,
    sort: str = "-created_at",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_tasks.list_tasks(
        db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        status=status,
        priority=priority,
        sort=sort,
    )


@router.get("/{task_id}", response_model=TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = crud_tasks.get_task(db, user_id=current_user.id, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = crud_tasks.update_task(db, user_id=current_user.id, task_id=task_id, task_in=task_in)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ok = crud_tasks.delete_task(db, user_id=current_user.id, task_id=task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return None

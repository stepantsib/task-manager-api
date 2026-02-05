from sqlalchemy.orm import Session
from sqlalchemy import select, desc, asc

from app.db.models import Task
from app.schemas.tasks import TaskCreate, TaskUpdate  # названия подстрой под себя

ALLOWED_SORT_FIELDS = {
    "created_at": Task.created_at,
    "priority": Task.priority,
    "status": Task.status,
    "title": Task.title,
}

def create_task(db: Session, user_id: int, task_in: TaskCreate) -> Task:
    task = Task(**task_in.model_dump(), user_id=user_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def get_task(db: Session, user_id: int, task_id: int) -> Task | None:
    stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    return db.execute(stmt).scalars().first()

def list_tasks(
    db: Session,
    user_id: int,
    limit: int = 20,
    offset: int = 0,
    status: str | None = None,
    priority: int | None = None,
    sort: str = "-created_at",
) -> list[Task]:
    stmt = select(Task).where(Task.user_id == user_id)

    if status:
        stmt = stmt.where(Task.status == status)

    if priority is not None:
        stmt = stmt.where(Task.priority == priority)

    # sort example: "created_at" or "-created_at"
    direction = desc if sort.startswith("-") else asc
    field_name = sort.lstrip("-")

    sort_field = ALLOWED_SORT_FIELDS.get(field_name)
    if sort_field is None:
        # можно либо молча дефолтить, либо кидать ошибку наверх
        sort_field = Task.created_at
        direction = desc

    stmt = stmt.order_by(direction(sort_field)).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars().all())


def update_task(db: Session, user_id: int, task_id: int, task_in: TaskUpdate) -> Task | None:
    task = get_task(db, user_id=user_id, task_id=task_id)
    if not task:
        return None

    data = task_in.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(task, k, v)

    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def delete_task(db: Session, user_id: int, task_id: int) -> bool:
    task = get_task(db, user_id=user_id, task_id=task_id)
    if not task:
        return False
    db.delete(task)
    db.commit()
    return True

from typing import List, Optional
from sqlmodel import Session, select
from ..models.task import Task, TaskCreate, TaskUpdate
from ..models.user import User


class TaskService:
    def __init__(self, session: Session):
        self.session = session

    def create_task(self, task_data: TaskCreate, user_id: str) -> Task:
        """Create a new task for the given user"""
        task = Task(**task_data.model_dump())
        task.user_id = user_id
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get_task_by_id(self, task_id: str, user_id: str) -> Optional[Task]:
        """Get a specific task by ID for the given user"""
        task = self.session.exec(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        ).first()
        return task

    def get_tasks_by_user(
        self, user_id: str, status: Optional[str] = None
    ) -> List[Task]:
        """Get all tasks for the given user, optionally filtered by status"""
        query = select(Task).where(Task.user_id == user_id)
        if status:
            query = query.where(Task.status == status)
        
        tasks = self.session.exec(query).all()
        return tasks

    def update_task(self, task_id: str, task_data: TaskUpdate, user_id: str) -> Optional[Task]:
        """Update a specific task for the given user"""
        task = self.get_task_by_id(task_id, user_id)
        if not task:
            return None
        
        update_data = task_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a specific task for the given user"""
        task = self.get_task_by_id(task_id, user_id)
        if not task:
            return False
        
        self.session.delete(task)
        self.session.commit()
        return True

    def complete_task(self, task_id: str, user_id: str) -> Optional[Task]:
        """Mark a specific task as completed for the given user"""
        task = self.get_task_by_id(task_id, user_id)
        if not task:
            return None
        
        task.status = "completed"
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task
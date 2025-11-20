from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any


class SystemSettingBase(BaseModel):
    key: str
    value: Optional[str] = None
    data_type: str = "string"
    description: Optional[str] = None
    group: str = "general"


class SystemSettingCreate(SystemSettingBase):
    pass


class SystemSettingUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None


class SystemSetting(SystemSettingBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WorkerLogBase(BaseModel):
    job_name: str
    job_type: str
    status: str = "pending"
    items_processed: int = 0
    items_created: int = 0
    items_updated: int = 0
    items_failed: int = 0


class WorkerLogCreate(WorkerLogBase):
    pass


class WorkerLog(WorkerLogBase):
    id: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[dict] = {}
    created_at: datetime
    
    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_products: int
    active_products: int
    total_categories: int
    active_deals: int
    total_price_checks_today: int
    telegram_messages_sent: int
    last_worker_run: Optional[datetime] = None
    system_health: str = "healthy"

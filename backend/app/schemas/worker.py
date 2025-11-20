"""Worker schemas for API responses"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class JobStatus(BaseModel):
    """Individual job status"""
    job_type: str
    status: str
    last_run: Optional[datetime]
    duration: Optional[int]
    items_processed: Optional[int]
    items_created: Optional[int]
    items_updated: Optional[int]
    items_failed: Optional[int]


class WorkerStatisticsData(BaseModel):
    """Worker statistics data"""
    total_products: int
    total_deals: int
    published_deals: int
    products_needing_check: int
    recent_jobs: int


class WorkerStatus(BaseModel):
    """Overall worker status"""
    is_running: bool
    jobs: List[JobStatus]
    statistics: WorkerStatisticsData


class WorkerLogDetail(BaseModel):
    """Detailed worker log"""
    id: int
    job_name: str
    job_type: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    items_processed: Optional[int]
    items_created: Optional[int]
    items_updated: Optional[int]
    items_failed: Optional[int]
    error_message: Optional[str]
    error_trace: Optional[str]
    job_metadata: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class WorkerStatistics(BaseModel):
    """Worker statistics summary"""
    period_days: int
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    success_rate: float
    total_items_processed: int
    total_items_created: int
    total_items_updated: int
    average_duration_seconds: float
    job_type_breakdown: Dict[str, Any]


class ProgressItem(BaseModel):
    """Progress tracking for a specific item"""
    total: int
    checked_recently: Optional[int] = None
    with_products: Optional[int] = None
    sent_to_telegram: Optional[int] = None
    percentage: float


class WorkerProgress(BaseModel):
    """Real-time worker progress"""
    products: ProgressItem
    categories: ProgressItem
    deals: ProgressItem

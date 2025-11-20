"""
Worker Management API
Real-time worker status, control, and monitoring
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, case, and_, or_
import httpx
from functools import lru_cache
import time

from app.db.database import get_db
from app.db import models
from app.schemas import worker as worker_schema
from app.api.auth import get_current_user
import json
from pathlib import Path

router = APIRouter()

# Worker control file path (shared volume)
WORKER_CONTROL_FILE = Path("/app/worker_control.json")

# Simple in-memory cache for worker status
_status_cache = {
    'data': None,
    'timestamp': 0,
    'ttl': 5  # 5 seconds cache
}


@router.get("/status", response_model=worker_schema.WorkerStatus)
async def get_worker_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    force_refresh: bool = Query(False, description="Force cache refresh")
):
    """Get overall worker system status with caching"""
    
    # Check cache if not forcing refresh
    current_time = time.time()
    if not force_refresh and _status_cache['data'] is not None:
        if current_time - _status_cache['timestamp'] < _status_cache['ttl']:
            return _status_cache['data']
    
    # Get latest logs for each job type
    # Map job types to display names
    job_types_map = {
        "fetch_products": ["fetch_products", "amazon_fetch"],
        "check_prices": ["check_prices", "price_check"],
        "send_telegram": ["send_telegram", "telegram_send"]
    }
    
    jobs_status = []
    for display_type, search_types in job_types_map.items():
        # Search for any of the possible type names
        latest_log = db.query(models.WorkerLog).filter(
            models.WorkerLog.job_type.in_(search_types)
        ).order_by(desc(models.WorkerLog.created_at)).first()
        
        if latest_log:
            jobs_status.append({
                "job_type": display_type,
                "status": latest_log.status,
                "last_run": latest_log.started_at,
                "duration": latest_log.duration_seconds,
                "items_processed": latest_log.items_processed,
                "items_created": latest_log.items_created,
                "items_updated": latest_log.items_updated,
                "items_failed": latest_log.items_failed
            })
        else:
            # Add placeholder for jobs that haven't run yet
            jobs_status.append({
                "job_type": display_type,
                "status": "never_run",
                "last_run": None,
                "duration": None,
                "items_processed": 0,
                "items_created": 0,
                "items_updated": 0,
                "items_failed": 0
            })
    
    # Get statistics with optimized single query (avoid N+1)
    cutoff_time = datetime.utcnow() - timedelta(hours=6)
    yesterday = datetime.utcnow() - timedelta(hours=24)
    
    # Optimized aggregation query - single DB roundtrip
    stats = db.query(
        func.count(func.distinct(case(
            (models.Product.is_active == True, models.Product.id)
        ))).label('total_products'),
        func.count(func.distinct(case(
            (models.Deal.is_active == True, models.Deal.id)
        ))).label('total_deals'),
        func.count(func.distinct(case(
            (and_(models.Deal.is_active == True, models.Deal.is_published == True), models.Deal.id)
        ))).label('published_deals'),
        func.count(func.distinct(case(
            (and_(
                models.Product.is_active == True,
                or_(
                    models.Product.last_checked_at == None,
                    models.Product.last_checked_at < cutoff_time
                )
            ), models.Product.id)
        ))).label('products_needing_check'),
        func.count(func.distinct(case(
            (models.WorkerLog.created_at >= yesterday, models.WorkerLog.id)
        ))).label('recent_logs')
    ).outerjoin(models.Product).outerjoin(models.Deal).outerjoin(models.WorkerLog).first()
    
    total_products = stats.total_products or 0
    total_deals = stats.total_deals or 0
    published_deals = stats.published_deals or 0
    products_needing_check = stats.products_needing_check or 0
    recent_logs = stats.recent_logs or 0
    
    result = {
        "is_running": any(job["status"] == "running" for job in jobs_status),
        "jobs": jobs_status,
        "statistics": {
            "total_products": total_products,
            "total_deals": total_deals,
            "published_deals": published_deals,
            "products_needing_check": products_needing_check,
            "recent_jobs": recent_logs
        }
    }
    
    # Update cache
    _status_cache['data'] = result
    _status_cache['timestamp'] = current_time
    
    return result


@router.get("/logs", response_model=List[worker_schema.WorkerLogDetail])
async def list_worker_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    job_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """List worker execution logs with filters"""
    
    query = db.query(models.WorkerLog)
    
    if job_type:
        query = query.filter(models.WorkerLog.job_type == job_type)
    
    if status:
        query = query.filter(models.WorkerLog.status == status)
    
    logs = query.order_by(desc(models.WorkerLog.created_at)).offset(skip).limit(limit).all()
    
    return logs


@router.get("/logs/{log_id}", response_model=worker_schema.WorkerLogDetail)
async def get_worker_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get detailed worker log"""
    
    log = db.query(models.WorkerLog).filter(models.WorkerLog.id == log_id).first()
    
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    return log


@router.get("/statistics/overview", response_model=worker_schema.WorkerStatistics)
async def get_worker_statistics(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get worker statistics for the last N days"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Logs in period
    logs = db.query(models.WorkerLog).filter(
        models.WorkerLog.created_at >= cutoff_date
    ).all()
    
    # Calculate statistics
    total_jobs = len(logs)
    completed_jobs = len([l for l in logs if l.status == "completed"])
    failed_jobs = len([l for l in logs if l.status == "failed"])
    
    total_items_processed = sum(l.items_processed or 0 for l in logs)
    total_items_created = sum(l.items_created or 0 for l in logs)
    total_items_updated = sum(l.items_updated or 0 for l in logs)
    
    # Average duration
    completed_with_duration = [l for l in logs if l.status == "completed" and l.duration_seconds]
    avg_duration = sum(l.duration_seconds for l in completed_with_duration) / len(completed_with_duration) if completed_with_duration else 0
    
    # Success rate
    success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
    
    # Job type breakdown
    job_type_stats = {}
    for log in logs:
        if log.job_type not in job_type_stats:
            job_type_stats[log.job_type] = {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "items_processed": 0
            }
        
        job_type_stats[log.job_type]["total"] += 1
        if log.status == "completed":
            job_type_stats[log.job_type]["completed"] += 1
        elif log.status == "failed":
            job_type_stats[log.job_type]["failed"] += 1
        job_type_stats[log.job_type]["items_processed"] += log.items_processed or 0
    
    return {
        "period_days": days,
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "success_rate": round(success_rate, 2),
        "total_items_processed": total_items_processed,
        "total_items_created": total_items_created,
        "total_items_updated": total_items_updated,
        "average_duration_seconds": round(avg_duration, 2),
        "job_type_breakdown": job_type_stats
    }


@router.get("/progress", response_model=worker_schema.WorkerProgress)
async def get_worker_progress(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get real-time worker progress"""
    
    # Products progress
    total_products = db.query(models.Product).filter(models.Product.is_active == True).count()
    
    cutoff_time = datetime.utcnow() - timedelta(hours=6)
    checked_products = db.query(models.Product).filter(
        models.Product.is_active == True,
        models.Product.last_checked_at != None,
        models.Product.last_checked_at >= cutoff_time
    ).count()
    
    # Categories progress
    total_categories = db.query(models.Category).filter(models.Category.is_active == True).count()
    categories_with_products = db.query(models.Category.id).join(models.Product).filter(
        models.Category.is_active == True
    ).distinct().count()
    
    # Deals progress
    total_deals = db.query(models.Deal).filter(models.Deal.is_active == True).count()
    telegram_sent = db.query(models.Deal).filter(
        models.Deal.is_active == True,
        models.Deal.telegram_sent == True
    ).count()
    
    return {
        "products": {
            "total": total_products,
            "checked_recently": checked_products,
            "percentage": round((checked_products / total_products * 100) if total_products > 0 else 0, 2)
        },
        "categories": {
            "total": total_categories,
            "with_products": categories_with_products,
            "percentage": round((categories_with_products / total_categories * 100) if total_categories > 0 else 0, 2)
        },
        "deals": {
            "total": total_deals,
            "sent_to_telegram": telegram_sent,
            "percentage": round((telegram_sent / total_deals * 100) if total_deals > 0 else 0, 2)
        }
    }


@router.post("/trigger/{job_type}")
async def trigger_worker_job(
    job_type: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Trigger a worker job manually
    Note: This creates a log entry but actual execution should be done by the worker
    """
    
    valid_job_types = ["fetch_products", "check_prices", "send_telegram"]
    
    if job_type not in valid_job_types:
        raise HTTPException(status_code=400, detail=f"Invalid job type. Must be one of: {valid_job_types}")
    
    # Check if job is already running
    running_job = db.query(models.WorkerLog).filter(
        models.WorkerLog.job_type == job_type,
        models.WorkerLog.status == "running"
    ).first()
    
    if running_job:
        raise HTTPException(status_code=409, detail=f"Job {job_type} is already running")
    
    # Create a pending job log
    log = models.WorkerLog(
        job_name=f"manual_{job_type}",
        job_type=job_type,
        status="pending",
        started_at=datetime.utcnow(),
        job_metadata={"triggered_by": current_user.username, "manual": True}
    )
    
    db.add(log)
    db.commit()
    db.refresh(log)
    
    return {
        "success": True,
        "message": f"Job {job_type} has been queued",
        "log_id": log.id
    }


@router.post("/control/pause")
async def pause_scheduler(
    current_user: models.User = Depends(get_current_user)
):
    """Pause the worker scheduler (all automatic jobs)"""
    try:
        # Load current state
        if WORKER_CONTROL_FILE.exists():
            with open(WORKER_CONTROL_FILE, 'r') as f:
                state = json.load(f)
        else:
            state = {"scheduler_enabled": True, "jobs": {}}
        
        # Update state
        state["scheduler_enabled"] = False
        
        # Save state
        with open(WORKER_CONTROL_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        
        return {
            "success": True,
            "message": "✅ Scheduler paused. Automatic jobs will not run.",
            "note": "Manual jobs can still be triggered"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error pausing scheduler: {str(e)}")


@router.post("/control/resume")
async def resume_scheduler(
    current_user: models.User = Depends(get_current_user)
):
    """Resume the worker scheduler"""
    try:
        # Load current state
        if WORKER_CONTROL_FILE.exists():
            with open(WORKER_CONTROL_FILE, 'r') as f:
                state = json.load(f)
        else:
            state = {"scheduler_enabled": True, "jobs": {}}
        
        # Update state
        state["scheduler_enabled"] = True
        
        # Save state
        with open(WORKER_CONTROL_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        
        return {
            "success": True,
            "message": "▶️ Scheduler resumed. Automatic jobs will run on schedule."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resuming scheduler: {str(e)}")


@router.post("/control/job/{job_type}/enable")
async def enable_job(
    job_type: str,
    current_user: models.User = Depends(get_current_user)
):
    """Enable a specific job"""
    valid_job_types = ["fetch_products", "check_prices", "send_telegram"]
    
    if job_type not in valid_job_types:
        raise HTTPException(status_code=400, detail=f"Invalid job type. Must be one of: {valid_job_types}")
    
    try:
        # Load current state
        if WORKER_CONTROL_FILE.exists():
            with open(WORKER_CONTROL_FILE, 'r') as f:
                state = json.load(f)
        else:
            state = {"scheduler_enabled": True, "jobs": {}}
        
        # Update job state
        if "jobs" not in state:
            state["jobs"] = {}
        if job_type not in state["jobs"]:
            state["jobs"][job_type] = {}
        state["jobs"][job_type]["enabled"] = True
        
        # Save state
        with open(WORKER_CONTROL_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        
        return {
            "success": True,
            "message": f"✅ Job '{job_type}' enabled"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enabling job: {str(e)}")


@router.post("/control/job/{job_type}/disable")
async def disable_job(
    job_type: str,
    current_user: models.User = Depends(get_current_user)
):
    """Disable a specific job"""
    valid_job_types = ["fetch_products", "check_prices", "send_telegram"]
    
    if job_type not in valid_job_types:
        raise HTTPException(status_code=400, detail=f"Invalid job type. Must be one of: {valid_job_types}")
    
    try:
        # Load current state
        if WORKER_CONTROL_FILE.exists():
            with open(WORKER_CONTROL_FILE, 'r') as f:
                state = json.load(f)
        else:
            state = {"scheduler_enabled": True, "jobs": {}}
        
        # Update job state
        if "jobs" not in state:
            state["jobs"] = {}
        if job_type not in state["jobs"]:
            state["jobs"][job_type] = {}
        state["jobs"][job_type]["enabled"] = False
        
        # Save state
        with open(WORKER_CONTROL_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        
        return {
            "success": True,
            "message": f"⏸️ Job '{job_type}' disabled"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disabling job: {str(e)}")


@router.get("/control/status")
async def get_control_status(
    current_user: models.User = Depends(get_current_user)
):
    """Get current control status"""
    try:
        if WORKER_CONTROL_FILE.exists():
            with open(WORKER_CONTROL_FILE, 'r') as f:
                state = json.load(f)
            return state
        else:
            # Default state
            return {
                "scheduler_enabled": True,
                "jobs": {
                    "fetch_products": {"enabled": True},
                    "check_prices": {"enabled": True},
                    "send_telegram": {"enabled": True}
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading control status: {str(e)}")

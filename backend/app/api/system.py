"""
Professional System Monitoring & Control API
Unified endpoint for all system management needs
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import redis
from pydantic import BaseModel

from app.db.database import get_db
from app.db import models

router = APIRouter()

# Redis connection
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

# Response Models
class WorkerInfo(BaseModel):
    name: str
    status: str
    active_tasks: int
    pool_size: Optional[int] = None

class SystemHealth(BaseModel):
    status: str  # healthy, degraded, unhealthy
    score: int  # 0-100
    database: str
    redis: str
    workers_online: int
    workers_total: int

class SystemStats(BaseModel):
    total_products: int
    active_products: int
    active_deals: int
    price_checks_today: int
    tasks_active: int
    workers_online: int
    last_worker_run: Optional[datetime]

class SystemOverview(BaseModel):
    health: SystemHealth
    stats: SystemStats
    workers: List[WorkerInfo]
    recent_activity: List[Dict[str, Any]]


def get_celery_inspect_fast():
    """Get Celery inspect with aggressive timeout for speed"""
    from celery import Celery
    
    celery_app = Celery('fiyatradari')
    celery_app.config_from_object({
        'broker_url': 'redis://redis:6379/0',
        'result_backend': 'redis://redis:6379/1',
        'broker_connection_timeout': 1.0,  # 1 second
        'broker_connection_max_retries': 0,
    })
    
    return celery_app.control.inspect(timeout=0.5)  # 500ms timeout


@router.get("/overview", response_model=SystemOverview)
async def get_system_overview(db: Session = Depends(get_db)):
    """
    Get complete system overview - OPTIMIZED FOR SPEED
    Single endpoint that returns everything needed for dashboard
    """
    
    # === 1. DATABASE HEALTH ===
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "unhealthy"
    
    # === 2. REDIS HEALTH ===
    redis_status = "healthy"
    try:
        redis_client.ping()
    except:
        redis_status = "unhealthy"
    
    # === 3. WORKERS (FAST - cached or quick check) ===
    workers = []
    workers_online = 0
    tasks_active = 0
    
    try:
        inspect = get_celery_inspect_fast()
        stats = inspect.stats() or {}
        active = inspect.active() or {}
        
        workers_online = len(stats)
        
        for worker_name in stats.keys():
            worker_active_tasks = active.get(worker_name, [])
            tasks_active += len(worker_active_tasks)
            
            workers.append(WorkerInfo(
                name=worker_name.split('@')[1] if '@' in worker_name else worker_name,
                status='online',
                active_tasks=len(worker_active_tasks)
            ))
    except:
        # If Celery inspect fails, don't block - just show degraded status
        pass
    
    # === 4. DATABASE STATS (optimized queries) ===
    total_products = db.query(models.Product).count()
    active_products = db.query(models.Product).filter(models.Product.is_active == True).count()
    active_deals = db.query(models.Deal).filter(models.Deal.is_active == True).count()
    
    # Today's price checks
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    price_checks_today = db.query(models.Product).filter(
        models.Product.last_checked_at >= today
    ).count()
    
    # Last worker run
    last_worker_log = db.query(models.WorkerLog).order_by(
        models.WorkerLog.created_at.desc()
    ).first()
    last_worker_run = last_worker_log.created_at if last_worker_log else None
    
    # === 5. RECENT ACTIVITY (last 5 important events) ===
    recent_activity = []
    
    # Recent deals
    recent_deals = db.query(models.Deal).filter(
        models.Deal.is_active == True
    ).order_by(models.Deal.created_at.desc()).limit(3).all()
    
    for deal in recent_deals:
        recent_activity.append({
            'type': 'deal',
            'title': deal.title[:50],
            'discount': float(deal.discount_percentage),
            'time': deal.created_at.isoformat() if deal.created_at else datetime.utcnow().isoformat()
        })
    
    # Recent price changes
    recent_changes = db.query(models.PriceHistory).order_by(
        models.PriceHistory.recorded_at.desc()
    ).limit(2).all()
    
    for change in recent_changes:
        product = db.query(models.Product).filter(models.Product.id == change.product_id).first()
        if product:
            recent_activity.append({
                'type': 'price_change',
                'title': product.title[:50] if product.title else 'Unknown',
                'old_price': float(change.old_price) if change.old_price else 0,
                'new_price': float(change.new_price) if change.new_price else 0,
                'time': change.recorded_at.isoformat() if change.recorded_at else datetime.utcnow().isoformat()
            })
    
    # Sort by time
    recent_activity.sort(key=lambda x: x['time'], reverse=True)
    recent_activity = recent_activity[:5]
    
    # === 6. CALCULATE HEALTH SCORE ===
    health_score = 100
    
    if db_status != "healthy":
        health_score -= 50
    if redis_status != "healthy":
        health_score -= 20
    if workers_online < 5:  # Assuming you want at least 5 workers
        health_score -= 15
    if last_worker_run:
        hours_since = (datetime.utcnow() - last_worker_run).total_seconds() / 3600
        if hours_since > 24:
            health_score -= 15
    
    health_status = 'healthy' if health_score >= 80 else 'degraded' if health_score >= 50 else 'unhealthy'
    
    # === BUILD RESPONSE ===
    return SystemOverview(
        health=SystemHealth(
            status=health_status,
            score=health_score,
            database=db_status,
            redis=redis_status,
            workers_online=workers_online,
            workers_total=workers_online  # For now, online = total
        ),
        stats=SystemStats(
            total_products=total_products,
            active_products=active_products,
            active_deals=active_deals,
            price_checks_today=price_checks_today,
            tasks_active=tasks_active,
            workers_online=workers_online,
            last_worker_run=last_worker_run
        ),
        workers=workers,
        recent_activity=recent_activity
    )


@router.get("/workers")
async def get_workers_detailed():
    """Get detailed worker information"""
    try:
        inspect = get_celery_inspect_fast()
        
        active = inspect.active() or {}
        stats = inspect.stats() or {}
        registered = inspect.registered() or {}
        
        workers = []
        for worker_name in stats.keys():
            worker_stats = stats.get(worker_name, {})
            worker_active_tasks = active.get(worker_name, [])
            worker_registered = registered.get(worker_name, [])
            
            workers.append({
                'name': worker_name,
                'short_name': worker_name.split('@')[1] if '@' in worker_name else worker_name,
                'status': 'online',
                'active_tasks': len(worker_active_tasks),
                'current_tasks': [
                    {
                        'id': task.get('id'),
                        'name': task.get('name', '').split('.')[-1],  # Get task name without module
                        'args': str(task.get('args', []))[:100]  # Limit length
                    }
                    for task in worker_active_tasks[:5]  # Limit to 5 tasks
                ],
                'registered_tasks_count': len(worker_registered),
                'pool_info': worker_stats.get('pool', {})
            })
        
        return {
            'workers': workers,
            'total': len(workers),
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/workers/{worker_name}/restart")
async def restart_worker(worker_name: str):
    """Restart worker pool"""
    try:
        from celery import Celery
        
        celery_app = Celery('fiyatradari')
        celery_app.config_from_object({
            'broker_url': 'redis://redis:6379/0',
            'result_backend': 'redis://redis:6379/1',
        })
        
        celery_app.control.pool_restart(destination=[worker_name])
        
        return {
            'status': 'success',
            'message': f'Restart signal sent to {worker_name}',
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/recent")
async def get_recent_tasks(limit: int = 20):
    """Get recent task executions from worker logs"""
    try:
        from app.db import models
        from app.db.database import get_db
        
        db = next(get_db())
        
        logs = db.query(models.WorkerLog).order_by(
            models.WorkerLog.created_at.desc()
        ).limit(limit).all()
        
        return {
            'tasks': [
                {
                    'task_type': log.task_type,
                    'status': log.status,
                    'message': log.message[:100] if log.message else None,
                    'created_at': log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ],
            'total': len(logs)
        }
    except Exception as e:
        return {'tasks': [], 'total': 0, 'error': str(e)}

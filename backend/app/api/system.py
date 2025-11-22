"""
🚀 PROFESSIONAL SYSTEM MANAGEMENT API
Custom-built for FiyatRadarı - No external tools needed

Features:
- Worker pool scaling (dynamic concurrency)
- Schedule management (cron editor)
- Task monitoring & control
- Real-time system health
- Performance metrics
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, desc, func
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel
import redis
import json
import logging
from pathlib import Path

from app.db.database import get_db
from app.db import models
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Redis for real-time data
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

# Control files
WORKER_CONTROL_FILE = Path("/app/worker_control.json")
SCHEDULE_FILE = Path("/app/worker_schedule.json")

# ============================================================================
# MODELS
# ============================================================================

class WorkerPoolStatus(BaseModel):
    current_size: int
    max_size: int
    min_size: int
    active_workers: int
    idle_workers: int

class JobSchedule(BaseModel):
    job_type: str
    enabled: bool
    cron: str  # Cron expression
    last_run: Optional[datetime]
    next_run: Optional[str]
    
class ActiveTask(BaseModel):
    task_id: str
    task_name: str
    worker: str
    started: str
    duration_seconds: int

class SystemHealthStatus(BaseModel):
    status: str  # healthy, degraded, critical
    score: int
    database: bool
    redis: bool
    workers: int
    queue_size: int

class SystemDashboard(BaseModel):
    health: SystemHealthStatus
    workers: WorkerPoolStatus
    schedules: List[JobSchedule]
    active_tasks: List[ActiveTask]
    stats: Dict[str, int]

# ============================================================================
# WORKER POOL MANAGEMENT
# ============================================================================

@router.get("/workers/pool")
async def get_worker_pool_status():
    """Get current worker pool configuration"""
    try:
        from celery import Celery
        
        celery_app = Celery('fiyatradari')
        celery_app.config_from_object({
            'broker_url': 'redis://redis:6379/0',
            'result_backend': 'redis://redis:6379/1',
        })
        
        inspect = celery_app.control.inspect(timeout=1.0)
        stats = inspect.stats() or {}
        active = inspect.active() or {}
        
        # Count workers
        total_workers = len(stats)
        active_tasks = sum(len(tasks) for tasks in active.values())
        
        # Get pool sizes from worker stats
        pool_sizes = []
        for worker_stats in stats.values():
            pool = worker_stats.get('pool', {})
            max_concurrency = pool.get('max-concurrency', 4)
            pool_sizes.append(max_concurrency)
        
        current_pool_size = pool_sizes[0] if pool_sizes else 4
        
        return {
            'current_size': current_pool_size,
            'max_size': 20,
            'min_size': 1,
            'active_workers': total_workers,
            'idle_workers': max(0, total_workers - active_tasks),
            'tasks_running': active_tasks
        }
    except Exception as e:
        return {
            'current_size': 4,
            'max_size': 20,
            'min_size': 1,
            'active_workers': 0,
            'idle_workers': 0,
            'tasks_running': 0,
            'error': str(e)
        }


@router.post("/workers/pool/scale")
async def scale_worker_pool(
    size: int,
    current_user: models.User = Depends(get_current_user)
):
    """
    Scale worker pool size (set concurrency level)
    Size: 1-20 concurrent tasks
    
    NOTE: This saves the configuration. Workers will apply it on next restart.
    For immediate effect, restart workers after changing pool size.
    """
    if size < 1 or size > 20:
        raise HTTPException(status_code=400, detail="Size must be between 1 and 20")
    
    try:
        # Save configuration to Redis (permanent storage)
        config = {
            'pool_size': size, 
            'updated_at': datetime.utcnow().isoformat(),
            'updated_by': current_user.username
        }
        redis_client.set('worker:pool:config', json.dumps(config))
        
        # Also set a simple key for easier worker access
        redis_client.set('worker:pool:size', str(size))
        
        # Try to notify workers (best effort, may not work on all pool types)
        try:
            from celery import Celery
            
            celery_app = Celery('fiyatradari')
            celery_app.config_from_object({
                'broker_url': 'redis://redis:6379/0',
                'result_backend': 'redis://redis:6379/1',
            })
            
            # Send pool resize - this works differently on different pool types
            # For prefork pool, we can try pool_restart
            celery_app.control.pool_restart()
            
        except Exception as e:
            # Not critical if this fails, config is saved
            logger.warning(f"Could not send pool restart signal: {e}")
        
        return {
            'success': True,
            'message': f'Worker pool size set to {size}. Restart workers for immediate effect.',
            'new_size': size,
            'note': 'Configuration saved. Restart workers: docker compose restart celery_worker'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SCHEDULE MANAGEMENT
# ============================================================================

@router.get("/schedules")
async def get_schedules():
    """Get all job schedules"""
    try:
        if SCHEDULE_FILE.exists():
            with open(SCHEDULE_FILE, 'r') as f:
                schedules = json.load(f)
        else:
            # Default schedules
            schedules = {
                'fetch_products': {
                    'enabled': True,
                    'cron': '0 */6 * * *',  # Every 6 hours
                    'description': 'Ürün Çekme'
                },
                'check_prices': {
                    'enabled': True,
                    'cron': '0 */4 * * *',  # Every 4 hours
                    'description': 'Fiyat Kontrol'
                },
                'update_missing_ratings': {
                    'enabled': True,
                    'cron': '0 */8 * * *',  # Every 8 hours
                    'description': 'Rating Güncelleme'
                },
                'send_telegram': {
                    'enabled': True,
                    'cron': '*/30 * * * *',  # Every 30 minutes
                    'description': 'Telegram Bildirimleri'
                }
            }
        
        return {'schedules': schedules}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedules/{job_type}")
async def update_schedule(
    job_type: str,
    enabled: bool,
    cron: str,
    current_user: models.User = Depends(get_current_user)
):
    """Update job schedule"""
    try:
        # Load current schedules
        if SCHEDULE_FILE.exists():
            with open(SCHEDULE_FILE, 'r') as f:
                schedules = json.load(f)
        else:
            schedules = {}
        
        # Update schedule
        if job_type not in schedules:
            schedules[job_type] = {}
        
        schedules[job_type]['enabled'] = enabled
        schedules[job_type]['cron'] = cron
        schedules[job_type]['updated_at'] = datetime.utcnow().isoformat()
        schedules[job_type]['updated_by'] = current_user.username
        
        # Save
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump(schedules, f, indent=2)
        
        return {
            'success': True,
            'message': f'Schedule updated for {job_type}',
            'schedule': schedules[job_type]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TASK MANAGEMENT
# ============================================================================

@router.get("/tasks/active")
async def get_active_tasks():
    """Get currently running tasks"""
    try:
        from celery import Celery
        
        celery_app = Celery('fiyatradari')
        celery_app.config_from_object({
            'broker_url': 'redis://redis:6379/0',
            'result_backend': 'redis://redis:6379/1',
        })
        
        inspect = celery_app.control.inspect(timeout=1.0)
        active = inspect.active() or {}
        
        tasks = []
        for worker_name, worker_tasks in active.items():
            for task in worker_tasks:
                started = task.get('time_start', 0)
                duration = int(datetime.utcnow().timestamp() - started) if started else 0
                
                tasks.append({
                    'task_id': task.get('id', 'unknown'),
                    'task_name': task.get('name', '').split('.')[-1],
                    'worker': worker_name.split('@')[1] if '@' in worker_name else worker_name,
                    'started': datetime.fromtimestamp(started).isoformat() if started else 'unknown',
                    'duration_seconds': duration
                })
        
        return {'tasks': tasks, 'total': len(tasks)}
    except Exception as e:
        return {'tasks': [], 'total': 0, 'error': str(e)}


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: models.User = Depends(get_current_user)
):
    """Cancel a running task"""
    try:
        from celery import Celery
        
        celery_app = Celery('fiyatradari')
        celery_app.config_from_object({
            'broker_url': 'redis://redis:6379/0',
            'result_backend': 'redis://redis:6379/1',
        })
        
        celery_app.control.revoke(task_id, terminate=True, signal='SIGKILL')
        
        return {
            'success': True,
            'message': f'Task {task_id} cancelled'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DASHBOARD - MAIN ENDPOINT
# ============================================================================

@router.get("/dashboard")
async def get_system_dashboard(db: Session = Depends(get_db)):
    """
    🎯 MAIN DASHBOARD ENDPOINT
    Get everything needed for the system management dashboard
    """
    
    # === HEALTH CHECK ===
    db_healthy = True
    try:
        db.execute(text("SELECT 1"))
    except:
        db_healthy = False
    
    redis_healthy = True
    try:
        redis_client.ping()
    except:
        redis_healthy = False
    
    # === WORKER STATUS ===
    worker_count = 0
    queue_size = 0
    try:
        from celery import Celery
        celery_app = Celery('fiyatradari')
        celery_app.config_from_object({
            'broker_url': 'redis://redis:6379/0',
            'result_backend': 'redis://redis:6379/1',
        })
        inspect = celery_app.control.inspect(timeout=0.5)
        stats = inspect.stats() or {}
        worker_count = len(stats)
        
        # Queue size
        try:
            queue_size = redis_client.llen('celery') or 0
        except:
            pass
    except:
        pass
    
    # === HEALTH SCORE ===
    health_score = 100
    if not db_healthy:
        health_score -= 50
    if not redis_healthy:
        health_score -= 30
    if worker_count == 0:
        health_score -= 20
    
    health_status = 'healthy' if health_score >= 80 else 'degraded' if health_score >= 50 else 'critical'
    
    # === DATABASE STATS ===
    total_products = db.query(models.Product).filter(models.Product.is_active == True).count()
    active_deals = db.query(models.Deal).filter(models.Deal.is_active == True).count()
    
    # Tasks today - last 24 hours
    last_24h = datetime.utcnow() - timedelta(hours=24)
    tasks_today = db.query(models.WorkerLog).filter(
        models.WorkerLog.created_at >= last_24h
    ).count()
    
    # === RECENT ACTIVITY ===
    recent_logs = db.query(models.WorkerLog).order_by(
        desc(models.WorkerLog.created_at)
    ).limit(5).all()
    
    recent_activity = [
        {
            'type': log.job_type,
            'status': log.status,
            'time': log.created_at.isoformat() if log.created_at else None,
            'items': log.items_processed or 0
        }
        for log in recent_logs
    ]
    
    return {
        'health': {
            'status': health_status,
            'score': health_score,
            'database': db_healthy,
            'redis': redis_healthy,
            'workers': worker_count,
            'queue_size': queue_size
        },
        'stats': {
            'total_products': total_products,
            'active_deals': active_deals,
            'tasks_today': tasks_today,
            'worker_count': worker_count
        },
        'recent_activity': recent_activity,
        'timestamp': datetime.utcnow().isoformat()
    }


# ============================================================================
# CONTROL ACTIONS
# ============================================================================

@router.post("/control/pause")
async def pause_all_workers(current_user: models.User = Depends(get_current_user)):
    """Pause all automatic jobs"""
    try:
        # Create parent directory if not exists
        WORKER_CONTROL_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        if WORKER_CONTROL_FILE.exists():
            with open(WORKER_CONTROL_FILE, 'r') as f:
                state = json.load(f)
        else:
            state = {}
        
        state['scheduler_enabled'] = False
        state['paused_at'] = datetime.utcnow().isoformat()
        state['paused_by'] = current_user.username
        
        # Write to file
        with open(WORKER_CONTROL_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        
        # Also save to Redis for faster access
        redis_client.set('worker:control:scheduler_enabled', 'false', ex=86400)
        
        return {'success': True, 'message': 'All jobs paused', 'state': state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/control/resume")
async def resume_all_workers(current_user: models.User = Depends(get_current_user)):
    """Resume all automatic jobs"""
    try:
        # Create parent directory if not exists
        WORKER_CONTROL_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        if WORKER_CONTROL_FILE.exists():
            with open(WORKER_CONTROL_FILE, 'r') as f:
                state = json.load(f)
        else:
            state = {}
        
        state['scheduler_enabled'] = True
        state['resumed_at'] = datetime.utcnow().isoformat()
        state['resumed_by'] = current_user.username
        
        # Write to file
        with open(WORKER_CONTROL_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        
        # Also save to Redis for faster access
        redis_client.set('worker:control:scheduler_enabled', 'true', ex=86400)
        
        return {'success': True, 'message': 'All jobs resumed', 'state': state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/control/status")
async def get_control_status():
    """Get current control status"""
    try:
        if WORKER_CONTROL_FILE.exists():
            with open(WORKER_CONTROL_FILE, 'r') as f:
                return json.load(f)
        else:
            return {'scheduler_enabled': True, 'jobs': {}}
    except Exception as e:
        return {'scheduler_enabled': True, 'jobs': {}, 'error': str(e)}

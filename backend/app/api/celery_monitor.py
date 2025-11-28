"""
Celery task monitoring endpoints
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from datetime import datetime, timedelta

from app.api.auth import get_current_user
from app.db import models
from app.celery_app import celery_app

router = APIRouter()


@router.get("/celery/status")
async def celery_status(current_user: models.User = Depends(get_current_user)):
    """Celery worker ve scheduler durumu"""
    
    # Active workers
    inspect = celery_app.control.inspect()
    
    active_tasks = inspect.active()
    registered_tasks = inspect.registered()
    stats = inspect.stats()
    
    return {
        "workers_online": len(stats) if stats else 0,
        "active_tasks": active_tasks or {},
        "registered_tasks": registered_tasks or {},
        "stats": stats or {},
        "broker_url": "redis://redis:6379/0",
        "backend_url": "redis://redis:6379/0"
    }


@router.get("/celery/tasks")
async def celery_tasks(current_user: models.User = Depends(get_current_user)):
    """Kayıtlı task listesi"""
    
    inspect = celery_app.control.inspect()
    registered = inspect.registered()
    
    tasks = []
    if registered:
        for worker, task_list in registered.items():
            for task in task_list:
                if task not in [t["name"] for t in tasks]:
                    tasks.append({
                        "name": task,
                        "workers": [worker]
                    })
    
    return {
        "total_tasks": len(tasks),
        "tasks": tasks
    }


@router.get("/celery/scheduled")
async def celery_scheduled(current_user: models.User = Depends(get_current_user)):
    """Zamanlanmış task'lar (beat schedule)"""
    
    schedule = celery_app.conf.beat_schedule
    
    scheduled_tasks = []
    for name, config in schedule.items():
        task_info = {
            "name": name,
            "task": config["task"],
            "schedule": str(config["schedule"]),
            "options": config.get("options", {})
        }
        scheduled_tasks.append(task_info)
    
    return {
        "total_scheduled": len(scheduled_tasks),
        "tasks": scheduled_tasks
    }


@router.post("/celery/tasks/{task_name}/trigger")
async def trigger_task(
    task_name: str,
    current_user: models.User = Depends(get_current_user)
):
    """Manuel task tetikleme (debug için)"""
    
    # Task map
    task_map = {
        "check_categories": "app.tasks.check_categories_for_update",
        "update_statistics": "app.tasks.update_statistics",
        "cleanup_deals": "app.tasks.cleanup_old_deals",
        "check_deal_prices": "app.tasks.check_deal_prices"
    }
    
    if task_name not in task_map:
        return {
            "success": False,
            "error": f"Unknown task: {task_name}",
            "available_tasks": list(task_map.keys())
        }
    
    # Task'ı tetikle
    task = celery_app.send_task(task_map[task_name])
    
    return {
        "success": True,
        "task_name": task_name,
        "task_id": task.id,
        "status": "sent"
    }


@router.get("/celery/tasks/{task_id}/status")
async def task_status(
    task_id: str,
    current_user: models.User = Depends(get_current_user)
):
    """Task durumunu kontrol et"""
    
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": result.state,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None
    }
    
    if result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["error"] = str(result.info)
    
    return response


@router.get("/celery/recent-tasks")
async def recent_tasks(
    limit: int = 50,
    current_user: models.User = Depends(get_current_user)
):
    """
    Son çalışan task'ları getir (Redis'ten)
    Celery result backend kullanılarak task history
    """
    import redis
    import json
    from celery.result import AsyncResult
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo
    
    # Redis bağlantısı
    redis_client = redis.from_url("redis://redis:6379/0")
    
    # Celery task key'lerini bul
    pattern = "celery-task-meta-*"
    keys = redis_client.keys(pattern)
    
    # Istanbul timezone
    istanbul_tz = ZoneInfo('Europe/Istanbul')
    
    tasks = []
    for key in keys[:limit]:
        task_id = key.decode().replace("celery-task-meta-", "")
        result = AsyncResult(task_id, app=celery_app)
        
        # Redis'ten task metadata'yı direkt oku (daha detaylı bilgi için)
        meta_raw = redis_client.get(key)
        meta = json.loads(meta_raw) if meta_raw else {}
        
        # Timestamp'i ISO formatında al
        date_done = meta.get("date_done")
        if date_done:
            # UTC timestamp'i parse et ve Istanbul saatine çevir
            try:
                dt = datetime.fromisoformat(date_done.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                istanbul_time = dt.astimezone(istanbul_tz)
                timestamp = istanbul_time.isoformat()
            except:
                timestamp = date_done
        else:
            timestamp = datetime.now(istanbul_tz).isoformat()
        
        task_info = {
            "task_id": task_id,
            "status": result.state,
            "name": meta.get("name") or (result.name if hasattr(result, 'name') else None),
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "date_done": timestamp,  # ISO format timestamp (Istanbul timezone)
            "timestamp": timestamp,
        }
        
        # Result varsa ekle
        if result.ready():
            if result.successful():
                task_info["result"] = result.result
            else:
                task_info["error"] = str(result.info)
        
        tasks.append(task_info)
    
    # Timestamp'e göre sırala (en yeni önce)
    tasks.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "total": len(tasks),
        "tasks": tasks[:limit]
    }


@router.get("/celery/failed-tasks")
async def failed_tasks(
    current_user: models.User = Depends(get_current_user)
):
    """Başarısız task'ları getir"""
    import redis
    from celery.result import AsyncResult
    
    redis_client = redis.from_url("redis://redis:6379/0")
    pattern = "celery-task-meta-*"
    keys = redis_client.keys(pattern)
    
    failed = []
    for key in keys:
        task_id = key.decode().replace("celery-task-meta-", "")
        result = AsyncResult(task_id, app=celery_app)
        
        if result.state == "FAILURE":
            failed.append({
                "task_id": task_id,
                "status": result.state,
                "name": result.name if hasattr(result, 'name') else None,
                "error": str(result.info),
                "traceback": result.traceback if hasattr(result, 'traceback') else None
            })
    
    return {
        "total": len(failed),
        "tasks": failed
    }

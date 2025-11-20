from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
import redis
from datetime import datetime, timedelta
import json

router = APIRouter()

# Redis connection for Celery
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

# Cache for worker stats (to avoid slow Celery inspect calls)
_worker_stats_cache = None
_worker_stats_cache_time = None
CACHE_TTL_SECONDS = 10  # Cache for 10 seconds (reduced inspect frequency)


def get_celery_inspect():
    """Get Celery inspect instance with timeout"""
    from celery import Celery
    
    celery_app = Celery('fiyatradari')
    celery_app.config_from_object({
        'broker_url': 'redis://redis:6379/0',
        'result_backend': 'redis://redis:6379/1',
        'broker_connection_timeout': 3.0,  # 3 second timeout
        'broker_connection_max_retries': 1,
    })
    
    return celery_app.control.inspect(timeout=2.0)  # 2 second timeout for inspect


@router.get("/workers/quick-stats")
async def get_workers_quick_stats():
    """Get quick worker statistics (lightweight, fast, cached)"""
    global _worker_stats_cache, _worker_stats_cache_time
    
    # Check cache
    now = datetime.utcnow()
    if (_worker_stats_cache is not None and 
        _worker_stats_cache_time is not None and 
        (now - _worker_stats_cache_time).total_seconds() < CACHE_TTL_SECONDS):
        # Return cached data
        return _worker_stats_cache
    
    try:
        inspect = get_celery_inspect()
        
        # Just get stats (faster than getting everything)
        stats = inspect.stats() or {}
        active = inspect.active() or {}
        
        total_workers = len(stats)
        total_active_tasks = sum(len(tasks) for tasks in active.values())
        
        workers = []
        for worker_name in stats.keys():
            worker_active_tasks = active.get(worker_name, [])
            workers.append({
                'name': worker_name,
                'status': 'online',
                'active_tasks': len(worker_active_tasks)
            })
        
        result = {
            'total_workers': total_workers,
            'online_workers': total_workers,
            'total_active_tasks': total_active_tasks,
            'workers': workers,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Cache the result
        _worker_stats_cache = result
        _worker_stats_cache_time = now
        
        return result
        
    except Exception as e:
        # If error, return cached data if available
        if _worker_stats_cache is not None:
            return _worker_stats_cache
        raise HTTPException(status_code=500, detail=f"Error fetching quick stats: {str(e)}")


@router.get("/workers/stats")
async def get_workers_stats():
    """Get detailed statistics for all workers (slower, comprehensive)"""
    try:
        inspect = get_celery_inspect()
        
        # Get all worker info
        active = inspect.active() or {}
        stats = inspect.stats() or {}
        registered = inspect.registered() or {}
        active_queues = inspect.active_queues() or {}
        
        workers = []
        for worker_name in stats.keys():
            worker_stats = stats.get(worker_name, {})
            worker_active_tasks = active.get(worker_name, [])
            worker_registered = registered.get(worker_name, [])
            worker_queues = active_queues.get(worker_name, [])
            
            workers.append({
                'name': worker_name,
                'status': 'online',
                'active_tasks': len(worker_active_tasks),
                'tasks': worker_active_tasks,
                'registered_tasks': len(worker_registered),
                'queues': [q['name'] for q in worker_queues],
                'pool': worker_stats.get('pool', {}),
                'total_tasks': worker_stats.get('total', {}),
                'rusage': worker_stats.get('rusage', {})
            })
        
        return {
            'total_workers': len(workers),
            'online_workers': len(workers),
            'workers': workers,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching worker stats: {str(e)}")


@router.get("/tasks/stats")
async def get_tasks_stats():
    """Get task statistics"""
    try:
        inspect = get_celery_inspect()
        
        # Get scheduled, active, and reserved tasks
        scheduled = inspect.scheduled() or {}
        active = inspect.active() or {}
        reserved = inspect.reserved() or {}
        
        total_scheduled = sum(len(tasks) for tasks in scheduled.values())
        total_active = sum(len(tasks) for tasks in active.values())
        total_reserved = sum(len(tasks) for tasks in reserved.values())
        
        # Get queue lengths from Redis
        queue_lengths = {}
        for key in redis_client.keys('celery'):
            if key:
                length = redis_client.llen(key)
                queue_lengths[key] = length
        
        return {
            'scheduled': total_scheduled,
            'active': total_active,
            'reserved': total_reserved,
            'queues': queue_lengths,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching task stats: {str(e)}")


@router.get("/workers/active-tasks")
async def get_active_tasks():
    """Get all currently active tasks across workers"""
    try:
        inspect = get_celery_inspect()
        active = inspect.active() or {}
        
        all_tasks = []
        for worker_name, tasks in active.items():
            for task in tasks:
                all_tasks.append({
                    'worker': worker_name,
                    'task_id': task.get('id'),
                    'task_name': task.get('name'),
                    'args': task.get('args'),
                    'kwargs': task.get('kwargs'),
                    'time_start': task.get('time_start'),
                    'acknowledged': task.get('acknowledged', False),
                    'delivery_info': task.get('delivery_info', {})
                })
        
        return {
            'total': len(all_tasks),
            'tasks': all_tasks,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching active tasks: {str(e)}")


@router.get("/workers/ping")
async def ping_workers():
    """Ping all workers to check availability"""
    try:
        from celery import Celery
        
        celery_app = Celery('fiyatradari')
        celery_app.config_from_object({
            'broker_url': 'redis://redis:6379/0',
            'result_backend': 'redis://redis:6379/1',
        })
        
        # Ping with timeout
        pong = celery_app.control.ping(timeout=1.0)
        
        workers = []
        for response in pong:
            for worker_name, info in response.items():
                workers.append({
                    'name': worker_name,
                    'status': 'online',
                    'response_time_ms': info.get('ok', 'pong')
                })
        
        return {
            'total': len(workers),
            'workers': workers,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error pinging workers: {str(e)}")


@router.get("/system/health")
async def get_system_health():
    """Get overall system health"""
    try:
        inspect = get_celery_inspect()
        
        # Get stats
        stats = inspect.stats() or {}
        active = inspect.active() or {}
        
        total_workers = len(stats)
        total_active_tasks = sum(len(tasks) for tasks in active.values())
        
        # Redis health
        redis_info = redis_client.info()
        redis_memory = redis_info.get('used_memory_human', 'N/A')
        redis_connected_clients = redis_info.get('connected_clients', 0)
        
        # Calculate health score
        health_score = 100
        if total_workers < 10:
            health_score -= 20
        if total_active_tasks > 100:
            health_score -= 10
        
        status = 'healthy' if health_score >= 80 else 'degraded' if health_score >= 60 else 'unhealthy'
        
        return {
            'status': status,
            'health_score': health_score,
            'workers': {
                'total': total_workers,
                'online': total_workers,
                'offline': 0
            },
            'tasks': {
                'active': total_active_tasks
            },
            'redis': {
                'memory_used': redis_memory,
                'connected_clients': redis_connected_clients
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'health_score': 0,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }


@router.post("/workers/control/shutdown/{worker_name}")
async def shutdown_worker(worker_name: str):
    """Shutdown a specific worker"""
    try:
        from celery import Celery
        
        celery_app = Celery('fiyatradari')
        celery_app.config_from_object({
            'broker_url': 'redis://redis:6379/0',
            'result_backend': 'redis://redis:6379/1',
        })
        
        celery_app.control.shutdown(destination=[worker_name])
        
        return {
            'status': 'success',
            'message': f'Shutdown signal sent to {worker_name}',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error shutting down worker: {str(e)}")


@router.post("/workers/control/pool-restart/{worker_name}")
async def restart_worker_pool(worker_name: str):
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
            'message': f'Pool restart signal sent to {worker_name}',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restarting worker pool: {str(e)}")

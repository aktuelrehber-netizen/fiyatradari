"""
Worker Control System
Allows pausing/resuming scheduler and enabling/disabling individual jobs
Uses Redis for cross-container communication
"""
import json
import redis
from typing import Dict
from loguru import logger

# Redis connection
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)


class WorkerControl:
    """Worker control state manager - uses Redis for real-time sync"""
    
    def __init__(self):
        pass
    
    def _load_state(self) -> Dict:
        """Load control state from Redis"""
        try:
            state_json = redis_client.get('worker:control:state')
            if state_json:
                return json.loads(state_json)
        except Exception as e:
            logger.error(f"Error loading control state from Redis: {e}")
        
        # Default state
        return {
            "scheduler_enabled": True,
            "jobs": {
                "fetch_products": {"enabled": True},
                "check_prices": {"enabled": True},
                "send_telegram": {"enabled": True},
                "update_missing_ratings": {"enabled": True}
            }
        }
    
    def is_scheduler_enabled(self) -> bool:
        """Check if scheduler is enabled - reads from Redis in real-time"""
        try:
            # Check Redis first (real-time)
            enabled = redis_client.get('worker:control:scheduler_enabled')
            if enabled is not None:
                return enabled.lower() == 'true'
        except Exception as e:
            logger.error(f"Error checking scheduler status from Redis: {e}")
        
        # Fallback to default
        return True
    
    def is_job_enabled(self, job_type: str) -> bool:
        """Check if specific job is enabled - reads from Redis"""
        try:
            state = self._load_state()
            return state.get("jobs", {}).get(job_type, {}).get("enabled", True)
        except Exception as e:
            logger.error(f"Error checking job {job_type} status: {e}")
            return True  # Default to enabled on error
    
    def should_run_job(self, job_type: str) -> bool:
        """Check if job should run (both scheduler and job must be enabled)"""
        return self.is_scheduler_enabled() and self.is_job_enabled(job_type)
    
    def get_status(self) -> Dict:
        """Get current control status"""
        state = self._load_state()
        return {
            "scheduler_enabled": self.is_scheduler_enabled(),
            "jobs": {
                job_type: {
                    "enabled": job_info.get("enabled", True),
                    "will_run": self.should_run_job(job_type)
                }
                for job_type, job_info in state.get("jobs", {}).items()
            }
        }


# Global instance
worker_control = WorkerControl()

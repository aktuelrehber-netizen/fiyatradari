"""
Worker Control System
Allows pausing/resuming scheduler and enabling/disabling individual jobs
"""
import json
import os
from pathlib import Path
from typing import Dict, Optional
from loguru import logger

CONTROL_FILE = Path(__file__).parent / "worker_control.json"


class WorkerControl:
    """Worker control state manager"""
    
    def __init__(self):
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load control state from file"""
        if CONTROL_FILE.exists():
            try:
                with open(CONTROL_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading control state: {e}")
        
        # Default state
        return {
            "scheduler_enabled": True,
            "jobs": {
                "fetch_products": {"enabled": True},
                "check_prices": {"enabled": True},
                "send_telegram": {"enabled": True}
            }
        }
    
    def _save_state(self):
        """Save control state to file"""
        try:
            with open(CONTROL_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.info("Control state saved")
        except Exception as e:
            logger.error(f"Error saving control state: {e}")
    
    def is_scheduler_enabled(self) -> bool:
        """Check if scheduler is enabled"""
        return self.state.get("scheduler_enabled", True)
    
    def is_job_enabled(self, job_type: str) -> bool:
        """Check if specific job is enabled"""
        return self.state.get("jobs", {}).get(job_type, {}).get("enabled", True)
    
    def should_run_job(self, job_type: str) -> bool:
        """Check if job should run (both scheduler and job must be enabled)"""
        return self.is_scheduler_enabled() and self.is_job_enabled(job_type)
    
    def pause_scheduler(self):
        """Pause scheduler (all automatic jobs)"""
        self.state["scheduler_enabled"] = False
        self._save_state()
        logger.warning("⏸️  Scheduler PAUSED")
    
    def resume_scheduler(self):
        """Resume scheduler"""
        self.state["scheduler_enabled"] = True
        self._save_state()
        logger.success("▶️  Scheduler RESUMED")
    
    def enable_job(self, job_type: str):
        """Enable specific job"""
        if job_type not in self.state["jobs"]:
            self.state["jobs"][job_type] = {}
        self.state["jobs"][job_type]["enabled"] = True
        self._save_state()
        logger.info(f"✅ Job '{job_type}' ENABLED")
    
    def disable_job(self, job_type: str):
        """Disable specific job"""
        if job_type not in self.state["jobs"]:
            self.state["jobs"][job_type] = {}
        self.state["jobs"][job_type]["enabled"] = False
        self._save_state()
        logger.warning(f"❌ Job '{job_type}' DISABLED")
    
    def get_status(self) -> Dict:
        """Get current control status"""
        return {
            "scheduler_enabled": self.is_scheduler_enabled(),
            "jobs": {
                job_type: {
                    "enabled": job_info.get("enabled", True),
                    "will_run": self.should_run_job(job_type)
                }
                for job_type, job_info in self.state.get("jobs", {}).items()
            }
        }


# Global instance
worker_control = WorkerControl()

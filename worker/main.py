"""
Fiyat Radarı Worker
Background job runner for product fetching, price checking, and notifications
"""
import time
import schedule
from datetime import datetime
from loguru import logger
import sys

from config import config
from database import get_db, WorkerLog
from jobs.amazon_fetcher import AmazonProductFetcher
from jobs.price_checker import PriceChecker
from jobs.telegram_sender import TelegramSender


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=config.LOG_LEVEL
)


class WorkerManager:
    """Manages and schedules worker jobs"""
    
    def __init__(self):
        self.amazon_fetcher = AmazonProductFetcher()
        self.price_checker = PriceChecker()
        self.telegram_sender = TelegramSender()
    
    def run_job(self, job_name, job_type, job_func):
        """Run a job and log results"""
        logger.info(f"Starting job: {job_name}")
        
        # Create log entry
        with get_db() as db:
            log = WorkerLog(
                job_name=job_name,
                job_type=job_type,
                status="running",
                started_at=datetime.utcnow()
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            log_id = log.id
        
        try:
            # Run the job
            start_time = time.time()
            result = job_func()
            duration = int(time.time() - start_time)
            
            # Update log with success
            with get_db() as db:
                log = db.query(WorkerLog).filter(WorkerLog.id == log_id).first()
                if log:
                    log.status = result.get("status", "completed")
                    log.completed_at = datetime.utcnow()
                    log.duration_seconds = duration
                    log.items_processed = result.get("items_processed", 0)
                    log.items_created = result.get("items_created", 0)
                    log.items_updated = result.get("items_updated", 0)
                    log.items_failed = result.get("items_failed", 0)
                    log.metadata = result
                    db.commit()
            
            logger.success(f"Job completed: {job_name} (took {duration}s)")
            
        except Exception as e:
            duration = int(time.time() - start_time) if 'start_time' in locals() else 0
            
            # Update log with error
            with get_db() as db:
                log = db.query(WorkerLog).filter(WorkerLog.id == log_id).first()
                if log:
                    log.status = "failed"
                    log.completed_at = datetime.utcnow()
                    log.duration_seconds = duration
                    log.error_message = str(e)
                    db.commit()
            
            logger.error(f"Job failed: {job_name} - {e}")
    
    def fetch_products(self):
        """Fetch products from Amazon"""
        self.run_job("fetch_products", "amazon_fetch", self.amazon_fetcher.run)
    
    def check_prices(self):
        """Check product prices"""
        self.run_job("check_prices", "price_check", self.price_checker.run)
    
    def send_telegram_notifications(self):
        """Send Telegram notifications"""
        self.run_job("send_telegram", "telegram_send", self.telegram_sender.run)
    
    def run_all_jobs(self):
        """Run all jobs in sequence"""
        logger.info("=" * 60)
        logger.info("Running all jobs...")
        logger.info("=" * 60)
        
        # 1. Check prices first (for existing products)
        self.check_prices()
        
        # 2. Send Telegram notifications
        self.send_telegram_notifications()
        
        # 3. Fetch new products (optional, can be less frequent)
        # Uncomment when Amazon API is configured
        # self.fetch_products()
        
        logger.info("=" * 60)
        logger.info("All jobs completed")
        logger.info("=" * 60)
    
    def start(self):
        """Start the worker with scheduled jobs"""
        logger.info("🚀 Starting Fiyat Radarı Worker...")
        logger.info(f"Worker interval: {config.WORKER_INTERVAL_MINUTES} minutes")
        logger.info(f"Price check interval: {config.PRICE_CHECK_INTERVAL_HOURS} hours")
        logger.info(f"Deal threshold: {config.DEAL_THRESHOLD_PERCENTAGE}%")
        logger.info("=" * 60)
        
        # Schedule jobs
        # Run all jobs every hour
        schedule.every(config.WORKER_INTERVAL_MINUTES).minutes.do(self.run_all_jobs)
        
        # Run immediately on startup
        self.run_all_jobs()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    """Main entry point"""
    try:
        manager = WorkerManager()
        manager.start()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Worker stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Worker crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Production Worker Manager
Orchestrates all background jobs with intelligent scheduling
"""
import time
import schedule
from datetime import datetime
from loguru import logger
import sys

from config import config
from database import get_db, WorkerLog
from jobs.amazon_fetcher_v2 import AmazonProductFetcher
from jobs.price_checker_v2 import PriceChecker
from jobs.telegram_sender_v2 import TelegramSender
from worker_control import worker_control


# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=config.LOG_LEVEL
)
logger.add(
    "logs/worker_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO"
)


class WorkerManager:
    """
    Production worker manager with intelligent job scheduling
    
    Job Schedule:
    - Price Check: Every 6 hours (configurable)
    - Deal Detection: Automatic (part of price check)
    - Telegram Send: Every hour
    - Product Fetch: Every 24 hours (less frequent)
    """
    
    def __init__(self):
        self.amazon_fetcher = AmazonProductFetcher()
        self.price_checker = PriceChecker()
        self.telegram_sender = TelegramSender()
    
    def run_job(self, job_name: str, job_type: str, job_func):
        """Run a job and log results"""
        # Check if job should run
        if not worker_control.should_run_job(job_type):
            logger.warning(f"⏭️  Skipping job '{job_name}' - disabled or scheduler paused")
            return {"status": "skipped", "reason": "disabled"}
        
        logger.info("=" * 80)
        logger.info(f"Starting job: {job_name}")
        logger.info("=" * 80)
        
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
        
        start_time = time.time()
        
        try:
            # Run the job
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
                    log.job_metadata = result
                    db.commit()
            
            logger.success(f"✅ Job completed: {job_name} (took {duration}s)")
            logger.info("=" * 80)
            return result
            
        except Exception as e:
            duration = int(time.time() - start_time)
            
            # Update log with error
            with get_db() as db:
                log = db.query(WorkerLog).filter(WorkerLog.id == log_id).first()
                if log:
                    log.status = "failed"
                    log.completed_at = datetime.utcnow()
                    log.duration_seconds = duration
                    log.error_message = str(e)
                    log.error_trace = str(e.__traceback__) if hasattr(e, '__traceback__') else None
                    db.commit()
            
            logger.error(f"❌ Job failed: {job_name} - {e}")
            logger.info("=" * 80)
            return {"status": "failed", "error": str(e)}
    
    def fetch_products(self):
        """Fetch new products from Amazon"""
        return self.run_job("fetch_products", "amazon_fetch", self.amazon_fetcher.run)
    
    def check_prices(self):
        """Check product prices and detect deals"""
        return self.run_job("check_prices", "price_check", self.price_checker.run)
    
    def send_telegram_notifications(self):
        """Send Telegram notifications for new deals"""
        return self.run_job("send_telegram", "telegram_send", self.telegram_sender.run)
    
    def run_hourly_jobs(self):
        """Jobs that run every hour"""
        logger.info("\n" + "🔄 " * 40)
        logger.info("Running hourly jobs...")
        logger.info("🔄 " * 40 + "\n")
        
        # Send Telegram notifications (quick)
        self.send_telegram_notifications()
    
    def run_price_check_jobs(self):
        """Jobs that run every N hours (default: 6h)"""
        logger.info("\n" + "💰 " * 40)
        logger.info("Running price check jobs...")
        logger.info("💰 " * 40 + "\n")
        
        # Check prices (auto-creates deals)
        self.check_prices()
        
        # Send new deals immediately
        self.send_telegram_notifications()
    
    def run_daily_jobs(self):
        """Run daily jobs - product fetching"""
        logger.info("\n📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦")
        logger.info("Running daily jobs...")
        logger.info("📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦 📦\n")
        
        self.run_job("Fetch Products from Amazon", "amazon_fetch", self.amazon_fetcher.run)
    
    def check_and_run_pending_jobs(self):
        """Check for pending manual jobs and run them"""
        from database import get_db
        
        with get_db() as db:
            # Find pending jobs
            pending_jobs = db.query(WorkerLog).filter(
                WorkerLog.status == "pending"
            ).order_by(WorkerLog.created_at).all()
            
            for job_log in pending_jobs:
                # Mark as running
                job_log.status = "running"
                job_log.started_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"🎯 Running manual job: {job_log.job_name} (type: {job_log.job_type})")
                
                # Map job type to function
                job_func = None
                job_name = job_log.job_name
                
                if job_log.job_type == "fetch_products":
                    job_func = self.amazon_fetcher.run
                    job_name = "Fetch Products from Amazon (Manual)"
                elif job_log.job_type == "check_prices":
                    job_func = self.price_checker.run
                    job_name = "Check Prices (Manual)"
                elif job_log.job_type == "send_telegram":
                    job_func = self.telegram_sender.run
                    job_name = "Send Telegram Notifications (Manual)"
                
                if job_func:
                    try:
                        result = job_func()
                        
                        # Update log with result
                        duration = (datetime.utcnow() - job_log.started_at).total_seconds()
                        job_log.status = result.get("status", "completed")
                        job_log.completed_at = datetime.utcnow()
                        job_log.duration_seconds = int(duration)
                        job_log.items_processed = result.get("items_processed", 0)
                        job_log.items_created = result.get("items_created", 0)
                        job_log.items_updated = result.get("items_updated", 0)
                        job_log.items_failed = result.get("items_failed", 0)
                        db.commit()
                        
                        logger.success(f"✅ Manual job completed: {job_name}")
                    except Exception as e:
                        job_log.status = "failed"
                        job_log.completed_at = datetime.utcnow()
                        job_log.error_message = str(e)
                        db.commit()
                        logger.error(f"❌ Manual job failed: {job_name} - {e}")
    
    def start(self):
        """Start the worker with intelligent scheduling"""
        logger.info("\n")
        logger.info("🚀 " * 40)
        logger.info("🚀  STARTING FIYAT RADARI WORKER  🚀")
        logger.info("🚀 " * 40)
        logger.info(f"\n📋 Configuration:")
        logger.info(f"   Price check interval: {config.PRICE_CHECK_INTERVAL_HOURS} hours")
        logger.info(f"   Deal threshold: {config.DEAL_THRESHOLD_PERCENTAGE}%")
        logger.info(f"   Worker interval: {config.WORKER_INTERVAL_MINUTES} minutes")
        logger.info(f"   Log level: {config.LOG_LEVEL}")
        logger.info("\n📅 Schedule:")
        logger.info(f"   Hourly: Telegram notifications")
        logger.info(f"   Every {config.PRICE_CHECK_INTERVAL_HOURS}h: Price checks & deal detection")
        logger.info(f"   Daily: Product fetching")
        logger.info("\n" + "=" * 80 + "\n")
        
        # Schedule jobs
        # Hourly: Telegram sender
        schedule.every().hour.do(self.run_hourly_jobs)
        
        # Every N hours: Price checker
        schedule.every(config.PRICE_CHECK_INTERVAL_HOURS).hours.do(self.run_price_check_jobs)
        
        # Daily: Product fetcher
        schedule.every().day.at("03:00").do(self.run_daily_jobs)  # 3 AM
        
        # Run immediately on startup (price check + telegram)
        logger.info("🎯 Running initial jobs...")
        self.run_price_check_jobs()
        
        # Keep running
        logger.info("\n✅ Worker is now running. Press Ctrl+C to stop.\n")
        
        while True:
            try:
                # Check for pending manual jobs
                self.check_and_run_pending_jobs()
                
                # Run scheduled jobs
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds for manual jobs
            except KeyboardInterrupt:
                logger.info("\n⚠️  Worker stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)


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
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Production Telegram Sender
Professional deal notifications with formatting and error handling
"""
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger
import asyncio

try:
    from telegram import Bot, ParseMode
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot not installed")

from database import get_db, Deal
from config import config


class TelegramSender:
    """
    Professional Telegram notification sender
    
    Features:
    - Beautiful message formatting
    - Image support
    - Affiliate link integration
    - Error handling & retry
    - Rate limiting
    """
    
    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.channel_id = config.TELEGRAM_CHANNEL_ID
        self.bot = None
        
        if TELEGRAM_AVAILABLE and self.bot_token:
            try:
                self.bot = Bot(token=self.bot_token)
                self.enabled = True
                logger.info("Telegram bot initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                self.enabled = False
        else:
            self.enabled = False
            logger.warning("Telegram not configured")
    
    def run(self) -> Dict:
        """Main job execution"""
        logger.info("=" * 80)
        logger.info("Starting Telegram Sender Job")
        logger.info("=" * 80)
        
        if not self.enabled:
            logger.warning("Telegram not configured")
            return {
                "status": "skipped",
                "message": "Telegram not configured",
                "items_processed": 0,
                "items_sent": 0,
                "items_failed": 0
            }
        
        stats = {
            "items_processed": 0,
            "items_sent": 0,
            "items_failed": 0
        }
        
        with get_db() as db:
            # Get published deals that haven't been sent to Telegram
            deals = db.query(Deal).filter(
                Deal.is_published == True,
                Deal.is_active == True,
                Deal.telegram_sent == False
            ).order_by(Deal.discount_percentage.desc()).limit(50).all()
            
            logger.info(f"Found {len(deals)} deals to send")
            
            if not deals:
                logger.info("No deals to send")
                return {"status": "completed", **stats}
            
            # Send each deal
            for deal in deals:
                stats["items_processed"] += 1
                
                try:
                    success = self._send_deal(deal, db)
                    if success:
                        stats["items_sent"] += 1
                    else:
                        stats["items_failed"] += 1
                    
                    # Small delay between messages
                    import time
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error sending deal {deal.id}: {e}")
                    stats["items_failed"] += 1
                    continue
            
            db.commit()
        
        logger.info("=" * 80)
        logger.info("Telegram Sender Job Completed")
        logger.info(f"Processed: {stats['items_processed']}")
        logger.info(f"Sent: {stats['items_sent']}")
        logger.info(f"Failed: {stats['items_failed']}")
        logger.info("=" * 80)
        
        return {"status": "completed", **stats}
    
    def _send_deal(self, deal: Deal, db) -> bool:
        """Send a single deal to Telegram"""
        try:
            # Build message
            message = self._format_deal_message(deal)
            
            # Get product image
            image_url = deal.product.image_url if deal.product else None
            
            # Send message
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                if image_url:
                    # Send with photo
                    result = loop.run_until_complete(
                        self.bot.send_photo(
                            chat_id=self.channel_id,
                            photo=image_url,
                            caption=message,
                            parse_mode='HTML'
                        )
                    )
                else:
                    # Send text only
                    result = loop.run_until_complete(
                        self.bot.send_message(
                            chat_id=self.channel_id,
                            text=message,
                            parse_mode='HTML',
                            disable_web_page_preview=False
                        )
                    )
                
                # Mark as sent
                deal.telegram_sent = True
                deal.telegram_message_id = str(result.message_id)
                deal.telegram_sent_at = datetime.utcnow()
                
                logger.success(f"Sent deal to Telegram: {deal.title[:50]}")
                return True
                
            finally:
                loop.close()
            
        except TelegramError as e:
            logger.error(f"Telegram error sending deal {deal.id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending deal {deal.id}: {e}")
            return False
    
    def _format_deal_message(self, deal: Deal) -> str:
        """
        Format deal message for Telegram using customizable template
        
        Variables available:
        - {title}: Product title
        - {brand_line}: Brand line (auto-generated)
        - {discount_percentage}: Discount %
        - {original_price}: Original price
        - {deal_price}: Deal price
        - {discount_amount}: Discount amount
        - {rating_line}: Rating stars (auto-generated)
        - {product_url}: Affiliate link
        """
        from database import SystemSetting
        
        # Get template from database
        with get_db() as db:
            template_setting = db.query(SystemSetting).filter(
                SystemSetting.key == 'telegram_message_template'
            ).first()
            
            if template_setting and template_setting.value:
                template = template_setting.value
            else:
                # Fallback to default template
                template = self._get_default_template()
        
        # Prepare variables
        discount_pct = int(deal.discount_percentage)
        
        # Brand line
        brand_line = ""
        if deal.product and deal.product.brand:
            brand_line = f"🏷 {deal.product.brand}\n\n"
        
        # Rating line
        rating_line = ""
        if deal.product and deal.product.rating:
            stars = "⭐" * int(deal.product.rating)
            rating_line = f"{stars} {deal.product.rating:.1f}/5"
            if deal.product.review_count:
                rating_line += f" ({deal.product.review_count} değerlendirme)"
            rating_line += "\n\n"
        
        # Product URL with affiliate tag
        product_url = ""
        if deal.product and deal.product.detail_page_url:
            url = deal.product.detail_page_url
            if config.AMAZON_PARTNER_TAG and 'tag=' not in url:
                separator = '&' if '?' in url else '?'
                url = f"{url}{separator}tag={config.AMAZON_PARTNER_TAG}"
            product_url = url
        
        # Replace variables in template
        message = template.format(
            title=deal.title[:200],
            brand_line=brand_line,
            discount_percentage=discount_pct,
            original_price=f"{float(deal.original_price):.2f}",
            deal_price=f"{float(deal.deal_price):.2f}",
            discount_amount=f"{float(deal.discount_amount):.2f}",
            rating_line=rating_line,
            product_url=product_url
        )
        
        return message
    
    def _get_default_template(self) -> str:
        """Get default template if database template not available"""
        return '''🔥 <b>%{discount_percentage}% İNDİRİM</b>

<b>{title}</b>

{brand_line}<s>₺{original_price}</s> → <b>₺{deal_price}</b>
💰 {discount_amount}₺ Tasarruf

{rating_line}🛒 <a href="{product_url}">Satın Al</a>

📱 @FirsatRadari'''

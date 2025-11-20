"""
Telegram Sender Job
Sends deal notifications to Telegram channel
"""
from datetime import datetime
from loguru import logger
import asyncio

from database import get_db, Deal, Product
from config import config


class TelegramSender:
    """Send deal notifications to Telegram"""
    
    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.channel_id = config.TELEGRAM_CHANNEL_ID
        self.enabled = bool(self.bot_token and self.channel_id)
    
    def run(self):
        """Main job execution"""
        logger.info("Starting Telegram sender job...")
        
        if not self.bot_token or not self.channel_id:
            logger.warning("Telegram credentials not configured, skipping...")
            return {
                "status": "skipped",
                "message": "Telegram credentials not configured"
            }
        
        with get_db() as db:
            # Get published deals that haven't been sent to Telegram
            deals = db.query(Deal).filter(
                Deal.is_active == True,
                Deal.is_published == True,
                Deal.telegram_sent == False
            ).limit(10).all()  # Limit to avoid rate limiting
            
            logger.info(f"Found {len(deals)} deals to send")
            
            total_sent = 0
            total_failed = 0
            
            for deal in deals:
                try:
                    # Send to Telegram
                    message_id = asyncio.run(self._send_deal_to_telegram(deal, db))
                    
                    if message_id:
                        deal.telegram_sent = True
                        deal.telegram_message_id = str(message_id)
                        deal.telegram_sent_at = datetime.utcnow()
                        total_sent += 1
                        logger.info(f"Sent deal to Telegram: {deal.title}")
                    else:
                        total_failed += 1
                    
                except Exception as e:
                    logger.error(f"Error sending deal {deal.id} to Telegram: {e}")
                    total_failed += 1
                    continue
            
            db.commit()
            
            logger.info(f"Telegram sender completed: {total_sent} sent, {total_failed} failed")
            
            return {
                "status": "completed",
                "items_sent": total_sent,
                "items_failed": total_failed
            }
    
    async def _send_deal_to_telegram(self, deal, db):
        """Send a single deal to Telegram"""
        try:
            from telegram import Bot
            from telegram.constants import ParseMode
            
            bot = Bot(token=self.bot_token)
            
            # Get product details
            product = db.query(Product).filter(Product.id == deal.product_id).first()
            
            if not product:
                logger.error(f"Product not found for deal {deal.id}")
                return None
            
            # Format message
            message = self._format_deal_message(deal, product)
            
            # Send message
            if product.image_url:
                # Send with photo
                result = await bot.send_photo(
                    chat_id=self.channel_id,
                    photo=product.image_url,
                    caption=message,
                    parse_mode=ParseMode.HTML
                )
            else:
                # Send text only
                result = await bot.send_message(
                    chat_id=self.channel_id,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=False
                )
            
            return result.message_id
            
        except Exception as e:
            logger.error(f"Error in _send_deal_to_telegram: {e}")
            return None
    
    def _format_deal_message(self, deal, product):
        """Format deal message for Telegram"""
        message = f"🔥 <b>{deal.title}</b>\n\n"
        
        if product.brand:
            message += f"🏷 Marka: {product.brand}\n"
        
        message += f"💰 Fiyat: <b>{deal.deal_price} {deal.currency}</b>\n"
        
        if deal.original_price:
            message += f"🔖 Liste Fiyatı: <s>{deal.original_price} {deal.currency}</s>\n"
            message += f"📉 İndirim: <b>%{deal.discount_percentage:.0f}</b> ({deal.discount_amount} {deal.currency})\n"
        
        if product.rating:
            stars = "⭐" * int(product.rating)
            message += f"\n{stars} {product.rating}/5"
            if product.review_count:
                message += f" ({product.review_count} değerlendirme)"
        
        message += f"\n\n"
        
        if product.detail_page_url:
            message += f"🛒 <a href='{product.detail_page_url}'>Amazon'da Görüntüle</a>\n"
        
        message += f"\n⏰ {datetime.utcnow().strftime('%d.%m.%Y %H:%M')}"
        
        return message
    
    def _send_deal(self, deal, db):
        """
        Send a single deal to Telegram (sync wrapper for celery tasks)
        Returns True if sent successfully, False otherwise
        """
        try:
            message_id = asyncio.run(self._send_deal_to_telegram(deal, db))
            return bool(message_id)
        except Exception as e:
            logger.error(f"Error in _send_deal: {e}")
            return False

"""
Telegram Bot Service
Sends deal notifications to Telegram channel with inline buttons
"""
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.db import models
from app.core.config import settings

import logging
logger = logging.getLogger(__name__)


def format_turkish_price(price: float) -> str:
    """Format price in Turkish format (1.999,90)"""
    if price is None:
        return "0,00"
    
    # Format with 2 decimals
    formatted = f"{price:,.2f}"
    
    # Replace comma with temp, dot with comma, temp with dot
    # English: 1,999.90 -> Turkish: 1.999,90
    formatted = formatted.replace(',', 'TEMP')
    formatted = formatted.replace('.', ',')
    formatted = formatted.replace('TEMP', '.')
    
    return formatted


def get_telegram_settings(db: Session) -> Dict[str, str]:
    """Get Telegram settings from database"""
    telegram_settings = db.query(models.SystemSetting).filter(
        models.SystemSetting.group == 'telegram'
    ).all()
    
    settings_dict = {}
    for setting in telegram_settings:
        settings_dict[setting.key] = setting.value
    
    return settings_dict


def format_deal_message(deal: models.Deal, template: str) -> str:
    """Format deal message using template"""
    
    # Get product info
    product = deal.product
    discount_pct = int(deal.discount_percentage)
    
    # Brand line
    brand_line = ""
    if product and product.brand:
        brand_line = f"🏷 {product.brand}\n\n"
    
    # Rating line
    rating_line = ""
    if product and product.rating:
        stars = "⭐" * int(product.rating)
        rating_line = f"{stars} {product.rating:.1f}/5"
        if product.review_count:
            rating_line += f" ({product.review_count} değerlendirme)"
        rating_line += "\n\n"
    
    # Cheapest badge
    cheapest_badge = ""
    if deal.is_cheapest_6months:
        cheapest_badge = "🏆 6 AYIN EN UCUZU\n\n"
    elif deal.is_cheapest_3months:
        cheapest_badge = "⭐ 3 AYIN EN UCUZU\n\n"
    elif deal.is_cheapest_1month:
        cheapest_badge = "💎 AYIN EN UCUZU\n\n"
    elif deal.is_cheapest_14days:
        cheapest_badge = "✨ 14 GÜNÜN EN UCUZU\n\n"
    
    # Extract rating and review count separately
    rating_value = ""
    review_count_value = ""
    if product and product.rating:
        rating_value = f"{product.rating:.1f}"
        if product.review_count:
            review_count_value = str(product.review_count)
    
    # Format message
    try:
        message = template.format(
            title=deal.title[:200],
            brand_line=brand_line,
            cheapest_badge=cheapest_badge,
            discount_percentage=discount_pct,
            original_price=format_turkish_price(float(deal.original_price)),
            deal_price=format_turkish_price(float(deal.deal_price)),
            previous_price=format_turkish_price(float(deal.previous_price)) if deal.previous_price else format_turkish_price(float(deal.original_price)),
            discount_amount=format_turkish_price(float(deal.discount_amount)),
            rating=rating_value,
            review_count=review_count_value,
            rating_line=rating_line,
            product_url=product.detail_page_url if product else "",
            is_cheapest_14days="true" if deal.is_cheapest_14days else "false",
            is_cheapest_1month="true" if deal.is_cheapest_1month else "false",
            is_cheapest_3months="true" if deal.is_cheapest_3months else "false",
            is_cheapest_6months="true" if deal.is_cheapest_6months else "false"
        )
        return message
    except Exception as e:
        logger.error(f"Template formatting error: {str(e)}")
        # Fallback to simple message
        return (
            f"{cheapest_badge}"
            f"🔥 <b>%{discount_pct} İNDİRİM</b>\n\n"
            f"<b>{deal.title[:200]}</b>\n\n"
            f"{brand_line}"
            f"<s>₺{format_turkish_price(float(deal.original_price))}</s> → <b>₺{format_turkish_price(float(deal.deal_price))}</b>\n"
            f"💰 ₺{format_turkish_price(float(deal.discount_amount))} Tasarruf\n\n"
            f"{rating_line}"
            f"📱 @FirsatRadari"
        )


def send_telegram_message(
    bot_token: str,
    chat_id: str,
    message: str,
    button_text: Optional[str] = None,
    button_url: Optional[str] = None,
    image_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send message to Telegram with optional inline button and image
    
    Args:
        bot_token: Telegram bot token
        chat_id: Channel/chat ID
        message: Message text (HTML formatted)
        button_text: Text for inline button (optional)
        button_url: URL for inline button (optional)
        image_url: Product image URL (optional)
    
    Returns:
        API response dict
    """
    
    # Determine if we're sending photo or text
    if image_url:
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": image_url,
            "caption": message,
            "parse_mode": "HTML"
        }
    else:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
    
    # Add inline button if provided
    if button_text and button_url:
        payload["reply_markup"] = {
            "inline_keyboard": [[
                {
                    "text": button_text,
                    "url": button_url
                }
            ]]
        }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if not result.get('ok'):
            logger.error(f"Telegram API error: {result}")
            return {"success": False, "error": result.get('description')}
        
        return {
            "success": True,
            "message_id": result['result']['message_id'],
            "chat_id": result['result']['chat']['id']
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram send error: {str(e)}")
        return {"success": False, "error": str(e)}


def send_deal_notification(deal: models.Deal, db: Session) -> bool:
    """
    Send deal notification to Telegram channel
    
    Args:
        deal: Deal object to send
        db: Database session
    
    Returns:
        True if sent successfully, False otherwise
    """
    
    try:
        # Get Telegram settings
        telegram_settings = get_telegram_settings(db)
        
        bot_token = telegram_settings.get('telegram_bot_token')
        channel_id = telegram_settings.get('telegram_channel_id')
        template = telegram_settings.get('telegram_message_template', '')
        
        if not bot_token or not channel_id:
            logger.error("Telegram bot_token or channel_id not configured")
            return False
        
        # Get Amazon partner tag for affiliate links
        partner_tag = db.query(models.SystemSetting).filter(
            models.SystemSetting.key == 'amazon_partner_tag'
        ).first()
        partner_tag_value = partner_tag.value if partner_tag else None
        
        # Format message
        message = format_deal_message(deal, template)
        
        # Get product URL and image
        product = deal.product
        
        # Generate Amazon URL from ASIN if detail_page_url is empty
        button_url = None
        if product:
            if product.detail_page_url:
                button_url = product.detail_page_url
            elif product.asin:
                # Generate Amazon TR URL from ASIN
                button_url = f"https://www.amazon.com.tr/dp/{product.asin}"
            
            # Add affiliate tag to URL
            if button_url and partner_tag_value:
                separator = '&' if '?' in button_url else '?'
                button_url = f"{button_url}{separator}tag={partner_tag_value}"
        
        image_url = product.image_url if product else None
        
        # Send to Telegram
        result = send_telegram_message(
            bot_token=bot_token,
            chat_id=channel_id,
            message=message,
            button_text="📦 Fırsata Git",
            button_url=button_url,
            image_url=image_url
        )
        
        if result.get('success'):
            # Update deal with Telegram info
            deal.telegram_sent = True
            deal.telegram_message_id = str(result.get('message_id'))
            deal.telegram_sent_at = datetime.now()
            db.commit()
            
            logger.info(f"Deal {deal.id} sent to Telegram successfully")
            return True
        else:
            logger.error(f"Failed to send deal {deal.id}: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending deal {deal.id} to Telegram: {str(e)}")
        db.rollback()
        return False

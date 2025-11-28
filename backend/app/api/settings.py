from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.db import models
from app.schemas import setting as setting_schema
from app.core.security import get_current_active_admin

router = APIRouter()


class TelegramTemplatePreview(BaseModel):
    template: str
    deal_id: Optional[int] = None


class TelegramTestMessage(BaseModel):
    message: str


@router.get("/", response_model=List[setting_schema.SystemSetting])
async def list_settings(
    group: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """List system settings (admin only)"""
    
    query = db.query(models.SystemSetting)
    
    if group:
        query = query.filter(models.SystemSetting.group == group)
    
    settings = query.all()
    return settings


@router.get("/{key}", response_model=setting_schema.SystemSetting)
async def get_setting(
    key: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Get setting by key (admin only)"""
    
    setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found"
        )
    
    return setting


@router.post("/", response_model=setting_schema.SystemSetting, status_code=status.HTTP_201_CREATED)
async def create_setting(
    setting: setting_schema.SystemSettingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Create a new setting (admin only)"""
    
    # Check if key exists
    if db.query(models.SystemSetting).filter(models.SystemSetting.key == setting.key).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setting with this key already exists"
        )
    
    db_setting = models.SystemSetting(**setting.dict())
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    
    return db_setting


@router.put("/{key}", response_model=setting_schema.SystemSetting)
async def update_setting(
    key: str,
    setting_update: setting_schema.SystemSettingUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Update setting (admin only)"""
    
    setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found"
        )
    
    update_data = setting_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(setting, field, value)
    
    db.commit()
    db.refresh(setting)
    
    return setting


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(
    key: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Delete setting (admin only)"""
    
    setting = db.query(models.SystemSetting).filter(models.SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found"
        )
    
    db.delete(setting)
    db.commit()
    
    return None


@router.get("/worker/logs", response_model=List[setting_schema.WorkerLog])
async def get_worker_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    job_name: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Get worker logs (admin only)"""
    
    query = db.query(models.WorkerLog)
    
    if job_name:
        query = query.filter(models.WorkerLog.job_name == job_name)
    
    if status:
        query = query.filter(models.WorkerLog.status == status)
    
    logs = query.order_by(models.WorkerLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return logs


@router.post("/telegram/preview-template")
async def preview_telegram_template(
    preview_data: TelegramTemplatePreview,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_admin)
):
    """Preview telegram template with sample or real deal data"""
    
    # Get a deal for preview (use provided or get latest)
    if preview_data.deal_id:
        deal = db.query(models.Deal).filter(models.Deal.id == preview_data.deal_id).first()
        if not deal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deal not found"
            )
    else:
        # Get latest deal with product info
        deal = db.query(models.Deal).filter(
            models.Deal.product_id.isnot(None)
        ).order_by(models.Deal.created_at.desc()).first()
        
        if not deal:
            # Return sample data
            return {
                "preview": "Önizleme için henüz ürün verisi yok. Örnek veri ile:",
                "rendered": preview_data.template.format(
                    title="Örnek Kahve Makinesi",
                    brand_line="🏷 Nespresso\n\n",
                    cheapest_badge="🏆 6 AYIN EN UCUZU",
                    discount_percentage="35",
                    original_price="2499.00",
                    deal_price="1624.00",
                    previous_price="2499.00",
                    discount_amount="875.00",
                    rating="4.5",
                    review_count="150",
                    rating_line="⭐⭐⭐⭐ 4.5/5 (150 değerlendirme)\n\n",
                    product_url="https://amazon.com.tr/example?tag=firsatradar06-21",
                    is_cheapest_14days="true",
                    is_cheapest_1month="true",
                    is_cheapest_3months="true",
                    is_cheapest_6months="true"
                ),
                "is_sample": True
            }
    
    # Prepare variables from deal
    discount_pct = int(deal.discount_percentage)
    
    brand_line = ""
    if deal.product and deal.product.brand:
        brand_line = f"🏷 {deal.product.brand}\n\n"
    
    rating_line = ""
    if deal.product and deal.product.rating:
        stars = "⭐" * int(deal.product.rating)
        rating_line = f"{stars} {deal.product.rating:.1f}/5"
        if deal.product.review_count:
            rating_line += f" ({deal.product.review_count} değerlendirme)"
        rating_line += "\n\n"
    
    product_url = deal.product.detail_page_url if deal.product else ""
    
    # Get cheapest badge
    cheapest_badge = ""
    if deal.is_cheapest_6months:
        cheapest_badge = "🏆 6 AYIN EN UCUZU"
    elif deal.is_cheapest_3months:
        cheapest_badge = "⭐ 3 AYIN EN UCUZU"
    elif deal.is_cheapest_1month:
        cheapest_badge = "💎 AYIN EN UCUZU"
    elif deal.is_cheapest_14days:
        cheapest_badge = "✨ 14 GÜNÜN EN UCUZU"
    
    # Extract rating and review count separately
    rating_value = ""
    review_count_value = ""
    if deal.product and deal.product.rating:
        rating_value = f"{deal.product.rating:.1f}"
        if deal.product.review_count:
            review_count_value = str(deal.product.review_count)
    
    # Render template
    try:
        rendered = preview_data.template.format(
            title=deal.title[:200],
            brand_line=brand_line,
            cheapest_badge=cheapest_badge,
            discount_percentage=discount_pct,
            original_price=f"{float(deal.original_price):.2f}",
            deal_price=f"{float(deal.deal_price):.2f}",
            previous_price=f"{float(deal.previous_price):.2f}" if deal.previous_price else f"{float(deal.original_price):.2f}",
            discount_amount=f"{float(deal.discount_amount):.2f}",
            rating=rating_value,
            review_count=review_count_value,
            rating_line=rating_line,
            product_url=product_url,
            is_cheapest_14days="true" if deal.is_cheapest_14days else "false",
            is_cheapest_1month="true" if deal.is_cheapest_1month else "false",
            is_cheapest_3months="true" if deal.is_cheapest_3months else "false",
            is_cheapest_6months="true" if deal.is_cheapest_6months else "false"
        )
        
        return {
            "preview": "Gerçek ürün verisi ile önizleme:",
            "rendered": rendered,
            "is_sample": False,
            "deal_id": deal.id,
            "deal_title": deal.title
        }
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Şablon hatası: Geçersiz değişken {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Şablon render hatası: {str(e)}"
        )

"""
Smart Deal Detection Service
Analyzes price history to detect real deals, not just temporary discounts
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, List, Tuple
from loguru import logger
from sqlalchemy.orm import Session

from database import Product, PriceHistory, Deal


class DealDetector:
    """
    Intelligent deal detection based on price history
    
    A deal is detected when:
    1. Current price < list_price (basic discount check)
    2. Current price is significantly lower than historical average
    3. Discount percentage meets threshold
    4. Product quality meets criteria (rating, reviews)
    
    This prevents false positives from inflated "list prices"
    """
    
    def __init__(self, deal_threshold_percentage: float = 15.0):
        self.deal_threshold = deal_threshold_percentage
        self.history_days = 30  # Look back 30 days
        self.min_history_records = 2  # Need at least 2 price records (more aggressive)
    
    def analyze_product(self, product: Product, db: Session) -> Tuple[bool, Optional[Dict]]:
        """
        Analyze if product has a real deal
        
        Returns:
            (is_deal, deal_info)
        """
        if not product.current_price or not product.is_available:
            return False, None
        
        # Get price history
        history = self._get_price_history(product, db)
        
        # Calculate metrics
        metrics = self._calculate_metrics(product, history)
        
        # Determine if it's a deal
        is_deal = self._is_deal(metrics)
        
        if is_deal:
            deal_info = {
                'current_price': float(product.current_price),
                'list_price': float(product.list_price) if product.list_price else None,
                'historical_avg': metrics['historical_avg'],
                'historical_min': metrics['historical_min'],
                'historical_max': metrics['historical_max'],
                'discount_vs_list': metrics['discount_vs_list'],
                'discount_vs_avg': metrics['discount_vs_avg'],
                'is_historical_low': metrics['is_historical_low'],
                'deal_score': metrics['deal_score']
            }
            return True, deal_info
        
        return False, None
    
    def _get_price_history(self, product: Product, db: Session) -> List[PriceHistory]:
        """Get recent price history"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.history_days)
        
        history = db.query(PriceHistory).filter(
            PriceHistory.product_id == product.id,
            PriceHistory.recorded_at >= cutoff_date,
            PriceHistory.is_available == True
        ).order_by(PriceHistory.recorded_at.desc()).all()
        
        return history
    
    def _calculate_metrics(self, product: Product, history: List[PriceHistory]) -> Dict:
        """Calculate price metrics (based only on real price history)"""
        current_price = float(product.current_price)
        
        metrics = {
            'current_price': current_price,
            'has_history': len(history) >= self.min_history_records,  # Now 2 records
            'history_count': len(history),
            'historical_avg': None,
            'historical_min': None,
            'historical_max': None,
            'discount_vs_list': 0.0,  # Add discount vs list price
            'discount_vs_avg': 0.0,
            'is_historical_low': False,
            'is_early_deal': len(history) <= 3,  # Flag for new products
            'deal_score': 0.0
        }
        
        # Calculate discount vs list price (if available)
        if product.list_price and product.list_price > current_price:
            metrics['discount_vs_list'] = ((float(product.list_price) - current_price) / float(product.list_price)) * 100
        
        # Calculate historical metrics
        if history:
            prices = [float(h.price) for h in history if h.price]
            
            if prices:
                metrics['historical_avg'] = sum(prices) / len(prices)
                metrics['historical_min'] = min(prices)
                metrics['historical_max'] = max(prices)
                
                # Discount vs historical average
                if metrics['historical_avg'] > current_price:
                    metrics['discount_vs_avg'] = ((metrics['historical_avg'] - current_price) / metrics['historical_avg']) * 100
                
                # Check if current price is historical low (or within 1%)
                if current_price <= metrics['historical_min'] * 1.01:
                    metrics['is_historical_low'] = True
        
        # Calculate deal score (0-100)
        metrics['deal_score'] = self._calculate_deal_score(metrics, product)
        
        return metrics
    
    def _calculate_deal_score(self, metrics: Dict, product: Product) -> float:
        """
        Calculate deal score (0-100)
        
        Factors:
        - Historical discount (50 points) - only real price drops
        - Product quality (30 points)
        - Availability & Prime (20 points)
        """
        score = 0.0
        
        # 1. Historical discount percentage (50 points max)
        discount = metrics['discount_vs_avg']
        if discount >= 40:
            score += 50  # Huge drop
        elif discount >= 30:
            score += 40
        elif discount >= 20:
            score += 30
        elif discount >= 15:
            score += 20
        elif discount >= 10:
            score += 10
        
        # 2. Historical low bonus (20 points max)
        if metrics['is_historical_low']:
            score += 20  # Best price ever - extra bonus
        
        # 3. Product quality (30 points max)
        if product.rating:
            if product.rating >= 4.5:
                score += 20
            elif product.rating >= 4.0:
                score += 15
            elif product.rating >= 3.5:
                score += 10
        
        if product.review_count:
            if product.review_count >= 1000:
                score += 10
            elif product.review_count >= 500:
                score += 7
            elif product.review_count >= 100:
                score += 5
        
        # 4. Availability & Prime (20 points max)
        if product.is_available:
            score += 10
        
        # Check if Prime eligible (from amazon_data)
        if product.amazon_data and product.amazon_data.get('is_prime'):
            score += 10
        
        return min(score, 100.0)
    
    def _is_deal(self, metrics: Dict) -> bool:
        """
        Determine if it's a real deal (based ONLY on price history)
        
        Criteria:
        1. Must have price history (at least 2 records) - AGGRESSIVE
        2. Must be at least threshold% cheaper than historical average
        3. Deal score >= 45 (lowered for early deals)
        """
        # MUST have at least 2 price records (current + 1 previous)
        if not metrics['has_history']:
            logger.debug(f"Not enough price history ({metrics['history_count']} records, need {self.min_history_records})")
            return False
        
        # Minimum discount vs historical average
        if metrics['discount_vs_avg'] < self.deal_threshold:
            logger.debug(f"Discount {metrics['discount_vs_avg']:.1f}% < threshold {self.deal_threshold}%")
            return False
        
        # Deal score threshold (lower for early deals)
        min_score = 45 if metrics['history_count'] <= 3 else 50
        if metrics['deal_score'] < min_score:
            logger.debug(f"Deal score {metrics['deal_score']:.0f} < {min_score}")
            return False
        
        return True
    
    def create_or_update_deal(
        self,
        product: Product,
        deal_info: Dict,
        db: Session
    ) -> Tuple[bool, Deal]:
        """
        Create or update deal
        
        Returns:
            (created, deal)
        """
        # Check if active deal exists
        active_deal = db.query(Deal).filter(
            Deal.product_id == product.id,
            Deal.is_active == True
        ).first()
        
        if active_deal:
            # Update existing deal (use historical avg as reference)
            active_deal.deal_price = product.current_price
            active_deal.original_price = Decimal(str(deal_info['historical_avg']))
            active_deal.discount_amount = active_deal.original_price - active_deal.deal_price
            active_deal.discount_percentage = deal_info['discount_vs_avg']
            active_deal.updated_at = datetime.utcnow()
            
            # Update metadata
            if not active_deal.description:
                active_deal.description = ""
            active_deal.description = self._generate_deal_description(product, deal_info)
            
            logger.info(f"Updated deal for {product.asin}: {active_deal.discount_percentage:.1f}% off (score: {deal_info['deal_score']:.0f})")
            return False, active_deal
        
        else:
            # Create new deal (use historical avg as reference price)
            original_price = Decimal(str(deal_info['historical_avg']))
            discount_amount = original_price - product.current_price
            discount_pct = deal_info['discount_vs_avg']
            
            deal = Deal(
                product_id=product.id,
                title=product.title[:500],
                description=self._generate_deal_description(product, deal_info),
                original_price=original_price,
                deal_price=product.current_price,
                discount_amount=discount_amount,
                discount_percentage=discount_pct,
                currency=product.currency,
                is_active=True,
                is_published=False,  # Admin reviews first
                telegram_sent=False,
                valid_from=datetime.utcnow()
            )
            db.add(deal)
            
            logger.success(f"Created deal for {product.asin}: {discount_pct:.1f}% off (score: {deal_info['deal_score']:.0f})")
            return True, deal
    
    def _generate_deal_description(self, product: Product, deal_info: Dict) -> str:
        """Generate deal description"""
        desc_parts = []
        
        if product.brand:
            desc_parts.append(f"{product.brand}")
        
        discount = deal_info['discount_vs_avg']
        desc_parts.append(f"%{int(discount)} Fiyat Düşüşü")
        
        if deal_info['is_historical_low']:
            desc_parts.append("🔥 En Düşük Fiyat")
        elif deal_info.get('is_early_deal'):
            desc_parts.append("🆕 Yeni Fırsat")
        
        if product.rating and product.rating >= 4.0:
            desc_parts.append(f"⭐ {product.rating:.1f}/5")
        
        score = deal_info['deal_score']
        if score >= 80:
            desc_parts.append("💎 Muhteşem Fırsat")
        elif score >= 70:
            desc_parts.append("🔥 Harika Fırsat")
        elif score >= 60:
            desc_parts.append("✨ İyi Fırsat")
        
        return " • ".join(desc_parts)

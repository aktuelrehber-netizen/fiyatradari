"""
Product Priority Calculator
Determines which products should be checked more frequently
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
from decimal import Decimal
from loguru import logger
from sqlalchemy.orm import Session

from database import Product, Deal, PriceHistory


class PriorityCalculator:
    """
    Calculate check priority for products
    
    Priority Score (0-100):
    - 100: Active deals, check every hour
    - 70-99: High volatility, popular products
    - 40-69: Medium volatility
    - 10-39: Low volatility
    - 0-9: Very stable products
    """
    
    def __init__(self):
        self.weights = {
            'has_active_deal': 50,
            'volatility': 25,
            'popularity': 15,
            'recency': 10
        }
        # Baseline priority to ensure workers don't idle
        self.baseline_priority = 40
    
    def calculate_priority(self, product: Product, db: Session) -> int:
        """
        Calculate priority score for a product
        
        Args:
            product: Product instance
            db: Database session
        
        Returns:
            Priority score (0-100)
        """
        # Start with baseline to ensure all products get checked regularly
        score = self.baseline_priority
        
        # 1. Active Deal Bonus (50 points)
        if self._has_active_deal(product, db):
            score += self.weights['has_active_deal']
        
        # 2. Price Volatility (25 points)
        volatility_score = self._calculate_volatility_score(product, db)
        score += volatility_score * (self.weights['volatility'] / 100)
        
        # 3. Popularity Score (15 points)
        popularity_score = self._calculate_popularity_score(product)
        score += popularity_score * (self.weights['popularity'] / 100)
        
        # 4. Recency Score (10 points)
        recency_score = self._calculate_recency_score(product)
        score += recency_score * (self.weights['recency'] / 100)
        
        # 5. New Product Bonus (if never checked, add 20 points)
        if not product.last_checked_at:
            score += 20
        
        # 6. Recently Added Bonus (first 7 days)
        if product.created_at:
            days_since_creation = (datetime.utcnow() - product.created_at).days
            if days_since_creation <= 7:
                score += 15  # High priority for new products
        
        return min(int(score), 100)
    
    def get_check_interval_hours(self, priority: int) -> int:
        """
        Get recommended check interval based on priority
        
        Args:
            priority: Priority score (0-100)
        
        Returns:
            Check interval in hours
        """
        if priority >= 80:
            return 1  # Every hour
        elif priority >= 60:
            return 2  # Every 2 hours
        elif priority >= 40:
            return 4  # Every 4 hours
        elif priority >= 20:
            return 8  # Every 8 hours
        else:
            return 12  # Every 12 hours (minimum)
    
    def _has_active_deal(self, product: Product, db: Session) -> bool:
        """Check if product has an active deal"""
        active_deal = db.query(Deal).filter(
            Deal.product_id == product.id,
            Deal.is_active == True
        ).first()
        return active_deal is not None
    
    def _calculate_volatility_score(self, product: Product, db: Session) -> float:
        """
        Calculate price volatility score (0-100)
        
        High volatility = high score = check more often
        """
        # Get recent price history (30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        history = db.query(PriceHistory).filter(
            PriceHistory.product_id == product.id,
            PriceHistory.recorded_at >= cutoff_date,
            PriceHistory.is_available == True
        ).order_by(PriceHistory.recorded_at).all()
        
        if len(history) < 3:
            # Not enough data, assume medium-high volatility to ensure checking
            return 70.0
        
        # Calculate price changes
        prices = [float(h.price) for h in history if h.price]
        if not prices or len(prices) < 2:
            return 70.0
        
        # Calculate standard deviation as percentage of mean
        mean_price = sum(prices) / len(prices)
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        std_dev = variance ** 0.5
        
        # Coefficient of variation (CV) as percentage
        cv_percentage = (std_dev / mean_price * 100) if mean_price > 0 else 0
        
        # Map CV to score (0-100)
        # CV > 20% = very volatile (100 score)
        # CV < 2% = very stable (0 score)
        if cv_percentage >= 20:
            return 100.0
        elif cv_percentage <= 2:
            return 0.0
        else:
            return (cv_percentage - 2) / 18 * 100
    
    def _calculate_popularity_score(self, product: Product) -> float:
        """
        Calculate product popularity score (0-100)
        
        Based on:
        - Review count
        - Rating
        - Category popularity
        """
        score = 0.0
        
        # Review count (0-60 points)
        if product.review_count:
            if product.review_count >= 5000:
                score += 60
            elif product.review_count >= 1000:
                score += 50
            elif product.review_count >= 500:
                score += 40
            elif product.review_count >= 100:
                score += 30
            elif product.review_count >= 50:
                score += 20
            elif product.review_count >= 10:
                score += 10
        
        # Rating (0-40 points)
        if product.rating:
            if product.rating >= 4.5:
                score += 40
            elif product.rating >= 4.0:
                score += 30
            elif product.rating >= 3.5:
                score += 20
            elif product.rating >= 3.0:
                score += 10
        
        return min(score, 100.0)
    
    def _calculate_recency_score(self, product: Product) -> float:
        """
        Calculate recency score (0-100)
        
        Products checked recently get lower score
        Products not checked for a while get higher score
        """
        if not product.last_checked_at:
            return 100.0  # Never checked, high priority
        
        hours_since_check = (datetime.utcnow() - product.last_checked_at).total_seconds() / 3600
        
        # Map hours to score
        if hours_since_check >= 48:
            return 100.0  # 2+ days, very high priority
        elif hours_since_check >= 24:
            return 80.0  # 1-2 days
        elif hours_since_check >= 12:
            return 60.0  # 12-24 hours
        elif hours_since_check >= 6:
            return 40.0  # 6-12 hours
        elif hours_since_check >= 3:
            return 20.0  # 3-6 hours
        else:
            return 0.0  # Recently checked
    
    def get_priority_category(self, priority: int) -> str:
        """Get priority category name"""
        if priority >= 80:
            return "HIGH"
        elif priority >= 60:
            return "MEDIUM_HIGH"
        elif priority >= 40:
            return "MEDIUM"
        elif priority >= 20:
            return "MEDIUM_LOW"
        else:
            return "LOW"

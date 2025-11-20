"""
Amazon PA API endpoints for admin operations
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.db import models
from app.db.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


class BrowseNodeSearchRequest(BaseModel):
    keyword: str


class BrowseNodeInfo(BaseModel):
    id: str
    name: str
    context_free_name: str | None = None


class BrowseNodeSearchResponse(BaseModel):
    nodes: List[BrowseNodeInfo]


class ASINLookupRequest(BaseModel):
    asin: str


class BulkASINLookupRequest(BaseModel):
    asins: List[str]


class ASINLookupResponse(BaseModel):
    asin: str
    title: str
    brand: str | None = None
    current_price: float | None = None
    currency: str = "TRY"
    image_url: str | None = None
    detail_page_url: str | None = None
    rating: float | None = None
    review_count: int | None = None
    is_available: bool = True
    availability: str | None = None
    is_prime: bool = False
    ean: str | None = None
    upc: str | None = None
    isbn: str | None = None


class BulkASINResult(BaseModel):
    asin: str
    title: str | None = None
    ean: str | None = None
    upc: str | None = None
    isbn: str | None = None
    error: str | None = None


class BulkASINLookupResponse(BaseModel):
    results: List[BulkASINResult]
    total: int
    successful: int
    failed: int


class ProductSearchRequest(BaseModel):
    keyword: str
    max_results: int = 10


class ProductSearchResult(BaseModel):
    asin: str
    title: str
    brand: str | None = None
    current_price: float | None = None
    currency: str = "TRY"
    image_url: str | None = None
    detail_page_url: str | None = None
    ean: str | None = None
    upc: str | None = None
    isbn: str | None = None


class ProductSearchResponse(BaseModel):
    results: List[ProductSearchResult]
    total: int
    keyword: str


@router.post("/search-browse-nodes", response_model=BrowseNodeSearchResponse)
async def search_browse_nodes(
    request: BrowseNodeSearchRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Search Amazon for a keyword and return browse node IDs from results
    """
    try:
        # Get Amazon API credentials from settings
        access_key_setting = db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "amazon_access_key"
        ).first()
        
        secret_key_setting = db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "amazon_secret_key"
        ).first()
        
        partner_tag_setting = db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "amazon_partner_tag"
        ).first()
        
        if not access_key_setting or not secret_key_setting or not partner_tag_setting:
            raise HTTPException(status_code=400, detail="Amazon PA API credentials not configured in settings")
        
        if not access_key_setting.value or not secret_key_setting.value or not partner_tag_setting.value:
            raise HTTPException(status_code=400, detail="Amazon PA API credentials are empty")
        
        # Import here to avoid circular dependencies
        from amazon_paapi import AmazonApi
        
        # Initialize Amazon PA API with throttling
        amazon = AmazonApi(
            key=access_key_setting.value,
            secret=secret_key_setting.value,
            tag=partner_tag_setting.value,
            country='TR',
            throttling=1.0  # Wait 1 second between requests
        )
        
        # Search for products with the keyword
        search_result = amazon.search_items(
            keywords=request.keyword,
            item_count=10
        )
        
        # Extract unique browse nodes from results
        browse_nodes_dict: Dict[str, BrowseNodeInfo] = {}
        
        if hasattr(search_result, 'items') and search_result.items:
            for item in search_result.items:
                if hasattr(item, 'browse_node_info') and item.browse_node_info:
                    if hasattr(item.browse_node_info, 'browse_nodes'):
                        for node in item.browse_node_info.browse_nodes:
                            node_id = str(node.id) if hasattr(node, 'id') else None
                            node_name = node.display_name if hasattr(node, 'display_name') else None
                            context_free = node.context_free_name if hasattr(node, 'context_free_name') else None
                            
                            if node_id and node_name and node_id not in browse_nodes_dict:
                                browse_nodes_dict[node_id] = BrowseNodeInfo(
                                    id=node_id,
                                    name=node_name,
                                    context_free_name=context_free
                                )
        
        return BrowseNodeSearchResponse(
            nodes=list(browse_nodes_dict.values())
        )
        
    except ImportError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Amazon PA API library not available: {str(e)}"
        )
    except Exception as e:
        import traceback
        error_detail = f"Error searching Amazon: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log to console
        raise HTTPException(
            status_code=500,
            detail=f"Error searching Amazon: {str(e)}"
        )


@router.post("/lookup-asin", response_model=ASINLookupResponse)
async def lookup_asin(
    request: ASINLookupRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Lookup a single product by ASIN from Amazon PA API
    Returns product details including barcode information (EAN, UPC, ISBN)
    """
    try:
        # Get Amazon API credentials from settings
        access_key_setting = db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "amazon_access_key"
        ).first()
        
        secret_key_setting = db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "amazon_secret_key"
        ).first()
        
        partner_tag_setting = db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "amazon_partner_tag"
        ).first()
        
        if not access_key_setting or not secret_key_setting or not partner_tag_setting:
            raise HTTPException(status_code=400, detail="Amazon PA API credentials not configured in settings")
        
        if not access_key_setting.value or not secret_key_setting.value or not partner_tag_setting.value:
            raise HTTPException(status_code=400, detail="Amazon PA API credentials are empty")
        
        # Import here to avoid circular dependencies
        from amazon_paapi import AmazonApi
        
        # Initialize Amazon PA API with resources including ExternalIds for barcodes
        amazon = AmazonApi(
            key=access_key_setting.value,
            secret=secret_key_setting.value,
            tag=partner_tag_setting.value,
            country='TR',
            throttling=1.0,
            resources=[
                'ItemInfo.Title',
                'ItemInfo.ByLineInfo',
                'ItemInfo.ExternalIds',  # EAN, UPC, ISBN barcodes
                'ItemInfo.Classifications',
                'Offers.Listings.Price',
                'Offers.Listings.Availability',
                'Offers.Listings.DeliveryInfo.IsPrimeEligible',
                'Images.Primary.Large',
                'CustomerReviews.StarRating',
                'CustomerReviews.Count'
            ]
        )
        
        # Get item by ASIN
        items = amazon.get_items(items=[request.asin])
        
        if not items or len(items) == 0:
            raise HTTPException(status_code=404, detail=f"Product with ASIN {request.asin} not found on Amazon")
        
        item = items[0]
        
        # Extract data
        title = None
        brand = None
        if hasattr(item, 'item_info') and item.item_info:
            if hasattr(item.item_info, 'title'):
                title = item.item_info.title.display_value if item.item_info.title else None
            if hasattr(item.item_info, 'by_line_info') and item.item_info.by_line_info:
                if hasattr(item.item_info.by_line_info, 'brand'):
                    brand = item.item_info.by_line_info.brand.display_value if item.item_info.by_line_info.brand else None
        
        # Extract price
        price = None
        is_prime = False
        availability = None
        if hasattr(item, 'offers') and item.offers:
            listings = item.offers.listings
            if listings and len(listings) > 0:
                listing = listings[0]
                if hasattr(listing, 'price') and listing.price:
                    price = float(listing.price.amount) if listing.price.amount else None
                if hasattr(listing, 'availability'):
                    availability = listing.availability.message if listing.availability else None
                if hasattr(listing, 'delivery_info') and listing.delivery_info:
                    is_prime = listing.delivery_info.is_prime_eligible or False
        
        # Extract rating
        rating = None
        review_count = None
        if hasattr(item, 'customer_reviews') and item.customer_reviews:
            if hasattr(item.customer_reviews, 'star_rating'):
                rating = float(item.customer_reviews.star_rating.value) if item.customer_reviews.star_rating else None
            if hasattr(item.customer_reviews, 'count'):
                review_count = int(item.customer_reviews.count) if item.customer_reviews.count else None
        
        # Extract image
        image_url = None
        if hasattr(item, 'images') and item.images:
            if hasattr(item.images, 'primary') and item.images.primary:
                if hasattr(item.images.primary, 'large'):
                    image_url = item.images.primary.large.url if item.images.primary.large else None
        
        # Extract barcode information (EAN, UPC, ISBN)
        ean = None
        upc = None
        isbn = None
        if hasattr(item, 'item_info') and item.item_info:
            if hasattr(item.item_info, 'external_ids') and item.item_info.external_ids:
                external_ids = item.item_info.external_ids
                
                # EAN (European Article Number)
                if hasattr(external_ids, 'ea_ns') and external_ids.ea_ns:
                    if hasattr(external_ids.ea_ns, 'display_values') and external_ids.ea_ns.display_values:
                        ean = external_ids.ea_ns.display_values[0] if len(external_ids.ea_ns.display_values) > 0 else None
                
                # UPC (Universal Product Code)
                if hasattr(external_ids, 'up_cs') and external_ids.up_cs:
                    if hasattr(external_ids.up_cs, 'display_values') and external_ids.up_cs.display_values:
                        upc = external_ids.up_cs.display_values[0] if len(external_ids.up_cs.display_values) > 0 else None
                
                # ISBN (for books)
                if hasattr(external_ids, 'is_bns') and external_ids.is_bns:
                    if hasattr(external_ids.is_bns, 'display_values') and external_ids.is_bns.display_values:
                        isbn = external_ids.is_bns.display_values[0] if len(external_ids.is_bns.display_values) > 0 else None
        
        return ASINLookupResponse(
            asin=item.asin,
            title=title or '',
            brand=brand,
            current_price=price,
            currency='TRY',
            image_url=image_url,
            detail_page_url=item.detail_page_url,
            rating=rating,
            review_count=review_count,
            is_available=availability != 'Out of Stock' if availability else True,
            availability=availability,
            is_prime=is_prime,
            ean=ean,
            upc=upc,
            isbn=isbn
        )
        
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Amazon PA API library not available: {str(e)}"
        )
    except Exception as e:
        import traceback
        error_detail = f"Error looking up ASIN: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log to console
        raise HTTPException(
            status_code=500,
            detail=f"Error looking up ASIN: {str(e)}"
        )


@router.post("/bulk-lookup-asin", response_model=BulkASINLookupResponse)
async def bulk_lookup_asin(
    request: BulkASINLookupRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Lookup multiple products by ASIN from Amazon PA API
    Returns barcode information (EAN, UPC, ISBN) for each product
    """
    try:
        # Validate ASIN count
        if len(request.asins) == 0:
            raise HTTPException(status_code=400, detail="No ASINs provided")
        
        if len(request.asins) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 ASINs allowed per request")
        
        # Get Amazon API credentials from settings
        access_key_setting = db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "amazon_access_key"
        ).first()
        
        secret_key_setting = db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "amazon_secret_key"
        ).first()
        
        partner_tag_setting = db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "amazon_partner_tag"
        ).first()
        
        if not access_key_setting or not secret_key_setting or not partner_tag_setting:
            raise HTTPException(status_code=400, detail="Amazon PA API credentials not configured in settings")
        
        if not access_key_setting.value or not secret_key_setting.value or not partner_tag_setting.value:
            raise HTTPException(status_code=400, detail="Amazon PA API credentials are empty")
        
        # Import here to avoid circular dependencies
        from amazon_paapi import AmazonApi
        import time
        
        # Initialize Amazon PA API with resources including ExternalIds for barcodes
        amazon = AmazonApi(
            key=access_key_setting.value,
            secret=secret_key_setting.value,
            tag=partner_tag_setting.value,
            country='TR',
            throttling=1.0,
            resources=[
                'ItemInfo.Title',
                'ItemInfo.ExternalIds',  # EAN, UPC, ISBN barcodes
            ]
        )
        
        results = []
        successful = 0
        failed = 0
        
        # Process ASINs in batches of 10 (Amazon PA API limit)
        for i in range(0, len(request.asins), 10):
            batch = request.asins[i:i+10]
            
            try:
                # Get items by ASIN
                items = amazon.get_items(items=batch)
                
                if items:
                    for item in items:
                        try:
                            # Extract title
                            title = None
                            if hasattr(item, 'item_info') and item.item_info:
                                if hasattr(item.item_info, 'title'):
                                    title = item.item_info.title.display_value if item.item_info.title else None
                            
                            # Extract barcode information
                            ean = None
                            upc = None
                            isbn = None
                            if hasattr(item, 'item_info') and item.item_info:
                                if hasattr(item.item_info, 'external_ids') and item.item_info.external_ids:
                                    external_ids = item.item_info.external_ids
                                    
                                    if hasattr(external_ids, 'ea_ns') and external_ids.ea_ns:
                                        if hasattr(external_ids.ea_ns, 'display_values') and external_ids.ea_ns.display_values:
                                            ean = external_ids.ea_ns.display_values[0] if len(external_ids.ea_ns.display_values) > 0 else None
                                    
                                    if hasattr(external_ids, 'up_cs') and external_ids.up_cs:
                                        if hasattr(external_ids.up_cs, 'display_values') and external_ids.up_cs.display_values:
                                            upc = external_ids.up_cs.display_values[0] if len(external_ids.up_cs.display_values) > 0 else None
                                    
                                    if hasattr(external_ids, 'is_bns') and external_ids.is_bns:
                                        if hasattr(external_ids.is_bns, 'display_values') and external_ids.is_bns.display_values:
                                            isbn = external_ids.is_bns.display_values[0] if len(external_ids.is_bns.display_values) > 0 else None
                            
                            results.append(BulkASINResult(
                                asin=item.asin,
                                title=title,
                                ean=ean,
                                upc=upc,
                                isbn=isbn
                            ))
                            successful += 1
                        except Exception as e:
                            results.append(BulkASINResult(
                                asin=item.asin if hasattr(item, 'asin') else 'unknown',
                                error=f"Error parsing item: {str(e)}"
                            ))
                            failed += 1
                
                # Add not found ASINs
                if items:
                    found_asins = {item.asin for item in items}
                    for asin in batch:
                        if asin not in found_asins:
                            results.append(BulkASINResult(
                                asin=asin,
                                error="Product not found on Amazon"
                            ))
                            failed += 1
                else:
                    # All items in batch not found
                    for asin in batch:
                        results.append(BulkASINResult(
                            asin=asin,
                            error="Product not found on Amazon"
                        ))
                        failed += 1
                
            except Exception as e:
                # Batch failed - mark all ASINs as failed
                for asin in batch:
                    results.append(BulkASINResult(
                        asin=asin,
                        error=f"Batch error: {str(e)}"
                    ))
                    failed += 1
            
            # Rate limiting between batches
            if i + 10 < len(request.asins):
                time.sleep(1)
        
        return BulkASINLookupResponse(
            results=results,
            total=len(request.asins),
            successful=successful,
            failed=failed
        )
        
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Amazon PA API library not available: {str(e)}"
        )
    except Exception as e:
        import traceback
        error_detail = f"Error in bulk lookup: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log to console
        raise HTTPException(
            status_code=500,
            detail=f"Error in bulk lookup: {str(e)}"
        )


@router.post("/search-products", response_model=ProductSearchResponse)
async def search_products(
    request: ProductSearchRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Search Amazon products by keyword
    Returns product details including barcode information (EAN, UPC, ISBN)
    """
    try:
        # Validate keyword
        if not request.keyword.strip():
            raise HTTPException(status_code=400, detail="Keyword cannot be empty")
        
        if request.max_results < 1 or request.max_results > 10:
            raise HTTPException(status_code=400, detail="Max results must be between 1 and 10")
        
        # Get Amazon API credentials from settings
        access_key_setting = db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "amazon_access_key"
        ).first()
        
        secret_key_setting = db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "amazon_secret_key"
        ).first()
        
        partner_tag_setting = db.query(models.SystemSetting).filter(
            models.SystemSetting.key == "amazon_partner_tag"
        ).first()
        
        if not access_key_setting or not secret_key_setting or not partner_tag_setting:
            raise HTTPException(status_code=400, detail="Amazon PA API credentials not configured in settings")
        
        if not access_key_setting.value or not secret_key_setting.value or not partner_tag_setting.value:
            raise HTTPException(status_code=400, detail="Amazon PA API credentials are empty")
        
        # Import here to avoid circular dependencies
        from amazon_paapi import AmazonApi
        
        # Initialize Amazon PA API with resources including ExternalIds for barcodes
        amazon = AmazonApi(
            key=access_key_setting.value,
            secret=secret_key_setting.value,
            tag=partner_tag_setting.value,
            country='TR',
            throttling=1.0,
            resources=[
                'ItemInfo.Title',
                'ItemInfo.ByLineInfo',
                'ItemInfo.ExternalIds',  # EAN, UPC, ISBN barcodes
                'Offers.Listings.Price',
                'Images.Primary.Medium',
            ]
        )
        
        # Search for products
        search_result = amazon.search_items(
            keywords=request.keyword,
            item_count=request.max_results
        )
        
        results = []
        
        if hasattr(search_result, 'items') and search_result.items:
            for item in search_result.items:
                # Extract title
                title = None
                brand = None
                if hasattr(item, 'item_info') and item.item_info:
                    if hasattr(item.item_info, 'title'):
                        title = item.item_info.title.display_value if item.item_info.title else None
                    if hasattr(item.item_info, 'by_line_info') and item.item_info.by_line_info:
                        if hasattr(item.item_info.by_line_info, 'brand'):
                            brand = item.item_info.by_line_info.brand.display_value if item.item_info.by_line_info.brand else None
                
                # Extract price
                price = None
                if hasattr(item, 'offers') and item.offers:
                    listings = item.offers.listings
                    if listings and len(listings) > 0:
                        listing = listings[0]
                        if hasattr(listing, 'price') and listing.price:
                            price = float(listing.price.amount) if listing.price.amount else None
                
                # Extract image
                image_url = None
                if hasattr(item, 'images') and item.images:
                    if hasattr(item.images, 'primary') and item.images.primary:
                        if hasattr(item.images.primary, 'medium'):
                            image_url = item.images.primary.medium.url if item.images.primary.medium else None
                
                # Extract barcode information
                ean = None
                upc = None
                isbn = None
                if hasattr(item, 'item_info') and item.item_info:
                    if hasattr(item.item_info, 'external_ids') and item.item_info.external_ids:
                        external_ids = item.item_info.external_ids
                        
                        if hasattr(external_ids, 'ea_ns') and external_ids.ea_ns:
                            if hasattr(external_ids.ea_ns, 'display_values') and external_ids.ea_ns.display_values:
                                ean = external_ids.ea_ns.display_values[0] if len(external_ids.ea_ns.display_values) > 0 else None
                        
                        if hasattr(external_ids, 'up_cs') and external_ids.up_cs:
                            if hasattr(external_ids.up_cs, 'display_values') and external_ids.up_cs.display_values:
                                upc = external_ids.up_cs.display_values[0] if len(external_ids.up_cs.display_values) > 0 else None
                        
                        if hasattr(external_ids, 'is_bns') and external_ids.is_bns:
                            if hasattr(external_ids.is_bns, 'display_values') and external_ids.is_bns.display_values:
                                isbn = external_ids.is_bns.display_values[0] if len(external_ids.is_bns.display_values) > 0 else None
                
                results.append(ProductSearchResult(
                    asin=item.asin,
                    title=title or '',
                    brand=brand,
                    current_price=price,
                    currency='TRY',
                    image_url=image_url,
                    detail_page_url=item.detail_page_url,
                    ean=ean,
                    upc=upc,
                    isbn=isbn
                ))
        
        return ProductSearchResponse(
            results=results,
            total=len(results),
            keyword=request.keyword
        )
        
    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Amazon PA API library not available: {str(e)}"
        )
    except Exception as e:
        import traceback
        error_detail = f"Error searching products: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log to console
        raise HTTPException(
            status_code=500,
            detail=f"Error searching products: {str(e)}"
        )

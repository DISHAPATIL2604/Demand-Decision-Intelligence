from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.models.product import Product

router = APIRouter()


@router.get("")
def get_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get a paginated list of active products."""

    products = (
        db.query(Product)
        .filter(Product.is_active == True)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total_returned": len(products),
        "skip": skip,
        "limit": limit,
        "products": [
            {
                "product_id": product.product_id,
                "product_name": product.product_name,
                "unit": product.unit,
                "product_type": product.product_type,
                "brand_name": product.brand_name,
                "manufacturer_name": product.manufacturer_name,
                "l0_category": product.l0_category,
                "l1_category": product.l1_category,
                "l2_category": product.l2_category,
                "l0_category_id": product.l0_category_id,
                "l1_category_id": product.l1_category_id,
                "l2_category_id": product.l2_category_id,
                "is_active": product.is_active,
            }
            for product in products
        ]
    }


@router.get("/categories")
def get_categories(
    db: Session = Depends(get_db)
):
    """Get unique product categories."""

    rows = (
        db.query(
            Product.l0_category,
            Product.l1_category,
            Product.l2_category
        )
        .filter(Product.is_active == True)
        .all()
    )

    return {
        "l0_categories": sorted({
            row.l0_category
            for row in rows
            if row.l0_category
        }),
        "l1_categories": sorted({
            row.l1_category
            for row in rows
            if row.l1_category
        }),
        "l2_categories": sorted({
            row.l2_category
            for row in rows
            if row.l2_category
        })
    }


@router.get("/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get a single product by product ID."""

    product = (
        db.query(Product)
        .filter(Product.product_id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product {product_id} not found"
        )

    return {
        "product_id": product.product_id,
        "product_name": product.product_name,
        "unit": product.unit,
        "product_type": product.product_type,
        "brand_name": product.brand_name,
        "manufacturer_name": product.manufacturer_name,
        "l0_category": product.l0_category,
        "l1_category": product.l1_category,
        "l2_category": product.l2_category,
        "l0_category_id": product.l0_category_id,
        "l1_category_id": product.l1_category_id,
        "l2_category_id": product.l2_category_id,
        "is_active": product.is_active,
    }
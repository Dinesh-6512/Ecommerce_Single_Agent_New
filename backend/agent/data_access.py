"""
Read-Only Data Access Layer for the E-Commerce Agent.

This module provides strictly isolated, read-only database queries
for products, pricing, stock levels, and authenticated user carts.
It does not perform any database mutations (no INSERT, UPDATE, DELETE).
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

try:
    from .. import models
except ImportError:
    import models


def get_agent_products(
    db: Session,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Read-only retrieval of product catalog (including title, price, stock).
    """
    products = (
        db.query(models.Product)
        .order_by(models.Product.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": p.id,
            "title": p.title,
            "price": float(p.price),
            "stock": p.stock,
            "description": p.description or "",
            "image_url": p.image_url or "",
        }
        for p in products
    ]


def get_agent_product_by_id(
    db: Session,
    product_id: int
) -> Optional[Dict[str, Any]]:
    """
    Read-only lookup for a single product by ID.
    """
    p = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not p:
        return None

    return {
        "id": p.id,
        "title": p.title,
        "price": float(p.price),
        "stock": p.stock,
        "description": p.description or "",
        "image_url": p.image_url or "",
    }


def search_agent_products(
    db: Session,
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Read-only search across product titles and descriptions.
    """
    search_filter = f"%{query.strip()}%"
    products = (
        db.query(models.Product)
        .filter(
            (models.Product.title.ilike(search_filter)) |
            (models.Product.description.ilike(search_filter))
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "id": p.id,
            "title": p.title,
            "price": float(p.price),
            "stock": p.stock,
            "description": p.description or "",
            "image_url": p.image_url or "",
        }
        for p in products
    ]


def get_agent_user_cart(
    db: Session,
    user_id: int
) -> Dict[str, Any]:
    """
    Read-only retrieval of the cart belonging to the logged-in user.
    Reads items, product info, price, quantity, available stock, and calculates total.
    Does not insert or create records if user has no cart yet.
    """
    cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
    if not cart:
        return {
            "cart_id": None,
            "user_id": user_id,
            "items": [],
            "total": 0.0,
        }

    cart_items = (
        db.query(models.CartItem)
        .filter(models.CartItem.cart_id == cart.id)
        .all()
    )

    items_result = []
    total = 0.0

    for item in cart_items:
        p = item.product
        if not p:
            continue
        subtotal = float(p.price) * item.quantity
        total += subtotal
        items_result.append({
            "cart_item_id": item.id,
            "product_id": p.id,
            "product_title": p.title,
            "price": float(p.price),
            "quantity": item.quantity,
            "available_stock": p.stock,
            "subtotal": round(subtotal, 2),
        })

    return {
        "cart_id": cart.id,
        "user_id": user_id,
        "items": items_result,
        "total": round(total, 2),
    }

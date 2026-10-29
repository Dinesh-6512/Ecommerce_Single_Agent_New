import os
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

try:
    from .database import engine, Base, get_db, SessionLocal
    from . import models, schemas, auth
    from .agent.flow import run_store_agent
except ImportError:
    from database import engine, Base, get_db, SessionLocal
    import models, schemas, auth
    from agent.flow import run_store_agent


# Helper to seed sample data and an admin user if not already present
def seed_initial_data(db: Session):
    # 1. Seed sample products if empty
    existing_count = db.query(models.Product).count()
    if existing_count == 0:
        sample_products = [
            models.Product(
                title="Wireless Bluetooth Headphones",
                price=59.99,
                stock=15,
                image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80",
                description="High quality over-ear headphones with noise isolation and rich bass."
            ),
            models.Product(
                title="Smart Fitness Watch",
                price=89.50,
                stock=10,
                image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&q=80",
                description="Track your heart rate, workouts, steps, and daily activity with water resistance."
            ),
            models.Product(
                title="Ergonomic Laptop Stand",
                price=29.99,
                stock=20,
                image_url="https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=500&q=80",
                description="Aluminum portable stand that elevates your laptop for better posture and airflow."
            ),
            models.Product(
                title="Mechanical Gaming Keyboard",
                price=74.99,
                stock=8,
                image_url="https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500&q=80",
                description="RGB backlit tactile mechanical switches for comfortable typing and gaming."
            ),
        ]
        db.add_all(sample_products)
        db.commit()
        print("Sample product data successfully seeded.")

    # 2. Seed a default admin user if not present
    admin_user = db.query(models.User).filter(models.User.email == "admin@store.com").first()
    if not admin_user:
        hashed_admin_pwd = auth.hash_password("AdminPass123!")
        admin_user = models.User(
            email="admin@store.com",
            hashed_password=hashed_admin_pwd,
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        # Create cart for admin as well
        admin_cart = models.Cart(user_id=admin_user.id)
        db.add(admin_cart)
        db.commit()
        print("Default admin user created: admin@store.com / AdminPass123!")

# FastAPI lifespan for startup table creation and seeding
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables verified/created in Neon PostgreSQL.")
        db = SessionLocal()
        try:
            seed_initial_data(db)
        finally:
            db.close()
    except Exception as e:
        print(f"Database connection error on startup: {e}")
    yield

app = FastAPI(title="Simple E-Commerce API", lifespan=lifespan)

# Allow React frontend to communicate with FastAPI backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to the Simple E-Commerce API"}

@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint: tests connection to Neon PostgreSQL database."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected to Neon PostgreSQL",
            "tables": ["users", "products", "cart", "cart_items"]
        }
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection failed: {str(err)}"
        )

# ================= AUTHENTICATION ROUTES =================

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    """
    Register a new customer account.
    Creates user record and initializes their empty shopping cart.
    """
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    hashed_pwd = auth.hash_password(user_data.password)

    new_user = models.User(
        email=user_data.email,
        hashed_password=hashed_pwd,
        is_admin=bool(user_data.is_admin)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Initialize user's shopping cart
    user_cart = models.Cart(user_id=new_user.id)
    db.add(user_cart)
    db.commit()

    return new_user

@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return a JWT access token along with is_admin status.
    """
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if not user or not auth.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = auth.create_access_token(data={"sub": str(user.id)})

    return schemas.TokenResponse(
        access_token=access_token,
        token_type="bearer",
        is_admin=bool(user.is_admin)
    )

@app.get("/api/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    """Protected endpoint to test token authentication."""
    return current_user

# ================= PRODUCT ROUTES =================

@app.get("/api/products", response_model=List[schemas.ProductResponse])
def get_products(db: Session = Depends(get_db)):
    """
    View all products in catalog.
    Open to everyone (no login required).
    """
    products = db.query(models.Product).order_by(models.Product.id).all()
    return products

@app.post("/api/products", status_code=status.HTTP_201_CREATED, response_model=schemas.ProductResponse)
def add_product(
    product_data: schemas.ProductCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a new product to the catalog.
    Admin only (checks current_user.is_admin).
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required to add products"
        )

    if product_data.price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be non-negative"
        )

    new_product = models.Product(
        title=product_data.title,
        price=product_data.price,
        stock=product_data.stock if product_data.stock is not None else 10,
        image_url=product_data.image_url,
        description=product_data.description
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product

# ================= CART ROUTES =================

@app.post("/api/cart", status_code=status.HTTP_200_OK)
def add_to_cart(
    item_data: schemas.AddToCartRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a product to the user's cart.
    Validates that total cart quantity does not exceed available stock.
    """
    qty_to_add = item_data.quantity if item_data.quantity and item_data.quantity > 0 else 1

    # 1. Ensure user's cart exists
    cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
    if not cart:
        cart = models.Cart(user_id=current_user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    # 2. Check product existence
    product = db.query(models.Product).filter(models.Product.id == item_data.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # 3. Check stock availability
    if product.stock <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{product.title}' is currently out of stock"
        )

    # 4. Check existing item in cart
    existing_item = (
        db.query(models.CartItem)
        .filter(models.CartItem.cart_id == cart.id, models.CartItem.product_id == product.id)
        .first()
    )

    current_qty = existing_item.quantity if existing_item else 0
    new_total_qty = current_qty + qty_to_add

    # 5. Stock constraint: Do not allow quantity greater than available stock
    if new_total_qty > product.stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot add {qty_to_add} item(s). Requested total ({new_total_qty}) "
                f"exceeds available stock ({product.stock})"
            )
        )

    # 6. Update or insert cart item
    if existing_item:
        existing_item.quantity = new_total_qty
    else:
        new_item = models.CartItem(
            cart_id=cart.id,
            product_id=product.id,
            quantity=qty_to_add
        )
        db.add(new_item)

    db.commit()

    return {
        "message": "Product added to cart",
        "product_id": product.id,
        "quantity": new_total_qty,
        "product_title": product.title
    }

@app.get("/api/cart", response_model=schemas.CartResponse)
def get_cart(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    View all items currently in the logged-in user's cart and calculate total.
    """
    cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
    if not cart:
        return schemas.CartResponse(items=[], total=0.0)

    cart_items = (
        db.query(models.CartItem)
        .filter(models.CartItem.cart_id == cart.id)
        .all()
    )

    items_list = []
    total = 0.0

    for item in cart_items:
        product = item.product
        if product:
            subtotal = round(product.price * item.quantity, 2)
            total += subtotal
            items_list.append(
                schemas.CartItemResponse(
                    id=item.id,
                    product_id=product.id,
                    title=product.title,
                    price=product.price,
                    image_url=product.image_url,
                    quantity=item.quantity,
                    subtotal=subtotal
                )
            )

    return schemas.CartResponse(
        items=items_list,
        total=round(total, 2)
    )

# ================= AGENT ROUTE =================

@app.post("/api/agent/ask", response_model=schemas.AgentAskResponse, status_code=status.HTTP_200_OK)
def ask_store_agent(
    request: schemas.AgentAskRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ask the Store AI agent a question.
    Requires authentication (accepts tokens from both regular users and admins).
    Executes the LangGraph flow with the user's ID and question.
    """
    # 1. Validate input
    if not request or not request.question or not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid question."
        )

    clean_question = request.question.strip()
    if len(clean_question) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question is too long (maximum 1000 characters)."
        )

    # 2. Execute LangGraph agent safely
    try:
        answer = run_store_agent(question=clean_question, user_id=current_user.id, db=db)
    except ValueError as ve:
        err_msg = str(ve).lower()
        if "groq_api_key" in err_msg or "api_key" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI assistant is unavailable because the Groq API key is not configured."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The assistant was unable to process your question at this time."
        )
    except Exception as e:
        err_str = str(e).lower()
        # Rate limit or quota issues
        if any(term in err_str for term in ["rate_limit", "rate limit", "429", "quota", "too many requests"]):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI assistant is temporarily unavailable due to Groq rate limits. Please try again shortly."
            )
        # Authentication or invalid API key
        if any(term in err_str for term in ["invalid_api_key", "unauthorized", "invalid api key"]):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The AI assistant could not be authenticated with Groq. Please check your API key."
            )
        # Model availability
        if any(term in err_str for term in ["model_not_found", "model not available", "not_found"]):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="The Groq AI model is currently unavailable. Please try again later."
            )
        # General safe error - never expose stack trace, secrets, or SQL
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The assistant encountered an error while answering your question. Please try again."
        )

    # 3. Validate answer output
    if not answer or not answer.strip():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The assistant was unable to find an answer. Please try rephrasing your question."
        )

    return schemas.AgentAskResponse(answer=answer)


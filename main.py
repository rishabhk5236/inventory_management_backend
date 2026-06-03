from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Inventory Assessment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Product Endpoints
@app.post("/products/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = db.query(models.Product).filter(models.Product.sku == product.sku).first()
    if db_product:
        raise HTTPException(status_code=400, detail="SKU already registered")
    new_product = models.Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@app.get("/products/", response_model=List[schemas.Product])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Product).offset(skip).limit(limit).all()

@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(models.Product).filter(models.Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
            
        if product.stock > 0:
            raise HTTPException(status_code=400, detail="Cannot delete product while stock is greater than 0")
            
        pending_order = db.query(models.Order).filter(models.Order.product_id == product_id, models.Order.status == "pending").first()
        if pending_order:
            raise HTTPException(status_code=400, detail="Cannot delete product with pending orders")
            
        # Delete any completed/cancelled orders 
        db.query(models.Order).filter(models.Order.product_id == product_id).delete()
        
        db.delete(product)
        db.commit()
        return None
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Customer Endpoints
@app.post("/customers/", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    db_customer = db.query(models.Customer).filter(models.Customer.email == customer.email).first()
    if db_customer:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_customer = models.Customer(**customer.dict())
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer

@app.get("/customers/", response_model=List[schemas.Customer])
def get_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Customer).offset(skip).limit(limit).all()

@app.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    try:
        customer = db.query(models.Customer).filter(models.Customer.id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        db.delete(customer)
        db.commit()
        return None
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete customer with existing orders")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Order Endpoints
@app.post("/orders/", response_model=schemas.Order)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    try:
        
        product = db.query(models.Product).filter(models.Product.id == order.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        customer = db.query(models.Customer).filter(models.Customer.id == order.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        if product.stock < order.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")

        # Reduce stock
        product.stock -= order.quantity
        
        # Create order
        new_order = models.Order(**order.dict())
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        return new_order
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders/", response_model=List[schemas.Order])
def get_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Order).offset(skip).limit(limit).all()

@app.put("/orders/{order_id}/cancel", response_model=schemas.Order)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    try:
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.status == "cancelled":
            raise HTTPException(status_code=400, detail="Order is already cancelled")
            
        # Refill the stock
        product = db.query(models.Product).filter(models.Product.id == order.product_id).first()
        if product:
            product.stock += order.quantity
            
        order.status = "cancelled"
        db.commit()
        db.refresh(order)
        return order
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/orders/{order_id}/complete", response_model=schemas.Order)
def complete_order(order_id: int, db: Session = Depends(get_db)):
    try:
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.status == "cancelled":
            raise HTTPException(status_code=400, detail="Cannot complete a cancelled order")
        
        if order.status == "completed":
            raise HTTPException(status_code=400, detail="Order is already completed")
            
        order.status = "completed"
        db.commit()
        db.refresh(order)
        return order
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

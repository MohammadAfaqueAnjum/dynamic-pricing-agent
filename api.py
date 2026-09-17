from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database.connection import get_db, Base, engine
from database.models import Product, CompetitorTracker, PriceLog
from graph import pricing_app


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Competitive Intelligence & Dynamic Pricing Agent API",
    version="1.0.0",
    description="Agentic system for e-commerce competitor scraping, margin enforcement, and dynamic pricing."
)

# Mount static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic Schemas for API Requests & Responses
class ProductResponse(BaseModel):
    id: int
    sku: str
    title: str
    base_cost: float
    current_price: float
    min_margin_percent: float
    stock_count: int

    class Config:
        from_attributes = True

class PriceLogResponse(BaseModel):
    id: int
    product_id: int
    old_price: float
    suggested_price: float
    final_price: float
    reasoning: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class PriceApprovalRequest(BaseModel):
    override_price: Optional[float] = None
    action: str # "APPROVE" or "REJECT"

# --- Endpoints ---

@app.get("/")
def serve_dashboard():
    """Serves the frontend dashboard HTML."""
    return FileResponse("static/index.html")

@app.get("/products", response_model=List[ProductResponse])
def list_products(db: Session = Depends(get_db)):
    """Fetch all tracked catalog items."""
    return db.query(Product).all()

@app.post("/agent/run/{product_id}")
def trigger_agent_for_product(product_id: int, db: Session = Depends(get_db)):
    """Triggers the complete LangGraph agent cycle for a given product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    tracker = db.query(CompetitorTracker).filter(CompetitorTracker.product_id == product.id).first()
    if not tracker:
        raise HTTPException(status_code=400, detail="No competitor tracker configured for this product")

    initial_state = {
        "product_id": product.id,
        "sku": product.sku,
        "title": product.title,
        "base_cost": product.base_cost,
        "current_price": product.current_price,
        "min_margin_percent": product.min_margin_percent,
        "competitor_url": tracker.competitor_url,
        "competitor_name": tracker.competitor_name,
        "scraped_title": None,
        "scraped_price": None,
        "scraped_in_stock": None,
        "sku_match_score": None,
        "is_valid_match": None,
        "suggested_price": None,
        "strategy_reasoning": None,
        "requires_human_approval": False,
        "status": "INITIALIZED"
    }

    # Execute LangGraph Pipeline
    final_output = pricing_app.invoke(initial_state)

    # Determine final applied price
    is_auto = not final_output["requires_human_approval"]
    applied_price = final_output["suggested_price"] if is_auto else product.current_price

    if is_auto:
        product.current_price = applied_price
        tracker.last_scraped_price = final_output["scraped_price"]
        tracker.in_stock = final_output["scraped_in_stock"]

    # Log the decision
    log = PriceLog(
        product_id=product.id,
        old_price=final_output["current_price"],
        suggested_price=final_output["suggested_price"],
        final_price=applied_price,
        reasoning=final_output["strategy_reasoning"],
        status=final_output["status"]
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return {
        "message": "Pricing evaluation cycle complete",
        "result": final_output,
        "log_id": log.id
    }

@app.get("/logs/{product_id}", response_model=List[PriceLogResponse])
def get_price_history(product_id: int, db: Session = Depends(get_db)):
    """Fetch audit history logs and agent reasoning for a product."""
    return db.query(PriceLog).filter(PriceLog.product_id == product_id).order_by(PriceLog.created_at.desc()).all()

@app.post("/agent/approval/{log_id}")
def human_in_the_loop_decision(log_id: int, decision: PriceApprovalRequest, db: Session = Depends(get_db)):
    """Human-in-the-loop endpoint to approve, reject, or manually override a flagged price change."""
    log = db.query(PriceLog).filter(PriceLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")

    product = db.query(Product).filter(Product.id == log.product_id).first()

    if decision.action == "APPROVE":
        final_price = decision.override_price if decision.override_price else log.suggested_price
        product.current_price = final_price
        log.final_price = final_price
        log.status = "APPROVED_BY_ADMIN"
    else:
        log.status = "REJECTED_BY_ADMIN"

    db.commit()
    return {"message": f"Action {decision.action} processed successfully.", "current_product_price": product.current_price}
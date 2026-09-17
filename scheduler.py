from apscheduler.schedulers.background import BackgroundScheduler
from database.connection import SessionLocal
from database.models import Product, CompetitorTracker, PriceLog
from graph import pricing_app

def run_catalog_repricing_job():
    """Scans all products with active competitor trackers and executes repricing."""
    db = SessionLocal()
    products = db.query(Product).all()
    print(f"\n[Scheduler] Running autonomous pricing cycle for {len(products)} products...")

    for product in products:
        tracker = db.query(CompetitorTracker).filter(CompetitorTracker.product_id == product.id).first()
        if not tracker:
            continue

        state_input = {
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
            "status": "SCHEDULED_RUN"
        }

        try:
            result = pricing_app.invoke(state_input)
            is_auto = not result["requires_human_approval"]
            applied_price = result["suggested_price"] if is_auto else product.current_price

            if is_auto:
                product.current_price = applied_price
                tracker.last_scraped_price = result["scraped_price"]
                tracker.in_stock = result["scraped_in_stock"]

            log = PriceLog(
                product_id=product.id,
                old_price=result["current_price"],
                suggested_price=result["suggested_price"],
                final_price=applied_price,
                reasoning=result["strategy_reasoning"],
                status=result["status"]
            )
            db.add(log)
            db.commit()
            print(f"   Processed SKU {product.sku}: Old=${result['current_price']} -> New=${applied_price} [{result['status']}]")
        except Exception as e:
            db.rollback()
            print(f"   Error processing product {product.sku}: {e}")

    db.close()

scheduler = BackgroundScheduler()
# Run every 6 hours (or adjust interval as needed)
scheduler.add_job(run_catalog_repricing_job, 'interval', minutes=30)

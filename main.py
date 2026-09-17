from database.connection import SessionLocal
from database.models import Product, CompetitorTracker, PriceLog
from graph import pricing_app

def run_agent_for_product():
    db = SessionLocal()
    product = db.query(Product).first()
    tracker = db.query(CompetitorTracker).filter(CompetitorTracker.product_id == product.id).first()

    if not product or not tracker:
        print("No product or tracker found in database.")
        return

    initial_state = {
        "product_id": product.id,
        "sku": product.sku,
        "title": product.title,
        "base_cost": product.base_cost,
        "current_price": product.current_price,
        "min_margin_percent": product.min_margin_percent,
        "competitor_url": tracker.competitor_url,
        "competitor_name": tracker.competitor_name,
        "scraped_price": None,
        "scraped_in_stock": None,
        "suggested_price": None,
        "strategy_reasoning": None,
        "requires_human_approval": False,
        "status": "INITIALIZED"
    }

    print(f"\n--- Running Pricing Agent for: {product.title} ---")
    final_output = pricing_app.invoke(initial_state)

    print("\n--- Agent Execution Completed ---")
    print(f"Old Price: ${final_output['current_price']}")
    print(f"Scraped Competitor Price: ${final_output['scraped_price']}")
    print(f"Suggested Price: ${final_output['suggested_price']}")
    print(f"Reasoning: {final_output['strategy_reasoning']}")
    print(f"Human Approval Required: {final_output['requires_human_approval']}")
    print(f"Status: {final_output['status']}")

    # Save to PriceLog
    log = PriceLog(
        product_id=product.id,
        old_price=final_output["current_price"],
        suggested_price=final_output["suggested_price"],
        final_price=final_output["suggested_price"] if not final_output["requires_human_approval"] else final_output["current_price"],
        reasoning=final_output["strategy_reasoning"],
        status=final_output["status"]
    )
    db.add(log)
    db.commit()
    db.close()

if __name__ == "__main__":
    run_agent_for_product()

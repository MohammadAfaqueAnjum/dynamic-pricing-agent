from database.connection import Base, engine, SessionLocal
from database.models import Product, CompetitorTracker

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Avoid duplicate seeds
    if db.query(Product).first():
        print("Database already seeded.")
        db.close()
        return

    # Seed an example product
    sample_product = Product(
        sku="B001-LIGHT-ATTIC",
        title="A Light in the Attic",
        base_cost=35.00,
        current_price=51.77,
        min_margin_percent=0.20, # Must not sell below $42.00 (35 * 1.20)
        stock_count=15
    )
    db.add(sample_product)
    db.commit()
    db.refresh(sample_product)

    # Competitor link pointing to the test site
    tracker = CompetitorTracker(
        product_id=sample_product.id,
        competitor_name="BooksToScrape Corp",
        competitor_url="https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        last_scraped_price=51.77,
        in_stock=True
    )
    db.add(tracker)
    db.commit()
    db.close()
    print("Database tables created and sample data seeded successfully.")

if __name__ == "__main__":
    init_db()

import asyncio
from playwright.async_api import async_playwright
from pydantic import BaseModel, Field

class ScrapedProduct(BaseModel):
    title: str = Field(description="Product name")
    price: float = Field(description="Current product price")
    in_stock: bool = Field(description="Availability flag")

async def test_scrape():
    async with async_playwright() as p:
        # Launch Chromium headless browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Target demo store URL
        target_url = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
        print(f"Connecting to: {target_url}")
        await page.goto(target_url)
        
        # Locate HTML elements
        title_element = await page.query_selector("h1")
        price_element = await page.query_selector(".price_color")
        stock_element = await page.query_selector(".availability")
        
        raw_title = await title_element.inner_text() if title_element else "N/A"
        raw_price = await price_element.inner_text() if price_element else "£0.0"
        raw_stock = await stock_element.inner_text() if stock_element else ""
        
        # Clean extracted price string to a float
        clean_price = float(raw_price.replace("£", "").replace("$", "").strip())
        is_in_stock = "In stock" in raw_stock
        
        # Validate data structure using Pydantic
        item = ScrapedProduct(
            title=raw_title.strip(),
            price=clean_price,
            in_stock=is_in_stock
        )
        
        print("\n=== Scraped & Validated Output ===")
        print(item.model_dump_json(indent=2))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_scrape())

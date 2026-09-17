from typing import TypedDict, Optional

class PricingAgentState(TypedDict):
    product_id: int
    sku: str
    title: str
    base_cost: float
    current_price: float
    min_margin_percent: float
    competitor_url: str
    competitor_name: str
    scraped_title: Optional[str]
    scraped_price: Optional[float]
    scraped_in_stock: Optional[bool]
    sku_match_score: Optional[float]
    is_valid_match: Optional[bool]
    suggested_price: Optional[float]
    strategy_reasoning: Optional[str]
    requires_human_approval: bool
    status: str

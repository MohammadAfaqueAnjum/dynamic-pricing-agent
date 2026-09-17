from agents.state import PricingAgentState
from typing import Dict, Any
from agents.state import PricingAgentState

def pricing_strategy_node(state: PricingAgentState) -> Dict[str, Any]:
    base_cost = state["base_cost"]
    min_margin = state["min_margin_percent"]
    current_price = state["current_price"]
    comp_price = state.get("scraped_price")
    comp_in_stock = state.get("scraped_in_stock", True)

    floor_price = round(base_cost * (1 + min_margin), 2)
    suggested_price = current_price
    reasoning = ""

    # Rule 1: Competitor out of stock -> Opportunity to capture margin (+5%)
    if not comp_in_stock:
        suggested_price = round(current_price * 1.05, 2)
        reasoning = f"Competitor is OUT OF STOCK. Increased price by 5% to maximize margin."

    # Rule 2: Competitor in stock and cheaper -> Undercut by $0.50 if above floor
    elif comp_price and comp_price < current_price:
        target_price = round(comp_price - 0.50, 2)
        if target_price >= floor_price:
            suggested_price = target_price
            reasoning = f"Undercut competitor price (${comp_price}) by $0.50. New price: ${suggested_price}."
        else:
            suggested_price = floor_price
            reasoning = f"Competitor price (${comp_price}) is too aggressive. Set to absolute margin floor (${floor_price})."

    # Rule 3: Competitor in stock and higher -> Match or hold
    elif comp_price and comp_price >= current_price:
        suggested_price = current_price
        reasoning = f"Current price (${current_price}) is already competitive against competitor (${comp_price})."

    # Safety Check: Flag for human review if price changes by more than 15%
    price_delta_percent = abs(suggested_price - current_price) / current_price
    requires_approval = price_delta_percent > 0.15

    return {
        "suggested_price": suggested_price,
        "strategy_reasoning": reasoning,
        "requires_human_approval": requires_approval,
        "status": "PENDING_APPROVAL" if requires_approval else "AUTO_APPLIED"
    }

import os
from typing import Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

load_dotenv()


# Schema for extracted competitor product data
class ExtractedCompetitorData(BaseModel):
    product_title: Optional[str] = Field(
        default=None,
        description="Name or title of the product found on the page",
    )
    price: Optional[float] = Field(
        default=None,
        description="Current selling price as a float (exclude currency symbols)",
    )
    currency: Optional[str] = Field(
        default=None, description="Currency code like USD, EUR, GBP, or INR"
    )
    in_stock: bool = Field(
        default=True,
        description="True if the item is in stock/available to buy, False if sold out or unavailable",
    )
    stock_count: Optional[int] = Field(
        default=None,
        description="Exact remaining inventory units if explicitly mentioned",
    )


def clean_html(raw_html: str) -> str:
    """Removes scripts, styles, svg, and metadata to reduce LLM token overhead."""
    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(
        ["script", "style", "svg", "noscript", "header", "footer", "nav"]
    ):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    # Take the first 4,000 characters to keep within fast context limits
    return text[:4000]


def extract_pricing_with_llm(
    cleaned_text: str, expected_title: str
) -> ExtractedCompetitorData:
    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash")
    structured_llm = llm.with_structured_output(
        ExtractedCompetitorData, method="json_schema"
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an expert e-commerce data extraction engine. Extract structured product pricing and stock availability from the provided raw web page text.",
        ),
        (
            "user",
            "Target product we are matching: '{expected_title}'\n\nPage Content:\n{page_content}",
        ),
    ])

    chain = prompt | structured_llm
    result: ExtractedCompetitorData = chain.invoke({
        "expected_title": expected_title,
        "page_content": cleaned_text,
    })
    return result

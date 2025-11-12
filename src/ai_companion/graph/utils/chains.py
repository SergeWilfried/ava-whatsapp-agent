from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from typing import List, Optional

from ai_companion.core.prompts import get_character_card_prompt, ROUTER_PROMPT, ORDER_PROCESSING_PROMPT, MENU_DISPLAY_PROMPT
from ai_companion.graph.utils.helpers import AsteriskRemovalParser, get_chat_model
from ai_companion.settings import settings


class RouterResponse(BaseModel):
    response_type: str = Field(
        description="The response type to give to the user. It must be one of: 'conversation', 'order', 'menu', 'image' or 'audio'"
    )


class OrderItem(BaseModel):
    name: str = Field(description="Name of the menu item")
    quantity: int = Field(description="Quantity ordered")
    price: float = Field(description="Price per item")


class OrderProcessingResponse(BaseModel):
    items: List[OrderItem] = Field(description="List of items in the order")
    subtotal: float = Field(description="Subtotal before tax")
    tax: float = Field(description="Tax amount")
    total: float = Field(description="Total amount including tax")
    confirmation_message: str = Field(description="Friendly confirmation message for the customer")


def get_router_chain():
    model = get_chat_model(temperature=0.3).with_structured_output(RouterResponse)

    prompt = ChatPromptTemplate.from_messages(
        [("system", ROUTER_PROMPT), MessagesPlaceholder(variable_name="messages")]
    )

    return prompt | model


def get_character_response_chain(summary: str = ""):
    model = get_chat_model()
    system_message = get_character_card_prompt(settings.LANGUAGE)

    if summary:
        system_message += f"\n\nSummary of conversation earlier with the customer: {summary}"

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    return prompt | model | AsteriskRemovalParser()


def get_order_processing_chain():
    """Get chain for processing customer orders."""
    model = get_chat_model(temperature=0.3).with_structured_output(OrderProcessingResponse)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", ORDER_PROCESSING_PROMPT),
            MessagesPlaceholder(variable_name="messages")
        ]
    )

    return prompt | model


def get_menu_display_chain():
    """Get chain for displaying menu items."""
    model = get_chat_model()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", MENU_DISPLAY_PROMPT),
            MessagesPlaceholder(variable_name="messages")
        ]
    )

    return prompt | model | AsteriskRemovalParser()

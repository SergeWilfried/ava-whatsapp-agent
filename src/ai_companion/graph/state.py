from typing import Dict, List, Optional
from langgraph.graph import MessagesState


class AICompanionState(MessagesState):
    """State class for the AI Companion workflow.

    Extends MessagesState to track conversation history and maintains the last message received.

    Attributes:
        last_message (AnyMessage): The most recent message in the conversation, can be any valid
            LangChain message type (HumanMessage, AIMessage, etc.)
        workflow (str): The current workflow. Can be "conversation", "order", "menu", "image", or "audio".
        audio_buffer (bytes): The audio buffer to be used for speech-to-text conversion.
        current_activity (str): The current restaurant status and activity.
        memory_context (str): The context of the memories to be injected into the character card.
        use_interactive_menu (bool): Flag to send interactive menu component instead of plain text.
        interactive_component (dict): Structured data for WhatsApp interactive components.

        # Shopping cart fields
        shopping_cart (dict): Shopping cart data (serialized ShoppingCart)
        order_stage (str): Current ordering stage (browsing, selecting, customizing, checkout, etc.)
        current_item (dict): Item currently being customized
        pending_customization (dict): Pending customization data (size, extras)
        delivery_method (str): Chosen delivery method (delivery, pickup, dine_in)
        payment_method (str): Chosen payment method
        active_order_id (str): ID of the currently active order
        delivery_address (str): Delivery address for delivery orders
        customer_name (str): Customer name for orders
        customer_phone (str): Customer phone number (required for all order types)

        # Location fields
        user_location (dict): User's shared location with latitude, longitude, address, name
        awaiting_location (bool): Flag indicating system is waiting for user to share location

        # Delivery zone fields (for mileage-based delivery)
        delivery_zone (dict): Selected delivery zone information from API
        delivery_distance (float): Distance in km from restaurant to delivery location
        api_delivery_cost (float): Delivery cost calculated by API based on zone
        zone_validated (bool): Whether delivery zone has been validated
        zone_validation_error (str): Error message if zone validation failed

        # User information
        user_phone (str): User's WhatsApp phone number
    """

    summary: str
    workflow: str
    audio_buffer: bytes
    image_path: str
    current_activity: str
    apply_activity: bool
    memory_context: str
    use_interactive_menu: bool
    interactive_component: dict

    # Shopping cart state
    shopping_cart: Optional[Dict]
    order_stage: str
    current_item: Optional[Dict]
    pending_customization: Optional[Dict]
    delivery_method: Optional[str]
    payment_method: Optional[str]
    active_order_id: Optional[str]

    # Location state
    user_location: Optional[Dict]
    awaiting_location: bool

    # Delivery zone state (mileage-based delivery)
    delivery_zone: Optional[Dict]
    delivery_distance: Optional[float]
    api_delivery_cost: Optional[float]
    zone_validated: bool
    zone_validation_error: Optional[str]

    # User information
    user_phone: Optional[str]

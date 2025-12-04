import logging
import os
from io import BytesIO
from typing import Dict, Optional

import httpx
from fastapi import APIRouter, Request, Response
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ai_companion.graph import graph_builder
from ai_companion.modules.image import ImageToText
from ai_companion.modules.speech import SpeechToText, TextToSpeech
from ai_companion.settings import settings
# Use optimized business service for production (500+ concurrent requests)
from ai_companion.services.business_service_optimized import get_optimized_business_service
# Cart integration
from ai_companion.interfaces.whatsapp.cart_handler import process_cart_interaction
from ai_companion.graph import cart_nodes
from ai_companion.interfaces.whatsapp.interactive_components_v2 import (
    create_category_selection_list,
    create_button_component,
)
# Legacy imports for backward compatibility (will be migrated)
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_menu_list_from_restaurant_menu,
    create_quick_actions_buttons,
)
from ai_companion.interfaces.whatsapp.carousel_components_v2 import (
    create_product_carousel,
)
# Legacy import (will be migrated)
from ai_companion.interfaces.whatsapp.carousel_components import (
    create_restaurant_menu_carousel,
)
from ai_companion.interfaces.whatsapp.image_utils import (
    prepare_menu_items_for_carousel,
)
from ai_companion.core.schedules import RESTAURANT_MENU
from ai_companion.modules.cart import OrderStage
from ai_companion.services.menu_adapter import MenuAdapter

logger = logging.getLogger(__name__)

# Global module instances
speech_to_text = SpeechToText()
text_to_speech = TextToSpeech()
image_to_text = ImageToText()

# Router for WhatsApp respo
whatsapp_router = APIRouter()

# Fallback WhatsApp API credentials (for backwards compatibility)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")


@whatsapp_router.api_route("/whatsapp_response", methods=["GET", "POST"])
async def whatsapp_handler(request: Request) -> Response:
    """Handles incoming messages and status updates from the WhatsApp Cloud API."""

    if request.method == "GET":
        params = request.query_params
        if params.get("hub.verify_token") == os.getenv("WHATSAPP_VERIFY_TOKEN"):
            return Response(content=params.get("hub.challenge"), status_code=200)
        return Response(content="Verification token mismatch", status_code=403)

    try:
        data = await request.json()
        change_value = data["entry"][0]["changes"][0]["value"]
        if "messages" in change_value:
            message = change_value["messages"][0]
            from_number = message["from"]

            # Extract phone number ID from metadata (this is the business phone number ID)
            phone_number_id = change_value.get("metadata", {}).get("phone_number_id")

            if not phone_number_id:
                logger.error("No phone_number_id found in webhook metadata")
                return Response(content="Missing phone_number_id in webhook", status_code=400)

            # Check if this is the special phone number ID that uses environment variables
            if phone_number_id == "709970042210245":
                whatsapp_token = WHATSAPP_TOKEN
                business_name = "Default Business (Environment Variables)"
                business_subdomain = "default"
                logger.info(f"Using environment variables for phone_number_id: {phone_number_id}")
            else:
                # Lookup business credentials by phone number ID (using optimized service)
                business_service = await get_optimized_business_service()
                business = await business_service.get_business_by_phone_number_id(phone_number_id)

                if not business:
                    logger.error(f"No business found for phone_number_id: {phone_number_id}")
                    return Response(content="Business not found for this phone number", status_code=404)

                # Extract business-specific credentials
                whatsapp_token = business.get("decryptedAccessToken")
                business_name = business.get("name", "Unknown Business")
                business_subdomain = business.get("subDomain", "unknown")

                if not whatsapp_token:
                    logger.error(f"No valid WhatsApp token for business: {business_name}")
                    return Response(content="Invalid business credentials", status_code=500)

            logger.info(f"Processing message for business: {business_name} (subdomain: {business_subdomain})")

            # Mark message as read and show typing indicator
            # This provides good UX while we process the message
            message_id = message.get("id")
            if message_id:
                await mark_message_read_and_show_typing(
                    message_id=message_id,
                    phone_number_id=phone_number_id,
                    whatsapp_token=whatsapp_token
                )

            # Get user message and handle different message types
            content = ""
            if message["type"] == "audio":
                content = await process_audio_message(message, whatsapp_token)
            elif message["type"] == "image":
                # Get image caption if any
                content = message.get("image", {}).get("caption", "")
                # Download and analyze image
                image_bytes = await download_media(message["image"]["id"], whatsapp_token)
                try:
                    description = await image_to_text.analyze_image(
                        image_bytes,
                        "Please describe what you see in this image in the context of our conversation.",
                    )
                    content += f"\n[Image Analysis: {description}]"
                except Exception as e:
                    logger.warning(f"Failed to analyze image: {e}")
            elif message["type"] == "interactive":
                # Handle button or list reply with cart routing
                interactive_data = message.get("interactive", {})
                interaction_type = interactive_data.get("type")  # "button_reply" or "list_reply"

                logger.info(f"Processing interactive message: type={interaction_type}")

                # Use business subdomain + user number as session ID for multi-tenancy
                session_id = f"{business_subdomain}:{from_number}"

                # Get current state BEFORE processing (important for cart context)
                async with AsyncSqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH) as short_term_memory:
                    graph = graph_builder.compile(checkpointer=short_term_memory)

                    # Get current state
                    output_state = await graph.aget_state(config={"configurable": {"thread_id": session_id}})
                    current_state_dict = dict(output_state.values) if output_state and output_state.values else {}

                    # Process cart interaction
                    node_name, state_updates, text_repr = process_cart_interaction(
                        interaction_type,
                        interactive_data,
                        current_state_dict
                    )

                    logger.info(f"Cart handler routed to: {node_name}")

                    # Handle cart-specific nodes
                    if node_name == "show_menu":
                        # Show quick actions instead of direct menu
                        interactive_comp = create_quick_actions_buttons()
                        success = await send_response(
                            from_number,
                            "Welcome! 👋 How can I help you today?",
                            "interactive_button",
                            phone_number_id=phone_number_id,
                            whatsapp_token=whatsapp_token,
                            interactive_component=interactive_comp
                        )
                        return Response(content="Quick actions sent", status_code=200)

                    elif node_name == "view_menu":
                        # User selected "View Menu" - show category selection
                        # Fetch categories from API (or use mock data as fallback)
                        menu_adapter = MenuAdapter()
                        try:
                            menu_structure = await menu_adapter.get_menu_structure()
                            categories = menu_structure.get("categories", [])
                            logger.info(f"Fetched {len(categories)} categories for menu display")
                            interactive_comp = create_category_selection_list(categories)
                        except Exception as e:
                            logger.error(f"Error fetching menu structure: {e}, using mock data")
                            interactive_comp = create_category_selection_list()

                        success = await send_response(
                            from_number,
                            "Browse our menu by category:",
                            "interactive_list",
                            phone_number_id=phone_number_id,
                            whatsapp_token=whatsapp_token,
                            interactive_component=interactive_comp
                        )
                        return Response(content="Category list sent", status_code=200)

                    elif node_name == "view_category_carousel":
                        # User selected a category - show items as carousel with images
                        # Handle both V2 (selected_category_id) and legacy (selected_category)
                        category_id = state_updates.get("selected_category_id")
                        category = state_updates.get("selected_category", "pizzas")

                        # V2 pattern: "cat_pizzas" -> extract "pizzas"
                        if category_id and category_id.startswith("cat_"):
                            category = category_id.replace("cat_", "")
                            logger.info(f"V2 category selected: {category_id} -> {category}")

                        if category in RESTAURANT_MENU:
                            # Prepare items with automatic images and WhatsApp deep links
                            # Using hardcoded WhatsApp number for deep links
                            menu_items = prepare_menu_items_for_carousel(
                                RESTAURANT_MENU[category],
                                category,
                                whatsapp_number="15551525021",  # Hardcoded phone number for carousel deep links
                                use_whatsapp_deep_link=True  # Enable deep links
                            )

                            # Create beautiful carousel with images
                            carousel = create_restaurant_menu_carousel(
                                menu_items,
                                body_text=f"Check out our {category}! 😋 Swipe to browse",
                                button_text="View"
                            )

                            # Send carousel
                            success = await send_response(
                                from_number,
                                "",  # Body text is in carousel
                                "interactive_carousel",
                                phone_number_id=phone_number_id,
                                whatsapp_token=whatsapp_token,
                                interactive_component=carousel
                            )

                            # Update state with category
                            await graph.aupdate_state(
                                config={"configurable": {"thread_id": session_id}},
                                values={"selected_category": category}
                            )

                            # Now send follow-up buttons for cart actions
                            buttons = create_button_component(
                                f"Which {category.rstrip('s')} would you like to add to your cart?",
                                [
                                    {"id": f"add_{category}_0", "title": f"Add {menu_items[0]['name'][:15]}"} if len(menu_items) > 0 else {"id": "back", "title": "Back"},
                                    {"id": f"add_{category}_1", "title": f"Add {menu_items[1]['name'][:15]}"} if len(menu_items) > 1 else {"id": "view_cart", "title": "View Cart"},
                                    {"id": "view_cart", "title": "🛒 View Cart"}
                                ][:3]  # Max 3 buttons
                            )

                            # Send action buttons after a brief moment
                            await send_response(
                                from_number,
                                "Select an item to add to your cart:",
                                "interactive_button",
                                phone_number_id=phone_number_id,
                                whatsapp_token=whatsapp_token,
                                interactive_component=buttons
                            )

                            return Response(content="Category carousel sent", status_code=200)
                        else:
                            # Category not found, send error
                            await send_response(
                                from_number,
                                "Sorry, that category is not available.",
                                "text",
                                phone_number_id=phone_number_id,
                                whatsapp_token=whatsapp_token
                            )
                            return Response(content="Invalid category", status_code=200)

                    elif node_name == "add_to_cart":
                        # Update state with selected item
                        current_state_dict.update(state_updates)
                        result = await cart_nodes.add_to_cart_node(current_state_dict)

                        # Persist state updates back to graph
                        await graph.aupdate_state(
                            config={"configurable": {"thread_id": session_id}},
                            values=result
                        )

                        # Send response (messages is a single AIMessage object, not a list)
                        message_obj = result.get("messages")
                        response_message = message_obj.content if message_obj else "Added to cart!"
                        interactive_comp = result.get("interactive_component")

                        if interactive_comp:
                            msg_type = "interactive_button" if interactive_comp.get("type") == "button" else "interactive_list"
                            success = await send_response(
                                from_number, response_message, msg_type,
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                                interactive_component=interactive_comp
                            )
                        else:
                            success = await send_response(
                                from_number, response_message, "text",
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token
                            )

                        return Response(content="Item added", status_code=200)

                    elif node_name == "view_cart":
                        result = await cart_nodes.view_cart_node(current_state_dict)

                        # Persist state updates back to graph
                        await graph.aupdate_state(
                            config={"configurable": {"thread_id": session_id}},
                            values=result
                        )

                        message_obj = result.get("messages")
                        response_message = message_obj.content if message_obj else "Your cart"
                        interactive_comp = result.get("interactive_component")

                        if interactive_comp:
                            success = await send_response(
                                from_number, response_message, "interactive_button",
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                                interactive_component=interactive_comp
                            )
                        else:
                            success = await send_response(
                                from_number, response_message, "text",
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token
                            )

                        return Response(content="Cart viewed", status_code=200)

                    elif node_name == "checkout":
                        result = await cart_nodes.checkout_node(current_state_dict)

                        # Persist state updates back to graph
                        await graph.aupdate_state(
                            config={"configurable": {"thread_id": session_id}},
                            values=result
                        )

                        message_obj = result.get("messages")
                        response_message = message_obj.content if message_obj else "Checkout"
                        interactive_comp = result.get("interactive_component")

                        if interactive_comp:
                            success = await send_response(
                                from_number, response_message, "interactive_button",
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                                interactive_component=interactive_comp
                            )
                        else:
                            success = await send_response(
                                from_number, response_message, "text",
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token
                            )

                        return Response(content="Checkout started", status_code=200)

                    elif node_name == "handle_size":
                        current_state_dict.update(state_updates)
                        result = await cart_nodes.handle_size_selection_node(current_state_dict)

                        # Persist state updates back to graph
                        await graph.aupdate_state(
                            config={"configurable": {"thread_id": session_id}},
                            values=result
                        )

                        message_obj = result.get("messages")
                        response_message = message_obj.content if message_obj else "Size selected"
                        interactive_comp = result.get("interactive_component")

                        if interactive_comp:
                            msg_type = "interactive_button" if interactive_comp.get("type") == "button" else "interactive_list"
                            success = await send_response(
                                from_number, response_message, msg_type,
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                                interactive_component=interactive_comp
                            )
                        else:
                            success = await send_response(
                                from_number, response_message, "text",
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token
                            )

                        return Response(content="Size selected", status_code=200)

                    elif node_name == "handle_extras":
                        current_state_dict.update(state_updates)
                        result = await cart_nodes.handle_extras_selection_node(current_state_dict)

                        # Persist state updates back to graph
                        await graph.aupdate_state(
                            config={"configurable": {"thread_id": session_id}},
                            values=result
                        )

                        message_obj = result.get("messages")
                        response_message = message_obj.content if message_obj else "Extra added"
                        interactive_comp = result.get("interactive_component")

                        if interactive_comp:
                            msg_type = "interactive_button" if interactive_comp.get("type") == "button" else "interactive_list"
                            success = await send_response(
                                from_number, response_message, msg_type,
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                                interactive_component=interactive_comp
                            )
                        else:
                            success = await send_response(
                                from_number, response_message, "text",
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token
                            )

                        return Response(content="Extra added", status_code=200)

                    elif node_name == "handle_delivery_method":
                        current_state_dict.update(state_updates)
                        result = await cart_nodes.handle_delivery_method_node(current_state_dict)

                        # Persist state updates back to graph
                        await graph.aupdate_state(
                            config={"configurable": {"thread_id": session_id}},
                            values=result
                        )

                        message_obj = result.get("messages")
                        response_message = message_obj.content if message_obj else "Delivery selected"
                        interactive_comp = result.get("interactive_component")

                        if interactive_comp:
                            msg_type = "interactive_list"
                            success = await send_response(
                                from_number, response_message, msg_type,
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                                interactive_component=interactive_comp
                            )
                        else:
                            success = await send_response(
                                from_number, response_message, "text",
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token
                            )

                        return Response(content="Delivery method selected", status_code=200)

                    elif node_name == "handle_payment_method":
                        current_state_dict.update(state_updates)
                        result = await cart_nodes.handle_payment_method_node(current_state_dict)

                        # Persist state updates back to graph
                        await graph.aupdate_state(
                            config={"configurable": {"thread_id": session_id}},
                            values=result
                        )

                        message_obj = result.get("messages")
                        response_message = message_obj.content if message_obj else "Payment selected"
                        interactive_comp = result.get("interactive_component")

                        if interactive_comp:
                            logger.info(f"Sending order confirmation component: {interactive_comp.get('type')}")
                            success = await send_response(
                                from_number, response_message, "interactive_button",
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                                interactive_component=interactive_comp
                            )
                            if not success:
                                logger.error("Failed to send order confirmation interactive message")
                        else:
                            success = await send_response(
                                from_number, response_message, "text",
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token
                            )

                        return Response(content="Payment method selected", status_code=200)

                    elif node_name == "confirm_order":
                        result = await cart_nodes.confirm_order_node(current_state_dict)

                        # Persist state updates back to graph
                        await graph.aupdate_state(
                            config={"configurable": {"thread_id": session_id}},
                            values=result
                        )

                        message_obj = result.get("messages")
                        response_message = message_obj.content if message_obj else "Order confirmed!"
                        interactive_comp = result.get("interactive_component")

                        if interactive_comp:
                            success = await send_response(
                                from_number, response_message, "interactive_button",
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                                interactive_component=interactive_comp
                            )
                        else:
                            success = await send_response(
                                from_number, response_message, "text",
                                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token
                            )

                        return Response(content="Order confirmed", status_code=200)

                    else:
                        # Not a cart interaction or fallback to conversation
                        # Use text representation for conversation flow
                        content = text_repr

                        # Continue with normal graph processing below...
                        await graph.ainvoke(
                            {"messages": [HumanMessage(content=content)]},
                            {"configurable": {"thread_id": session_id}},
                        )

                        # Get the workflow type and response from the state
                        output_state = await graph.aget_state(config={"configurable": {"thread_id": session_id}})

                        workflow = output_state.values.get("workflow", "conversation")
                        response_message = output_state.values["messages"][-1].content
                        use_interactive_menu = output_state.values.get("use_interactive_menu", False)

            elif message["type"] == "location":
                # User shared their location
                from .location_components import format_location_for_display
                from ai_companion.interfaces.whatsapp.interactive_components import create_payment_method_list

                location_data = message.get("location", {})
                latitude = location_data.get("latitude")
                longitude = location_data.get("longitude")
                address = location_data.get("address", "")
                name = location_data.get("name", "")

                logger.info(f"Received location from {from_number}: lat={latitude}, long={longitude}, name={name}")

                # Store location in state for cart/delivery processing
                session_id = f"{business_subdomain}:{from_number}"

                async with AsyncSqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH) as short_term_memory:
                    graph = graph_builder.compile(checkpointer=short_term_memory)

                    # Get current state to check order stage
                    output_state = await graph.aget_state(config={"configurable": {"thread_id": session_id}})
                    current_state_dict = dict(output_state.values) if output_state and output_state.values else {}
                    order_stage = current_state_dict.get("order_stage", "")

                    # Update state with location data
                    await graph.aupdate_state(
                        config={"configurable": {"thread_id": session_id}},
                        values={
                            "user_location": {
                                "latitude": latitude,
                                "longitude": longitude,
                                "address": address,
                                "name": name
                            },
                            "awaiting_location": False
                        }
                    )

                    # If in checkout flow waiting for location, proceed to payment
                    if order_stage == OrderStage.AWAITING_LOCATION.value:
                        logger.info("Location received during checkout, proceeding to payment")

                        # Format location for confirmation message
                        location_display = format_location_for_display(
                            latitude=latitude,
                            longitude=longitude,
                            name=name,
                            address=address
                        )

                        # Ask for payment method
                        interactive_comp = create_payment_method_list()

                        success = await send_response(
                            from_number,
                            f"Great! We'll deliver to: {location_display}\n\nHow would you like to pay?",
                            "interactive_list",
                            phone_number_id=phone_number_id,
                            whatsapp_token=whatsapp_token,
                            interactive_component=interactive_comp
                        )

                        # Update order stage to payment
                        await graph.aupdate_state(
                            config={"configurable": {"thread_id": session_id}},
                            values={"order_stage": OrderStage.PAYMENT.value}
                        )

                        return Response(content="Location received, payment requested", status_code=200)
                    else:
                        # Not in checkout flow, process normally through conversation
                        location_display = format_location_for_display(
                            latitude=latitude,
                            longitude=longitude,
                            name=name,
                            address=address
                        )
                        content = f"[User shared location: {location_display}]"

                        # Process location through the graph
                        await graph.ainvoke(
                            {"messages": [HumanMessage(content=content)]},
                            {"configurable": {"thread_id": session_id}},
                        )

                        # Get response
                        output_state = await graph.aget_state(config={"configurable": {"thread_id": session_id}})

                workflow = output_state.values.get("workflow", "conversation")
                response_message = output_state.values["messages"][-1].content
                use_interactive_menu = output_state.values.get("use_interactive_menu", False)

            else:
                content = message["text"]["body"]

                # Check if this is a cart action from WhatsApp deep link (e.g., "add_pizzas_0")
                # This allows carousel buttons to directly trigger cart actions
                from ai_companion.interfaces.whatsapp.cart_handler import CartInteractionHandler

                if CartInteractionHandler.is_cart_interaction(content):
                    # Treat text message as if it were an interactive button
                    logger.info(f"Detected cart action from deep link: {content}")

                    # Use business subdomain + user number as session ID
                    session_id = f"{business_subdomain}:{from_number}"

                    async with AsyncSqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH) as short_term_memory:
                        graph = graph_builder.compile(checkpointer=short_term_memory)

                        # Get current state
                        output_state = await graph.aget_state(config={"configurable": {"thread_id": session_id}})
                        current_state_dict = dict(output_state.values) if output_state and output_state.values else {}

                        # Process as cart interaction (simulate interactive button)
                        node_name, state_updates, text_repr = process_cart_interaction(
                            "button_reply",  # Treat as button reply
                            {"button_reply": {"id": content, "title": content}},
                            current_state_dict
                        )

                        # Handle the cart node response
                        if node_name == "view_category_carousel":
                            # User selected a category via deep link - show items as carousel
                            category = state_updates.get("selected_category", "pizzas")

                            if category in RESTAURANT_MENU:
                                # Prepare items with automatic images and WhatsApp deep links
                                # Using hardcoded WhatsApp number for deep links
                                menu_items = prepare_menu_items_for_carousel(
                                    RESTAURANT_MENU[category],
                                    category,
                                    whatsapp_number="15551525021",  # Hardcoded phone number for carousel deep links
                                    use_whatsapp_deep_link=True
                                )

                                # Create carousel
                                carousel = create_restaurant_menu_carousel(
                                    menu_items,
                                    body_text=f"Check out our {category}! 😋 Swipe to browse",
                                    button_text="View"
                                )

                                # Send carousel
                                await send_response(
                                    from_number,
                                    "",
                                    "interactive_carousel",
                                    phone_number_id=phone_number_id,
                                    whatsapp_token=whatsapp_token,
                                    interactive_component=carousel
                                )

                                # Update state
                                await graph.aupdate_state(
                                    config={"configurable": {"thread_id": session_id}},
                                    values={"selected_category": category}
                                )

                                return Response(content="Category carousel sent from deep link", status_code=200)

                        elif node_name == "add_to_cart":
                            # Item added to cart from deep link - update state and trigger cart flow
                            await graph.aupdate_state(
                                config={"configurable": {"thread_id": session_id}},
                                values=state_updates
                            )

                            # Invoke the add_to_cart node to process the item
                            await graph.ainvoke(
                                {"messages": [HumanMessage(content=text_repr)]},
                                {"configurable": {"thread_id": session_id}},
                            )

                            # Get the response from the cart flow
                            output_state = await graph.aget_state(config={"configurable": {"thread_id": session_id}})

                            # Extract response message and interactive component
                            if output_state and output_state.values:
                                response_message = output_state.values["messages"][-1].content
                                interactive_comp = output_state.values.get("interactive_component")

                                # Send the response to user
                                if interactive_comp:
                                    # Send message with interactive component
                                    await send_response(
                                        from_number,
                                        response_message,
                                        "interactive_button",
                                        phone_number_id=phone_number_id,
                                        whatsapp_token=whatsapp_token,
                                        interactive_component=interactive_comp
                                    )
                                else:
                                    # Send text message
                                    await send_response(
                                        from_number,
                                        response_message,
                                        "text",
                                        phone_number_id=phone_number_id,
                                        whatsapp_token=whatsapp_token
                                    )

                                return Response(content="Item added from deep link", status_code=200)
                            else:
                                # Fallback if no state
                                await send_response(
                                    from_number,
                                    "Item added to cart! 🛒",
                                    "text",
                                    phone_number_id=phone_number_id,
                                    whatsapp_token=whatsapp_token
                                )
                                return Response(content="Item added (fallback)", status_code=200)

                        # For other cart nodes, fall through to normal handling
                        # This shouldn't happen with deep links, but just in case

                # Normal text message - process through conversation graph
                # Use business subdomain + user number as session ID for multi-tenancy
                session_id = f"{business_subdomain}:{from_number}"

                async with AsyncSqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH) as short_term_memory:
                    graph = graph_builder.compile(checkpointer=short_term_memory)
                    await graph.ainvoke(
                        {"messages": [HumanMessage(content=content)]},
                        {"configurable": {"thread_id": session_id}},
                    )

                    # Get the workflow type and response from the state
                    output_state = await graph.aget_state(config={"configurable": {"thread_id": session_id}})

                workflow = output_state.values.get("workflow", "conversation")
                response_message = output_state.values["messages"][-1].content
                use_interactive_menu = output_state.values.get("use_interactive_menu", False)

            # Handle different response types based on workflow
            # Pass business credentials to send_response
            if workflow == "audio":
                audio_buffer = output_state.values["audio_buffer"]
                success = await send_response(
                    from_number, response_message, "audio", audio_buffer,
                    phone_number_id=phone_number_id, whatsapp_token=whatsapp_token
                )
            elif workflow == "image":
                image_path = output_state.values["image_path"]
                with open(image_path, "rb") as f:
                    image_data = f.read()
                success = await send_response(
                    from_number, response_message, "image", image_data,
                    phone_number_id=phone_number_id, whatsapp_token=whatsapp_token
                )
            elif use_interactive_menu:
                # Send category selection list (new flow)
                interactive_comp = create_category_selection_list()
                success = await send_response(
                    from_number, response_message, "interactive_list",
                    phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                    interactive_component=interactive_comp
                )
            else:
                success = await send_response(
                    from_number, response_message, "text",
                    phone_number_id=phone_number_id, whatsapp_token=whatsapp_token
                )

            if not success:
                return Response(content="Failed to send message", status_code=500)

            return Response(content="Message processed", status_code=200)

        elif "statuses" in change_value:
            return Response(content="Status update received", status_code=200)

        else:
            return Response(content="Unknown event type", status_code=400)

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        return Response(content="Internal server error", status_code=500)


async def download_media(media_id: str, whatsapp_token: Optional[str] = None) -> bytes:
    """Download media from WhatsApp."""
    token = whatsapp_token or WHATSAPP_TOKEN
    media_metadata_url = f"https://graph.facebook.com/v21.0/{media_id}"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        metadata_response = await client.get(media_metadata_url, headers=headers)
        metadata_response.raise_for_status()
        metadata = metadata_response.json()
        download_url = metadata.get("url")

        media_response = await client.get(download_url, headers=headers)
        media_response.raise_for_status()
        return media_response.content


async def mark_message_read_and_show_typing(
    message_id: str,
    phone_number_id: str,
    whatsapp_token: str
) -> bool:
    """
    Mark a message as read and display typing indicator to the user.

    The typing indicator will be dismissed once you respond, or after 25 seconds,
    whichever comes first. This is good practice if it will take a few seconds to respond.

    Args:
        message_id: WhatsApp message ID from the webhook
        phone_number_id: WhatsApp Business phone number ID
        whatsapp_token: WhatsApp API access token

    Returns:
        bool: True if successful, False otherwise
    """
    if not whatsapp_token or not whatsapp_token.strip():
        logger.error("WhatsApp token is missing or empty. Cannot mark message as read.")
        return False

    headers = {
        "Authorization": f"Bearer {whatsapp_token}",
        "Content-Type": "application/json",
    }

    json_data = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
        "typing_indicator": {
            "type": "text"
        }
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://graph.facebook.com/v21.0/{phone_number_id}/messages",
                headers=headers,
                json=json_data,
            )

        if response.status_code == 200:
            logger.info(f"Marked message {message_id} as read with typing indicator")
            return True
        else:
            logger.warning(f"Failed to mark message as read: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error marking message as read: {e}", exc_info=True)
        return False


async def process_audio_message(message: Dict, whatsapp_token: Optional[str] = None) -> str:
    """Download and transcribe audio message."""
    token = whatsapp_token or WHATSAPP_TOKEN
    audio_id = message["audio"]["id"]
    media_metadata_url = f"https://graph.facebook.com/v21.0/{audio_id}"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        metadata_response = await client.get(media_metadata_url, headers=headers)
        metadata_response.raise_for_status()
        metadata = metadata_response.json()
        download_url = metadata.get("url")

    # Download the audio file
    async with httpx.AsyncClient() as client:
        audio_response = await client.get(download_url, headers=headers)
        audio_response.raise_for_status()

    # Prepare for transcription
    audio_buffer = BytesIO(audio_response.content)
    audio_buffer.seek(0)
    audio_data = audio_buffer.read()

    return await speech_to_text.transcribe(audio_data)


async def send_response(
    from_number: str,
    response_text: str,
    message_type: str = "text",
    media_content: bytes = None,
    phone_number_id: Optional[str] = None,
    whatsapp_token: Optional[str] = None,
    interactive_component: Optional[Dict] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    location_name: Optional[str] = None,
    location_address: Optional[str] = None,
) -> bool:
    """Send response to user via WhatsApp API.

    Args:
        from_number: Recipient's phone number
        response_text: Message text or header text for interactive messages
        message_type: One of "text", "audio", "image", "interactive_button", "interactive_list",
                     "interactive_carousel", "location", "location_request"
        media_content: Binary content for audio/image
        phone_number_id: WhatsApp Business phone number ID
        whatsapp_token: WhatsApp API access token
        interactive_component: Structured data for interactive messages (buttons, lists, carousels)
        latitude: Latitude for location messages (required for message_type="location")
        longitude: Longitude for location messages (required for message_type="location")
        location_name: Optional name for location messages
        location_address: Optional address for location messages
    """
    # Use business-specific credentials or fallback to env vars
    token = whatsapp_token or WHATSAPP_TOKEN
    phone_id = phone_number_id or WHATSAPP_PHONE_NUMBER_ID

    # Validate token is not empty
    if not token or not token.strip():
        logger.error("WhatsApp token is missing or empty. Cannot send message.")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    if message_type in ["audio", "image"]:
        try:
            mime_type = "audio/mpeg" if message_type == "audio" else "image/png"
            media_buffer = BytesIO(media_content)
            media_id = await upload_media(media_buffer, mime_type, phone_id, token)
            json_data = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "type": message_type,
                message_type: {"id": media_id},
            }

            # Add caption for images
            if message_type == "image":
                json_data["image"]["caption"] = response_text
        except Exception as e:
            logger.error(f"Media upload failed, falling back to text: {e}")
            message_type = "text"

    elif message_type == "interactive_button":
        # Reply buttons (up to 3 buttons)
        json_data = {
            "messaging_product": "whatsapp",
            "to": from_number,
            "type": "interactive",
            "interactive": interactive_component or {
                "type": "button",
                "body": {"text": response_text},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": "btn_1", "title": "Option 1"}},
                        {"type": "reply", "reply": {"id": "btn_2", "title": "Option 2"}},
                    ]
                }
            }
        }

    elif message_type == "interactive_list":
        # List message (up to 10 items per section)
        json_data = {
            "messaging_product": "whatsapp",
            "to": from_number,
            "type": "interactive",
            "interactive": interactive_component or {
                "type": "list",
                "header": {"type": "text", "text": "Menu"},
                "body": {"text": response_text},
                "action": {
                    "button": "View Options",
                    "sections": [
                        {
                            "title": "Categories",
                            "rows": [
                                {"id": "cat_1", "title": "Option 1", "description": "Description"},
                            ]
                        }
                    ]
                }
            }
        }

    elif message_type == "interactive":
        # For order_details and order_status types
        if not interactive_component:
            logger.error("Interactive component is missing for interactive message type")
            return False

        json_data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": from_number,
            "type": "interactive",
            "interactive": interactive_component
        }

        logger.info(f"Sending interactive message of type: {interactive_component.get('type')}")
        logger.debug(f"Interactive component data: {interactive_component}")

    elif message_type == "location":
        # Send a location message with coordinates
        from .location_components import create_location_message_payload

        if latitude is None or longitude is None:
            logger.error("Latitude and longitude are required for location messages")
            return False

        json_data = {
            "messaging_product": "whatsapp",
            "to": from_number,
            "type": "location",
            "location": create_location_message_payload(
                latitude=latitude,
                longitude=longitude,
                name=location_name,
                address=location_address
            )
        }

        logger.info(f"Sending location message to {from_number}: ({latitude}, {longitude})")

    elif message_type == "location_request":
        # Request user's location using interactive message
        from .location_components import create_location_request_component

        json_data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": from_number,
            "type": "interactive",
            "interactive": create_location_request_component(
                body_text=response_text or "Please share your location"
            )
        }

        logger.info(f"Sending location request to {from_number}")

    elif message_type == "interactive_carousel":
        # Send carousel message with horizontally scrollable cards
        if not interactive_component:
            logger.error("Interactive component is missing for carousel message type")
            return False

        if interactive_component.get("type") != "carousel":
            logger.error(f"Expected carousel component, got {interactive_component.get('type')}")
            return False

        json_data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": from_number,
            "type": "interactive",
            "interactive": interactive_component
        }

        logger.info(f"Sending carousel message to {from_number} with {len(interactive_component.get('action', {}).get('cards', []))} cards")

    else:  # Default to text
        json_data = {
            "messaging_product": "whatsapp",
            "to": from_number,
            "type": "text",
            "text": {"body": response_text},
        }

    logger.debug(f"Sending message to {from_number} via phone number ID: {phone_id}")
    logger.debug(f"Message data: {json_data}")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://graph.facebook.com/v21.0/{phone_id}/messages",
            headers=headers,
            json=json_data,
        )

    if response.status_code != 200:
        logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
        return False

    logger.info(f"Message sent successfully to {from_number}")
    return True


async def upload_media(
    media_content: BytesIO,
    mime_type: str,
    phone_number_id: Optional[str] = None,
    whatsapp_token: Optional[str] = None,
) -> str:
    """Upload media to WhatsApp servers."""
    token = whatsapp_token or WHATSAPP_TOKEN
    phone_id = phone_number_id or WHATSAPP_PHONE_NUMBER_ID

    # Validate token is not empty
    if not token or not token.strip():
        raise ValueError("WhatsApp token is missing or empty. Cannot upload media.")

    headers = {"Authorization": f"Bearer {token}"}
    files = {"file": ("response.mp3", media_content, mime_type)}
    data = {"messaging_product": "whatsapp", "type": mime_type}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://graph.facebook.com/v21.0/{phone_id}/media",
            headers=headers,
            files=files,
            data=data,
        )
        result = response.json()

    if "id" not in result:
        raise Exception("Failed to upload media")
    return result["id"]

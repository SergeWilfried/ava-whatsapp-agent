"""
Integration code for webhook handler to process cart interactions.

Add this to your whatsapp_response.py webhook handler to fix the "View Menu" loop.
"""

# ============================================================================
# STEP 1: Add these imports at the top of whatsapp_response.py
# ============================================================================

from ai_companion.interfaces.whatsapp.cart_handler import process_cart_interaction
from ai_companion.graph import cart_nodes
from ai_companion.interfaces.whatsapp.interactive_components import (
    create_menu_list_from_restaurant_menu,
)
from ai_companion.core.schedules import RESTAURANT_MENU


# ============================================================================
# STEP 2: Replace the interactive message handling (around line 100-115)
# ============================================================================

# OLD CODE (REMOVE THIS):
"""
elif message["type"] == "interactive":
    # Handle button or list reply
    interactive_data = message.get("interactive", {})
    if interactive_data.get("type") == "button_reply":
        # User clicked a button
        button_id = interactive_data["button_reply"]["id"]
        button_title = interactive_data["button_reply"]["title"]
        content = f"{button_title}"  # Use button title as message
        logger.info(f"User clicked button: {button_id} - {button_title}")
    elif interactive_data.get("type") == "list_reply":
        # User selected from list
        list_id = interactive_data["list_reply"]["id"]
        list_title = interactive_data["list_reply"]["title"]
        content = f"I'd like to order {list_title}"  # Convert to order intent
        logger.info(f"User selected from list: {list_id} - {list_title}")
"""

# NEW CODE (USE THIS):
"""
elif message["type"] == "interactive":
    # Handle button or list reply with cart routing
    interactive_data = message.get("interactive", {})
    interaction_type = interactive_data.get("type")  # "button_reply" or "list_reply"

    logger.info(f"Processing interactive message: type={interaction_type}")

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
            # User wants to see the menu
            interactive_comp = create_menu_list_from_restaurant_menu(RESTAURANT_MENU)
            success = await send_response(
                from_number,
                "Here's our menu! 😋",
                "interactive_list",
                phone_number_id=phone_number_id,
                whatsapp_token=whatsapp_token,
                interactive_component=interactive_comp
            )
            return Response(content="Menu sent", status_code=200)

        elif node_name == "add_to_cart":
            # Update state with selected item
            current_state_dict.update(state_updates)
            result = await cart_nodes.add_to_cart_node(current_state_dict)

            # Send response
            response_message = result.get("messages", [])[-1].content if result.get("messages") else "Added to cart!"
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

            response_message = result.get("messages", [])[-1].content if result.get("messages") else "Your cart"
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

            response_message = result.get("messages", [])[-1].content if result.get("messages") else "Checkout"
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
            result = await cart_nodes.handle_size_selection_node(current_state_dict)

            response_message = result.get("messages", [])[-1].content if result.get("messages") else "Size selected"
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

        elif node_name == "handle_delivery_method":
            result = await cart_nodes.handle_delivery_method_node(current_state_dict)

            response_message = result.get("messages", [])[-1].content if result.get("messages") else "Delivery selected"
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
            result = await cart_nodes.handle_payment_method_node(current_state_dict)

            response_message = result.get("messages", [])[-1].content if result.get("messages") else "Payment selected"
            interactive_comp = result.get("interactive_component")

            if interactive_comp:
                success = await send_response(
                    from_number, response_message, "interactive",
                    phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                    interactive_component=interactive_comp
                )
            else:
                success = await send_response(
                    from_number, response_message, "text",
                    phone_number_id=phone_number_id, whatsapp_token=whatsapp_token
                )

            return Response(content="Payment method selected", status_code=200)

        else:
            # Not a cart interaction or fallback to conversation
            # Use text representation for conversation flow
            content = text_repr

            # Continue with normal graph processing below...
            # (your existing code continues here)
"""


# ============================================================================
# COMPLETE EXAMPLE: Full interactive message handler
# ============================================================================

async def handle_interactive_message_example(message, session_id, from_number, phone_number_id, whatsapp_token):
    """
    Complete example of handling interactive messages with cart routing.

    Use this as a reference for updating your whatsapp_response.py
    """
    interactive_data = message.get("interactive", {})
    interaction_type = interactive_data.get("type")

    logger.info(f"Processing interactive: type={interaction_type}, data={interactive_data}")

    # Get current state
    async with AsyncSqliteSaver.from_conn_string(settings.SHORT_TERM_MEMORY_DB_PATH) as short_term_memory:
        graph = graph_builder.compile(checkpointer=short_term_memory)
        output_state = await graph.aget_state(config={"configurable": {"thread_id": session_id}})
        current_state_dict = dict(output_state.values) if output_state and output_state.values else {}

        # Process cart interaction
        node_name, state_updates, text_repr = process_cart_interaction(
            interaction_type,
            interactive_data,
            current_state_dict
        )

        logger.info(f"Routed to node: {node_name}, updates: {state_updates}")

        # Update state with any changes
        current_state_dict.update(state_updates)

        # Route to appropriate cart node
        result = None

        if node_name == "show_menu":
            interactive_comp = create_menu_list_from_restaurant_menu(RESTAURANT_MENU)
            await send_response(
                from_number, "Here's our menu! 😋", "interactive_list",
                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                interactive_component=interactive_comp
            )
            return Response(content="OK", status_code=200)

        elif node_name in ["add_to_cart", "view_cart", "checkout", "handle_size",
                          "handle_delivery_method", "handle_payment_method"]:
            # Call the appropriate node
            node_func = getattr(cart_nodes, f"{node_name}_node", None)
            if node_func:
                result = await node_func(current_state_dict)
            else:
                logger.error(f"Node function not found: {node_name}")
                result = {"messages": [AIMessage(content="Sorry, something went wrong.")]}

        else:
            # Fallback to conversation (not a cart interaction)
            content = text_repr
            # Process through normal graph workflow...
            # (continue with your existing conversation flow)
            return  # Let normal flow handle it

        # Send cart node response
        if result:
            response_message = result.get("messages", [])[-1].content if result.get("messages") else "Processing..."
            interactive_comp = result.get("interactive_component")

            if interactive_comp:
                comp_type = interactive_comp.get("type", "button")
                if comp_type == "order_details" or comp_type == "order_status":
                    msg_type = "interactive"
                elif comp_type == "list":
                    msg_type = "interactive_list"
                else:
                    msg_type = "interactive_button"

                await send_response(
                    from_number, response_message, msg_type,
                    phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                    interactive_component=interactive_comp
                )
            else:
                await send_response(
                    from_number, response_message, "text",
                    phone_number_id=phone_number_id, whatsapp_token=whatsapp_token
                )

            return Response(content="OK", status_code=200)


# ============================================================================
# QUICK FIX: Minimal changes to stop the loop
# ============================================================================

"""
If you just want to stop the loop quickly, add this right after the interactive message handling:

elif message["type"] == "interactive":
    interactive_data = message.get("interactive", {})
    interaction_type = interactive_data.get("type")

    # Quick fix for "view_menu" button
    if interaction_type == "button_reply":
        button_id = interactive_data["button_reply"]["id"]

        if button_id == "view_menu" or button_id == "continue_shopping":
            # Show menu and return immediately (stops loop)
            from ai_companion.interfaces.whatsapp.interactive_components import create_menu_list_from_restaurant_menu
            from ai_companion.core.schedules import RESTAURANT_MENU

            menu = create_menu_list_from_restaurant_menu(RESTAURANT_MENU)
            await send_response(
                from_number, "Here's our menu! 😋", "interactive_list",
                phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                interactive_component=menu
            )
            return Response(content="Menu shown", status_code=200)

    # Continue with existing interactive handling...
"""

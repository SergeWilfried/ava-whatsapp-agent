"""
WhatsApp Flow Data Exchange Endpoints
Handles Flow screen rendering and data processing
"""
import logging
import hmac
import hashlib
import base64
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel

from ai_companion.services.product_service import get_product_service
from ai_companion.services.business_service_optimized import get_optimized_business_service
from ai_companion.models.schemas import Product

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flows", tags=["WhatsApp Flows"])


class FlowRequest(BaseModel):
    """WhatsApp Flow data exchange request"""
    version: str
    screen: str
    data: Dict[str, Any]
    flow_token: str
    action: str  # INIT | data_exchange | BACK | error_return


class FlowResponse(BaseModel):
    """WhatsApp Flow data exchange response"""
    version: str = "3.0"
    screen: str
    data: Dict[str, Any]


def verify_flow_signature(
    request_body: bytes,
    signature_header: str,
    app_secret: str
) -> bool:
    """
    Verify WhatsApp Flow request signature.

    Args:
        request_body: Raw request body bytes
        signature_header: X-Hub-Signature-256 header value
        app_secret: App secret from Meta

    Returns:
        True if signature is valid
    """
    try:
        # Extract signature from header (format: "sha256=<signature>")
        if not signature_header.startswith("sha256="):
            return False

        expected_signature = signature_header.split("sha256=")[1]

        # Calculate HMAC
        hmac_obj = hmac.new(
            app_secret.encode(),
            request_body,
            hashlib.sha256
        )
        calculated_signature = hmac_obj.hexdigest()

        # Compare signatures
        return hmac.compare_digest(calculated_signature, expected_signature)

    except Exception as e:
        logger.error(f"Failed to verify Flow signature: {e}")
        return False


@router.post("/product/{product_id}/{sub_domain}")
async def product_flow_data_exchange(
    product_id: str,
    sub_domain: str,
    flow_request: FlowRequest,
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None)
):
    """
    WhatsApp Flow data exchange endpoint for product customization.

    Flow screens:
    1. SIZE_SELECTION - Choose product presentation/size
    2. MODIFIERS_SELECTION - Select modifiers (toppings, add-ons, etc.)
    3. ORDER_SUMMARY - Review order before adding to cart

    Args:
        product_id: Product rId
        sub_domain: Business subdomain
        flow_request: Flow data exchange request
        x_hub_signature_256: Signature header for verification

    Returns:
        FlowResponse with screen data
    """
    try:
        # Verify signature (optional in development, required in production)
        app_secret = os.getenv("META_APP_SECRET")
        if app_secret and x_hub_signature_256:
            request_body = await request.body()
            is_valid = verify_flow_signature(
                request_body,
                x_hub_signature_256,
                app_secret
            )

            if not is_valid:
                raise HTTPException(status_code=403, detail="Invalid signature")

        # Get business service
        business_service = await get_optimized_business_service()
        business = await business_service.get_business_by_subdomain(sub_domain)

        if not business:
            raise HTTPException(status_code=404, detail="Business not found")

        # Get product service
        product_service = await get_product_service(business_service.db)

        # Handle different flow actions
        action = flow_request.action
        screen = flow_request.screen

        if action == "INIT":
            # Initialize flow - show first screen (SIZE_SELECTION)
            return await _handle_init_screen(product_id, sub_domain, product_service)

        elif action == "data_exchange":
            # Process screen data and navigate to next screen
            if screen == "SIZE_SELECTION":
                return await _handle_size_selection(
                    product_id,
                    sub_domain,
                    flow_request.data,
                    product_service
                )

            elif screen == "MODIFIERS_SELECTION":
                return await _handle_modifiers_selection(
                    product_id,
                    sub_domain,
                    flow_request.data,
                    product_service
                )

            elif screen == "ORDER_SUMMARY":
                return await _handle_order_summary(
                    product_id,
                    sub_domain,
                    flow_request.data,
                    product_service
                )

        elif action == "BACK":
            # Handle back navigation
            return await _handle_back_navigation(screen, product_id, sub_domain, product_service)

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Flow endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_init_screen(
    product_id: str,
    sub_domain: str,
    product_service
) -> FlowResponse:
    """Initialize flow with SIZE_SELECTION screen"""
    try:
        # Get product details
        product = await product_service.get_product_by_id(product_id, sub_domain)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Get presentations
        presentations = await product_service.get_presentations_for_product(product_id, sub_domain)

        # Build presentation options for dropdown
        size_options = [
            {
                "id": p.r_id,
                "title": p.name,
                "description": f"${p.discounted_price or p.price:.2f}"
            }
            for p in presentations
            if p.is_active
        ]

        # If no presentations, use base product
        if not size_options:
            size_options = [
                {
                    "id": "base",
                    "title": "Standard",
                    "description": f"${product.base_price:.2f}"
                }
            ]

        return FlowResponse(
            screen="SIZE_SELECTION",
            data={
                "product_name": product.name,
                "product_image": product.image_url or "",
                "product_description": product.description or "",
                "size_options": size_options,
                "selected_size": size_options[0]["id"] if size_options else None
            }
        )

    except Exception as e:
        logger.error(f"Failed to handle init screen: {e}", exc_info=True)
        raise


async def _handle_size_selection(
    product_id: str,
    sub_domain: str,
    data: Dict[str, Any],
    product_service
) -> FlowResponse:
    """Handle size selection and move to modifiers screen"""
    try:
        selected_size = data.get("selected_size")

        # Get modifiers for the product
        modifiers = await product_service.get_modifiers_for_product(product_id, sub_domain)

        if not modifiers:
            # No modifiers, skip to order summary
            return await _build_order_summary_screen(product_id, sub_domain, data, product_service)

        # Build modifier groups
        modifier_groups = []
        for modifier in modifiers:
            modifier_group = {
                "id": modifier.r_id,
                "name": modifier.name,
                "is_multiple": modifier.is_multiple,
                "min_quantity": modifier.min_quantity,
                "max_quantity": modifier.max_quantity or 10,
                "options": [
                    {
                        "id": opt.option_id,
                        "title": opt.name,
                        "price": opt.price,
                        "is_active": opt.is_active
                    }
                    for opt in modifier.options
                    if opt.is_active
                ]
            }
            modifier_groups.append(modifier_group)

        return FlowResponse(
            screen="MODIFIERS_SELECTION",
            data={
                "selected_size": selected_size,
                "modifier_groups": modifier_groups,
                "selected_modifiers": {}  # Initialize empty selections
            }
        )

    except Exception as e:
        logger.error(f"Failed to handle size selection: {e}", exc_info=True)
        raise


async def _handle_modifiers_selection(
    product_id: str,
    sub_domain: str,
    data: Dict[str, Any],
    product_service
) -> FlowResponse:
    """Handle modifier selection and move to order summary"""
    return await _build_order_summary_screen(product_id, sub_domain, data, product_service)


async def _build_order_summary_screen(
    product_id: str,
    sub_domain: str,
    data: Dict[str, Any],
    product_service
) -> FlowResponse:
    """Build order summary screen with price calculation"""
    try:
        product = await product_service.get_product_by_id(product_id, sub_domain)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        selected_size = data.get("selected_size")
        selected_modifiers = data.get("selected_modifiers", {})

        # Calculate price
        base_price = product.base_price

        # Get presentation price if selected
        if selected_size and selected_size != "base":
            presentations = await product_service.get_presentations_for_product(product_id, sub_domain)
            presentation = next((p for p in presentations if p.r_id == selected_size), None)
            if presentation:
                base_price = presentation.discounted_price or presentation.price

        # Calculate modifiers total
        modifiers_total = 0.0
        modifier_summary = []

        for modifier_id, options in selected_modifiers.items():
            if isinstance(options, list):
                for option in options:
                    option_id = option.get("id")
                    quantity = option.get("quantity", 1)
                    price = option.get("price", 0)

                    modifiers_total += price * quantity
                    modifier_summary.append({
                        "name": option.get("name"),
                        "quantity": quantity,
                        "price": price
                    })

        total_price = base_price + modifiers_total

        return FlowResponse(
            screen="ORDER_SUMMARY",
            data={
                "product_name": product.name,
                "selected_size": selected_size,
                "base_price": base_price,
                "modifiers_total": modifiers_total,
                "total_price": total_price,
                "modifier_summary": modifier_summary,
                "quantity": data.get("quantity", 1)
            }
        )

    except Exception as e:
        logger.error(f"Failed to build order summary: {e}", exc_info=True)
        raise


async def _handle_order_summary(
    product_id: str,
    sub_domain: str,
    data: Dict[str, Any],
    product_service
) -> Dict[str, Any]:
    """
    Handle order submission from order summary.
    This is the final step - flow should close after this.
    """
    try:
        # Extract order data
        order_data = {
            "product_id": product_id,
            "selected_size": data.get("selected_size"),
            "selected_modifiers": data.get("selected_modifiers", {}),
            "quantity": data.get("quantity", 1),
            "total_price": data.get("total_price"),
            "special_instructions": data.get("special_instructions", "")
        }

        # Store order data in session (will be picked up by graph workflow)
        # For now, return success message
        return {
            "version": "3.0",
            "screen": "SUCCESS",
            "data": {
                "success": True,
                "message": "Added to cart!",
                "order_data": order_data
            }
        }

    except Exception as e:
        logger.error(f"Failed to handle order summary: {e}", exc_info=True)
        raise


async def _handle_back_navigation(
    current_screen: str,
    product_id: str,
    sub_domain: str,
    product_service
) -> FlowResponse:
    """Handle back button navigation between screens"""
    try:
        if current_screen == "MODIFIERS_SELECTION":
            # Go back to SIZE_SELECTION
            return await _handle_init_screen(product_id, sub_domain, product_service)

        elif current_screen == "ORDER_SUMMARY":
            # Go back to MODIFIERS_SELECTION
            modifiers = await product_service.get_modifiers_for_product(product_id, sub_domain)
            if not modifiers:
                # No modifiers, go back to SIZE_SELECTION
                return await _handle_init_screen(product_id, sub_domain, product_service)
            else:
                return FlowResponse(
                    screen="MODIFIERS_SELECTION",
                    data={}
                )

        else:
            # Default: go to init screen
            return await _handle_init_screen(product_id, sub_domain, product_service)

    except Exception as e:
        logger.error(f"Failed to handle back navigation: {e}", exc_info=True)
        raise


# Checkout flow endpoint
@router.post("/checkout/{sub_domain}")
async def checkout_flow_data_exchange(
    sub_domain: str,
    flow_request: FlowRequest,
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None)
):
    """
    WhatsApp Flow data exchange endpoint for checkout.

    Flow screens:
    1. CART_REVIEW - Review cart items
    2. DELIVERY_ADDRESS - Enter/select delivery address
    3. PAYMENT_METHOD - Select payment method
    4. ORDER_CONFIRMATION - Confirm and place order

    Args:
        sub_domain: Business subdomain
        flow_request: Flow data exchange request
        x_hub_signature_256: Signature header for verification

    Returns:
        FlowResponse with screen data
    """
    try:
        # TODO: Implement checkout flow screens
        # For now, return placeholder
        return FlowResponse(
            screen="CART_REVIEW",
            data={
                "message": "Checkout flow coming soon"
            }
        )

    except Exception as e:
        logger.error(f"Checkout flow endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


import os

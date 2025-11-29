"""
Meta Business Webhooks Handler
Handles webhooks from Meta for catalog updates, order events, etc.
"""
import logging
import hmac
import hashlib
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Query
from pydantic import BaseModel

from ai_companion.services.product_service import get_product_service
from ai_companion.services.business_service_optimized import get_optimized_business_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/meta", tags=["Meta Webhooks"])


class WebhookEntry(BaseModel):
    """Meta webhook entry"""
    id: str
    time: int
    changes: list


class MetaWebhook(BaseModel):
    """Meta webhook payload"""
    object: str
    entry: list


def verify_meta_signature(
    payload: bytes,
    signature: str,
    app_secret: str
) -> bool:
    """
    Verify Meta webhook signature.

    Args:
        payload: Raw request body
        signature: X-Hub-Signature-256 header
        app_secret: Meta app secret

    Returns:
        True if signature is valid
    """
    try:
        if not signature.startswith("sha256="):
            return False

        expected_signature = signature.split("sha256=")[1]

        hmac_obj = hmac.new(
            app_secret.encode(),
            payload,
            hashlib.sha256
        )
        calculated_signature = hmac_obj.hexdigest()

        return hmac.compare_digest(calculated_signature, expected_signature)

    except Exception as e:
        logger.error(f"Failed to verify Meta signature: {e}")
        return False


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    """
    Verify webhook endpoint (GET request from Meta).

    This is called once when setting up the webhook in Meta Developer Portal.

    Args:
        hub_mode: Should be "subscribe"
        hub_verify_token: Verification token (set in Meta Developer Portal)
        hub_challenge: Challenge string to return

    Returns:
        Challenge string if verification succeeds
    """
    import os
    verify_token = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "your_verify_token_here")

    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("Meta webhook verified successfully")
        return int(hub_challenge)
    else:
        logger.warning("Meta webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def handle_webhook(request: Request):
    """
    Handle Meta webhook events (POST request).

    Webhook events include:
    - Product catalog updates
    - Order events
    - Commerce events
    - Page events

    Args:
        request: FastAPI request object

    Returns:
        Success response
    """
    try:
        import os

        # Verify signature
        signature = request.headers.get("X-Hub-Signature-256", "")
        app_secret = os.getenv("META_APP_SECRET")

        if app_secret:
            payload = await request.body()
            if not verify_meta_signature(payload, signature, app_secret):
                raise HTTPException(status_code=403, detail="Invalid signature")

        # Parse webhook data
        data = await request.json()
        webhook_object = data.get("object")

        logger.info(f"Received Meta webhook: {webhook_object}")

        # Route to appropriate handler
        if webhook_object == "page":
            await handle_page_webhook(data)
        elif webhook_object == "commerce_account":
            await handle_commerce_webhook(data)
        elif webhook_object == "whatsapp_business_account":
            await handle_whatsapp_webhook(data)
        else:
            logger.warning(f"Unknown webhook object: {webhook_object}")

        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Meta webhook error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


async def handle_page_webhook(data: Dict[str, Any]):
    """Handle page-related webhooks"""
    try:
        for entry in data.get("entry", []):
            changes = entry.get("changes", [])

            for change in changes:
                field = change.get("field")
                value = change.get("value", {})

                logger.info(f"Page webhook field: {field}")

                if field == "feed":
                    # Handle page feed updates
                    await handle_feed_update(value)

                elif field == "commerce_order_update":
                    # Handle order updates
                    await handle_order_update(value)

    except Exception as e:
        logger.error(f"Error handling page webhook: {e}", exc_info=True)


async def handle_commerce_webhook(data: Dict[str, Any]):
    """Handle commerce-related webhooks"""
    try:
        for entry in data.get("entry", []):
            changes = entry.get("changes", [])

            for change in changes:
                field = change.get("field")
                value = change.get("value", {})

                logger.info(f"Commerce webhook field: {field}")

                if field == "product_item_update":
                    # Handle product updates from catalog
                    await handle_product_update(value)

                elif field == "product_set_update":
                    # Handle product set updates
                    await handle_product_set_update(value)

    except Exception as e:
        logger.error(f"Error handling commerce webhook: {e}", exc_info=True)


async def handle_whatsapp_webhook(data: Dict[str, Any]):
    """Handle WhatsApp Business Account webhooks"""
    try:
        for entry in data.get("entry", []):
            changes = entry.get("changes", [])

            for change in changes:
                field = change.get("field")
                value = change.get("value", {})

                logger.info(f"WhatsApp webhook field: {field}")

                # This is handled by the main WhatsApp webhook endpoint
                # Just log for debugging
                if field == "messages":
                    logger.debug("Message webhook received (handled elsewhere)")

    except Exception as e:
        logger.error(f"Error handling WhatsApp webhook: {e}", exc_info=True)


async def handle_feed_update(value: Dict[str, Any]):
    """Handle page feed updates"""
    try:
        item = value.get("item")
        verb = value.get("verb")  # add, edit, remove

        logger.info(f"Feed update: {verb} - {item}")

        # Handle feed item updates if needed

    except Exception as e:
        logger.error(f"Error handling feed update: {e}", exc_info=True)


async def handle_order_update(value: Dict[str, Any]):
    """Handle commerce order updates"""
    try:
        order_id = value.get("id")
        status = value.get("status")

        logger.info(f"Order update: {order_id} - {status}")

        # TODO: Update order status in database
        # This would sync Meta commerce orders with your local orders collection

    except Exception as e:
        logger.error(f"Error handling order update: {e}", exc_info=True)


async def handle_product_update(value: Dict[str, Any]):
    """
    Handle product catalog updates from Meta.

    This is triggered when products are updated in Meta Commerce Manager.
    Syncs changes back to local database.

    Args:
        value: Webhook value data
    """
    try:
        product_id = value.get("id")
        retailer_id = value.get("retailer_id")  # Our internal product ID
        action = value.get("action")  # CREATE, UPDATE, DELETE

        logger.info(f"Product update: {retailer_id} - {action}")

        if not retailer_id:
            logger.warning("No retailer_id in product update")
            return

        # Get services
        business_service = await get_optimized_business_service()
        product_service = await get_product_service(business_service.db)

        if action == "DELETE":
            # Product deleted in Meta catalog
            logger.info(f"Product {retailer_id} deleted in Meta catalog")
            # Optionally mark as inactive or sync deletion

        elif action in ["CREATE", "UPDATE"]:
            # Product created or updated in Meta catalog
            # Could fetch latest data from Meta and update local DB
            logger.info(f"Product {retailer_id} updated in Meta catalog")

    except Exception as e:
        logger.error(f"Error handling product update: {e}", exc_info=True)


async def handle_product_set_update(value: Dict[str, Any]):
    """Handle product set (collection) updates"""
    try:
        set_id = value.get("id")
        action = value.get("action")

        logger.info(f"Product set update: {set_id} - {action}")

        # Handle product set updates if using collections

    except Exception as e:
        logger.error(f"Error handling product set update: {e}", exc_info=True)


@router.post("/catalog/sync/{sub_domain}")
async def trigger_catalog_sync(sub_domain: str):
    """
    Manually trigger catalog sync to Meta.

    Useful for:
    - Initial catalog setup
    - Bulk product updates
    - Recovery from sync failures

    Args:
        sub_domain: Business subdomain

    Returns:
        Sync results
    """
    try:
        # Get services
        business_service = await get_optimized_business_service()
        product_service = await get_product_service(business_service.db)

        # Get business
        business = await business_service.get_business_by_subdomain(sub_domain)

        if not business:
            raise HTTPException(status_code=404, detail="Business not found")

        # Get all active products
        products = await product_service.get_products_by_category(
            sub_domain=sub_domain,
            limit=1000  # Sync all products
        )

        synced_count = 0
        failed_count = 0
        errors = []

        for product in products:
            try:
                result = await product_service.sync_product_to_meta_catalog(product, business)

                if result.get("success"):
                    synced_count += 1
                else:
                    failed_count += 1
                    errors.append({
                        "product_id": product.r_id,
                        "error": result.get("error")
                    })

            except Exception as e:
                failed_count += 1
                errors.append({
                    "product_id": product.r_id,
                    "error": str(e)
                })

        return {
            "status": "completed",
            "total_products": len(products),
            "synced": synced_count,
            "failed": failed_count,
            "errors": errors[:10]  # Return first 10 errors
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Catalog sync error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

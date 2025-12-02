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
            else:
                content = message["text"]["body"]

            # Process message through the graph agent
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
                # Send interactive menu list
                from ai_companion.interfaces.whatsapp.interactive_components import create_menu_list_from_restaurant_menu
                from ai_companion.core.schedules import RESTAURANT_MENU

                interactive_comp = create_menu_list_from_restaurant_menu(RESTAURANT_MENU)
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
) -> bool:
    """Send response to user via WhatsApp API.

    Args:
        from_number: Recipient's phone number
        response_text: Message text or header text for interactive messages
        message_type: One of "text", "audio", "image", "interactive_button", "interactive_list"
        media_content: Binary content for audio/image
        phone_number_id: WhatsApp Business phone number ID
        whatsapp_token: WhatsApp API access token
        interactive_component: Structured data for interactive messages
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

    return response.status_code == 200


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

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

logger = logging.getLogger(__name__)

# Global module instances
speech_to_text = SpeechToText()
text_to_speech = TextToSpeech()
image_to_text = ImageToText()

# Router for WhatsApp respo
whatsapp_router = APIRouter()

# WhatsApp API credentials from environment variables
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
            session_id = from_number

            # Use environment variables for WhatsApp credentials
            whatsapp_token = WHATSAPP_TOKEN
            phone_number_id = WHATSAPP_PHONE_NUMBER_ID

            if not whatsapp_token:
                logger.error("WHATSAPP_TOKEN environment variable is not set")
                return Response(content="WhatsApp token not configured", status_code=500)

            if not phone_number_id:
                logger.error("WHATSAPP_PHONE_NUMBER_ID environment variable is not set")
                return Response(content="WhatsApp phone number ID not configured", status_code=500)

            logger.info(f"Processing message from {from_number}")

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
                # Handle interactive message responses (button clicks, list selections)
                content = process_interactive_response(message)
            elif message["type"] == "location":
                # Handle location sharing
                location = message["location"]
                lat = location.get("latitude")
                lon = location.get("longitude")
                name = location.get("name", "")
                address = location.get("address", "")
                content = f"[Location shared: {name or 'Location'} at ({lat}, {lon})"
                if address:
                    content += f" - {address}"
                content += "]"
            elif message["type"] == "contacts":
                # Handle contact sharing
                contacts = message["contacts"]
                content = f"[Contact(s) shared: "
                content += ", ".join([c.get("name", {}).get("formatted_name", "Unknown") for c in contacts])
                content += "]"
            else:
                content = message["text"]["body"]

            # Process message through the graph agent
            # Use user number as session ID
            session_id = from_number

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

            # Check for interactive components in state
            interactive_component = output_state.values.get("interactive_component")
            interactive_type = output_state.values.get("interactive_type")
            location_data = output_state.values.get("location_data")
            contact_data = output_state.values.get("contact_data")

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
            elif interactive_component or location_data or contact_data:
                # Send interactive, location, or contact message
                if location_data:
                    message_type = "location"
                elif contact_data:
                    message_type = "contacts"
                else:
                    message_type = "interactive"

                success = await send_response(
                    from_number, response_message, message_type,
                    phone_number_id=phone_number_id, whatsapp_token=whatsapp_token,
                    interactive_component=interactive_component,
                    location_data=location_data,
                    contact_data=contact_data
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


def process_interactive_response(message: Dict) -> str:
    """Process interactive message response (button click or list selection).

    Args:
        message: WhatsApp message dict containing interactive response

    Returns:
        str: Formatted response text
    """
    interactive = message.get("interactive", {})
    response_type = interactive.get("type")

    if response_type == "button_reply":
        # User clicked a button
        button_reply = interactive.get("button_reply", {})
        button_id = button_reply.get("id", "")
        button_title = button_reply.get("title", "")
        return f"[Button clicked: {button_title} (ID: {button_id})]"

    elif response_type == "list_reply":
        # User selected from a list
        list_reply = interactive.get("list_reply", {})
        row_id = list_reply.get("id", "")
        row_title = list_reply.get("title", "")
        row_description = list_reply.get("description", "")
        result = f"[List selection: {row_title} (ID: {row_id})"
        if row_description:
            result += f" - {row_description}"
        result += "]"
        return result

    else:
        return f"[Interactive response: {response_type}]"


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
    location_data: Optional[Dict] = None,
    contact_data: Optional[Dict] = None,
) -> bool:
    """Send response to user via WhatsApp API.

    Args:
        from_number: Recipient's WhatsApp number
        response_text: Text message content
        message_type: Type of message (text, audio, image, interactive, location, contacts, poll)
        media_content: Binary media content for audio/image
        phone_number_id: WhatsApp Business phone number ID
        whatsapp_token: WhatsApp API token
        interactive_component: Interactive component dict (buttons, lists, etc.)
        location_data: Location data dict from create_location_message()
        contact_data: Contact data dict from create_contact_message()

    Returns:
        bool: True if message sent successfully
    """
    # Use business-specific credentials or fallback to env vars
    token = whatsapp_token or WHATSAPP_TOKEN
    phone_id = phone_number_id or WHATSAPP_PHONE_NUMBER_ID

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

    if message_type == "interactive":
        # Send interactive message (buttons, lists, etc.)
        if not interactive_component:
            logger.error("Interactive message type requires interactive_component")
            message_type = "text"  # Fallback to text
        else:
            json_data = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "type": "interactive",
                "interactive": interactive_component
            }

    elif message_type == "location":
        # Send location message
        if not location_data:
            logger.error("Location message type requires location_data")
            message_type = "text"
        else:
            json_data = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "type": "location",
                "location": location_data
            }

    elif message_type == "contacts":
        # Send contact message
        if not contact_data:
            logger.error("Contacts message type requires contact_data")
            message_type = "text"
        else:
            json_data = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "type": "contacts",
                **contact_data
            }

    if message_type == "text":
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

from langgraph.graph import MessagesState


class AICompanionState(MessagesState):
    """State class for the AI Companion workflow.

    Extends MessagesState to track conversation history and maintains the last message received.

    Attributes:
        last_message (AnyMessage): The most recent message in the conversation, can be any valid
            LangChain message type (HumanMessage, AIMessage, etc.)
        workflow (str): The current workflow the AI Companion is in. Can be "conversation", "image", "audio", or "interactive".
        audio_buffer (bytes): The audio buffer to be used for speech-to-text conversion.
        image_path (str): Path to generated image file.
        current_activity (str): The current activity of Ava based on the schedule.
        apply_activity (bool): Whether to apply the current activity context.
        memory_context (str): The context of the memories to be injected into the character card.
        interactive_component (dict): Interactive component data (buttons, lists, location, etc.).
        interactive_type (str): Type of interactive message (buttons, list, location, location_request, contacts).
        location_data (dict): Location data for location messages.
        contact_data (dict): Contact data for contact messages.
    """

    summary: str
    workflow: str
    audio_buffer: bytes
    image_path: str
    current_activity: str
    apply_activity: bool
    memory_context: str
    interactive_component: dict
    interactive_type: str
    location_data: dict
    contact_data: dict

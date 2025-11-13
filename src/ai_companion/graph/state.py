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

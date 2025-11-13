import os
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig

from ai_companion.graph.state import AICompanionState
from ai_companion.graph.utils.chains import (
    get_character_response_chain,
    get_router_chain,
)
from ai_companion.graph.utils.helpers import (
    get_chat_model,
    get_text_to_image_module,
    get_text_to_speech_module,
)
from ai_companion.modules.memory.long_term.memory_manager import get_memory_manager
from ai_companion.modules.schedules.context_generation import ScheduleContextGenerator
from ai_companion.settings import settings


async def router_node(state: AICompanionState):
    chain = get_router_chain()
    response = await chain.ainvoke({"messages": state["messages"][-settings.ROUTER_MESSAGES_TO_ANALYZE :]})
    return {"workflow": response.response_type}


def context_injection_node(state: AICompanionState):
    schedule_context = ScheduleContextGenerator.get_current_activity()
    if schedule_context != state.get("current_activity", ""):
        apply_activity = True
    else:
        apply_activity = False
    return {"apply_activity": apply_activity, "current_activity": schedule_context}


async def conversation_node(state: AICompanionState, config: RunnableConfig):
    """Conversation node with intelligent interactive message support."""
    from ai_companion.graph.interactive_logic import (
        InteractiveMessageDecider,
        should_send_interactive_after_response
    )

    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")
    user_message = state["messages"][-1].content

    # Check if user message warrants immediate interactive response
    intent = InteractiveMessageDecider.detect_intent(user_message)

    # Handle specific intents with pre-built interactive messages
    if intent == "list" and any(word in user_message.lower() for word in ["subject", "topic", "learn"]):
        # User wants to see subjects/topics
        interactive = InteractiveMessageDecider.create_tutoring_subject_list()
        return {
            "messages": AIMessage(content="Choose a subject to learn:"),
            "interactive_component": interactive
        }

    elif intent == "binary":
        # User asked a yes/no question, respond with yes/no buttons
        # Generate response first
        chain = get_character_response_chain(state.get("summary", ""))
        response = await chain.ainvoke(
            {
                "messages": state["messages"],
                "current_activity": current_activity,
                "memory_context": memory_context,
            },
            config,
        )

        # If response contains a question, add yes/no buttons
        if "?" in response:
            question = response.split("?")[0].strip() + "?"
            if len(question) < 150:
                interactive = InteractiveMessageDecider.create_binary_response(question)
                return {
                    "messages": AIMessage(content=response),
                    "interactive_component": interactive
                }

        return {"messages": AIMessage(content=response)}

    elif intent == "confirmation":
        # User needs to confirm something
        interactive = InteractiveMessageDecider.create_confirmation_response(
            "Please confirm to proceed:"
        )
        return {
            "messages": AIMessage(content="I need your confirmation:"),
            "interactive_component": interactive
        }

    # Handle responses to interactive messages
    elif "[List selection:" in user_message:
        # User selected from a list - offer difficulty level
        interactive = InteractiveMessageDecider.create_difficulty_buttons()
        return {
            "messages": AIMessage(content="Great choice! What's your skill level?"),
            "interactive_component": interactive
        }

    elif "[Button clicked:" in user_message and any(word in user_message.lower() for word in ["beginner", "intermediate", "advanced"]):
        # User selected difficulty - offer learning mode
        interactive = InteractiveMessageDecider.create_learning_mode_buttons()
        return {
            "messages": AIMessage(content="How would you like to learn today?"),
            "interactive_component": interactive
        }

    # Generate regular response
    chain = get_character_response_chain(state.get("summary", ""))
    response = await chain.ainvoke(
        {
            "messages": state["messages"],
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )

    # Check if response warrants a follow-up interactive message
    interactive = should_send_interactive_after_response(response)

    if interactive:
        return {
            "messages": AIMessage(content=response),
            "interactive_component": interactive
        }

    return {"messages": AIMessage(content=response)}


async def image_node(state: AICompanionState, config: RunnableConfig):
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))
    text_to_image_module = get_text_to_image_module()

    scenario = await text_to_image_module.create_scenario(state["messages"][-5:])
    os.makedirs("generated_images", exist_ok=True)
    img_path = f"generated_images/image_{str(uuid4())}.png"
    await text_to_image_module.generate_image(scenario.image_prompt, img_path)

    # Inject the image prompt information as an AI message
    scenario_message = HumanMessage(content=f"<image attached by Ava generated from prompt: {scenario.image_prompt}>")
    updated_messages = state["messages"] + [scenario_message]

    response = await chain.ainvoke(
        {
            "messages": updated_messages,
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )

    return {"messages": AIMessage(content=response), "image_path": img_path}


async def audio_node(state: AICompanionState, config: RunnableConfig):
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    chain = get_character_response_chain(state.get("summary", ""))
    text_to_speech_module = get_text_to_speech_module()

    response = await chain.ainvoke(
        {
            "messages": state["messages"],
            "current_activity": current_activity,
            "memory_context": memory_context,
        },
        config,
    )
    output_audio = await text_to_speech_module.synthesize(response)

    return {"messages": response, "audio_buffer": output_audio}


async def summarize_conversation_node(state: AICompanionState):
    model = get_chat_model()
    summary = state.get("summary", "")

    if summary:
        summary_message = (
            f"This is summary of the conversation to date between Ava and the user: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = (
            "Create a summary of the conversation above between Ava and the user. "
            "The summary must be a short description of the conversation so far, "
            "but that captures all the relevant information shared between Ava and the user:"
        )

    messages = state["messages"] + [HumanMessage(content=summary_message)]
    response = await model.ainvoke(messages)

    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][: -settings.TOTAL_MESSAGES_AFTER_SUMMARY]]
    return {"summary": response.content, "messages": delete_messages}


async def memory_extraction_node(state: AICompanionState):
    """Extract and store important information from the last message."""
    if not state["messages"]:
        return {}

    memory_manager = get_memory_manager()
    await memory_manager.extract_and_store_memories(state["messages"][-1])
    return {}


def memory_injection_node(state: AICompanionState):
    """Retrieve and inject relevant memories into the character card."""
    memory_manager = get_memory_manager()

    # Get relevant memories based on recent conversation
    recent_context = " ".join([m.content for m in state["messages"][-3:]])
    memories = memory_manager.get_relevant_memories(recent_context)

    # Format memories for the character card
    memory_context = memory_manager.format_memories_for_prompt(memories)

    return {"memory_context": memory_context}

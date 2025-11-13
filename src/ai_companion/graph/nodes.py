import os
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig

from ai_companion.graph.state import AICompanionState
from ai_companion.graph.utils.chains import (
    get_character_response_chain,
    get_router_chain,
    get_order_processing_chain,
    get_menu_display_chain,
)
from ai_companion.graph.utils.helpers import (
    get_chat_model,
    get_text_to_image_module,
    get_text_to_speech_module,
)
from ai_companion.modules.memory.long_term.memory_manager import get_memory_manager
from ai_companion.modules.schedules.context_generation import ScheduleContextGenerator
from ai_companion.settings import settings
from ai_companion.core.schedules import RESTAURANT_MENU, BUSINESS_HOURS, RESTAURANT_INFO, SPECIAL_OFFERS
import json
from datetime import datetime


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
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")

    # Format restaurant info for injection
    restaurant_info = f"{RESTAURANT_INFO['name']}\n"
    restaurant_info += f"Address: {RESTAURANT_INFO['address']}\nPhone: {RESTAURANT_INFO['phone']}"

    # Create modified messages with injected restaurant info
    system_prompt = get_character_response_chain(state.get("summary", ""))

    # Manually format the system message with all variables
    from ai_companion.core.prompts import get_character_card_prompt
    system_message = get_character_card_prompt(settings.LANGUAGE)
    if state.get("summary", ""):
        system_message += f"\n\nSummary of conversation earlier with the customer: {state.get('summary', '')}"

    # Replace placeholders
    system_message = system_message.replace("{restaurant_name}", RESTAURANT_INFO['name'])
    system_message = system_message.replace("{restaurant_info}", current_activity)
    system_message = system_message.replace("{memory_context}", memory_context if memory_context else "No previous information about this customer.")
    system_message = system_message.replace("{current_activity}", current_activity)

    # Use the chain directly with the formatted prompt
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from ai_companion.graph.utils.helpers import AsteriskRemovalParser, get_chat_model

    model = get_chat_model()
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        MessagesPlaceholder(variable_name="messages"),
    ])
    chain = prompt | model | AsteriskRemovalParser()

    response = await chain.ainvoke({"messages": state["messages"]}, config)
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


async def order_node(state: AICompanionState, config: RunnableConfig):
    """Process customer order and calculate total."""
    memory_context = state.get("memory_context", "")

    # Format menu data for the chain
    menu_data = json.dumps(RESTAURANT_MENU, indent=2)

    chain = get_order_processing_chain()

    try:
        # Add menu data to messages
        system_msg = HumanMessage(content=f"Restaurant Menu:\n{menu_data}\n\nTax Rate: {settings.TAX_RATE}")
        messages_with_menu = state["messages"] + [system_msg]

        response = await chain.ainvoke(
            {
                "messages": messages_with_menu,
                "menu_data": menu_data,
            },
            config
        )

        # Format the confirmation message
        confirmation = response.confirmation_message

        return {"messages": AIMessage(content=confirmation)}
    except Exception as e:
        # Fallback to conversation if order processing fails
        fallback_msg = "I'd be happy to help you with your order! Could you please tell me what items you'd like?"
        return {"messages": AIMessage(content=fallback_msg)}


async def menu_node(state: AICompanionState, config: RunnableConfig):
    """Display menu items to the customer using interactive list."""
    # Store flag to send interactive menu
    # The response will be handled in the webhook with interactive components

    # Add today's special to the message
    today = datetime.now().strftime("%A").lower()
    special_text = ""
    if today in SPECIAL_OFFERS["daily_specials"]:
        special_text = f"\n\n✨ Today's Special: {SPECIAL_OFFERS['daily_specials'][today]}"

    menu_message = f"Here's our menu!{special_text}"

    return {
        "messages": AIMessage(content=menu_message),
        "use_interactive_menu": True  # Flag to trigger interactive component
    }

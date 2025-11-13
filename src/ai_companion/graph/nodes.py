import os
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig

from ai_companion.graph.state import AICompanionState
from ai_companion.graph.interactive_logic import (
    InteractiveMessageDecider,
    should_send_interactive_after_response,
)
from ai_companion.graph.information_collector import InformationCollector
from ai_companion.graph.quiz_evaluator import QuizEvaluator
from ai_companion.interfaces.whatsapp.interactive_components import create_location_request
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
    """Conversation node with intelligent interactive message support and information collection."""
    current_activity = ScheduleContextGenerator.get_current_activity()
    memory_context = state.get("memory_context", "")
    user_message = state["messages"][-1].content
    is_button_response = "[Button clicked:" in user_message
    last_interactive_sent = state.get("last_interactive_sent", "")

    # Check for information collection intents
    collection_intent = InformationCollector.detect_collection_intent(user_message)

    # Handle information collection scenarios
    if collection_intent == "scheduling":
        # User wants to schedule/book something
        interactive = InformationCollector.create_date_selection_list(
            title="Schedule Session"
        )
        return {
            "messages": AIMessage(content="Let's schedule a session! When would you like to meet?"),
            "interactive_component": interactive,
            "last_interactive_sent": "date_selection"
        }

    elif collection_intent == "location":
        # Request user's location
        interactive = create_location_request(
            "Please share your location so I can help you better"
        )
        return {
            "messages": AIMessage(content="I need your location to assist you:"),
            "interactive_component": interactive,
            "last_interactive_sent": "location_request"
        }

    # Handle scheduling flow responses (most specific first)
    elif "[List selection:" in user_message and "date_" in user_message and last_interactive_sent == "date_selection":
        # User selected a date - now show time slots
        interactive = InformationCollector.create_time_slot_list()
        return {
            "messages": AIMessage(content="Great! Now choose a convenient time:"),
            "interactive_component": interactive,
            "last_interactive_sent": "time_selection"
        }

    elif "[List selection:" in user_message and any(x in user_message for x in ["Morning", "Afternoon", "Evening"]) and last_interactive_sent == "time_selection":
        # User selected a time - ask for duration
        interactive = InformationCollector.create_duration_buttons()
        return {
            "messages": AIMessage(content="How long would you like the session?"),
            "interactive_component": interactive,
            "last_interactive_sent": "duration_selection"
        }

    elif "[Button clicked:" in user_message and "duration_" in user_message and last_interactive_sent == "duration_selection":
        # User selected duration - confirm booking
        booking_details = InformationCollector.extract_booking_info(
            [msg.content for msg in state["messages"]]
        )
        interactive = InformationCollector.create_confirmation_with_details(booking_details)
        return {
            "messages": AIMessage(content="Perfect! Please confirm your booking:"),
            "interactive_component": interactive,
            "last_interactive_sent": "booking_confirmation"
        }

    elif "[Button clicked:" in user_message and "confirm_booking" in user_message and last_interactive_sent == "booking_confirmation":
        # Booking confirmed - send confirmation
        return {
            "messages": AIMessage(content="✅ Your session has been booked! You'll receive a confirmation shortly."),
            "last_interactive_sent": ""  # Reset state
        }
    elif "[Button clicked:" in user_message and "cancel_booking" in user_message and last_interactive_sent == "booking_confirmation":
        return {
            "messages": AIMessage(content="Got it — I've cancelled that booking. Let me know if you want to pick a new time."),
            "last_interactive_sent": ""  # Reset state
        }
    elif "[Location shared:" in user_message:
        return {
            "messages": AIMessage(content="Thanks for sharing your location. I'll use it to tailor the next steps for you."),
            "last_interactive_sent": ""  # Reset state
        }

    # QUIZ EVALUATION LOGIC
    # Check if this is a quiz answer response
    quiz_answer_index = QuizEvaluator.parse_quiz_response(user_message)
    user_phone = state.get("user_phone", "")  # Assuming user_phone is in state

    if quiz_answer_index is not None and QuizEvaluator.has_active_quiz(user_phone):
        # Evaluate the quiz answer
        evaluation = QuizEvaluator.evaluate_answer(user_phone, quiz_answer_index)

        if evaluation.get("error"):
            # Error occurred
            return {
                "messages": AIMessage(content=evaluation["error"]),
                "last_interactive_sent": ""
            }

        # Check if quiz is complete
        if evaluation["is_quiz_complete"]:
            # Quiz finished - send completion message with navigation
            completion_msg = QuizEvaluator.create_completion_message(evaluation)
            nav_buttons = InteractiveMessageDecider.create_lesson_navigation_buttons()

            # End the quiz session
            QuizEvaluator.end_session(user_phone)

            return {
                "messages": AIMessage(content=completion_msg),
                "interactive_component": nav_buttons,
                "last_interactive_sent": "lesson_navigation"
            }
        else:
            # Quiz continues - send feedback and next question
            feedback_msg = QuizEvaluator.create_feedback_message(evaluation)

            # Get next question
            session = QuizEvaluator.get_session(user_phone)
            if session and session.current_question:
                next_question = session.current_question

                # Create interactive buttons for next question
                quiz_buttons = InteractiveMessageDecider.create_quiz_buttons(
                    question=next_question.question,
                    options=next_question.options,
                    header=f"Question {session.progress}"
                )

                return {
                    "messages": AIMessage(content=feedback_msg),
                    "interactive_component": quiz_buttons,
                    "last_interactive_sent": "quiz_question"
                }
            else:
                # Shouldn't happen, but handle gracefully
                return {
                    "messages": AIMessage(content=feedback_msg),
                    "last_interactive_sent": ""
                }

    # Check if user message warrants immediate interactive response
    # CRITICAL: Don't detect intent on button responses - they're already handled
    intent = InteractiveMessageDecider.detect_intent(user_message) if not is_button_response else "none"

    # Handle specific intents with pre-built interactive messages
    if intent == "list" and any(word in user_message.lower() for word in ["subject", "topic", "learn"]) and last_interactive_sent != "subject_list":
        # User wants to see subjects/topics (guard: don't resend if already sent)
        interactive = InteractiveMessageDecider.create_tutoring_subject_list()
        return {
            "messages": AIMessage(content="Choose a subject to learn:"),
            "interactive_component": interactive,
            "last_interactive_sent": "subject_list"
        }

    elif intent == "binary" and last_interactive_sent != "binary_buttons":
        # User asked a yes/no question, respond with yes/no buttons
        # Guard: Don't resend if already sent
        interactive = InteractiveMessageDecider.create_binary_response(
            "Would you like me to help you?"
        )

        # Generate response
        chain = get_character_response_chain(state.get("summary", ""))
        response = await chain.ainvoke(
            {
                "messages": state["messages"],
                "current_activity": current_activity,
                "memory_context": memory_context,
            },
            config,
        )

        return {
            "messages": AIMessage(content=response),
            "interactive_component": interactive,
            "last_interactive_sent": "binary_buttons"
        }

    elif intent == "confirmation" and last_interactive_sent != "confirmation_buttons":
        # User needs to confirm something
        # Guard: Don't resend if already sent (prevents reset memory loop!)
        interactive = InteractiveMessageDecider.create_confirmation_response(
            "Please confirm to proceed:"
        )
        return {
            "messages": AIMessage(content="I need your confirmation:"),
            "interactive_component": interactive,
            "last_interactive_sent": "confirmation_buttons"
        }

    # Handle confirmation button responses (e.g., from reset memory)
    # MUST be checked BEFORE other button handlers to prevent re-triggering
    if is_button_response and last_interactive_sent == "confirmation_buttons":
        # User responded to confirmation - generate response and CLEAR state
        chain = get_character_response_chain(state.get("summary", ""))
        response = await chain.ainvoke(
            {
                "messages": state["messages"],
                "current_activity": current_activity,
                "memory_context": memory_context,
            },
            config,
        )
        # CRITICAL: Clear state to prevent loop
        return {
            "messages": AIMessage(content=response),
            "last_interactive_sent": ""  # Reset state immediately
        }

    # Handle responses to interactive messages (subject/topic flow only)
    # CRITICAL FIX: Add guards to prevent catching unrelated list selections
    elif "[List selection:" in user_message and last_interactive_sent == "subject_list" and not any(x in user_message for x in ["date_", "Morning", "Afternoon", "Evening", "time_"]):
        # User selected from subject list - offer difficulty level
        # Guard: Only trigger if we just sent a subject list
        if last_interactive_sent == "difficulty_buttons":
            # Prevent loop: Already sent difficulty buttons, don't resend
            pass
        else:
            interactive = InteractiveMessageDecider.create_difficulty_buttons()
            return {
                "messages": AIMessage(content="Great choice! What's your skill level?"),
                "interactive_component": interactive,
                "last_interactive_sent": "difficulty_buttons"
            }

    elif "[Button clicked:" in user_message and any(word in user_message.lower() for word in ["beginner", "intermediate", "advanced"]) and last_interactive_sent == "difficulty_buttons":
        # User selected difficulty - offer learning mode
        # Guard: Only trigger if we just sent difficulty buttons
        interactive = InteractiveMessageDecider.create_learning_mode_buttons()
        return {
            "messages": AIMessage(content="How would you like to learn today?"),
            "interactive_component": interactive,
            "last_interactive_sent": "learning_mode_buttons"
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
    interactive = None
    if not is_button_response:
        interactive = should_send_interactive_after_response(response)

    if interactive:
        return {
            "messages": AIMessage(content=response),
            "interactive_component": interactive,
            "last_interactive_sent": "auto_detected"  # Mark as auto-detected
        }

    return {
        "messages": AIMessage(content=response),
        "last_interactive_sent": ""  # Clear state for normal responses
    }


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

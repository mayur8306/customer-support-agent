




import os

from typing import Dict, Any

from dotenv import load_dotenv
from groq import Groq
from langdetect import detect
from deep_translator import GoogleTranslator

from backend.models import (
    ConversationState,
    NLUAnalysis,
    calculate_satisfaction_score
)

from backend.tools import (
    tool_check_order,
    tool_escalate_to_zendesk,
    knowledge_base
)

# -----------------------------
# Environment & Groq Setup
# -----------------------------

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")

client = None

if groq_api_key:
    client = Groq(api_key=groq_api_key)


# -----------------------------
# Language Processing
# -----------------------------

def process_language_pre_step(text: str, state: ConversationState) -> str:
    """Translate incoming text to English."""
    try:
        lang = detect(text)

        if str(lang).startswith("hi"):
            state.detected_language = "hi"
        else:
            state.detected_language = "en"

    except Exception:
        state.detected_language = "en"

    if state.detected_language.startswith("hi"):
        return GoogleTranslator(
            source="hi",
            target="en"
        ).translate(text)

    return text


def process_language_post_step(
    english_response: str,
    state: ConversationState
) -> str:
    """Translate response back to Hindi if needed."""

    if state.detected_language.startswith("hi") and not state.is_escalated:
        return GoogleTranslator(
            source="en",
            target="hi"
        ).translate(english_response)

    return english_response


# -----------------------------
# Fallback NLU
# -----------------------------

def mock_nlu_fallback(text: str) -> NLUAnalysis:

    text_lower = text.lower()

    intent = "general_chat"
    sentiment = "neutral"
    order_id = None

    if (
        any(
            word in text_lower
            for word in [
                "angry",
                "worst",
                "unacceptable",
                "ridiculous",
                "frustrated"
            ]
        )
        or text.isupper()
    ):
        sentiment = "angry"

    if any(
        word in text_lower
        for word in [
            "human",
            "agent",
            "manager",
            "representative"
        ]
    ):
        intent = "human_handoff"

    elif "return" in text_lower or "refund" in text_lower:
        intent = "return_policy"

    elif any(
        word in text_lower
        for word in [
            "faq",
            "warranty",
            "sell",
            "electronics",
            "shipping"
        ]
    ):
        intent = "product_faq"

    elif (
        "track" in text_lower
        or "where" in text_lower
        or "order" in text_lower
    ):
        intent = "track_order"

    if "ord1001" in text_lower:
        order_id = "ORD1001"
        intent = "track_order"

    elif "ord1002" in text_lower:
        order_id = "ORD1002"
        intent = "track_order"

    return NLUAnalysis(
        intent=intent,
        sentiment=sentiment,
        order_id=order_id,
        satisfaction_score=calculate_satisfaction_score(
            sentiment
        ),
        confidence=0.85
    )


# -----------------------------
# Fallback Response Generator
# -----------------------------

def mock_generator_fallback(
    action: str,
    data: Any
) -> str:

    if isinstance(data, dict) and "status" in data:
        return (
            f"Good news! Your order for "
            f"{data.get('item')} is currently "
            f"{data.get('status')} "
            f"(ETA: {data.get('eta')})."
        )

    elif isinstance(data, dict) and "error" in data:
        return (
            f"I'm sorry, I couldn't find "
            f"order {data.get('order_id')} in our system."
        )

    return str(data)


# -----------------------------
# NLU Agent
# -----------------------------

def run_nlu_agent(
    english_text: str
) -> NLUAnalysis:

    if not groq_api_key:
        return mock_nlu_fallback(english_text)

    system_prompt = """
You are an expert NLU extraction AI.

Analyze the user text and output strict JSON.

{
  "intent": "track_order" |
            "return_policy" |
            "product_faq" |
            "human_handoff" |
            "general_chat",

  "sentiment": "positive" |
               "neutral" |
               "angry",

  "satisfaction_score": 1|3|5,

  "confidence": 0.0-1.0,

  "order_id": "<id_or_null>"
}

Rules:
1. Use only allowed intents.
2. order_id must be null unless user explicitly provides one.
3. Messages containing angry, frustrated, upset, furious, ridiculous,
   unacceptable, terrible, worst, useless must be classified as sentiment="angry".
4. Requests for manager, human, representative or real person must be intent="human_handoff".
"""

    try:

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": english_text
                }
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        return NLUAnalysis.model_validate_json(
            response.choices[0].message.content
        )

    except Exception:
        return mock_nlu_fallback(english_text)


# -----------------------------
# Router
# -----------------------------


def customer_support_router(
    user_text: str,
    nlu_data: NLUAnalysis,
    state: ConversationState
) -> Dict[str, Any]:
    


    if nlu_data.sentiment == "angry":
        state.frustration_count += 1

    if (
        not state.is_escalated
        and (
            state.frustration_count >= 2
            or nlu_data.intent == "human_handoff"
        )
    ):

        escalation_msg = tool_escalate_to_zendesk(state)

        state.frustration_count = 0
        state.saved_order_id = None
        state.waiting_for_order_id = False

        return {
            "action": "escalate",
            "data": escalation_msg
        }

    if (
        state.waiting_for_order_id
        and nlu_data.order_id
    ):
        state.saved_order_id = nlu_data.order_id
        state.waiting_for_order_id = False
        nlu_data.intent = "track_order"

    if nlu_data.intent == "return_policy":
        return {
            "action": "provide_info",
            "data": knowledge_base["return_policy"]
        }

    elif nlu_data.intent == "product_faq":

        text_lower = user_text.lower()

        if "warranty" in text_lower:
            return {
                "action": "provide_info",
                "data": knowledge_base["warranty"]
            }

        elif "shipping" in text_lower:
            return {
                "action": "provide_info",
                "data": knowledge_base["shipping"]
            }

        return {
            "action": "provide_info",
            "data": knowledge_base["general_products"]
        }

    elif nlu_data.intent == "track_order":

        if nlu_data.order_id:
            state.saved_order_id = nlu_data.order_id
            state.waiting_for_order_id = False

        if not state.saved_order_id:
            state.waiting_for_order_id = True

            return {
                "action": "ask_slot",
                "data": "missing_order_id"
            }

        result = tool_check_order(
            state.saved_order_id
        )

        state.saved_order_id = None

        return {
            "action": "provide_info",
            "data": result
        }

    return {
        "action": "provide_info",
        "data": (
            "Hello! I am your AI support "
            "agent. How can I help?"
        )
    }


# -----------------------------
# Response Generator
# -----------------------------

def generate_customer_response(
    user_text: str,
    nlu_data: NLUAnalysis,
    router_result: dict
) -> str:

    action = router_result["action"]
    data = router_result["data"]

    if action == "escalate":
        return data

    if (
        action == "ask_slot"
        and data == "missing_order_id"
    ):
        return (
            "I can certainly help you track "
            "that. Could you please provide "
            "your Order ID (e.g., ORD1001)?"
        )

    if not groq_api_key:
        return mock_generator_fallback(
            action,
            data
        )

    prompt = f"""
You are a professional customer support agent.

Customer Message:
{user_text}

System Data:
{data}

Generate a friendly customer-support chat response.

Rules:
- Maximum 2-3 sentences.
- Do not write email greetings.
- Do not write "Best regards".
- Do not sign your name.
- Respond like a live chat agent.
"""

    try:

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        return (
            response
            .choices[0]
            .message.content
            .strip()
        )

    except Exception:

        return mock_generator_fallback(
            action,
            data
        )


# -----------------------------
# Main Pipeline
# -----------------------------

def chat_turn(
    user_input: str,
    state: ConversationState
) -> str:

    english_input = process_language_pre_step(
        user_input,
        state
    )

    nlu_data = run_nlu_agent(
        english_input
    )

    router_result = customer_support_router(
        english_input,
        nlu_data,
        state
    )

    english_response = (
        generate_customer_response(
            english_input,
            nlu_data,
            router_result
        )
    )

    final_response = (
        process_language_post_step(
            english_response,
            state
        )
    )

    state.history.append(
        {
            "user": user_input,
            "bot": final_response,
            "satisfaction_score": (
                nlu_data.satisfaction_score
            )
        }
    )

    return final_response

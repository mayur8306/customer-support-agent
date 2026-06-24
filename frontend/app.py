import sys
import os

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)

import uuid
import streamlit as st

from backend.agent import chat_turn
from backend.models import ConversationState


st.set_page_config(
    page_title="Customer Support Agent",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 Customer Support Agent")


if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_state" not in st.session_state:
    st.session_state.agent_state = ConversationState()


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


user_input = st.chat_input(
    "Type your message..."
)


if user_input:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    try:

        bot_response = chat_turn(
            user_input,
            st.session_state.agent_state
        )

    except Exception as e:

        bot_response = (
            f"Agent Error: {str(e)}"
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": bot_response
        }
    )

    with st.chat_message("assistant"):
        st.markdown(bot_response)
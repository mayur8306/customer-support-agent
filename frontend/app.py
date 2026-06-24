import uuid
import requests
import streamlit as st


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

        response = requests.post(
            "http://backend:8000/chat",
            json={
                "session_id": st.session_state.session_id,
                "message": user_input
            }
        )

        bot_response = response.json()["response"]

    except Exception as e:

        bot_response = (
            f"Backend connection error: {e}"
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": bot_response
        }
    )

    with st.chat_message("assistant"):
        st.markdown(bot_response)



from fastapi import FastAPI
from pydantic import BaseModel

from backend.agent import chat_turn
from backend.models import ConversationState

from fastapi.responses import StreamingResponse
import asyncio


async def fake_stream(text: str):
    words = text.split()

    for word in words:
        yield word + " "
        await asyncio.sleep(0.03)


app = FastAPI(
    title="Customer Support Agent API"
)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store conversation sessions
sessions = {}


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.get("/")
def home():
    return {
        "status": "running",
        "service": "customer-support-agent"
    }


@app.post("/chat")
def chat(request: ChatRequest):

    if request.session_id not in sessions:
        sessions[request.session_id] = ConversationState()

    state = sessions[request.session_id]

    response = chat_turn(
        request.message,
        state
    )

    return {
        "response": response   
    }

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):

    if request.session_id not in sessions:
        sessions[request.session_id] = ConversationState()

    state = sessions[request.session_id]

    response_text = chat_turn(
        request.message,
        state
    )

    return StreamingResponse(
        fake_stream(response_text),
        media_type="text/plain"
    )
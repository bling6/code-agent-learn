import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.agent import Agent
from agents.utils.Memory import memory_manager
from agents.utils.watch_skill import run_watch_skill, stop_watch_skill
from service.session import session_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    memory_manager.load_all()
    run_watch_skill()
    yield
    stop_watch_skill()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response Models ---


class CreateSessionResponse(BaseModel):
    session_id: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    run_id: str


class EventItem(BaseModel):
    type: str
    data: dict


class EventResponse(BaseModel):
    events: list[EventItem]
    run_status: str


class MessageItem(BaseModel):
    role: str
    content: str | None = None


class HistoryResponse(BaseModel):
    messages: list[MessageItem]


# --- Endpoints ---


@app.post("/api/sessions", response_model=CreateSessionResponse)
def create_session():
    session = session_manager.create_session()
    return CreateSessionResponse(session_id=session.session_id)


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    session = session_manager.get_session(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if session.active_run_id:
        active_run = session_manager.get_run(session.active_run_id)
        if active_run and active_run.status == "running":
            raise HTTPException(409, "Agent is already running")

    session.messages.append({"role": "user", "content": req.message})
    session.output_handler.clear()
    run = session_manager.create_run(session)

    def run_agent():
        try:
            agent = Agent(
                messages=session.messages,
                permission=session.permission,
                output_handler=session.output_handler,
            )
            agent.run()
            run.status = "completed"
        except Exception as e:
            run.status = "error"
            run.error = str(e)
            session.output_handler.error(str(e))
        finally:
            session.active_run_id = None

    thread = threading.Thread(target=run_agent, daemon=True)
    thread.start()
    return ChatResponse(run_id=run.run_id)


@app.get("/api/runs/{run_id}/events", response_model=EventResponse)
def get_run_events(run_id: str, after: int = 0):
    run = session_manager.get_run(run_id)
    if not run:
        raise HTTPException(404, "Run not found")

    all_events = run.session.output_handler.events
    new_events = all_events[after:]
    events_data = [EventItem(type=e.type, data=e.data) for e in new_events]
    return EventResponse(events=events_data, run_status=run.status)


@app.get("/api/sessions/{session_id}/history", response_model=HistoryResponse)
def get_history(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    msgs = []
    for m in session.messages:
        if m["role"] in ("user", "assistant") and m.get("content"):
            msgs.append(MessageItem(role=m["role"], content=m["content"]))
    return HistoryResponse(messages=msgs)


@app.post("/api/sessions/{session_id}/clear")
def clear_session(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    session.messages = [{"role": "system", "content": ""}]
    session.output_handler.clear()
    return {"status": "cleared"}

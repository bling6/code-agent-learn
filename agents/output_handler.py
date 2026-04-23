from dataclasses import dataclass, field
import threading


@dataclass
class AgentEvent:
    type: str  # thinking, reasoning, tool_call, tool_result, response, error, permission_denied
    data: dict = field(default_factory=dict)


class OutputHandler:
    def emit(self, event: AgentEvent):
        pass

    def thinking(self, agent_name: str = ""):
        self.emit(AgentEvent("thinking", {"agent_name": agent_name}))

    def reasoning(self, content: str):
        self.emit(AgentEvent("reasoning", {"content": content}))

    def tool_call(self, tool_name: str, args: dict):
        self.emit(AgentEvent("tool_call", {"tool_name": tool_name, "args": args}))

    def tool_result(self, tool_name: str, result: str, truncated: bool = False):
        self.emit(AgentEvent("tool_result", {
            "tool_name": tool_name, "result": result, "truncated": truncated,
        }))

    def permission_denied(self, tool_name: str, reason: str):
        self.emit(AgentEvent("permission_denied", {"tool_name": tool_name, "reason": reason}))

    def response(self, content: str):
        self.emit(AgentEvent("response", {"content": content}))

    def error(self, message: str):
        self.emit(AgentEvent("error", {"message": message}))


class CliOutputHandler(OutputHandler):
    def emit(self, event: AgentEvent):
        if event.type == "thinking":
            name = event.data.get("agent_name", "")
            label = f"({name})" if name else ""
            print(f"\033[92m思考中...{label}\033[0m")
        elif event.type == "reasoning":
            print("\033[94m思考内容: \033[0m")
            print(f"\033[90m {event.data['content']}\033[0m")
        elif event.type == "tool_call":
            name = event.data.get("agent_name", "")
            prefix = f"{name}🛠️ " if name else ""
            print(f"\n\033[33m{prefix}[调用工具] {event.data['tool_name']}\033[0m")
            print(f"\033[90m   参数:  \033[0m{event.data['args']}")
        elif event.type == "tool_result":
            print("\033[32m 执行结果:\033[0m")
            print(f"\033[32m{event.data['result']}\033[0m")
        elif event.type == "permission_denied":
            print("\033[32m 执行结果:\033[0m")
            print(f"\033[32m{event.data['reason']}\033[0m")
        elif event.type == "response":
            print(event.data["content"])
            print()
        elif event.type == "error":
            print(f"\033[91m[错误] {event.data['message']}\033[0m")


class ServiceOutputHandler(OutputHandler):
    def __init__(self):
        self.events: list[AgentEvent] = []
        self._subscribers: list[threading.Event] = []
        self._done = threading.Event()

    def emit(self, event: AgentEvent):
        self.events.append(event)
        # Wake up all SSE listeners waiting for new events
        for notify in self._subscribers:
            notify.set()

        # Mark done on terminal events
        if event.type in ("response", "error"):
            self._done.set()
            for notify in self._subscribers:
                notify.set()

    def clear(self):
        self.events.clear()
        self._subscribers.clear()
        self._done.clear()

    def subscribe(self) -> threading.Event:
        notify = threading.Event()
        self._subscribers.append(notify)
        return notify

    def unsubscribe(self, notify: threading.Event):
        if notify in self._subscribers:
            self._subscribers.remove(notify)

    def is_done(self) -> bool:
        return self._done.is_set()

    def wait_for_event(self, notify: threading.Event, timeout: float = 30.0) -> bool:
        return notify.wait(timeout=timeout)

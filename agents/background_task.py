import threading
import uuid
import time
from pathlib import Path
import json
import subprocess

WORKDIR = Path.cwd()

RUNTIME_DIR = WORKDIR / ".runtime-tasks"
RUNTIME_DIR.mkdir(exist_ok=True)

STALL_THRESHOLD_S = 60


class BackgroundManager:
    def __init__(self):
        self.dir = RUNTIME_DIR
        self.tasks = {}
        self._notification_queue = []
        self._lock = threading.Lock()

    def _output_path(self, task_id: str) -> Path:
        return self.dir / f"{task_id}.log"

    def _record_path(self, task_id: str) -> Path:
        return self.dir / f"{task_id}.json"

    def _persist_task(self, task_id: str):
        record = dict(self.tasks[task_id])
        self._record_path(task_id).write_text(
            json.dumps(record, indent=2, ensure_ascii=False)
        )

    def _preview(self, output: str, limit: int = 500) -> str:
        compact = " ".join((output or "(no output)").split())
        return compact[:limit]

    def run(self, command: str) -> str:
        # 启动一个后台线程执行命令
        task_id = str(uuid.uuid4())[:8]
        output_file = self._output_path(task_id)
        self.tasks[task_id] = {
            "id": task_id,
            "status": "running",
            "result": None,
            "command": command,
            "started_at": time.time(),
            "finished_at": None,
            "result_preview": "",
            "output_file": str(output_file.relative_to(WORKDIR)),
        }
        self._persist_task(task_id)
        thread = threading.Thread(
            target=self._execute, args=(task_id, command), daemon=True
        )
        thread.start()
        return (
            f"Background task {task_id} started: {command[:80]} "
            f"(output_file={output_file.relative_to(WORKDIR)})"
        )

    def _execute(self, task_id: str, command: str):
        """Thread target: 运行子进程, 捕获输出并推送至队列."""
        try:
            r = subprocess.run(
                command,
                shell=True,
                cwd=WORKDIR,
                capture_output=True,
                text=True,
                timeout=300,
            )
            output = (r.stdout + r.stderr).strip()[:50000]
            status = "completed"
        except subprocess.TimeoutExpired:
            output = "Error: Timeout (300s)"
            status = "timeout"
        except Exception as e:
            output = f"Error: {e}"
            status = "error"
        final_output = output or "(no output)"
        preview = self._preview(final_output)
        output_path = self._output_path(task_id)
        output_path.write_text(final_output)
        self.tasks[task_id]["status"] = status
        self.tasks[task_id]["result"] = final_output
        self.tasks[task_id]["finished_at"] = time.time()
        self.tasks[task_id]["result_preview"] = preview
        self._persist_task(task_id)
        with self._lock:
            self._notification_queue.append(
                {
                    "task_id": task_id,
                    "status": status,
                    "command": command[:80],
                    "preview": preview,
                    "output_file": str(output_path.relative_to(WORKDIR)),
                }
            )

    def check(self, task_id: str = None) -> str:
        """检查任务状态"""
        if task_id:
            t = self.tasks.get(task_id)
            if not t:
                return "Task not found"
            value = {
                "id": t["id"],
                "status": t["status"],
                "command": t["command"],
                "result_preview": t.get("result_preview", ""),
                "output_file": t.get("output_file", ""),
            }
            return json.dumps(value, indent=2, ensure_ascii=False)
        lines = []
        for tid, t in self.tasks.items():
            lines.append(
                f"{tid}: [{t['status']}] {t['command'][:60]} "
                f"-> {t.get('result_preview') or '(running)'}"
            )
        return "\n".join(lines) if lines else "无后台任务"

    def drain_notifications(self) -> list:
        """Return and clear all pending completion notifications."""
        with self._lock:
            notifies = list(self._notification_queue)
            self._notification_queue.clear()
        return notifies

    def detect_stalled(self) -> list[str]:
        """
        Return task IDs that have been running longer than STALL_THRESHOLD_S.
        """
        now = time.time()
        stalled = []
        for task_id, t in self.tasks.items():
            if t["status"] != "running":
                continue
            elapsed = now - t.get("started_at", now)
            if elapsed > STALL_THRESHOLD_S:
                stalled.append(task_id)
        return stalled


bgManager = BackgroundManager()

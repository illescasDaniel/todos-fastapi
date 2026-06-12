import json
import os
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from todos_mcp.config import Settings

_host_process: subprocess.Popen[bytes] | None = None

_SCRIPT_TIMEOUT_SECONDS = 600


@dataclass(frozen=True, slots=True)
class ScriptResult:
    ok: bool
    stdout: str
    stderr: str
    exit_code: int
    extra: dict[str, Any] | None = None

    def to_json(self) -> str:
        payload: dict[str, Any] = {
            "ok": self.ok,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
        }
        if self.extra:
            payload.update(self.extra)
        return json.dumps(payload, indent=2)


def _resolve_script(settings: Settings, relative_path: str) -> Path:
    script_path = (settings.repo_root / relative_path).resolve()
    repo_root = settings.repo_root.resolve()
    if not script_path.is_relative_to(repo_root):
        raise ValueError(f"Script path escapes repo root: {relative_path}")
    if not script_path.is_file():
        raise FileNotFoundError(f"Script not found: {script_path}")
    return script_path


def run_script(
    settings: Settings,
    relative_path: str,
    *args: str,
    timeout: int = _SCRIPT_TIMEOUT_SECONDS,
) -> ScriptResult:
    script_path = _resolve_script(settings, relative_path)
    result = subprocess.run(
        ["bash", str(script_path), *args],
        cwd=settings.repo_root,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return ScriptResult(
        ok=result.returncode == 0,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.returncode,
    )


def start_host_background(settings: Settings, mode: str = "dev") -> ScriptResult:
    global _host_process

    if _host_process is not None and _host_process.poll() is None:
        return ScriptResult(
            ok=False,
            stdout="",
            stderr="Host server already running via MCP.",
            exit_code=1,
            extra={"pid": _host_process.pid},
        )

    script_path = _resolve_script(settings, "scripts/start.sh")
    args = [str(script_path)]
    if mode == "pro":
        args.append("pro")

    env = os.environ.copy()
    _host_process = subprocess.Popen(
        ["bash", *args],
        cwd=settings.repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
        env=env,
    )
    return ScriptResult(
        ok=True,
        stdout=f"Started host API in background (mode={mode}).",
        stderr="",
        exit_code=0,
        extra={"pid": _host_process.pid},
    )


def stop_host_background() -> ScriptResult:
    global _host_process

    if _host_process is None or _host_process.poll() is not None:
        _host_process = None
        return ScriptResult(
            ok=False,
            stdout="",
            stderr="No MCP-spawned host server is running.",
            exit_code=1,
        )

    pid = _host_process.pid
    try:
        os.killpg(_host_process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    _host_process.wait(timeout=15)
    _host_process = None
    return ScriptResult(
        ok=True,
        stdout=f"Stopped host API (pid={pid}).",
        stderr="",
        exit_code=0,
        extra={"pid": pid},
    )


def stack_health_curl(settings: Settings) -> ScriptResult:
    result = subprocess.run(
        ["curl", "-sf", settings.health_url],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return ScriptResult(
        ok=result.returncode == 0,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.returncode,
    )

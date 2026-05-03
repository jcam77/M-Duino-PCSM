from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
from urllib import error as urllib_error
from urllib import request as urllib_request

from flask import Flask, jsonify, request

ROOT = Path(__file__).resolve().parent.parent
FIRMWARE_ROOT = ROOT / "M-DuinoScripts"
RESEARCH_ROOTS = [ROOT / "Documentation", FIRMWARE_ROOT]
OLLAMA_CANDIDATES = [
    "http://10.211.55.2:11434",
    "http://127.0.0.1:11434",
    "http://localhost:11434",
]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mduino_pcsm.service_registry import create_services  # noqa: E402
from mduino_pcsm.models import ControllerSnapshot, PARAMETER_DEFINITIONS  # noqa: E402
from mduino_pcsm.services.base import ControllerService  # noqa: E402


app = Flask(__name__)

SERVICES: dict[str, ControllerService] = create_services()


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat()


def _serialize_snapshot(snapshot: ControllerSnapshot) -> dict:
    status = asdict(snapshot.status)
    status["last_state_change"] = _serialize_datetime(snapshot.status.last_state_change)
    events = [
        {
            "timestamp": _serialize_datetime(entry.timestamp),
            "message": entry.message,
        }
        for entry in snapshot.events
    ]
    return {
        "status": status,
        "parameters": snapshot.parameters,
        "events": events,
    }


def _serialize_parameter_definitions() -> list[dict]:
    return [
        {
            "protocol_name": definition.protocol_name,
            "label": definition.label,
            "ui_unit": definition.ui_unit,
            "kind": definition.kind,
            "default": definition.raw_to_display(definition.default),
            "help_text": definition.help_text,
            "step": definition.step,
        }
        for definition in PARAMETER_DEFINITIONS
    ]


def _service_from_request() -> tuple[str, ControllerService]:
    backend = request.args.get("backend")
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        backend = payload.get("backend", backend)
    backend = backend or "Mock controller"
    service = SERVICES.get(backend)
    if service is None:
        raise KeyError(backend)
    return backend, service


def _bootstrap_payload(backend_name: str, service: ControllerService) -> dict:
    return {
        "backend": backend_name,
        "backends": list(SERVICES.keys()),
        "ports": service.list_available_ports(),
        "parameterDefinitions": _serialize_parameter_definitions(),
        "snapshot": _serialize_snapshot(service.refresh()),
    }


def _firmware_files() -> list[Path]:
    if not FIRMWARE_ROOT.exists():
        return []
    return sorted(FIRMWARE_ROOT.rglob("*.ino"))


def _research_files() -> list[Path]:
    patterns = ("*.md", "*.ino", "*.txt")
    files: list[Path] = []
    for base in RESEARCH_ROOTS:
        if not base.exists():
            continue
        for pattern in patterns:
            files.extend(base.rglob(pattern))
    return sorted({path.resolve() for path in files})


def _query_terms(text: str) -> list[str]:
    raw_terms = re.findall(r"[A-Za-z0-9_]{3,}", text.lower())
    stop_words = {
        "the", "and", "for", "with", "that", "this", "from", "into", "what",
        "when", "where", "which", "about", "would", "could", "should", "have",
        "there", "their", "they", "them", "then", "than", "your", "while",
        "does", "how", "why", "into", "also", "been", "were", "will",
    }
    seen: list[str] = []
    for term in raw_terms:
        if term in stop_words or term in seen:
            continue
        seen.append(term)
    return seen


def _extract_snippets(content: str, terms: list[str], limit: int = 3) -> list[str]:
    if not content.strip():
        return []

    lines = [line.strip() for line in content.splitlines()]
    scored: list[tuple[int, str]] = []
    for line in lines:
        if len(line) < 8:
            continue
        lower = line.lower()
        score = sum(lower.count(term) for term in terms)
        if score > 0:
            scored.append((score, line))

    if not scored:
        fallback = [line for line in lines if line][:limit]
        return fallback

    scored.sort(key=lambda item: (-item[0], len(item[1])))
    snippets: list[str] = []
    for _, line in scored:
        if line not in snippets:
            snippets.append(line)
        if len(snippets) >= limit:
            break
    return snippets


def _research_response(question: str) -> dict:
    terms = _query_terms(question)
    results: list[dict] = []

    for path in _research_files():
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lower = content.lower()
        score = sum(lower.count(term) for term in terms)
        if score <= 0 and terms:
            continue

        snippets = _extract_snippets(content, terms or ["controller"], limit=3)
        if not snippets:
            continue

        relative = str(path.relative_to(ROOT)).replace("\\", "/")
        results.append(
            {
                "path": relative,
                "score": score if terms else 1,
                "snippets": snippets,
            }
        )

    results.sort(key=lambda item: (-item["score"], item["path"]))
    top_results = results[:4]

    if not top_results:
        return {
            "answer": "I could not find a strong local match for that question in the current documentation or firmware files. Try asking with parameter names, file versions, or controller terms such as HOTWIRE_US, SPARK_US, DAQ_US, mode, trigger, or firmware version.",
            "sources": [],
        }

    answer_lines = [
        "Here are the most relevant local notes I found for that question:",
    ]
    for item in top_results:
        answer_lines.append(f"- {item['path']}: {item['snippets'][0]}")
    answer_lines.append("Use the source list below to inspect the exact document or firmware file in more detail.")

    return {
        "answer": "\n".join(answer_lines),
        "sources": top_results,
    }


def _ollama_host_candidates() -> list[str]:
    explicit = os.environ.get("OLLAMA_HOST", "").strip()
    candidates: list[str] = []
    if explicit:
        candidates.append(explicit.rstrip("/"))
    for candidate in OLLAMA_CANDIDATES:
        if candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _ollama_request(method: str, url: str, payload: dict | None = None, timeout: float = 2.5) -> dict | list:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib_request.Request(url, data=data, headers=headers, method=method)
    with urllib_request.urlopen(req, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def _resolve_ollama_host() -> str | None:
    for host in _ollama_host_candidates():
        try:
            _ollama_request("GET", f"{host}/api/tags", timeout=1.5)
            return host
        except (urllib_error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            continue
    return None


def _ollama_models(host: str | None) -> list[str]:
    if not host:
        return []
    try:
        payload = _ollama_request("GET", f"{host}/api/tags", timeout=2.5)
    except (urllib_error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return []

    models = payload.get("models", []) if isinstance(payload, dict) else []
    names = [item.get("name", "") for item in models if isinstance(item, dict) and item.get("name")]
    return names


def _build_aira_context(question: str, sources: list[dict]) -> str:
    context_blocks = []
    for source in sources[:4]:
        snippets = "\n".join(f"- {snippet}" for snippet in source.get("snippets", [])[:3])
        context_blocks.append(f"Source: {source['path']}\n{snippets}")
    if not context_blocks:
        return f"Question: {question}"
    return "\n\n".join(context_blocks)


def _ollama_answer(question: str, sources: list[dict], model: str | None = None) -> dict | None:
    host = _resolve_ollama_host()
    if not host:
        return None

    models = _ollama_models(host)
    selected_model = model or os.environ.get("OLLAMA_MODEL", "").strip() or (models[0] if models else "")
    if not selected_model:
        return None

    prompt = (
        "You are AiRA, a research assistant for the M-Duino PCSM project.\n"
        "Answer using only the provided local repository context.\n"
        "Be concise, practical, and explicit when you are uncertain.\n\n"
        f"User question:\n{question}\n\n"
        f"Local context:\n{_build_aira_context(question, sources)}"
    )

    try:
        payload = _ollama_request(
            "POST",
            f"{host}/api/generate",
            {
                "model": selected_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=30.0,
        )
    except (urllib_error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None

    answer = str(payload.get("response", "")).strip()
    if not answer:
        return None

    return {
        "mode": "ollama",
        "host": host,
        "model": selected_model,
        "answer": answer,
    }


@app.after_request
def _cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify(
        {
            "ok": True,
            "app": "mduino-pcsm",
            "frontend": "EXDA-derived shell",
        }
    )


@app.route("/api/controller/bootstrap", methods=["GET"])
def controller_bootstrap():
    try:
        backend_name, service = _service_from_request()
    except KeyError as exc:
        return jsonify({"ok": False, "message": f"Unknown backend: {exc.args[0]}"}), 404
    return jsonify({"ok": True, **_bootstrap_payload(backend_name, service)})


@app.route("/api/controller/snapshot", methods=["GET"])
def controller_snapshot():
    try:
        backend_name, service = _service_from_request()
    except KeyError as exc:
        return jsonify({"ok": False, "message": f"Unknown backend: {exc.args[0]}"}), 404
    return jsonify(
        {
            "ok": True,
            "backend": backend_name,
            "ports": service.list_available_ports(),
            "snapshot": _serialize_snapshot(service.refresh()),
        }
    )


@app.route("/api/controller/connect", methods=["POST"])
def controller_connect():
    try:
        backend_name, service = _service_from_request()
    except KeyError as exc:
        return jsonify({"ok": False, "message": f"Unknown backend: {exc.args[0]}"}), 404
    payload = request.get_json(silent=True) or {}
    result = service.connect(payload.get("port"))
    return jsonify(
        {
            "ok": result.success,
            "message": result.message,
            **_bootstrap_payload(backend_name, service),
        }
    )


@app.route("/api/controller/disconnect", methods=["POST"])
def controller_disconnect():
    try:
        backend_name, service = _service_from_request()
    except KeyError as exc:
        return jsonify({"ok": False, "message": f"Unknown backend: {exc.args[0]}"}), 404
    result = service.disconnect()
    return jsonify(
        {
            "ok": result.success,
            "message": result.message,
            **_bootstrap_payload(backend_name, service),
        }
    )


@app.route("/api/controller/ports", methods=["GET"])
def controller_ports():
    try:
        backend_name, service = _service_from_request()
    except KeyError as exc:
        return jsonify({"ok": False, "message": f"Unknown backend: {exc.args[0]}"}), 404
    return jsonify({"ok": True, "backend": backend_name, "ports": service.list_available_ports()})


@app.route("/api/controller/parameters", methods=["POST"])
def controller_parameters():
    try:
        backend_name, service = _service_from_request()
    except KeyError as exc:
        return jsonify({"ok": False, "message": f"Unknown backend: {exc.args[0]}"}), 404
    payload = request.get_json(silent=True) or {}
    values: dict[str, object] = payload.get("values", {})
    messages: list[str] = []
    ok = True
    for definition in PARAMETER_DEFINITIONS:
        if definition.protocol_name not in values:
            continue
        raw_value = definition.display_to_raw(values[definition.protocol_name])
        result = service.set_parameter(definition.protocol_name, raw_value)
        messages.append(f"{definition.protocol_name}: {result.message}")
        if not result.success:
            ok = False
            break
    return jsonify(
        {
            "ok": ok,
            "message": " | ".join(messages) if messages else "No parameter updates submitted.",
            **_bootstrap_payload(backend_name, service),
        }
    )


@app.route("/api/controller/demo", methods=["POST"])
def controller_demo():
    try:
        backend_name, service = _service_from_request()
    except KeyError as exc:
        return jsonify({"ok": False, "message": f"Unknown backend: {exc.args[0]}"}), 404
    if not hasattr(service, "run_demo_transition"):
        return jsonify(
            {
                "ok": False,
                "message": "Demo transitions are only available on the mock backend.",
                **_bootstrap_payload(backend_name, service),
            }
        )
    result = service.run_demo_transition()
    return jsonify(
        {
            "ok": result.success,
            "message": result.message,
            **_bootstrap_payload(backend_name, service),
        }
    )


@app.route("/api/firmware/scripts", methods=["GET"])
def firmware_scripts():
    scripts = [
        {
            "name": path.name,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        }
        for path in _firmware_files()
    ]
    return jsonify({"ok": True, "scripts": scripts})


@app.route("/api/firmware/script", methods=["GET"])
def firmware_script():
    requested_path = request.args.get("path", "").strip()
    if not requested_path:
        return jsonify({"ok": False, "message": "Missing script path."}), 400

    target = (ROOT / requested_path).resolve()
    try:
        target.relative_to(FIRMWARE_ROOT.resolve())
    except ValueError:
        return jsonify({"ok": False, "message": "Script path is outside M-DuinoScripts."}), 400

    if not target.exists() or not target.is_file():
        return jsonify({"ok": False, "message": "Firmware script not found."}), 404

    return jsonify(
        {
            "ok": True,
            "path": str(target.relative_to(ROOT)).replace("\\", "/"),
            "content": target.read_text(encoding="utf-8", errors="replace"),
        }
    )


@app.route("/api/aira/context", methods=["GET"])
def aira_context():
    files = [
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in _research_files()
    ]
    host = _resolve_ollama_host()
    models = _ollama_models(host)
    return jsonify(
        {
            "ok": True,
            "files": files,
            "aiStatus": "online" if host and models else "local",
            "ollamaHost": host,
            "models": models,
        }
    )


@app.route("/api/aira/query", methods=["POST"])
def aira_query():
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip()
    if not question:
        return jsonify({"ok": False, "message": "Please enter a question for AiRA."}), 400

    local_response = _research_response(question)
    ollama_response = _ollama_answer(question, local_response["sources"], payload.get("model"))
    if ollama_response:
        return jsonify(
            {
                "ok": True,
                "answer": ollama_response["answer"],
                "sources": local_response["sources"],
                "mode": ollama_response["mode"],
                "model": ollama_response["model"],
                "ollamaHost": ollama_response["host"],
            }
        )

    return jsonify({"ok": True, **local_response, "mode": "local", "model": None, "ollamaHost": None})


if __name__ == "__main__":
    host = os.environ.get("MDUINO_BACKEND_HOST", "127.0.0.1")
    port = int(os.environ.get("MDUINO_BACKEND_PORT", "5001"))
    debug = os.environ.get("MDUINO_BACKEND_DEBUG", "1") not in {"0", "false", "False"}
    app.run(host=host, port=port, debug=debug)
